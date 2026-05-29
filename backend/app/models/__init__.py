"""
OpenMail Models - Import all models for Alembic to detect
"""
from app.db.database import Base

from app.models.user import User, Session
from app.models.domain import Domain, Mailbox
from app.models.domain import Domain
from app.models.email import Email, Folder, Label, Attachment, EmailFilter, email_labels

__all__ = [
    "Base",
    "User",
    "Mailbox",
    "Session",
    "Domain",
    "Email",
    "Folder",
    "Label",
    "Attachment",
    "EmailFilter",
    "email_labels",
]
