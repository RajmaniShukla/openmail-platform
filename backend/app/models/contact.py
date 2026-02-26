"""
OpenMail Platform - Contact Model
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.database import Base


class Contact(Base):
    """Contact/address book model."""
    __tablename__ = "contacts"

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
    
    # Contact info
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(200))
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    company: Mapped[Optional[str]] = mapped_column(String(200))
    job_title: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Extra fields
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Metadata
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    frequency: Mapped[int] = mapped_column(Integer, default=0)  # Contact frequency
    last_contacted: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user = relationship("User", back_populates="contacts")
    
    def __repr__(self):
        return f"<Contact(email={self.email}, name={self.name})>"
    
    @property
    def display_name(self) -> str:
        """Get display name for contact."""
        if self.name:
            return self.name
        if self.first_name or self.last_name:
            return f"{self.first_name or ''} {self.last_name or ''}".strip()
        return self.email


class ContactGroup(Base):
    """Contact group model for organizing contacts."""
    __tablename__ = "contact_groups"
    
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
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    color: Mapped[Optional[str]] = mapped_column(String(7))
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow
    )
    
    # Relationships
    user = relationship("User", back_populates="contact_groups")
    members = relationship(
        "Contact",
        secondary="contact_group_members",
        backref="groups"
    )


# Junction table for contact groups
from sqlalchemy import Table

contact_group_members = Table(
    "contact_group_members",
    Base.metadata,
    Column(
        "contact_id",
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        primary_key=True
    ),
    Column(
        "group_id",
        UUID(as_uuid=True),
        ForeignKey("contact_groups.id", ondelete="CASCADE"),
        primary_key=True
    ),
    Column("added_at", DateTime(timezone=True), default=datetime.utcnow),
)
