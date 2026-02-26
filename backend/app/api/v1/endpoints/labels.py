"""
OpenMail Platform - Label Endpoints
"""
from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.user import User
from app.models.email import Label
from app.models.domain import Mailbox
from app.api.v1.endpoints.auth import get_current_user
from app.schemas.email import LabelCreate, LabelUpdate, LabelResponse
from app.schemas.auth import MessageResponse

router = APIRouter()


@router.get("", response_model=List[LabelResponse])
async def list_labels(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    mailbox_id: Optional[UUID] = None
):
    """List all labels for user's mailboxes."""
    query = select(Mailbox.id).where(Mailbox.user_id == current_user.id)
    if mailbox_id:
        query = query.where(Mailbox.id == mailbox_id)
    
    result = await db.execute(query)
    mailbox_ids = [row[0] for row in result.fetchall()]
    
    if not mailbox_ids:
        return []
    
    result = await db.execute(
        select(Label)
        .where(Label.mailbox_id.in_(mailbox_ids))
        .order_by(Label.name)
    )
    labels = result.scalars().all()
    
    return [LabelResponse.model_validate(l) for l in labels]


@router.post("", response_model=LabelResponse, status_code=status.HTTP_201_CREATED)
async def create_label(
    label_data: LabelCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    mailbox_id: UUID = None
):
    """Create a new label."""
    # Get user's primary mailbox if not specified
    if not mailbox_id:
        result = await db.execute(
            select(Mailbox).where(
                Mailbox.user_id == current_user.id,
                Mailbox.is_primary == True
            )
        )
        mailbox = result.scalar_one_or_none()
        if not mailbox:
            result = await db.execute(
                select(Mailbox).where(Mailbox.user_id == current_user.id).limit(1)
            )
            mailbox = result.scalar_one_or_none()
        
        if not mailbox:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No mailbox found"
            )
        mailbox_id = mailbox.id
    else:
        # Verify mailbox belongs to user
        result = await db.execute(
            select(Mailbox).where(
                Mailbox.id == mailbox_id,
                Mailbox.user_id == current_user.id
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mailbox not found"
            )
    
    # Check for duplicate
    result = await db.execute(
        select(Label).where(
            Label.mailbox_id == mailbox_id,
            Label.name == label_data.name
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Label with this name already exists"
        )
    
    label = Label(
        mailbox_id=mailbox_id,
        name=label_data.name,
        color=label_data.color
    )
    
    db.add(label)
    await db.commit()
    await db.refresh(label)
    
    return LabelResponse.model_validate(label)


@router.put("/{label_id}", response_model=LabelResponse)
async def update_label(
    label_id: UUID,
    label_data: LabelUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Update a label."""
    result = await db.execute(
        select(Mailbox.id).where(Mailbox.user_id == current_user.id)
    )
    mailbox_ids = [row[0] for row in result.fetchall()]
    
    result = await db.execute(
        select(Label).where(
            Label.id == label_id,
            Label.mailbox_id.in_(mailbox_ids)
        )
    )
    label = result.scalar_one_or_none()
    
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Label not found"
        )
    
    update_data = label_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(label, field, value)
    
    await db.commit()
    await db.refresh(label)
    
    return LabelResponse.model_validate(label)


@router.delete("/{label_id}", response_model=MessageResponse)
async def delete_label(
    label_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Delete a label."""
    result = await db.execute(
        select(Mailbox.id).where(Mailbox.user_id == current_user.id)
    )
    mailbox_ids = [row[0] for row in result.fetchall()]
    
    result = await db.execute(
        select(Label).where(
            Label.id == label_id,
            Label.mailbox_id.in_(mailbox_ids)
        )
    )
    label = result.scalar_one_or_none()
    
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Label not found"
        )
    
    await db.delete(label)
    await db.commit()
    
    return MessageResponse(
        message="Label deleted successfully",
        success=True
    )
