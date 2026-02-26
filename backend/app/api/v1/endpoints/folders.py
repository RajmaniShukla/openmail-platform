"""
OpenMail Platform - Folder Endpoints
"""
from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.user import User
from app.models.email import Folder
from app.models.domain import Mailbox
from app.api.v1.endpoints.auth import get_current_user
from app.schemas.email import FolderCreate, FolderUpdate, FolderResponse
from app.schemas.auth import MessageResponse

router = APIRouter()


@router.get("", response_model=List[FolderResponse])
async def list_folders(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    mailbox_id: Optional[UUID] = None
):
    """List all folders for user's mailboxes."""
    # Get user's mailboxes
    query = select(Mailbox.id).where(Mailbox.user_id == current_user.id)
    if mailbox_id:
        query = query.where(Mailbox.id == mailbox_id)
    
    result = await db.execute(query)
    mailbox_ids = [row[0] for row in result.fetchall()]
    
    if not mailbox_ids:
        return []
    
    # Get folders
    result = await db.execute(
        select(Folder)
        .where(Folder.mailbox_id.in_(mailbox_ids))
        .order_by(Folder.sort_order, Folder.name)
    )
    folders = result.scalars().all()
    
    return [FolderResponse.model_validate(f) for f in folders]


@router.post("", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
async def create_folder(
    folder_data: FolderCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Create a new folder."""
    # Verify mailbox belongs to user
    result = await db.execute(
        select(Mailbox).where(
            Mailbox.id == folder_data.mailbox_id,
            Mailbox.user_id == current_user.id
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mailbox not found"
        )
    
    # Check for duplicate folder name
    result = await db.execute(
        select(Folder).where(
            Folder.mailbox_id == folder_data.mailbox_id,
            Folder.name == folder_data.name,
            Folder.parent_id == folder_data.parent_id
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Folder with this name already exists"
        )
    
    folder = Folder(
        mailbox_id=folder_data.mailbox_id,
        name=folder_data.name,
        type="custom",
        parent_id=folder_data.parent_id,
        color=folder_data.color,
        icon=folder_data.icon
    )
    
    db.add(folder)
    await db.commit()
    await db.refresh(folder)
    
    return FolderResponse.model_validate(folder)


@router.put("/{folder_id}", response_model=FolderResponse)
async def update_folder(
    folder_id: UUID,
    folder_data: FolderUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Update a folder."""
    # Get user's mailboxes
    result = await db.execute(
        select(Mailbox.id).where(Mailbox.user_id == current_user.id)
    )
    mailbox_ids = [row[0] for row in result.fetchall()]
    
    # Get folder
    result = await db.execute(
        select(Folder).where(
            Folder.id == folder_id,
            Folder.mailbox_id.in_(mailbox_ids)
        )
    )
    folder = result.scalar_one_or_none()
    
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )
    
    # Don't allow updating system folders
    if folder.type != "custom":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify system folders"
        )
    
    update_data = folder_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(folder, field, value)
    
    await db.commit()
    await db.refresh(folder)
    
    return FolderResponse.model_validate(folder)


@router.delete("/{folder_id}", response_model=MessageResponse)
async def delete_folder(
    folder_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Delete a folder."""
    # Get user's mailboxes
    result = await db.execute(
        select(Mailbox.id).where(Mailbox.user_id == current_user.id)
    )
    mailbox_ids = [row[0] for row in result.fetchall()]
    
    # Get folder
    result = await db.execute(
        select(Folder).where(
            Folder.id == folder_id,
            Folder.mailbox_id.in_(mailbox_ids)
        )
    )
    folder = result.scalar_one_or_none()
    
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )
    
    # Don't allow deleting system folders
    if folder.type != "custom":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete system folders"
        )
    
    await db.delete(folder)
    await db.commit()
    
    return MessageResponse(
        message="Folder deleted successfully",
        success=True
    )
