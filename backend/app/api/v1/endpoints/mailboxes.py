"""
OpenMail Platform - Mailbox Endpoints
"""
from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.models.user import User
from app.models.domain import Domain, Mailbox
from app.models.email import Folder, Email
from app.api.v1.endpoints.auth import get_current_user
from app.schemas.domain import (
    MailboxCreate,
    MailboxUpdate,
    MailboxResponse,
    MailboxStats,
    MailboxBrief
)
from app.schemas.auth import MessageResponse

router = APIRouter()


async def create_default_folders(db: AsyncSession, mailbox_id: UUID):
    """Create default folders for a new mailbox."""
    default_folders = [
        {"name": "Inbox", "type": "inbox", "sort_order": 1},
        {"name": "Sent", "type": "sent", "sort_order": 2},
        {"name": "Drafts", "type": "drafts", "sort_order": 3},
        {"name": "Spam", "type": "spam", "sort_order": 4},
        {"name": "Trash", "type": "trash", "sort_order": 5},
        {"name": "Starred", "type": "starred", "sort_order": 6},
    ]
    
    for folder_data in default_folders:
        folder = Folder(
            mailbox_id=mailbox_id,
            **folder_data
        )
        db.add(folder)


@router.get("", response_model=List[MailboxBrief])
async def list_mailboxes(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """List user's mailboxes."""
    result = await db.execute(
        select(Mailbox)
        .where(Mailbox.user_id == current_user.id)
        .order_by(Mailbox.is_primary.desc(), Mailbox.full_address)
    )
    mailboxes = result.scalars().all()
    
    # Get unread counts
    mailbox_briefs = []
    for mailbox in mailboxes:
        result = await db.execute(
            select(func.count(Email.id))
            .where(
                Email.mailbox_id == mailbox.id,
                Email.is_read == False,
                Email.deleted_at.is_(None)
            )
        )
        unread_count = result.scalar() or 0
        
        mailbox_briefs.append(MailboxBrief(
            id=mailbox.id,
            full_address=mailbox.full_address,
            is_primary=mailbox.is_primary,
            unread_count=unread_count
        ))
    
    return mailbox_briefs


@router.post("", response_model=MailboxResponse, status_code=status.HTTP_201_CREATED)
async def create_mailbox(
    mailbox_data: MailboxCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Create a new mailbox."""
    # Verify domain belongs to user and is verified
    result = await db.execute(
        select(Domain).where(
            Domain.id == mailbox_data.domain_id,
            Domain.owner_id == current_user.id
        )
    )
    domain = result.scalar_one_or_none()
    
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain not found"
        )
    
    if not domain.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Domain must be verified before creating mailboxes"
        )
    
    # Check if mailbox already exists
    full_address = f"{mailbox_data.local_part}@{domain.name}".lower()
    result = await db.execute(
        select(Mailbox).where(Mailbox.full_address == full_address)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mailbox already exists"
        )
    
    # Check if this is the first mailbox
    result = await db.execute(
        select(func.count(Mailbox.id)).where(Mailbox.user_id == current_user.id)
    )
    is_first = result.scalar() == 0
    
    # Create mailbox
    mailbox = Mailbox(
        user_id=current_user.id,
        domain_id=domain.id,
        local_part=mailbox_data.local_part.lower(),
        full_address=full_address,
        is_primary=is_first  # First mailbox is primary
    )
    db.add(mailbox)
    await db.flush()
    
    # Create default folders
    await create_default_folders(db, mailbox.id)
    
    await db.commit()
    await db.refresh(mailbox)
    
    return MailboxResponse.model_validate(mailbox)


@router.get("/{mailbox_id}", response_model=MailboxResponse)
async def get_mailbox(
    mailbox_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Get mailbox details."""
    result = await db.execute(
        select(Mailbox).where(
            Mailbox.id == mailbox_id,
            Mailbox.user_id == current_user.id
        )
    )
    mailbox = result.scalar_one_or_none()
    
    if not mailbox:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mailbox not found"
        )
    
    return MailboxResponse.model_validate(mailbox)


@router.get("/{mailbox_id}/stats", response_model=MailboxStats)
async def get_mailbox_stats(
    mailbox_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Get mailbox statistics."""
    result = await db.execute(
        select(Mailbox).where(
            Mailbox.id == mailbox_id,
            Mailbox.user_id == current_user.id
        )
    )
    mailbox = result.scalar_one_or_none()
    
    if not mailbox:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mailbox not found"
        )
    
    # Get email counts
    result = await db.execute(
        select(
            func.count(Email.id).label("total"),
            func.count(Email.id).filter(Email.is_read == False).label("unread"),
            func.count(Email.id).filter(Email.is_spam == True).label("spam"),
            func.count(Email.id).filter(Email.is_trash == True).label("trash")
        )
        .where(
            Email.mailbox_id == mailbox_id,
            Email.deleted_at.is_(None)
        )
    )
    counts = result.one()
    
    return MailboxStats(
        id=mailbox.id,
        full_address=mailbox.full_address,
        quota_bytes=mailbox.quota_bytes,
        used_bytes=mailbox.used_bytes,
        quota_used_percent=mailbox.quota_used_percent,
        total_emails=counts.total,
        unread_count=counts.unread,
        spam_count=counts.spam,
        trash_count=counts.trash
    )


@router.put("/{mailbox_id}", response_model=MailboxResponse)
async def update_mailbox(
    mailbox_id: UUID,
    mailbox_data: MailboxUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Update mailbox settings."""
    result = await db.execute(
        select(Mailbox).where(
            Mailbox.id == mailbox_id,
            Mailbox.user_id == current_user.id
        )
    )
    mailbox = result.scalar_one_or_none()
    
    if not mailbox:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mailbox not found"
        )
    
    update_data = mailbox_data.model_dump(exclude_unset=True)
    
    # If setting as primary, unset other primary mailboxes
    if update_data.get("is_primary"):
        await db.execute(
            select(Mailbox)
            .where(
                Mailbox.user_id == current_user.id,
                Mailbox.is_primary == True
            )
        )
        result = await db.execute(
            select(Mailbox).where(
                Mailbox.user_id == current_user.id,
                Mailbox.is_primary == True,
                Mailbox.id != mailbox_id
            )
        )
        for other_mailbox in result.scalars().all():
            other_mailbox.is_primary = False
    
    for field, value in update_data.items():
        setattr(mailbox, field, value)
    
    await db.commit()
    await db.refresh(mailbox)
    
    return MailboxResponse.model_validate(mailbox)


@router.delete("/{mailbox_id}", response_model=MessageResponse)
async def delete_mailbox(
    mailbox_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Delete a mailbox."""
    result = await db.execute(
        select(Mailbox).where(
            Mailbox.id == mailbox_id,
            Mailbox.user_id == current_user.id
        )
    )
    mailbox = result.scalar_one_or_none()
    
    if not mailbox:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mailbox not found"
        )
    
    # Don't allow deleting the only mailbox
    result = await db.execute(
        select(func.count(Mailbox.id)).where(Mailbox.user_id == current_user.id)
    )
    if result.scalar() <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the only mailbox"
        )
    
    await db.delete(mailbox)
    await db.commit()
    
    return MessageResponse(
        message="Mailbox deleted successfully",
        success=True
    )
