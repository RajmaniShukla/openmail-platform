"""
OpenMail Platform - Domain and Mailbox Models
"""
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer, Text,
    ForeignKey, BigInteger, Index, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.database import Base


class Domain(Base):
    """Domain model for custom email domains."""
    __tablename__ = "domains"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Verification
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_token: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # DKIM
    dkim_selector: Mapped[str] = mapped_column(String(50), default="mail")
    dkim_private_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dkim_public_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="domains")
    dns_records: Mapped[List["DNSRecord"]] = relationship(
        "DNSRecord",
        back_populates="domain",
        cascade="all, delete-orphan"
    )
    mailboxes: Mapped[List["Mailbox"]] = relationship(
        "Mailbox",
        back_populates="domain",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Domain {self.name}>"


class DNSRecord(Base):
    """DNS records required for domain verification."""
    __tablename__ = "dns_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    domain_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("domains.id", ondelete="CASCADE"),
        nullable=False
    )
    
    record_type: Mapped[str] = mapped_column(String(10), nullable=False)  # MX, TXT, CNAME, A
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ttl: Mapped[int] = mapped_column(Integer, default=3600)
    
    purpose: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # mx, spf, dkim, dmarc, verification
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationship
    domain: Mapped["Domain"] = relationship("Domain", back_populates="dns_records")

    def __repr__(self) -> str:
        return f"<DNSRecord {self.record_type} {self.name}>"


class Mailbox(Base):
    """Mailbox model for email addresses."""
    __tablename__ = "mailboxes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    domain_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("domains.id", ondelete="CASCADE"),
        nullable=False
    )
    
    local_part: Mapped[str] = mapped_column(String(64), nullable=False)
    full_address: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    
    # Quotas (in bytes)
    quota_bytes: Mapped[int] = mapped_column(BigInteger, default=5368709120)  # 5GB
    used_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Auto-reply
    auto_reply_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_reply_subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    auto_reply_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    auto_reply_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    auto_reply_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Forwarding
    forward_to: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    forward_keep_copy: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="mailboxes")
    domain: Mapped["Domain"] = relationship("Domain", back_populates="mailboxes")
    folders: Mapped[List["Folder"]] = relationship(
        "Folder",
        back_populates="mailbox",
        cascade="all, delete-orphan"
    )
    labels: Mapped[List["Label"]] = relationship(
        "Label",
        back_populates="mailbox",
        cascade="all, delete-orphan"
    )
    emails: Mapped[List["Email"]] = relationship(
        "Email",
        back_populates="mailbox",
        cascade="all, delete-orphan"
    )
    filters: Mapped[List["EmailFilter"]] = relationship(
        "EmailFilter",
        back_populates="mailbox",
        cascade="all, delete-orphan"
    )

    @property
    def quota_used_percent(self) -> float:
        if self.quota_bytes == 0:
            return 0.0
        return (self.used_bytes / self.quota_bytes) * 100

    def __repr__(self) -> str:
        return f"<Mailbox {self.full_address}>"


# Import at end to avoid circular imports
from app.models.user import User
from app.models.email import Folder, Label, Email, EmailFilter
