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
    
    # TODO: Actually send the email via Postfix
    # TODO: Handle attachments
    
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
    # Get original email
    # ... implementation similar to send_email
    pass


@router.post("/{email_id}/forward", response_model=EmailSendResponse)
async def forward_email(
    email_id: UUID,
    forward_data: EmailForward,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Forward an email."""
    # ... implementation similar to send_email
    pass


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
    per_page: int = Query(50, ge=1, le=100)
):
    """Advanced email search."""
    # This would ideally use Elasticsearch
    # For now, use database search
    return await list_emails(
        current_user=current_user,
        db=db,
        q=q,
        folder=None,
        page=page,
        per_page=per_page
    )
