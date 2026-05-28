"""
OpenMail Platform - Email Endpoints
"""
from typing import Annotated, Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.db.database import get_db
from app.models.user import User
from app.models.email import Email, Folder, Label, Attachment
from app.models.domain import Mailbox
from app.api.v1.endpoints.auth import get_current_user
from app.schemas.email import (
    EmailCreate,
    EmailUpdate,
    EmailReply,
    EmailForward,
    EmailBulkAction,
    EmailListItem,
    EmailDetail,
    EmailSendResponse
)
from app.schemas.auth import MessageResponse

router = APIRouter()


@router.get("", response_model=List[EmailListItem])
async def list_emails(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    mailbox_id: Optional[UUID] = None,
    folder: Optional[str] = "inbox",
    folder_id: Optional[UUID] = None,
    label_id: Optional[UUID] = None,
    is_read: Optional[bool] = None,
    is_starred: Optional[bool] = None,
    q: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    sort: str = "date",
    order: str = "desc"
):
    """List emails with filters."""
    # Get user's mailboxes
    result = await db.execute(
        select(Mailbox.id).where(Mailbox.user_id == current_user.id)
    )
    mailbox_ids = [row[0] for row in result.fetchall()]
    
    if not mailbox_ids:
        return []
    
    # Build query
    query = select(Email).where(
        Email.mailbox_id.in_(mailbox_ids),
        Email.deleted_at.is_(None)
    )
    
    # Apply mailbox filter
    if mailbox_id:
        query = query.where(Email.mailbox_id == mailbox_id)
    
    # Apply folder filter
    if folder_id:
        query = query.where(Email.folder_id == folder_id)
    elif folder:
        folder_result = await db.execute(
            select(Folder.id).where(
                Folder.mailbox_id.in_(mailbox_ids),
                Folder.type == folder
            )
        )
        folder_ids = [row[0] for row in folder_result.fetchall()]
        if folder_ids:
            query = query.where(Email.folder_id.in_(folder_ids))
    
    # Apply label filter
    if label_id:
        query = query.join(Email.labels).where(Label.id == label_id)
    
    # Apply read/starred filters
    if is_read is not None:
        query = query.where(Email.is_read == is_read)
    if is_starred is not None:
        query = query.where(Email.is_starred == is_starred)
    
    # Apply date filters
    if date_from:
        query = query.where(Email.date >= date_from)
    if date_to:
        query = query.where(Email.date <= date_to)
    
    # Apply search
    if q:
        search_term = f"%{q}%"
        query = query.where(
            or_(
                Email.subject.ilike(search_term),
                Email.body_text.ilike(search_term),
                Email.from_address.ilike(search_term)
            )
        )
    
    # Apply sorting
    sort_column = getattr(Email, sort, Email.date)
    if order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    
    # Include relationships
    query = query.options(
        selectinload(Email.labels),
        selectinload(Email.folder),
        selectinload(Email.attachments)
    )
    
    result = await db.execute(query)
    emails = result.scalars().all()
    
    return [
        EmailListItem(
            id=email.id,
            thread_id=email.thread_id,
            from_address=email.from_address,
            from_name=email.from_name,
            to_addresses=email.to_addresses,
            subject=email.subject,
            snippet=email.snippet,
            date=email.date,
            is_read=email.is_read,
            is_starred=email.is_starred,
            has_attachments=len(email.attachments) > 0,
            attachment_count=len(email.attachments),
            labels=email.labels,
            folder=email.folder
        )
        for email in emails
    ]


