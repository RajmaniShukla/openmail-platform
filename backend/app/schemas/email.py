"""
OpenMail Platform - Email Schemas
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# Address schemas
class EmailAddress(BaseModel):
    """Email address with optional name."""
    address: EmailStr
    name: Optional[str] = None


# Label schemas
class LabelBase(BaseModel):
    """Base label schema."""
    name: str
    color: str = "#808080"


class LabelCreate(LabelBase):
    """Schema for creating a label."""
    pass


class LabelUpdate(BaseModel):
    """Schema for updating a label."""
    name: Optional[str] = None
    color: Optional[str] = None


class LabelResponse(LabelBase):
    """Schema for label response."""
    id: UUID
    mailbox_id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Folder schemas
class FolderBase(BaseModel):
    """Base folder schema."""
    name: str
    color: Optional[str] = None
    icon: Optional[str] = None


class FolderCreate(FolderBase):
    """Schema for creating a folder."""
    mailbox_id: UUID
    parent_id: Optional[UUID] = None


class FolderUpdate(BaseModel):
    """Schema for updating a folder."""
    name: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class FolderResponse(FolderBase):
    """Schema for folder response."""
    id: UUID
    mailbox_id: UUID
    type: str
    parent_id: Optional[UUID] = None
    total_count: int
    unread_count: int
    sort_order: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Attachment schemas
class AttachmentBase(BaseModel):
    """Base attachment schema."""
    filename: str
    content_type: Optional[str] = None
    size_bytes: int


class AttachmentResponse(AttachmentBase):
    """Schema for attachment response."""
    id: UUID
    is_inline: bool = False
    
    model_config = ConfigDict(from_attributes=True)


class AttachmentUploadResponse(BaseModel):
    """Schema for attachment upload response."""
    id: UUID
    filename: str
    content_type: Optional[str] = None
    size_bytes: int


# Email schemas
class EmailBase(BaseModel):
    """Base email schema."""
    subject: Optional[str] = None
    body_text: Optional[str] = None
    body_html: Optional[str] = None


class EmailCreate(EmailBase):
    """Schema for sending an email."""
    from_mailbox_id: UUID
    to: List[EmailStr]
    cc: Optional[List[EmailStr]] = None
    bcc: Optional[List[EmailStr]] = None
    reply_to: Optional[EmailStr] = None
    in_reply_to: Optional[str] = None
    attachments: Optional[List[UUID]] = None
    is_draft: bool = False
    send_at: Optional[datetime] = None


class EmailUpdate(BaseModel):
    """Schema for updating an email."""
    is_read: Optional[bool] = None
    is_starred: Optional[bool] = None
    folder_id: Optional[UUID] = None
    label_ids: Optional[List[UUID]] = None


class EmailReply(BaseModel):
    """Schema for replying to an email."""
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    reply_all: bool = False
    attachments: Optional[List[UUID]] = None


class EmailForward(BaseModel):
    """Schema for forwarding an email."""
    to: List[EmailStr]
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    include_attachments: bool = True


class EmailBulkAction(BaseModel):
    """Schema for bulk email operations."""
    email_ids: List[UUID]
    action: str  # mark_read, mark_unread, star, unstar, trash, delete, move, label
    folder_id: Optional[UUID] = None
    label_ids: Optional[List[UUID]] = None


class EmailListItem(BaseModel):
    """Schema for email list item."""
    id: UUID
    thread_id: Optional[UUID] = None
    from_address: str
    from_name: Optional[str] = None
    to_addresses: List[Dict[str, Any]]
    subject: Optional[str] = None
    snippet: Optional[str] = None
    date: datetime
    is_read: bool
    is_starred: bool
    has_attachments: bool = False
    attachment_count: int = 0
    labels: List[LabelResponse] = []
    folder: Optional[FolderResponse] = None
    
    model_config = ConfigDict(from_attributes=True)


class EmailSecurity(BaseModel):
    """Email security info."""
    dkim: Optional[str] = None
    spf: Optional[str] = None
    dmarc: Optional[str] = None


class EmailDetail(EmailBase):
    """Schema for full email detail."""
    id: UUID
    thread_id: Optional[UUID] = None
    message_id: Optional[str] = None
    from_address: str
    from_name: Optional[str] = None
    to_addresses: List[Dict[str, Any]]
    cc_addresses: List[Dict[str, Any]] = []
    bcc_addresses: List[Dict[str, Any]] = []
    reply_to: Optional[str] = None
    date: datetime
    received_at: datetime
    is_read: bool
    is_starred: bool
    is_draft: bool
    is_sent: bool
    folder: Optional[FolderResponse] = None
    labels: List[LabelResponse] = []
    attachments: List[AttachmentResponse] = []
    security: Optional[EmailSecurity] = None
    
    model_config = ConfigDict(from_attributes=True)


class EmailSendResponse(BaseModel):
    """Schema for email send response."""
    id: UUID
    message_id: str
    status: str = "sent"


# Filter schemas
class FilterCondition(BaseModel):
    """Email filter condition."""
    field: str  # from, to, subject, body
    operator: str  # contains, equals, starts_with, ends_with
    value: str


class FilterAction(BaseModel):
    """Email filter action."""
    type: str  # move, label, mark_read, delete, forward
    folder_id: Optional[UUID] = None
    label_id: Optional[UUID] = None
    forward_to: Optional[EmailStr] = None


class FilterCreate(BaseModel):
    """Schema for creating a filter."""
    name: str
    conditions: List[FilterCondition]
    actions: List[FilterAction]
    stop_processing: bool = False


class FilterUpdate(BaseModel):
    """Schema for updating a filter."""
    name: Optional[str] = None
    is_active: Optional[bool] = None
    conditions: Optional[List[FilterCondition]] = None
    actions: Optional[List[FilterAction]] = None
    stop_processing: Optional[bool] = None


class FilterResponse(BaseModel):
    """Schema for filter response."""
    id: UUID
    mailbox_id: UUID
    name: str
    is_active: bool
    priority: int
    conditions: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    stop_processing: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
