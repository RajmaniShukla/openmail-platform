"""
OpenMail Platform - Contacts API Endpoints
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, or_

from app.db.database import get_db
from app.models.user import User
from app.models.contact import Contact, ContactGroup
from app.api.v1.endpoints.auth import get_current_user
from pydantic import BaseModel, EmailStr
from datetime import datetime

router = APIRouter(tags=["contacts"])


# Pydantic schemas
class ContactBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    notes: Optional[str] = None
    is_favorite: bool = False


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    notes: Optional[str] = None
    is_favorite: Optional[bool] = None


class ContactResponse(ContactBase):
    id: UUID
    user_id: UUID
    avatar_url: Optional[str]
    frequency: int
    last_contacted: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ContactGroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = None


class ContactGroupResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    color: Optional[str]
    member_count: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True


# Contact endpoints
@router.get("", response_model=List[ContactResponse])
async def list_contacts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search: Optional[str] = Query(None, description="Search contacts"),
    favorite: Optional[bool] = Query(None, description="Filter favorites"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """List all contacts for the current user."""
    query = select(Contact).where(Contact.user_id == current_user.id)
    
    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(
                Contact.email.ilike(pattern),
                Contact.name.ilike(pattern),
                Contact.first_name.ilike(pattern),
                Contact.last_name.ilike(pattern),
                Contact.company.ilike(pattern),
            )
        )
    
    if favorite is not None:
        query = query.where(Contact.is_favorite == favorite)
    
    query = query.order_by(Contact.frequency.desc(), Contact.name).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact_in: ContactCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new contact."""
    # Check if contact already exists
    existing = await db.execute(
        select(Contact).where(
            Contact.user_id == current_user.id,
            Contact.email == contact_in.email
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contact with this email already exists"
        )
    
    contact = Contact(
        user_id=current_user.id,
        **contact_in.model_dump()
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


@router.get("/frequent", response_model=List[ContactResponse])
async def get_frequent_contacts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=50),
):
    """Get most frequently contacted contacts."""
    query = (
        select(Contact)
        .where(Contact.user_id == current_user.id)
        .order_by(Contact.frequency.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/suggestions")
async def get_contact_suggestions(
    q: str = Query(..., min_length=1, description="Search query"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=20),
):
    """Get contact suggestions for autocomplete."""
    pattern = f"%{q}%"
    query = (
        select(Contact)
        .where(
            Contact.user_id == current_user.id,
            or_(
                Contact.email.ilike(pattern),
                Contact.name.ilike(pattern),
            )
        )
        .order_by(Contact.frequency.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    contacts = result.scalars().all()
    
    return [
        {
            "email": c.email,
            "name": c.name or c.email,
            "avatar_url": c.avatar_url,
        }
        for c in contacts
    ]


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific contact."""
    contact = await db.get(Contact, contact_id)
    if not contact or contact.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    return contact


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: UUID,
    contact_in: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a contact."""
    contact = await db.get(Contact, contact_id)
    if not contact or contact.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    update_data = contact_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contact, field, value)
    
    contact.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(contact)
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a contact."""
    contact = await db.get(Contact, contact_id)
    if not contact or contact.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    await db.delete(contact)
    await db.commit()


@router.post("/{contact_id}/favorite", response_model=ContactResponse)
async def toggle_favorite(
    contact_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Toggle contact favorite status."""
    contact = await db.get(Contact, contact_id)
    if not contact or contact.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    contact.is_favorite = not contact.is_favorite
    contact.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(contact)
    return contact


# Contact Groups endpoints
@router.get("/groups", response_model=List[ContactGroupResponse])
async def list_contact_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all contact groups."""
    query = (
        select(ContactGroup)
        .where(ContactGroup.user_id == current_user.id)
        .order_by(ContactGroup.name)
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/groups", response_model=ContactGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_contact_group(
    group_in: ContactGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new contact group."""
    group = ContactGroup(
        user_id=current_user.id,
        **group_in.model_dump()
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


@router.post("/groups/{group_id}/members/{contact_id}")
async def add_contact_to_group(
    group_id: UUID,
    contact_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a contact to a group."""
    group = await db.get(ContactGroup, group_id)
    if not group or group.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    contact = await db.get(Contact, contact_id)
    if not contact or contact.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    group.members.append(contact)
    await db.commit()
    
    return {"status": "success", "message": "Contact added to group"}


@router.delete("/groups/{group_id}/members/{contact_id}")
async def remove_contact_from_group(
    group_id: UUID,
    contact_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a contact from a group."""
    group = await db.get(ContactGroup, group_id)
    if not group or group.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    contact = await db.get(Contact, contact_id)
    if contact in group.members:
        group.members.remove(contact)
        await db.commit()
    
    return {"status": "success", "message": "Contact removed from group"}


# Import contacts
@router.post("/import")
async def import_contacts(
    contacts: List[ContactCreate],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bulk import contacts."""
    imported = 0
    skipped = 0
    
    for contact_data in contacts:
        # Check if exists
        existing = await db.execute(
            select(Contact).where(
                Contact.user_id == current_user.id,
                Contact.email == contact_data.email
            )
        )
        if existing.scalar_one_or_none():
            skipped += 1
            continue
        
        contact = Contact(
            user_id=current_user.id,
            **contact_data.model_dump()
        )
        db.add(contact)
        imported += 1
    
    await db.commit()
    
    return {
        "status": "success",
        "imported": imported,
        "skipped": skipped,
        "total": len(contacts)
    }


# Export contacts
@router.get("/export")
async def export_contacts(
    format: str = Query("json", regex="^(json|csv)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export all contacts."""
    query = select(Contact).where(Contact.user_id == current_user.id)
    result = await db.execute(query)
    contacts = result.scalars().all()
    
    if format == "csv":
        import csv
        from io import StringIO
        from fastapi.responses import StreamingResponse
        
        output = StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=["email", "name", "first_name", "last_name", "phone", "company", "notes"]
        )
        writer.writeheader()
        for contact in contacts:
            writer.writerow({
                "email": contact.email,
                "name": contact.name,
                "first_name": contact.first_name,
                "last_name": contact.last_name,
                "phone": contact.phone,
                "company": contact.company,
                "notes": contact.notes,
            })
        
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=contacts.csv"}
        )
    
    return [
        {
            "email": c.email,
            "name": c.name,
            "first_name": c.first_name,
            "last_name": c.last_name,
            "phone": c.phone,
            "company": c.company,
            "notes": c.notes,
        }
        for c in contacts
    ]
