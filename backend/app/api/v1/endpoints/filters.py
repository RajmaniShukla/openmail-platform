"""
OpenMail Platform - Email Filters API Endpoints
"""
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from pydantic import BaseModel

from app.db.database import get_db
from app.models.user import User, Mailbox
from app.models.email import EmailFilter
from app.core.security import get_current_user
from datetime import datetime

router = APIRouter(prefix="/filters", tags=["filters"])


# Pydantic schemas
class FilterCondition(BaseModel):
    field: str  # from, to, subject, body, has_attachment
    operator: str  # contains, equals, starts_with, ends_with, not_contains
    value: str


class FilterAction(BaseModel):
    type: str  # move, label, star, mark_read, delete, forward
    value: Optional[str] = None


class FilterCreate(BaseModel):
    name: str
    conditions: List[FilterCondition]
    actions: List[FilterAction]
    match_mode: str = "all"  # all or any
    stop_processing: bool = False
    is_active: bool = True
    mailbox_id: Optional[UUID] = None


class FilterUpdate(BaseModel):
    name: Optional[str] = None
    conditions: Optional[List[FilterCondition]] = None
    actions: Optional[List[FilterAction]] = None
    match_mode: Optional[str] = None
    stop_processing: Optional[bool] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None


class FilterResponse(BaseModel):
    id: UUID
    mailbox_id: UUID
    name: str
    conditions: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    match_mode: str
    stop_processing: bool
    is_active: bool
    priority: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


@router.get("", response_model=List[FilterResponse])
async def list_filters(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    mailbox_id: Optional[UUID] = Query(None, description="Filter by mailbox"),
):
    """List all filters for the current user."""
    # Get user's mailboxes
    mailboxes_query = select(Mailbox.id).where(Mailbox.user_id == current_user.id)
    if mailbox_id:
        mailboxes_query = mailboxes_query.where(Mailbox.id == mailbox_id)
    
    mailboxes_result = await db.execute(mailboxes_query)
    mailbox_ids = [m.id for m in mailboxes_result.scalars().all()]
    
    if not mailbox_ids:
        return []
    
    # Get filters
    query = (
        select(EmailFilter)
        .where(EmailFilter.mailbox_id.in_(mailbox_ids))
        .order_by(EmailFilter.priority.desc(), EmailFilter.name)
    )
    
    result = await db.execute(query)
    filters = result.scalars().all()
    
    # Convert conditions/actions to dict format
    return [
        FilterResponse(
            id=f.id,
            mailbox_id=f.mailbox_id,
            name=f.name,
            conditions=f.conditions if isinstance(f.conditions, list) else [],
            actions=f.actions if isinstance(f.actions, list) else [],
            match_mode=f.conditions.get('match_mode', 'all') if isinstance(f.conditions, dict) else 'all',
            stop_processing=f.stop_processing,
            is_active=f.is_active,
            priority=f.priority,
            created_at=f.created_at,
            updated_at=f.updated_at,
        )
        for f in filters
    ]


@router.post("", response_model=FilterResponse, status_code=status.HTTP_201_CREATED)
async def create_filter(
    filter_in: FilterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new email filter."""
    # Get or validate mailbox
    if filter_in.mailbox_id:
        mailbox = await db.get(Mailbox, filter_in.mailbox_id)
        if not mailbox or mailbox.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mailbox not found"
            )
        mailbox_id = filter_in.mailbox_id
    else:
        # Use primary mailbox
        result = await db.execute(
            select(Mailbox).where(
                and_(Mailbox.user_id == current_user.id, Mailbox.is_primary == True)
            )
        )
        mailbox = result.scalar_one_or_none()
        if not mailbox:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No mailbox available"
            )
        mailbox_id = mailbox.id
    
    # Get max priority
    priority_result = await db.execute(
        select(EmailFilter.priority)
        .where(EmailFilter.mailbox_id == mailbox_id)
        .order_by(EmailFilter.priority.desc())
        .limit(1)
    )
    max_priority = priority_result.scalar() or 0
    
    # Create filter
    email_filter = EmailFilter(
        mailbox_id=mailbox_id,
        name=filter_in.name,
        conditions=[c.model_dump() for c in filter_in.conditions],
        actions=[a.model_dump() for a in filter_in.actions],
        stop_processing=filter_in.stop_processing,
        is_active=filter_in.is_active,
        priority=max_priority + 1,
    )
    
    db.add(email_filter)
    await db.commit()
    await db.refresh(email_filter)
    
    return FilterResponse(
        id=email_filter.id,
        mailbox_id=email_filter.mailbox_id,
        name=email_filter.name,
        conditions=email_filter.conditions,
        actions=email_filter.actions,
        match_mode=filter_in.match_mode,
        stop_processing=email_filter.stop_processing,
        is_active=email_filter.is_active,
        priority=email_filter.priority,
        created_at=email_filter.created_at,
        updated_at=email_filter.updated_at,
    )


@router.get("/{filter_id}", response_model=FilterResponse)
async def get_filter(
    filter_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific filter."""
    email_filter = await db.get(EmailFilter, filter_id)
    if not email_filter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filter not found"
        )
    
    # Verify ownership
    mailbox = await db.get(Mailbox, email_filter.mailbox_id)
    if not mailbox or mailbox.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filter not found"
        )
    
    return FilterResponse(
        id=email_filter.id,
        mailbox_id=email_filter.mailbox_id,
        name=email_filter.name,
        conditions=email_filter.conditions,
        actions=email_filter.actions,
        match_mode='all',  # Default
        stop_processing=email_filter.stop_processing,
        is_active=email_filter.is_active,
        priority=email_filter.priority,
        created_at=email_filter.created_at,
        updated_at=email_filter.updated_at,
    )


