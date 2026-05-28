"""
OpenMail Platform - User Endpoints
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password, hash_password
from app.db.database import get_db
from app.models.user import User
from app.api.v1.endpoints.auth import get_current_user
from app.schemas.user import (
    UserResponse,
    UserUpdate,
    PasswordChange,
    UserSettings
)
from app.schemas.auth import MessageResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get current user profile."""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_data: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile."""
    update_data = user_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    await db.commit()
    await db.refresh(current_user)
    
    return UserResponse.model_validate(current_user)


@router.put("/me/password", response_model=MessageResponse)
async def change_password(
    password_data: PasswordChange,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Change current user password."""
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    current_user.password_hash = hash_password(password_data.new_password)
    await db.commit()
    
    return MessageResponse(
        message="Password changed successfully",
        success=True
    )


@router.put("/me/settings", response_model=UserResponse)
async def update_user_settings(
    settings_data: UserSettings,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Update user settings."""
    current_user.settings = {
        **current_user.settings,
        **settings_data.model_dump(exclude_unset=True)
    }
    await db.commit()
    await db.refresh(current_user)
    
    return UserResponse.model_validate(current_user)


@router.put("/me/avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: AsyncSession = Depends(get_db)
):
    """Upload user avatar."""
    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png", "image/gif"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only JPEG, PNG, and GIF are allowed."
        )
    
    # Validate file size (max 5MB)
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 5MB."
        )
    
    # Upload to MinIO
    import io
    import uuid
    from minio import Minio
    from minio.error import S3Error
    from app.core.config import settings

    ext = (file.filename or "avatar").rsplit(".", 1)[-1].lower()
    object_name = f"avatars/{current_user.id}/{uuid.uuid4()}.{ext}"
    bucket = "avatars"

    try:
        minio_client = Minio(
            settings.S3_ENDPOINT,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            secure=settings.S3_USE_SSL,
        )
        # Ensure bucket exists
        if not minio_client.bucket_exists(bucket):
            minio_client.make_bucket(bucket)

        minio_client.put_object(
            bucket,
            object_name,
            io.BytesIO(content),
            length=len(content),
            content_type=file.content_type,
        )

        # Build public URL (served via nginx proxy or direct MinIO)
        avatar_url = f"/api/v1/users/avatars/{current_user.id}/{object_name.split('/')[-1]}"
        current_user.avatar_url = avatar_url
        await db.commit()
        await db.refresh(current_user)

    except S3Error as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Storage service error: {exc}",
        )

    return UserResponse.model_validate(current_user)
