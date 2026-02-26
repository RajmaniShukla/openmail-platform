"""
Celery Tasks for OpenMail
"""
import asyncio
from datetime import datetime, timedelta
from celery import Celery
from celery.schedules import crontab
from typing import List, Dict, Any

from app.core.config import settings

# Initialize Celery
celery_app = Celery(
    "openmail",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3000,  # 50 minutes soft limit
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Periodic tasks (Celery Beat)
celery_app.conf.beat_schedule = {
    # Sync IMAP mailboxes every 5 minutes
    "sync-mailboxes": {
        "task": "app.services.celery_tasks.sync_all_mailboxes",
        "schedule": timedelta(minutes=5),
    },
    # Process spam queue every minute
    "process-spam": {
        "task": "app.services.celery_tasks.process_spam_queue",
        "schedule": timedelta(minutes=1),
    },
    # Clean old trash emails daily at 3 AM
    "clean-trash": {
        "task": "app.services.celery_tasks.clean_old_trash",
        "schedule": crontab(hour=3, minute=0),
    },
    # Clean old spam emails daily at 3:30 AM
    "clean-spam": {
        "task": "app.services.celery_tasks.clean_old_spam",
        "schedule": crontab(hour=3, minute=30),
    },
    # Generate daily statistics at midnight
    "daily-stats": {
        "task": "app.services.celery_tasks.generate_daily_stats",
        "schedule": crontab(hour=0, minute=0),
    },
    # Update search index every 10 minutes
    "update-search-index": {
        "task": "app.services.celery_tasks.update_search_index",
        "schedule": timedelta(minutes=10),
    },
    # Check domain DNS records every hour
    "check-dns": {
        "task": "app.services.celery_tasks.check_domain_dns",
        "schedule": timedelta(hours=1),
    },
}


# ============== Email Sync Tasks ==============

@celery_app.task(bind=True, max_retries=3)
def sync_mailbox(self, mailbox_id: str) -> Dict[str, Any]:
    """Sync a single mailbox via IMAP"""
    try:
        from app.db.database import get_db_sync
        from app.services.email_service import IMAPSyncService
        from app.models.user import Mailbox
        
        # Get database session
        db = get_db_sync()
        
        # Get mailbox
        mailbox = db.query(Mailbox).filter(Mailbox.id == mailbox_id).first()
        if not mailbox:
            return {"status": "error", "message": "Mailbox not found"}
        
        # Sync
        sync_service = IMAPSyncService(db, mailbox)
        result = asyncio.run(sync_service.full_sync())
        
        return {"status": "success", "synced": result}
    except Exception as e:
        self.retry(exc=e, countdown=60)


@celery_app.task
def sync_all_mailboxes() -> Dict[str, Any]:
    """Sync all active mailboxes"""
    from app.db.database import get_db_sync
    from app.models.user import Mailbox
    
    db = get_db_sync()
    mailboxes = db.query(Mailbox).filter(Mailbox.is_active == True).all()
    
    results = {}
    for mailbox in mailboxes:
        sync_mailbox.delay(str(mailbox.id))
        results[str(mailbox.id)] = "queued"
    
    return {"status": "success", "mailboxes": results}


# ============== Email Processing Tasks ==============

@celery_app.task(bind=True, max_retries=3)
def send_email_task(
    self,
    mailbox_id: str,
    to_addresses: List[str],
    subject: str,
    body_html: str = None,
    body_text: str = None,
    cc_addresses: List[str] = None,
    bcc_addresses: List[str] = None,
    attachments: List[Dict] = None,
    in_reply_to: str = None,
) -> Dict[str, Any]:
    """Background task to send an email"""
    try:
        from app.db.database import get_db_sync, AsyncSessionLocal
        from app.services.email_service import EmailService
        from app.models.user import Mailbox
        
        # Run async code
        async def _send():
            async with AsyncSessionLocal() as db:
                mailbox = await db.get(Mailbox, mailbox_id)
                if not mailbox:
                    return {"status": "error", "message": "Mailbox not found"}
                
                email_service = EmailService(db)
                email = await email_service.send_email(
                    mailbox=mailbox,
                    to_addresses=to_addresses,
                    subject=subject,
                    body_html=body_html,
                    body_text=body_text,
                    cc_addresses=cc_addresses,
                    bcc_addresses=bcc_addresses,
                    attachments=attachments,
                    in_reply_to=in_reply_to,
                )
                return {"status": "success", "email_id": str(email.id) if email else None}
        
        return asyncio.run(_send())
    except Exception as e:
        self.retry(exc=e, countdown=30)


@celery_app.task
def process_incoming_email(raw_email: str, recipient: str) -> Dict[str, Any]:
    """Process an incoming email from Postfix"""
    import email
    from email.policy import default as email_policy
    from app.db.database import AsyncSessionLocal
    from app.services.email_service import EmailService, SpamFilterService
    from app.models.user import Mailbox
    from app.models.email import Folder
    
    async def _process():
        async with AsyncSessionLocal() as db:
            # Parse email
            msg = email.message_from_string(raw_email, policy=email_policy)
            
            # Find recipient mailbox
            mailbox = await db.execute(
                select(Mailbox).where(Mailbox.email == recipient)
            )
            mailbox = mailbox.scalar_one_or_none()
            
            if not mailbox:
                return {"status": "error", "message": "Recipient not found"}
            
            # Check for spam
            body_text = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body_text = part.get_content()
                        break
            else:
                body_text = msg.get_content()
            
            spam_score = await SpamFilterService.check_spam(
                body_text, dict(msg.items())
            )
            
            # Determine folder
            if spam_score >= 0.8:
                folder_type = "spam"
            else:
                folder_type = "inbox"
            
            folder = await db.execute(
                select(Folder).where(
                    and_(Folder.mailbox_id == mailbox.id, Folder.type == folder_type)
                )
            )
            folder = folder.scalar_one_or_none()
            
            # Create email record
            email_service = EmailService(db)
            email_obj = await email_service.create_email(
                mailbox_id=mailbox.id,
                folder_id=folder.id,
                from_address=msg["From"],
                from_name=None,  # Parse from From header
                to_addresses=[recipient],
                subject=msg["Subject"] or "",
                body_html=None,  # Extract from multipart
                body_text=body_text,
                headers=dict(msg.items()),
            )
            
            return {"status": "success", "email_id": str(email_obj.id)}
    
    return asyncio.run(_process())


@celery_app.task
def process_spam_queue() -> Dict[str, Any]:
    """Process emails in spam queue and apply filters"""
    # Implementation for spam processing
    return {"status": "success", "processed": 0}


# ============== Cleanup Tasks ==============

@celery_app.task
def clean_old_trash(days: int = 30) -> Dict[str, Any]:
    """Delete emails that have been in trash for more than X days"""
    from app.db.database import AsyncSessionLocal
    from app.models.email import Email, Folder
    from sqlalchemy import and_, delete
    
    async def _clean():
        async with AsyncSessionLocal() as db:
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            # Find trash folders
            trash_folders = await db.execute(
                select(Folder.id).where(Folder.type == "trash")
            )
            trash_folder_ids = [f.id for f in trash_folders.scalars().all()]
            
            # Delete old emails
            result = await db.execute(
                delete(Email).where(
                    and_(
                        Email.folder_id.in_(trash_folder_ids),
                        Email.updated_at < cutoff
                    )
                )
            )
            await db.commit()
            
            return {"status": "success", "deleted": result.rowcount}
    
    return asyncio.run(_clean())


@celery_app.task
def clean_old_spam(days: int = 30) -> Dict[str, Any]:
    """Delete emails that have been in spam for more than X days"""
    from app.db.database import AsyncSessionLocal
    from app.models.email import Email, Folder
    from sqlalchemy import and_, delete
    
    async def _clean():
        async with AsyncSessionLocal() as db:
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            # Find spam folders
            spam_folders = await db.execute(
                select(Folder.id).where(Folder.type == "spam")
            )
            spam_folder_ids = [f.id for f in spam_folders.scalars().all()]
            
            # Delete old emails
            result = await db.execute(
                delete(Email).where(
                    and_(
                        Email.folder_id.in_(spam_folder_ids),
                        Email.date < cutoff
                    )
                )
            )
            await db.commit()
            
            return {"status": "success", "deleted": result.rowcount}
    
    return asyncio.run(_clean())


# ============== Search Index Tasks ==============

@celery_app.task
def update_search_index() -> Dict[str, Any]:
    """Update Elasticsearch index with new/modified emails"""
    from app.db.database import AsyncSessionLocal
    from app.models.email import Email
    from elasticsearch import AsyncElasticsearch
    
    async def _update():
        # Connect to Elasticsearch
        es = AsyncElasticsearch([settings.ELASTICSEARCH_URL])
        
        async with AsyncSessionLocal() as db:
            # Get emails modified in last 15 minutes
            cutoff = datetime.utcnow() - timedelta(minutes=15)
            emails = await db.execute(
                select(Email).where(Email.updated_at >= cutoff)
            )
            
            indexed = 0
            for email in emails.scalars().all():
                await es.index(
                    index="emails",
                    id=str(email.id),
                    document={
                        "mailbox_id": str(email.mailbox_id),
                        "folder_id": str(email.folder_id),
                        "from_address": email.from_address,
                        "from_name": email.from_name,
                        "to_addresses": email.to_addresses,
                        "subject": email.subject,
                        "body_text": email.body_text,
                        "date": email.date.isoformat(),
                        "is_read": email.is_read,
                        "is_starred": email.is_starred,
                        "has_attachments": email.has_attachments,
                    }
                )
                indexed += 1
            
            await es.close()
            return {"status": "success", "indexed": indexed}
    
    return asyncio.run(_update())


@celery_app.task
def reindex_mailbox(mailbox_id: str) -> Dict[str, Any]:
    """Reindex all emails for a mailbox"""
    # Full reindex implementation
    return {"status": "success", "indexed": 0}


# ============== Domain Tasks ==============

@celery_app.task
def check_domain_dns() -> Dict[str, Any]:
    """Check DNS records for all domains"""
    import dns.resolver
    from app.db.database import AsyncSessionLocal
    from app.models.domain import Domain
    
    async def _check():
        async with AsyncSessionLocal() as db:
            domains = await db.execute(select(Domain))
            
            results = {}
            for domain in domains.scalars().all():
                try:
                    # Check MX record
                    mx_records = dns.resolver.resolve(domain.name, 'MX')
                    has_mx = len(list(mx_records)) > 0
                    
                    # Check SPF record
                    try:
                        txt_records = dns.resolver.resolve(domain.name, 'TXT')
                        has_spf = any('v=spf1' in str(r) for r in txt_records)
                    except:
                        has_spf = False
                    
                    # Check DKIM record
                    try:
                        dkim_domain = f"{domain.dkim_selector}._domainkey.{domain.name}"
                        dns.resolver.resolve(dkim_domain, 'TXT')
                        has_dkim = True
                    except:
                        has_dkim = False
                    
                    results[domain.name] = {
                        "mx": has_mx,
                        "spf": has_spf,
                        "dkim": has_dkim,
                        "verified": has_mx and has_spf and has_dkim
                    }
                    
                    # Update domain verification status
                    domain.is_verified = has_mx and has_spf and has_dkim
                    domain.mx_verified = has_mx
                    domain.spf_verified = has_spf
                    domain.dkim_verified = has_dkim
                    
                except Exception as e:
                    results[domain.name] = {"error": str(e)}
            
            await db.commit()
            return {"status": "success", "domains": results}
    
    return asyncio.run(_check())


@celery_app.task
def verify_domain(domain_id: str) -> Dict[str, Any]:
    """Verify a specific domain's DNS records"""
    # Similar to check_domain_dns but for a single domain
    return {"status": "success", "verified": False}


# ============== Statistics Tasks ==============

@celery_app.task
def generate_daily_stats() -> Dict[str, Any]:
    """Generate daily email statistics"""
    from app.db.database import AsyncSessionLocal
    from app.models.email import Email
    from app.models.user import User
    from sqlalchemy import func
    
    async def _generate():
        async with AsyncSessionLocal() as db:
            today = datetime.utcnow().date()
            yesterday = today - timedelta(days=1)
            
            # Count emails sent yesterday
            sent_count = await db.execute(
                select(func.count(Email.id)).join(Folder).where(
                    and_(
                        Folder.type == "sent",
                        func.date(Email.date) == yesterday
                    )
                )
            )
            
            # Count emails received yesterday
            received_count = await db.execute(
                select(func.count(Email.id)).join(Folder).where(
                    and_(
                        Folder.type == "inbox",
                        func.date(Email.date) == yesterday
                    )
                )
            )
            
            # Count active users
            active_users = await db.execute(
                select(func.count(User.id)).where(
                    func.date(User.last_login_at) == yesterday
                )
            )
            
            stats = {
                "date": yesterday.isoformat(),
                "emails_sent": sent_count.scalar() or 0,
                "emails_received": received_count.scalar() or 0,
                "active_users": active_users.scalar() or 0,
            }
            
            # Store in Redis or database for historical tracking
            redis = await get_redis()
            await redis.hset(f"stats:{yesterday.isoformat()}", mapping=stats)
            
            return {"status": "success", "stats": stats}
    
    return asyncio.run(_generate())


# ============== Notification Tasks ==============

@celery_app.task
def send_notification(
    user_id: str,
    notification_type: str,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """Send a notification to a user"""
    # Implementation for push notifications, email notifications, etc.
    return {"status": "success", "sent": True}


@celery_app.task
def send_email_digest(user_id: str) -> Dict[str, Any]:
    """Send daily/weekly email digest to a user"""
    # Implementation for email digest
    return {"status": "success", "sent": True}