@router.get("/{email_id}", response_model=EmailDetail)
async def get_email(
    email_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Get single email with full details."""
    # Get user's mailboxes
    result = await db.execute(
        select(Mailbox.id).where(Mailbox.user_id == current_user.id)
    )
    mailbox_ids = [row[0] for row in result.fetchall()]
    
    # Get email
    result = await db.execute(
        select(Email)
        .where(
            Email.id == email_id,
            Email.mailbox_id.in_(mailbox_ids)
        )
        .options(
            selectinload(Email.labels),
            selectinload(Email.folder),
            selectinload(Email.attachments)
        )
    )
    email = result.scalar_one_or_none()
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )
    
    # Mark as read if not already
    if not email.is_read:
        email.is_read = True
        await db.commit()
    
    return EmailDetail.model_validate(email)


@router.post("", response_model=EmailSendResponse, status_code=status.HTTP_201_CREATED)
async def send_email(
    email_data: EmailCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Send a new email."""
    # Verify mailbox belongs to user
    result = await db.execute(
        select(Mailbox).where(
            Mailbox.id == email_data.from_mailbox_id,
            Mailbox.user_id == current_user.id
        )
    )
    mailbox = result.scalar_one_or_none()
    
    if not mailbox:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mailbox not found"
        )
    
    # Get sent folder
    result = await db.execute(
        select(Folder).where(
            Folder.mailbox_id == mailbox.id,
            Folder.type == "sent"
        )
    )
    sent_folder = result.scalar_one_or_none()
    
    # Generate message ID
    import uuid
    message_id = f"<{uuid.uuid4()}@{mailbox.domain.name}>"
    
    # Create email record
    email = Email(
        mailbox_id=mailbox.id,
        folder_id=sent_folder.id if sent_folder else None,
        message_id=message_id,
        from_address=mailbox.full_address,
        from_name=current_user.full_name,
        to_addresses=[{"address": addr, "name": None} for addr in email_data.to],
        cc_addresses=[{"address": addr, "name": None} for addr in (email_data.cc or [])],
        bcc_addresses=[{"address": addr, "name": None} for addr in (email_data.bcc or [])],
        reply_to=email_data.reply_to,
        subject=email_data.subject,
        body_text=email_data.body_text,
        body_html=email_data.body_html,
        snippet=(email_data.body_text or "")[:200] if email_data.body_text else None,
        date=datetime.utcnow(),
        is_sent=True,
        is_read=True,
        is_draft=email_data.is_draft
    )
    
    db.add(email)
    await db.flush()

    # Link pre-uploaded attachments to this email
    if email_data.attachments:
        att_result = await db.execute(
            select(Attachment).where(Attachment.id.in_(email_data.attachments))
        )
        for att in att_result.scalars().all():
            att.email_id = email.id

    # Queue actual delivery via Celery → Postfix
    if not email_data.is_draft:
        from app.services.celery_tasks import send_email_task
        # Resolve attachment MinIO paths for SMTP delivery
        attachment_payloads = []
        if email_data.attachments:
            att_result2 = await db.execute(
                select(Attachment).where(Attachment.id.in_(email_data.attachments))
            )
            for att in att_result2.scalars().all():
                attachment_payloads.append({
                    "filename": att.filename,
                    "content_type": att.content_type,
                    "storage_path": att.storage_path,
                    "storage_bucket": att.storage_bucket,
                })

        send_email_task.delay(
            mailbox_id=str(mailbox.id),
            to_addresses=email_data.to,
            subject=email_data.subject,
            body_html=email_data.body_html,
            body_text=email_data.body_text,
            cc_addresses=email_data.cc,
            bcc_addresses=email_data.bcc,
            attachments=attachment_payloads or None,
        )

    await db.commit()

    return EmailSendResponse(
        id=email.id,
        message_id=message_id,
        status="sent" if not email_data.is_draft else "draft"
    )