@router.put("/{filter_id}", response_model=FilterResponse)
async def update_filter(
    filter_id: UUID,
    filter_in: FilterUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a filter."""
    email_filter = await db.get(EmailFilter, filter_id)
    if not email_filter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filter not found"
        )
    
    # Verify ownership
    mailbox = await db.get(Mailbox, email_filter.mailbox_id)
    if not mailbox or mailbox.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filter not found"
        )
    
    # Update fields
    update_data = filter_in.model_dump(exclude_unset=True)
    
    if 'conditions' in update_data:
        update_data['conditions'] = [c.model_dump() if hasattr(c, 'model_dump') else c for c in update_data['conditions']]
    if 'actions' in update_data:
        update_data['actions'] = [a.model_dump() if hasattr(a, 'model_dump') else a for a in update_data['actions']]
    
    # Remove match_mode from update_data as it's not a model field
    update_data.pop('match_mode', None)
    
    for field, value in update_data.items():
        setattr(email_filter, field, value)
    
    email_filter.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(email_filter)
    
    return FilterResponse(
        id=email_filter.id,
        mailbox_id=email_filter.mailbox_id,
        name=email_filter.name,
        conditions=email_filter.conditions,
        actions=email_filter.actions,
        match_mode=filter_in.match_mode or 'all',
        stop_processing=email_filter.stop_processing,
        is_active=email_filter.is_active,
        priority=email_filter.priority,
        created_at=email_filter.created_at,
        updated_at=email_filter.updated_at,
    )


@router.patch("/{filter_id}", response_model=FilterResponse)
async def partial_update_filter(
    filter_id: UUID,
    filter_in: FilterUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Partially update a filter (e.g., toggle is_active)."""
    return await update_filter(filter_id, filter_in, db, current_user)


@router.delete("/{filter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_filter(
    filter_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a filter."""
    email_filter = await db.get(EmailFilter, filter_id)
    if not email_filter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filter not found"
        )
    
    # Verify ownership
    mailbox = await db.get(Mailbox, email_filter.mailbox_id)
    if not mailbox or mailbox.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filter not found"
        )
    
    await db.delete(email_filter)
    await db.commit()


@router.post("/{filter_id}/test")
async def test_filter(
    filter_id: UUID,
    email_content: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Test a filter against sample email content."""
    email_filter = await db.get(EmailFilter, filter_id)
    if not email_filter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filter not found"
        )
    
    # Verify ownership
    mailbox = await db.get(Mailbox, email_filter.mailbox_id)
    if not mailbox or mailbox.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filter not found"
        )
    
    # Test conditions
    conditions = email_filter.conditions or []
    match_mode = 'all'  # Default
    
    results = []
    for condition in conditions:
        field = condition.get('field', '')
        operator = condition.get('operator', 'contains')
        value = condition.get('value', '')
        
        email_value = str(email_content.get(field, '')).lower()
        test_value = value.lower()
        
        if operator == 'contains':
            matched = test_value in email_value
        elif operator == 'equals':
            matched = email_value == test_value
        elif operator == 'starts_with':
            matched = email_value.startswith(test_value)
        elif operator == 'ends_with':
            matched = email_value.endswith(test_value)
        elif operator == 'not_contains':
            matched = test_value not in email_value
        else:
            matched = False
        
        results.append({
            'condition': condition,
            'matched': matched,
        })
    
    # Determine overall match
    if match_mode == 'all':
        overall_match = all(r['matched'] for r in results)
    else:
        overall_match = any(r['matched'] for r in results)
    
    return {
        'filter_id': str(filter_id),
        'filter_name': email_filter.name,
        'overall_match': overall_match,
        'match_mode': match_mode,
        'condition_results': results,
        'actions_would_apply': email_filter.actions if overall_match else [],
    }


@router.post("/reorder")
async def reorder_filters(
    filter_orders: List[Dict[str, Any]],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reorder filters by priority."""
    # filter_orders: [{"id": "uuid", "priority": 1}, ...]
    
    for order in filter_orders:
        filter_id = order.get('id')
        priority = order.get('priority', 0)
        
        email_filter = await db.get(EmailFilter, filter_id)
        if email_filter:
            # Verify ownership
            mailbox = await db.get(Mailbox, email_filter.mailbox_id)
            if mailbox and mailbox.user_id == current_user.id:
                email_filter.priority = priority
    
    await db.commit()
    
    return {"status": "success", "message": "Filters reordered"}
