"""
OpenMail Platform - Statistics and Analytics Endpoints
"""
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.db.database import get_db
from app.models.user import User, Mailbox
from app.models.email import Email, Folder
from app.core.security import get_current_user

router = APIRouter(prefix="/stats", tags=["statistics"])


@router.get("/overview")
async def get_overview_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    mailbox_id: Optional[UUID] = Query(None),
):
    """Get overview statistics for the user's mailboxes."""
    # Get user's mailboxes
    if mailbox_id:
        mailbox_ids = [mailbox_id]
    else:
        result = await db.execute(
            select(Mailbox.id).where(Mailbox.user_id == current_user.id)
        )
        mailbox_ids = [m.id for m in result.scalars().all()]
    
    if not mailbox_ids:
        return {
            "total_emails": 0,
            "unread_emails": 0,
            "starred_emails": 0,
            "draft_emails": 0,
            "sent_today": 0,
            "received_today": 0,
            "spam_count": 0,
            "storage_used_bytes": 0,
        }
    
    # Get total emails
    total_result = await db.execute(
        select(func.count(Email.id)).where(Email.mailbox_id.in_(mailbox_ids))
    )
    total_emails = total_result.scalar() or 0
    
    # Get unread count
    unread_result = await db.execute(
        select(func.count(Email.id)).where(
            and_(Email.mailbox_id.in_(mailbox_ids), Email.is_read == False)
        )
    )
    unread_emails = unread_result.scalar() or 0
    
    # Get starred count
    starred_result = await db.execute(
        select(func.count(Email.id)).where(
            and_(Email.mailbox_id.in_(mailbox_ids), Email.is_starred == True)
        )
    )
    starred_emails = starred_result.scalar() or 0
    
    # Get drafts count
    draft_result = await db.execute(
        select(func.count(Email.id)).where(
            and_(Email.mailbox_id.in_(mailbox_ids), Email.is_draft == True)
        )
    )
    draft_emails = draft_result.scalar() or 0
    
    # Get spam folders
    spam_folders = await db.execute(
        select(Folder.id).where(
            and_(Folder.mailbox_id.in_(mailbox_ids), Folder.type == "spam")
        )
    )
    spam_folder_ids = [f.id for f in spam_folders.scalars().all()]
    
    spam_result = await db.execute(
        select(func.count(Email.id)).where(Email.folder_id.in_(spam_folder_ids))
    ) if spam_folder_ids else None
    spam_count = spam_result.scalar() if spam_result else 0
    
    # Get today's stats
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Sent today
    sent_folders = await db.execute(
        select(Folder.id).where(
            and_(Folder.mailbox_id.in_(mailbox_ids), Folder.type == "sent")
        )
    )
    sent_folder_ids = [f.id for f in sent_folders.scalars().all()]
    
    sent_today_result = await db.execute(
        select(func.count(Email.id)).where(
            and_(
                Email.folder_id.in_(sent_folder_ids),
                Email.date >= today_start
            )
        )
    ) if sent_folder_ids else None
    sent_today = sent_today_result.scalar() if sent_today_result else 0
    
    # Received today (inbox)
    inbox_folders = await db.execute(
        select(Folder.id).where(
            and_(Folder.mailbox_id.in_(mailbox_ids), Folder.type == "inbox")
        )
    )
    inbox_folder_ids = [f.id for f in inbox_folders.scalars().all()]
    
    received_today_result = await db.execute(
        select(func.count(Email.id)).where(
            and_(
                Email.folder_id.in_(inbox_folder_ids),
                Email.date >= today_start
            )
        )
    ) if inbox_folder_ids else None
    received_today = received_today_result.scalar() if received_today_result else 0
    
    # Storage used
    storage_result = await db.execute(
        select(func.sum(Email.size_bytes)).where(Email.mailbox_id.in_(mailbox_ids))
    )
    storage_used = storage_result.scalar() or 0
    
    return {
        "total_emails": total_emails,
        "unread_emails": unread_emails,
        "starred_emails": starred_emails,
        "draft_emails": draft_emails,
        "sent_today": sent_today,
        "received_today": received_today,
        "spam_count": spam_count,
        "storage_used_bytes": storage_used,
    }


