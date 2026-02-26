"""
Email Service - Handles email operations
"""
import asyncio
import email
import os
import uuid
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
import aiosmtplib
import aioimaplib
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.orm import selectinload

from app.models.email import Email, Attachment, Folder, Label, EmailLabel
from app.models.user import Mailbox
from app.core.config import settings
from app.db.database import get_redis


class EmailService:
    """Service for handling email operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_emails(
        self,
        mailbox_id: uuid.UUID,
        folder: Optional[str] = None,
        folder_id: Optional[uuid.UUID] = None,
        label_id: Optional[uuid.UUID] = None,
        is_read: Optional[bool] = None,
        is_starred: Optional[bool] = None,
        has_attachments: Optional[bool] = None,
        search_query: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Email]:
        """Get emails with filters"""
        query = (
            select(Email)
            .options(selectinload(Email.attachments), selectinload(Email.labels))
            .where(Email.mailbox_id == mailbox_id)
            .order_by(Email.date.desc())
        )
        
        if folder:
            query = query.join(Folder).where(Folder.type == folder)
        elif folder_id:
            query = query.where(Email.folder_id == folder_id)
        
        if label_id:
            query = query.join(EmailLabel).where(EmailLabel.label_id == label_id)
        
        if is_read is not None:
            query = query.where(Email.is_read == is_read)
        
        if is_starred is not None:
            query = query.where(Email.is_starred == is_starred)
        
        if has_attachments is not None:
            query = query.where(Email.has_attachments == has_attachments)
        
        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.where(
                or_(
                    Email.subject.ilike(search_pattern),
                    Email.body_text.ilike(search_pattern),
                    Email.from_address.ilike(search_pattern),
                )
            )
        
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_email(self, email_id: uuid.UUID, mailbox_id: uuid.UUID) -> Optional[Email]:
        """Get a single email by ID"""
        query = (
            select(Email)
            .options(selectinload(Email.attachments), selectinload(Email.labels))
            .where(and_(Email.id == email_id, Email.mailbox_id == mailbox_id))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def create_email(
        self,
        mailbox_id: uuid.UUID,
        folder_id: uuid.UUID,
        from_address: str,
        from_name: Optional[str],
        to_addresses: List[str],
        subject: str,
        body_html: Optional[str],
        body_text: Optional[str],
        cc_addresses: Optional[List[str]] = None,
        bcc_addresses: Optional[List[str]] = None,
        in_reply_to: Optional[str] = None,
        thread_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Email:
        """Create a new email record"""
        message_id = f"<{uuid.uuid4()}@{settings.DOMAIN}>"
        
        # Generate thread ID if not provided
        if not thread_id:
            thread_id = str(uuid.uuid4())
        
        # Calculate snippet
        snippet = (body_text or "")[:200] if body_text else ""
        
        email_obj = Email(
            id=uuid.uuid4(),
            mailbox_id=mailbox_id,
            folder_id=folder_id,
            message_id=message_id,
            thread_id=thread_id,
            in_reply_to=in_reply_to,
            from_address=from_address,
            from_name=from_name,
            to_addresses=to_addresses,
            cc_addresses=cc_addresses or [],
            bcc_addresses=bcc_addresses or [],
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            snippet=snippet,
            date=datetime.utcnow(),
            headers=headers or {},
            is_read=True,  # Sent emails are always read
            is_starred=False,
            is_draft=False,
            has_attachments=False,
        )
        
        self.db.add(email_obj)
        await self.db.commit()
        await self.db.refresh(email_obj)
        return email_obj
    
    async def update_email(
        self,
        email_id: uuid.UUID,
        mailbox_id: uuid.UUID,
        **kwargs
    ) -> Optional[Email]:
        """Update an email"""
        email_obj = await self.get_email(email_id, mailbox_id)
        if not email_obj:
            return None
        
        for key, value in kwargs.items():
            if hasattr(email_obj, key):
                setattr(email_obj, key, value)
        
        email_obj.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(email_obj)
        return email_obj
    
    async def delete_email(
        self,
        email_id: uuid.UUID,
        mailbox_id: uuid.UUID,
        permanent: bool = False
    ) -> bool:
        """Delete or move email to trash"""
        email_obj = await self.get_email(email_id, mailbox_id)
        if not email_obj:
            return False
        
        if permanent:
            # Permanently delete
            await self.db.delete(email_obj)
        else:
            # Move to trash
            trash_folder = await self._get_folder_by_type(mailbox_id, "trash")
            if trash_folder:
                email_obj.folder_id = trash_folder.id
                email_obj.updated_at = datetime.utcnow()
        
        await self.db.commit()
        return True
    
    async def bulk_update(
        self,
        email_ids: List[uuid.UUID],
        mailbox_id: uuid.UUID,
        **kwargs
    ) -> int:
        """Bulk update emails"""
        stmt = (
            update(Email)
            .where(and_(Email.id.in_(email_ids), Email.mailbox_id == mailbox_id))
            .values(**kwargs, updated_at=datetime.utcnow())
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount
    
    async def move_emails(
        self,
        email_ids: List[uuid.UUID],
        mailbox_id: uuid.UUID,
        target_folder_id: uuid.UUID
    ) -> int:
        """Move emails to a different folder"""
        return await self.bulk_update(
            email_ids,
            mailbox_id,
            folder_id=target_folder_id
        )
    
    async def send_email(
        self,
        mailbox: Mailbox,
        to_addresses: List[str],
        subject: str,
        body_html: Optional[str] = None,
        body_text: Optional[str] = None,
        cc_addresses: Optional[List[str]] = None,
        bcc_addresses: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        in_reply_to: Optional[str] = None,
        thread_id: Optional[str] = None,
    ) -> Email:
        """Send an email via SMTP"""
        # Build the message
        if body_html:
            msg = MIMEMultipart("alternative")
            if body_text:
                msg.attach(MIMEText(body_text, "plain"))
            msg.attach(MIMEText(body_html, "html"))
        else:
            msg = MIMEText(body_text or "", "plain")
        
        msg["From"] = f"{mailbox.display_name} <{mailbox.email}>" if mailbox.display_name else mailbox.email
        msg["To"] = ", ".join(to_addresses)
        msg["Subject"] = subject
        msg["Date"] = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
        msg["Message-ID"] = f"<{uuid.uuid4()}@{settings.DOMAIN}>"
        
        if cc_addresses:
            msg["Cc"] = ", ".join(cc_addresses)
        
        if in_reply_to:
            msg["In-Reply-To"] = in_reply_to
            msg["References"] = in_reply_to
        
        # Add attachments
        if attachments:
            outer = MIMEMultipart()
            outer.attach(msg)
            for att in attachments:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(att["content"])
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f'attachment; filename="{att["filename"]}"'
                )
                outer.attach(part)
            msg = outer
        
        # Send via SMTP
        all_recipients = to_addresses + (cc_addresses or []) + (bcc_addresses or [])
        
        try:
            async with aiosmtplib.SMTP(
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                use_tls=settings.SMTP_TLS,
            ) as smtp:
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    await smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                
                await smtp.send_message(msg, recipients=all_recipients)
        except Exception as e:
            raise Exception(f"Failed to send email: {str(e)}")
        
        # Save to sent folder
        sent_folder = await self._get_folder_by_type(mailbox.id, "sent")
        if sent_folder:
            email_obj = await self.create_email(
                mailbox_id=mailbox.id,
                folder_id=sent_folder.id,
                from_address=mailbox.email,
                from_name=mailbox.display_name,
                to_addresses=to_addresses,
                cc_addresses=cc_addresses,
                bcc_addresses=bcc_addresses,
                subject=subject,
                body_html=body_html,
                body_text=body_text,
                in_reply_to=in_reply_to,
                thread_id=thread_id,
            )
            return email_obj
        
        return None
    
    async def _get_folder_by_type(self, mailbox_id: uuid.UUID, folder_type: str) -> Optional[Folder]:
        """Get a folder by type"""
        query = select(Folder).where(
            and_(Folder.mailbox_id == mailbox_id, Folder.type == folder_type)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def search_emails(
        self,
        mailbox_id: uuid.UUID,
        query: str,
        from_address: Optional[str] = None,
        to_address: Optional[str] = None,
        has_attachment: Optional[bool] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        folder: Optional[str] = None,
        limit: int = 50,
    ) -> List[Email]:
        """Advanced email search"""
        # For production, this would use Elasticsearch
        # For now, use PostgreSQL full-text search
        search_query = (
            select(Email)
            .options(selectinload(Email.attachments), selectinload(Email.labels))
            .where(Email.mailbox_id == mailbox_id)
        )
        
        if query:
            pattern = f"%{query}%"
            search_query = search_query.where(
                or_(
                    Email.subject.ilike(pattern),
                    Email.body_text.ilike(pattern),
                    Email.from_address.ilike(pattern),
                    Email.from_name.ilike(pattern),
                )
            )
        
        if from_address:
            search_query = search_query.where(Email.from_address.ilike(f"%{from_address}%"))
        
        if to_address:
            search_query = search_query.where(Email.to_addresses.contains([to_address]))
        
        if has_attachment is not None:
            search_query = search_query.where(Email.has_attachments == has_attachment)
        
        if date_from:
            search_query = search_query.where(Email.date >= date_from)
        
        if date_to:
            search_query = search_query.where(Email.date <= date_to)
        
        if folder:
            search_query = search_query.join(Folder).where(Folder.type == folder)
        
        search_query = search_query.order_by(Email.date.desc()).limit(limit)
        
        result = await self.db.execute(search_query)
        return result.scalars().all()


class IMAPSyncService:
    """Service for syncing emails via IMAP"""
    
    def __init__(self, db: AsyncSession, mailbox: Mailbox):
        self.db = db
        self.mailbox = mailbox
    
    async def sync_folder(self, folder_name: str = "INBOX") -> int:
        """Sync emails from an IMAP folder"""
        # This would connect to the IMAP server and sync emails
        # Implementation depends on the specific IMAP library used
        pass
    
    async def full_sync(self) -> Dict[str, int]:
        """Perform a full sync of all folders"""
        pass


class SpamFilterService:
    """Service for spam filtering"""
    
    @staticmethod
    async def check_spam(email_content: str, headers: Dict[str, str]) -> float:
        """
        Check if an email is spam
        Returns a spam score from 0.0 to 1.0
        """
        # In production, this would integrate with SpamAssassin or similar
        spam_score = 0.0
        
        # Simple heuristics for demo
        spam_keywords = ["viagra", "lottery", "winner", "prize", "nigerian", "prince"]
        content_lower = email_content.lower()
        
        for keyword in spam_keywords:
            if keyword in content_lower:
                spam_score += 0.2
        
        # Check for suspicious headers
        if "X-Spam-Flag" in headers and headers["X-Spam-Flag"].upper() == "YES":
            spam_score = 1.0
        
        return min(spam_score, 1.0)
