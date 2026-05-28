"""
OpenMail Platform - Attachment Endpoints
"""
import io
import uuid
import hashlib
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import get_db
from app.models.user import User
from app.models.email import Attachment
from app.api.v1.endpoints.auth import get_current_user
from app.schemas.email import AttachmentUploadResponse

router = APIRouter()


def _get_minio():
    from minio import Minio
    return Minio(
        settings.S3_ENDPOINT,
        access_key=settings.S3_ACCESS_KEY,
        secret_key=settings.S3_SECRET_KEY,
        secure=settings.S3_USE_SSL,
    )


@router.post("/upload", response_model=AttachmentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    file: UploadFile = File(...),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Upload an attachment to MinIO before sending.
    Returns an attachment ID that can be referenced in EmailCreate.attachments[].
    """
    # Validate content type
    if file.content_type not in settings.ALLOWED_ATTACHMENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{file.content_type}' is not allowed.",
        )

    content = await file.read()

    # Validate size
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB limit.",
        )

    # Compute checksums
    md5 = hashlib.md5(content).hexdigest()
    sha256 = hashlib.sha256(content).hexdigest()

    # Store in MinIO
    bucket = settings.S3_BUCKET_ATTACHMENTS
    object_name = f"uploads/{current_user.id}/{uuid.uuid4()}/{file.filename}"

    try:
        client = _get_minio()
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
        client.put_object(
            bucket,
            object_name,
            io.BytesIO(content),
            length=len(content),
            content_type=file.content_type or "application/octet-stream",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Storage error: {exc}",
        )

    # Persist metadata (email_id is null until the email is sent)
    attachment = Attachment(
        id=uuid.uuid4(),
        email_id=None,          # linked when email is created
        filename=file.filename or "attachment",
        content_type=file.content_type,
        size_bytes=len(content),
        storage_path=object_name,
        storage_bucket=bucket,
        checksum_md5=md5,
        checksum_sha256=sha256,
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)

    return AttachmentUploadResponse(
        id=attachment.id,
        filename=attachment.filename,
        content_type=attachment.content_type,
        size_bytes=attachment.size_bytes,
    )


@router.get("/{attachment_id}/download")
async def download_attachment(
    attachment_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Download an attachment from MinIO."""
    result = await db.execute(
        select(Attachment).where(Attachment.id == attachment_id)
    )
    attachment = result.scalar_one_or_none()
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")

    try:
        client = _get_minio()
        response = client.get_object(attachment.storage_bucket, attachment.storage_path)
        data = response.read()
        response.close()
        response.release_conn()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Storage error: {exc}",
        )

    return StreamingResponse(
        io.BytesIO(data),
        media_type=attachment.content_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{attachment.filename}"',
            "Content-Length": str(attachment.size_bytes),
        },
    )