@router.get("/activity")
async def get_activity_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = Query(7, ge=1, le=90),
    mailbox_id: Optional[UUID] = Query(None),
):
    """Get email activity over time (sent/received per day)."""
    # Get user's mailboxes
    if mailbox_id:
        mailbox_ids = [mailbox_id]
    else:
        result = await db.execute(
            select(Mailbox.id).where(Mailbox.user_id == current_user.id)
        )
        mailbox_ids = [m.id for m in result.scalars().all()]
    
    if not mailbox_ids:
        return {"activity": []}
    
    # Get date range
    end_date = datetime.utcnow().replace(hour=23, minute=59, second=59)
    start_date = end_date - timedelta(days=days)
    
    # Get sent folders
    sent_folders = await db.execute(
        select(Folder.id).where(
            and_(Folder.mailbox_id.in_(mailbox_ids), Folder.type == "sent")
        )
    )
    sent_folder_ids = [f.id for f in sent_folders.scalars().all()]
    
    # Get inbox folders
    inbox_folders = await db.execute(
        select(Folder.id).where(
            and_(Folder.mailbox_id.in_(mailbox_ids), Folder.type == "inbox")
        )
    )
    inbox_folder_ids = [f.id for f in inbox_folders.scalars().all()]
    
    # Build activity data
    activity = []
    current_date = start_date
    
    while current_date <= end_date:
        day_start = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = current_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Count sent
        sent_count = 0
        if sent_folder_ids:
            sent_result = await db.execute(
                select(func.count(Email.id)).where(
                    and_(
                        Email.folder_id.in_(sent_folder_ids),
                        Email.date >= day_start,
                        Email.date <= day_end
                    )
                )
            )
            sent_count = sent_result.scalar() or 0
        
        # Count received
        received_count = 0
        if inbox_folder_ids:
            received_result = await db.execute(
                select(func.count(Email.id)).where(
                    and_(
                        Email.folder_id.in_(inbox_folder_ids),
                        Email.date >= day_start,
                        Email.date <= day_end
                    )
                )
            )
            received_count = received_result.scalar() or 0
        
        activity.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "sent": sent_count,
            "received": received_count,
        })
        
        current_date += timedelta(days=1)
    
    return {"activity": activity}


@router.get("/top-senders")
async def get_top_senders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=50),
    mailbox_id: Optional[UUID] = Query(None),
):
    """Get top email senders."""
    # Get user's mailboxes
    if mailbox_id:
        mailbox_ids = [mailbox_id]
    else:
        result = await db.execute(
            select(Mailbox.id).where(Mailbox.user_id == current_user.id)
        )
        mailbox_ids = [m.id for m in result.scalars().all()]
    
    if not mailbox_ids:
        return {"senders": []}
    
    # Get inbox folders
    inbox_folders = await db.execute(
        select(Folder.id).where(
            and_(Folder.mailbox_id.in_(mailbox_ids), Folder.type == "inbox")
        )
    )
    inbox_folder_ids = [f.id for f in inbox_folders.scalars().all()]
    
    if not inbox_folder_ids:
        return {"senders": []}
    
    # Get top senders
    result = await db.execute(
        select(
            Email.from_address,
            Email.from_name,
            func.count(Email.id).label("count")
        )
        .where(Email.folder_id.in_(inbox_folder_ids))
        .group_by(Email.from_address, Email.from_name)
        .order_by(func.count(Email.id).desc())
        .limit(limit)
    )
    
    senders = [
        {
            "email": row.from_address,
            "name": row.from_name,
            "count": row.count,
        }
        for row in result.all()
    ]
    
    return {"senders": senders}


@router.get("/folder-stats")
async def get_folder_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    mailbox_id: Optional[UUID] = Query(None),
):
    """Get email count per folder."""
    # Get user's mailboxes
    if mailbox_id:
        mailbox_ids = [mailbox_id]
    else:
        result = await db.execute(
            select(Mailbox.id).where(Mailbox.user_id == current_user.id)
        )
        mailbox_ids = [m.id for m in result.scalars().all()]
    
    if not mailbox_ids:
        return {"folders": []}
    
    # Get all folders with counts
    result = await db.execute(
        select(
            Folder.id,
            Folder.name,
            Folder.type,
            Folder.total_count,
            Folder.unread_count,
        )
        .where(Folder.mailbox_id.in_(mailbox_ids))
        .order_by(Folder.type)
    )
    
    folders = [
        {
            "id": str(row.id),
            "name": row.name,
            "type": row.type,
            "total": row.total_count,
            "unread": row.unread_count,
        }
        for row in result.all()
    ]
    
    return {"folders": folders}
