"""
OpenMail Platform - Domain and Mailbox Schemas
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# DNS Record schemas
class DNSRecordBase(BaseModel):
    """Base DNS record schema."""
    record_type: str
    name: str
    value: str
    priority: Optional[int] = None
    ttl: int = 3600


class DNSRecordResponse(DNSRecordBase):
    """Schema for DNS record response."""
    id: UUID
    purpose: Optional[str] = None
    is_verified: bool
    
    model_config = ConfigDict(from_attributes=True)


# Domain schemas
class DomainBase(BaseModel):
    """Base domain schema."""
    name: str


class DomainCreate(DomainBase):
    """Schema for creating a domain."""
    pass


class DomainResponse(DomainBase):
    """Schema for domain response."""
    id: UUID
    owner_id: UUID
    is_verified: bool
    verified_at: Optional[datetime] = None
    is_active: bool
    dkim_selector: str
    created_at: datetime
    dns_records: List[DNSRecordResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


class DomainVerifyResponse(BaseModel):
    """Schema for domain verification response."""
    is_verified: bool
    checks: Dict[str, Dict[str, Any]]


class DomainDNSResponse(BaseModel):
    """Schema for domain DNS records response."""
    domain: str
    records: List[DNSRecordResponse]


# Mailbox schemas
class MailboxBase(BaseModel):
    """Base mailbox schema."""
    local_part: str


class MailboxCreate(MailboxBase):
    """Schema for creating a mailbox."""
    domain_id: UUID


class MailboxUpdate(BaseModel):
    """Schema for updating a mailbox."""
    is_active: Optional[bool] = None
    is_primary: Optional[bool] = None
    auto_reply_enabled: Optional[bool] = None
    auto_reply_subject: Optional[str] = None
    auto_reply_body: Optional[str] = None
    auto_reply_start: Optional[datetime] = None
    auto_reply_end: Optional[datetime] = None
    forward_to: Optional[List[EmailStr]] = None
    forward_keep_copy: Optional[bool] = None


class MailboxResponse(MailboxBase):
    """Schema for mailbox response."""
    id: UUID
    user_id: UUID
    domain_id: UUID
    full_address: str
    quota_bytes: int
    used_bytes: int
    is_active: bool
    is_primary: bool
    auto_reply_enabled: bool
    forward_to: Optional[List[str]] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
    @property
    def quota_used_percent(self) -> float:
        if self.quota_bytes == 0:
            return 0.0
        return (self.used_bytes / self.quota_bytes) * 100


class MailboxStats(BaseModel):
    """Schema for mailbox statistics."""
    id: UUID
    full_address: str
    quota_bytes: int
    used_bytes: int
    quota_used_percent: float
    total_emails: int
    unread_count: int
    spam_count: int
    trash_count: int
    
    model_config = ConfigDict(from_attributes=True)


class MailboxBrief(BaseModel):
    """Brief mailbox info for listings."""
    id: UUID
    full_address: str
    is_primary: bool
    unread_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)