@router.put("/{email_id}", response_model=EmailDetail)
async def update_email(
    email_id: UUID,
    email_data: EmailUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Update email (move, mark read, star, labels)."""
    # Get user's mailboxes
    result = await db.execute(
        select(Mailbox.id).where(Mailbox.user_id == current_user.id)
    )
    mailbox_ids = [row[0] for row in result.fetchall()]
    
    # Get email
    result = await db.execute(
        select(Email)
        .where(
            Email.id == email_id,
            Email.mailbox_id.in_(mailbox_ids)
        )
        .options(selectinload(Email.labels))
    )
    email = result.scalar_one_or_none()
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )
    
    # Update fields
    update_data = email_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if field == "label_ids":
            # Handle labels separately
            if value is not None:
                result = await db.execute(
                    select(Label).where(Label.id.in_(value))
                )
                email.labels = list(result.scalars().all())
        else:
            setattr(email, field, value)
    
    await db.commit()
    await db.refresh(email)
    
    return EmailDetail.model_validate(email)


@router.delete("/{email_id}", response_model=MessageResponse)
async def delete_email(
    email_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    permanent: bool = False
):
    """Move email to trash or permanently delete."""
    # Get user's mailboxes
    result = await db.execute(
        select(Mailbox.id).where(Mailbox.user_id == current_user.id)
    )
    mailbox_ids = [row[0] for row in result.fetchall()]
    
    # Get email
    result = await db.execute(
        select(Email).where(
            Email.id == email_id,
            Email.mailbox_id.in_(mailbox_ids)
        )
    )
    email = result.scalar_one_or_none()
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )
    
    if permanent:
        # Permanently delete
        await db.delete(email)
    else:
        # Move to trash
        result = await db.execute(
            select(Folder).where(
                Folder.mailbox_id == email.mailbox_id,
                Folder.type == "trash"
            )
        )
        trash_folder = result.scalar_one_or_none()
        
        email.folder_id = trash_folder.id if trash_folder else None
        email.is_trash = True
        email.deleted_at = datetime.utcnow()
    
    await db.commit()
    
    return MessageResponse(
        message="Email deleted successfully",
        success=True
    )


@router.post("/{email_id}/reply", response_model=EmailSendResponse)
async def reply_to_email(
    email_id: UUID,
    reply_data: EmailReply,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Reply to an email."""
    import uuid as uuid_lib

    # Get user's mailbox IDs
    result = await db.execute(select(Mailbox.id).where(Mailbox.user_id == current_user.id))
    mailbox_ids = [row[0] for row in result.fetchall()]

    # Get original email
    result = await db.execute(
        select(Email).where(Email.id == email_id, Email.mailbox_id.in_(mailbox_ids))
    )
    original = result.scalar_one_or_none()
    if not original:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")

    # Verify sender mailbox belongs to user
    result = await db.execute(
        select(Mailbox).where(Mailbox.id == reply_data.from_mailbox_id, Mailbox.user_id == current_user.id)
    )
    mailbox = result.scalar_one_or_none()
    if not mailbox:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mailbox not found")

    # Get sent folder
    result = await db.execute(
        select(Folder).where(Folder.mailbox_id == mailbox.id, Folder.type == "sent")
    )
    sent_folder = result.scalar_one_or_none()

    message_id = f"<{uuid_lib.uuid4()}@{mailbox.domain_name or 'mail.local'}>"

    # Build reply subject
    original_subject = original.subject or ""
    subject = original_subject if original_subject.lower().startswith("re:") else f"Re: {original_subject}"

    # Reply-to the sender of the original
    to_addresses = [{"address": original.from_address, "name": original.from_name}]

    email = Email(
        mailbox_id=mailbox.id,
        folder_id=sent_folder.id if sent_folder else None,
        message_id=message_id,
        thread_id=original.thread_id,
        in_reply_to=original.message_id,
        from_address=getattr(mailbox, 'full_address', mailbox.email),
        from_name=current_user.full_name,
        to_addresses=to_addresses,
        subject=subject,
        body_text=reply_data.body_text,
        body_html=reply_data.body_html,
        snippet=(reply_data.body_text or "")[:200],
        date=datetime.utcnow(),
        is_sent=True,
        is_read=True,
        is_draft=False,
    )
    db.add(email)
    await db.flush()

    # Queue delivery via Celery → Postfix
    from app.services.celery_tasks import send_email_task
    send_email_task.delay(
        mailbox_id=str(mailbox.id),
        to_addresses=[original.from_address],
        subject=subject,
        body_html=reply_data.body_html,
        body_text=reply_data.body_text,
        in_reply_to=original.message_id,
    )

    await db.commit()
    return EmailSendResponse(id=email.id, message_id=message_id, status="sent")


@router.post("/{email_id}/forward", response_model=EmailSendResponse)
async def forward_email(
    email_id: UUID,
    forward_data: EmailForward,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Forward an email."""
    import uuid as uuid_lib

    # Get user's mailbox IDs
    result = await db.execute(select(Mailbox.id).where(Mailbox.user_id == current_user.id))
    mailbox_ids = [row[0] for row in result.fetchall()]

    # Get original email
    result = await db.execute(
        select(Email).where(Email.id == email_id, Email.mailbox_id.in_(mailbox_ids))
    )
    original = result.scalar_one_or_none()
    if not original:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")

    # Verify sender mailbox
    result = await db.execute(
        select(Mailbox).where(Mailbox.id == forward_data.from_mailbox_id, Mailbox.user_id == current_user.id)
    )
    mailbox = result.scalar_one_or_none()
    if not mailbox:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mailbox not found")

    # Get sent folder
    result = await db.execute(
        select(Folder).where(Folder.mailbox_id == mailbox.id, Folder.type == "sent")
    )
    sent_folder = result.scalar_one_or_none()

    message_id = f"<{uuid_lib.uuid4()}@{getattr(mailbox, 'domain_name', 'mail.local')}>"

    # Build forward subject
    original_subject = original.subject or ""
    subject = original_subject if original_subject.lower().startswith("fwd:") else f"Fwd: {original_subject}"

    # Build forward body: append original content
    fwd_header = (
        f"\n\n---------- Forwarded message ----------\n"
        f"From: {original.from_name or ''} <{original.from_address}>\n"
        f"Date: {original.date.strftime('%a, %d %b %Y %H:%M:%S +0000')}\n"
        f"Subject: {original.subject or ''}\n"
        f"To: {', '.join(a.get('address','') if isinstance(a, dict) else str(a) for a in (original.to_addresses or []))}\n\n"
    )
    body_text = (forward_data.body_text or "") + fwd_header + (original.body_text or "")
    fwd_header_html = (
        f"<br><br><p>---------- Forwarded message ----------</p>"
        f"<p>From: {original.from_name or ''} &lt;{original.from_address}&gt;</p>"
        f"<p>Date: {original.date.strftime('%a, %d %b %Y %H:%M:%S +0000')}</p>"
        f"<p>Subject: {original.subject or ''}</p><br>"
    )
    body_html = (forward_data.body_html or "") + fwd_header_html + (original.body_html or original.body_text or "")

    to_addresses = [{"address": addr, "name": None} for addr in forward_data.to]

    email = Email(
        mailbox_id=mailbox.id,
        folder_id=sent_folder.id if sent_folder else None,
        message_id=message_id,
        from_address=getattr(mailbox, 'full_address', mailbox.email),
        from_name=current_user.full_name,
        to_addresses=to_addresses,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        snippet=body_text[:200],
        date=datetime.utcnow(),
        is_sent=True,
        is_read=True,
        is_draft=False,
    )
    db.add(email)
    await db.flush()

    # Queue delivery via Celery → Postfix
    from app.services.celery_tasks import send_email_task
    send_email_task.delay(
        mailbox_id=str(mailbox.id),
        to_addresses=forward_data.to,
        subject=subject,
        body_html=body_html,
        body_text=body_text,
    )

    await db.commit()
    return EmailSendResponse(id=email.id, message_id=message_id, status="sent")


@router.post("/bulk", response_model=MessageResponse)
async def bulk_action(
    action_data: EmailBulkAction,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Perform bulk action on multiple emails."""
    # Get user's mailboxes
    result = await db.execute(
        select(Mailbox.id).where(Mailbox.user_id == current_user.id)
    )
    mailbox_ids = [row[0] for row in result.fetchall()]
    
    # Get emails
    result = await db.execute(
        select(Email).where(
            Email.id.in_(action_data.email_ids),
            Email.mailbox_id.in_(mailbox_ids)
        )
    )
    emails = result.scalars().all()
    
    # Perform action
    for email in emails:
        if action_data.action == "mark_read":
            email.is_read = True
        elif action_data.action == "mark_unread":
            email.is_read = False
        elif action_data.action == "star":
            email.is_starred = True
        elif action_data.action == "unstar":
            email.is_starred = False
        elif action_data.action == "trash":
            email.is_trash = True
            email.deleted_at = datetime.utcnow()
        elif action_data.action == "move" and action_data.folder_id:
            email.folder_id = action_data.folder_id
    
    await db.commit()
    
    return MessageResponse(
        message=f"Action '{action_data.action}' performed on {len(emails)} emails",
        success=True
    )


@router.get("/search", response_model=List[EmailListItem])
async def search_emails(
    q: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    from_address: Optional[str] = Query(None),
    has_attachment: Optional[bool] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    folder: Optional[str] = Query(None),
):
    """Advanced email search — uses Elasticsearch when available, falls back to DB."""
    # Get user's mailbox IDs for ownership check
    result = await db.execute(
        select(Mailbox.id).where(Mailbox.user_id == current_user.id)
    )
    mailbox_ids = [row[0] for row in result.fetchall()]
    if not mailbox_ids:
        return []

    # --- Try Elasticsearch first ---
    try:
        from elasticsearch import AsyncElasticsearch
        es = AsyncElasticsearch([settings.ELASTICSEARCH_URL])
        index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}_emails"

        must_clauses = []
        filter_clauses = [
            {"terms": {"mailbox_id": [str(mid) for mid in mailbox_ids]}}
        ]

        if q:
            must_clauses.append({
                "multi_match": {
                    "query": q,
                    "fields": ["subject^3", "body_text", "from_address^2", "from_name"],
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                }
            })
        if from_address:
            filter_clauses.append({"term": {"from_address": from_address}})
        if has_attachment is not None:
            filter_clauses.append({"term": {"has_attachments": has_attachment}})
        if date_from:
            filter_clauses.append({"range": {"date": {"gte": date_from.isoformat()}}})
        if date_to:
            filter_clauses.append({"range": {"date": {"lte": date_to.isoformat()}}})
        if folder:
            # Resolve folder type to folder IDs
            folder_result = await db.execute(
                select(Folder.id).where(
                    Folder.mailbox_id.in_(mailbox_ids),
                    Folder.type == folder
                )
            )
            folder_ids = [str(r[0]) for r in folder_result.fetchall()]
            if folder_ids:
                filter_clauses.append({"terms": {"folder_id": folder_ids}})

        es_query = {
            "bool": {
                "must": must_clauses or [{"match_all": {}}],
                "filter": filter_clauses,
            }
        }

        offset = (page - 1) * per_page
        resp = await es.search(
            index=index_name,
            body={
                "query": es_query,
                "from": offset,
                "size": per_page,
                "sort": [{"date": {"order": "desc"}}],
            },
        )
        await es.close()

        hits = resp["hits"]["hits"]
        if not hits:
            return []

        # Fetch full Email objects from DB using hit IDs
        hit_ids = [h["_id"] for h in hits]
        from uuid import UUID as UUIDType
        result = await db.execute(
            select(Email)
            .where(
                Email.id.in_([UUIDType(hid) for hid in hit_ids]),
                Email.mailbox_id.in_(mailbox_ids)
            )
            .options(
                selectinload(Email.labels),
                selectinload(Email.folder),
                selectinload(Email.attachments)
            )
        )
        emails = result.scalars().all()
        # Preserve ES relevance order
        email_map = {str(e.id): e for e in emails}
        ordered = [email_map[hid] for hid in hit_ids if hid in email_map]

        return [
            EmailListItem(
                id=email.id,
                thread_id=email.thread_id,
                from_address=email.from_address,
                from_name=email.from_name,
                to_addresses=email.to_addresses,
                subject=email.subject,
                snippet=email.snippet,
                date=email.date,
                is_read=email.is_read,
                is_starred=email.is_starred,
                has_attachments=len(email.attachments) > 0,
                attachment_count=len(email.attachments),
                labels=email.labels,
                folder=email.folder,
            )
            for email in ordered
        ]

    except Exception:
        # Elasticsearch unavailable — fall back to DB full-text search
        pass

    # --- DB fallback ---
    return await list_emails(
        current_user=current_user,
        db=db,
        q=q,
        folder=folder,
        date_from=date_from,
        date_to=date_to,
        page=page,
        per_page=per_page,
    )
