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

from app.models.email import Email, Attachment, Folder, Label, email_labels
from app.models.domain import Mailbox
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
            query = query.join(email_labels, email_labels.c.email_id == Email.id).where(email_labels.c.label_id == label_id)
        
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
        """Sync emails from an IMAP folder via aioimaplib."""
        from app.core.config import settings
        import email as email_lib
        from email.policy import default as email_policy

        imap_host = settings.POSTFIX_HOST  # Dovecot runs on same host
        imap_port = 993

        imap = aioimaplib.IMAP4_SSL(host=imap_host, port=imap_port)
        await imap.wait_hello_from_server()

        login_resp = await imap.login(self.mailbox.email, self.mailbox.password or "")
        if login_resp.result != "OK":
            return 0

        await imap.select(folder_name)

        # Fetch UIDs of all messages
        _, uid_data = await imap.uid("search", "ALL")
        if not uid_data or not uid_data[0]:
            await imap.logout()
            return 0

        uids = uid_data[0].split()
        if not uids:
            await imap.logout()
            return 0

        # Only sync the most recent 100 messages to avoid overload
        uids_to_sync = uids[-100:]

        # Get existing message IDs from DB to avoid duplicates
        existing = await self.db.execute(
            select(Email.message_id).where(Email.mailbox_id == self.mailbox.id)
        )
        existing_ids: set = {row[0] for row in existing.fetchall() if row[0]}

        # Determine target folder
        folder_obj = await self._get_folder_by_type(self.mailbox.id, folder_name.lower() if folder_name.lower() in {"inbox", "sent", "drafts", "spam", "trash"} else "inbox")

        synced = 0
        for uid in uids_to_sync:
            try:
                _, msg_data = await imap.uid("fetch", uid, "(RFC822)")
                if not msg_data or len(msg_data) < 2:
                    continue

                raw_bytes = msg_data[1]
                if isinstance(raw_bytes, (bytes, bytearray)):
                    raw_str = raw_bytes.decode("utf-8", errors="replace")
                else:
                    continue

                msg = email_lib.message_from_string(raw_str, policy=email_policy)
                message_id = msg.get("Message-ID", "").strip()

                if message_id and message_id in existing_ids:
                    continue  # Already have this one

                # Extract body parts
                body_text, body_html = "", ""
                if msg.is_multipart():
                    for part in msg.walk():
                        ct = part.get_content_type()
                        if ct == "text/plain" and not body_text:
                            body_text = part.get_content()
                        elif ct == "text/html" and not body_html:
                            body_html = part.get_content()
                else:
                    if msg.get_content_type() == "text/html":
                        body_html = msg.get_content()
                    else:
                        body_text = msg.get_content()

                # Parse addresses
                from_header = msg.get("From", "")
                from_addr = from_header
                from_name = None
                if "<" in from_header:
                    parts = from_header.split("<")
                    from_name = parts[0].strip().strip('"')
                    from_addr = parts[1].rstrip(">")

                to_raw = msg.get("To", "")
                to_addresses = [{"address": a.strip(), "name": None} for a in to_raw.split(",") if a.strip()]

                import uuid as uuid_lib
                from datetime import timezone
                date_header = msg.get("Date")
                try:
                    from email.utils import parsedate_to_datetime
                    mail_date = parsedate_to_datetime(date_header) if date_header else datetime.utcnow()
                    if mail_date.tzinfo is not None:
                        mail_date = mail_date.astimezone(timezone.utc).replace(tzinfo=None)
                except Exception:
                    mail_date = datetime.utcnow()

                email_obj = Email(
                    id=uuid_lib.uuid4(),
                    mailbox_id=self.mailbox.id,
                    folder_id=folder_obj.id if folder_obj else None,
                    message_id=message_id or str(uuid_lib.uuid4()),
                    thread_id=uuid_lib.uuid4(),
                    in_reply_to=msg.get("In-Reply-To"),
                    from_address=from_addr,
                    from_name=from_name,
                    to_addresses=to_addresses,
                    subject=msg.get("Subject", ""),
                    body_text=body_text,
                    body_html=body_html,
                    snippet=body_text[:200] if body_text else body_html[:200] if body_html else "",
                    date=mail_date,
                    is_read=False,
                    is_starred=False,
                    is_draft=False,
                    is_sent=folder_name.lower() == "sent",
                )
                self.db.add(email_obj)
                existing_ids.add(message_id)
                synced += 1

            except Exception:
                continue  # Skip malformed messages

        if synced > 0:
            await self.db.commit()

        await imap.logout()
        return synced

    async def full_sync(self) -> Dict[str, int]:
        """Perform a full sync of inbox, sent, drafts, spam, trash."""
        folders_to_sync = [
            ("INBOX", "inbox"),
            ("Sent", "sent"),
            ("Drafts", "drafts"),
            ("Spam", "spam"),
            ("Trash", "trash"),
        ]
        results: Dict[str, int] = {}
        for imap_folder, _ in folders_to_sync:
            try:
                count = await self.sync_folder(imap_folder)
                results[imap_folder] = count
            except Exception:
                results[imap_folder] = 0
        return results


