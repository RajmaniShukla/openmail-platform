"""
OpenMail Platform - Email Models
"""
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer, Text,
    ForeignKey, BigInteger, Float, Index, Table
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.database import Base


class Folder(Base):
    """Email folder model."""
    __tablename__ = "folders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    mailbox_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mailboxes.id", ondelete="CASCADE"),
        nullable=False
    )
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(
        String(20),
        default="custom"
    )  # inbox, sent, drafts, spam, trash, starred, custom
    
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("folders.id", ondelete="CASCADE"),
        nullable=True
    )
    
    # Cached counts
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    unread_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Display
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
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
    mailbox: Mapped["Mailbox"] = relationship("Mailbox", back_populates="folders")
    parent: Mapped[Optional["Folder"]] = relationship(
        "Folder",
        remote_side=[id],
        backref="children"
    )
    emails: Mapped[List["Email"]] = relationship(
        "Email",
        back_populates="folder",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Folder {self.name}>"


class Label(Base):
    """Email label model."""
    __tablename__ = "labels"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    mailbox_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mailboxes.id", ondelete="CASCADE"),
        nullable=False
    )
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(7), default="#808080")
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Relationships
    mailbox: Mapped["Mailbox"] = relationship("Mailbox", back_populates="labels")
    emails: Mapped[List["Email"]] = relationship(
        "Email",
        secondary="email_labels",
        back_populates="labels"
    )

    def __repr__(self) -> str:
        return f"<Label {self.name}>"


# Association table for email-label many-to-many
email_labels = Table(
    "email_labels",
    Base.metadata,
    Column("email_id", UUID(as_uuid=True), ForeignKey("emails.id", ondelete="CASCADE"), primary_key=True),
    Column("label_id", UUID(as_uuid=True), ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now())
)


class Email(Base):
    """Email model."""
    __tablename__ = "emails"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    mailbox_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mailboxes.id", ondelete="CASCADE"),
        nullable=False
    )
    folder_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("folders.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Message ID (RFC 5322)
    message_id: Mapped[Optional[str]] = mapped_column(String(500), unique=True, nullable=True)
    
    # Threading
    thread_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    in_reply_to: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    references: Mapped[Optional[list]] = mapped_column(ARRAY(String), nullable=True)
    
    # Envelope
    from_address: Mapped[str] = mapped_column(String(255), nullable=False)
    from_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    to_addresses: Mapped[list] = mapped_column(JSON, default=list)
    cc_addresses: Mapped[list] = mapped_column(JSON, default=list)
    bcc_addresses: Mapped[list] = mapped_column(JSON, default=list)
    reply_to: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Content
    subject: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    body_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    body_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    snippet: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Storage
    raw_message_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    maildir_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    
    # Flags
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_starred: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_draft: Mapped[bool] = mapped_column(Boolean, default=False)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    is_spam: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_trash: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Spam
    spam_score: Mapped[float] = mapped_column(Float, default=0)
    spam_report: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Security
    has_dkim: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_spf: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    dkim_result: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    spf_result: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    dmarc_result: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Timestamps
    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relationships
    mailbox: Mapped["Mailbox"] = relationship("Mailbox", back_populates="emails")
    folder: Mapped[Optional["Folder"]] = relationship("Folder", back_populates="emails")
    attachments: Mapped[List["Attachment"]] = relationship(
        "Attachment",
        back_populates="email",
        cascade="all, delete-orphan"
    )
    labels: Mapped[List["Label"]] = relationship(
        "Label",
        secondary="email_labels",
        back_populates="emails"
    )

    # Indexes
    __table_args__ = (
        Index("idx_emails_mailbox_date", "mailbox_id", "date"),
        Index("idx_emails_thread", "thread_id"),
        Index("idx_emails_from", "from_address"),
    )

    @property
    def has_attachments(self) -> bool:
        return len(self.attachments) > 0

    def __repr__(self) -> str:
        return f"<Email {self.subject[:50] if self.subject else 'No Subject'}>"


class Attachment(Base):
    """Email attachment model."""
    __tablename__ = "attachments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    email_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("emails.id", ondelete="CASCADE"),
        nullable=False
    )
    
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    
    # Storage
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_bucket: Mapped[str] = mapped_column(String(100), default="attachments")
    
    # Metadata
    content_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_inline: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Checksum
    checksum_md5: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    checksum_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Relationship
    email: Mapped["Email"] = relationship("Email", back_populates="attachments")

    def __repr__(self) -> str:
        return f"<Attachment {self.filename}>"


class EmailFilter(Base):
    """Email filter/rule model."""
    __tablename__ = "email_filters"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    mailbox_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mailboxes.id", ondelete="CASCADE"),
        nullable=False
    )
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    
    # Conditions (JSON array)
    conditions: Mapped[list] = mapped_column(JSON, nullable=False)
    # Example: [{"field": "from", "operator": "contains", "value": "@example.com"}]
    
    # Actions (JSON array)
    actions: Mapped[list] = mapped_column(JSON, nullable=False)
    # Example: [{"type": "move", "folder_id": "uuid"}, {"type": "label", "label_id": "uuid"}]
    
    stop_processing: Mapped[bool] = mapped_column(Boolean, default=False)
    
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
    mailbox: Mapped["Mailbox"] = relationship("Mailbox", back_populates="filters")

    def __repr__(self) -> str:
        return f"<EmailFilter {self.name}>"


# Import at end to avoid circular imports
from app.models.domain import Mailbox