class SpamFilterService:
    """Service for spam filtering via SpamAssassin spamd protocol."""

    @staticmethod
    async def check_spam(email_content: str, headers: Dict[str, str]) -> float:
        """
        Check email against SpamAssassin via the SPAMC protocol.
        Returns a normalized spam score 0.0–1.0 (threshold is settings.SPAM_THRESHOLD).
        Falls back to heuristic check if SpamAssassin is unavailable.
        """
        import asyncio
        from app.core.config import settings

        # --- Try SpamAssassin first ---
        try:
            raw = email_content.encode("utf-8", errors="replace")
            request = (
                f"REPORT SPAMC/1.5\r\n"
                f"Content-length: {len(raw)}\r\n"
                f"User: openmail\r\n"
                f"\r\n"
            ).encode() + raw

            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(settings.SPAMASSASSIN_HOST, settings.SPAMASSASSIN_PORT),
                timeout=5.0,
            )
            writer.write(request)
            await writer.drain()
            writer.write_eof()

            response = await asyncio.wait_for(reader.read(65536), timeout=10.0)
            writer.close()
            await writer.wait_closed()

            response_str = response.decode("utf-8", errors="replace")
            # Parse score line: e.g. "Spam: True ; 8.3 / 5.0"
            for line in response_str.splitlines():
                if line.lower().startswith("spam:"):
                    parts = line.split(";")
                    if len(parts) >= 2:
                        score_part = parts[1].strip().split("/")
                        raw_score = float(score_part[0].strip())
                        threshold = float(score_part[1].strip()) if len(score_part) > 1 else settings.SPAM_THRESHOLD
                        # Normalize to 0.0–1.0
                        return min(max(raw_score / max(threshold * 2, 1), 0.0), 1.0)
        except Exception:
            pass  # SpamAssassin unavailable — fall through to heuristics

        # --- Heuristic fallback ---
        spam_score = 0.0
        spam_keywords = ["viagra", "lottery", "winner", "prize", "nigerian", "prince",
                         "click here", "act now", "free money", "earn $", "make money fast"]
        content_lower = email_content.lower()
        for keyword in spam_keywords:
            if keyword in content_lower:
                spam_score += 0.15

        # Header signals
        if headers.get("X-Spam-Flag", "").upper() == "YES":
            spam_score = 1.0
        if headers.get("X-Spam-Status", "").lower().startswith("yes"):
            spam_score = max(spam_score, 0.9)

        # Missing standard headers is a mild signal
        if not headers.get("Date"):
            spam_score += 0.1
        if not headers.get("Message-ID"):
            spam_score += 0.1

        return min(spam_score, 1.0)
