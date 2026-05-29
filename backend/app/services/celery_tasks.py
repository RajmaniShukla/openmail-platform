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
        from app.models.domain import Mailbox
        
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
    from app.models.domain import Mailbox
    
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
        from app.models.domain import Mailbox
        
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
    from app.models.domain import Mailbox
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
    """
    Re-evaluate recent unscored inbox emails against SpamAssassin.
    Emails above threshold are moved to spam folder.
    """
    from app.db.database import AsyncSessionLocal
    from app.models.email import Email, Folder
    from app.services.email_service import SpamFilterService
    from sqlalchemy import and_
    from datetime import timedelta

    async def _process():
        async with AsyncSessionLocal() as db:
            # Fetch inbox emails received in the last hour with no spam score yet
            cutoff = datetime.utcnow() - timedelta(hours=1)
            result = await db.execute(
                select(Email)
                .join(Folder)
                .where(
                    and_(
                        Folder.type == "inbox",
                        Email.spam_score == 0.0,
                        Email.received_at >= cutoff,
                        Email.is_spam == False,
                    )
                )
                .limit(200)
            )
            emails = result.scalars().all()

            processed = 0
            moved_to_spam = 0

            for email in emails:
                try:
                    content = email.body_text or email.body_html or ""
                    headers = dict(email.headers or {})
                    score = await SpamFilterService.check_spam(content, headers)
                    email.spam_score = score

                    # Threshold: score >= 0.8 (normalised) → move to spam
                    if score >= 0.8:
                        spam_folder_result = await db.execute(
                            select(Folder).where(
                                and_(
                                    Folder.mailbox_id == email.mailbox_id,
                                    Folder.type == "spam",
                                )
                            )
                        )
                        spam_folder = spam_folder_result.scalar_one_or_none()
                        if spam_folder:
                            email.folder_id = spam_folder.id
                            email.is_spam = True
                            moved_to_spam += 1

                    processed += 1
                except Exception:
                    continue

            if processed:
                await db.commit()

            return {"status": "success", "processed": processed, "moved_to_spam": moved_to_spam}

    return asyncio.run(_process())


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
    """Reindex all emails for a mailbox into Elasticsearch."""
    from app.db.database import AsyncSessionLocal
    from app.models.email import Email
    from elasticsearch import AsyncElasticsearch
    from app.core.config import settings

    async def _reindex():
        es = AsyncElasticsearch([settings.ELASTICSEARCH_URL])
        try:
            # Ensure index exists with correct mapping
            index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}_emails"
            if not await es.indices.exists(index=index_name):
                await es.indices.create(
                    index=index_name,
                    body={
                        "mappings": {
                            "properties": {
                                "mailbox_id": {"type": "keyword"},
                                "folder_id": {"type": "keyword"},
                                "from_address": {"type": "keyword"},
                                "from_name": {"type": "text"},
                                "to_addresses": {"type": "keyword"},
                                "subject": {"type": "text", "analyzer": "standard"},
                                "body_text": {"type": "text", "analyzer": "standard"},
                                "date": {"type": "date"},
                                "is_read": {"type": "boolean"},
                                "is_starred": {"type": "boolean"},
                                "is_spam": {"type": "boolean"},
                                "is_trash": {"type": "boolean"},
                            }
                        }
                    },
                )

            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(Email).where(Email.mailbox_id == mailbox_id)
                )
                emails = result.scalars().all()

                # Bulk index in batches of 100
                batch = []
                indexed = 0
                for email in emails:
                    batch.append({"index": {"_index": index_name, "_id": str(email.id)}})
                    batch.append({
                        "mailbox_id": str(email.mailbox_id),
                        "folder_id": str(email.folder_id) if email.folder_id else None,
                        "from_address": email.from_address,
                        "from_name": email.from_name,
                        "to_addresses": [
                            a.get("address") if isinstance(a, dict) else str(a)
                            for a in (email.to_addresses or [])
                        ],
                        "subject": email.subject,
                        "body_text": email.body_text,
                        "snippet": email.snippet,
                        "date": email.date.isoformat() if email.date else None,
                        "is_read": email.is_read,
                        "is_starred": email.is_starred,
                        "is_spam": email.is_spam,
                        "is_trash": email.is_trash,
                    })
                    indexed += 1
                    if len(batch) >= 200:  # 100 pairs
                        await es.bulk(body=batch)
                        batch = []

                if batch:
                    await es.bulk(body=batch)
            return {"status": "success", "indexed": indexed}
        finally:
            await es.close()

    return asyncio.run(_reindex())


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
    """Verify a specific domain's DNS records and update DB."""
    import dns.resolver
    from uuid import UUID
    from app.db.database import AsyncSessionLocal
    from app.models.domain import Domain
    from app.core.config import settings

    async def _verify():
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Domain).where(Domain.id == UUID(domain_id))
            )
            domain = result.scalar_one_or_none()
            if not domain:
                return {"status": "error", "message": "Domain not found"}

            checks = {"mx": False, "spf": False, "dkim": False, "dmarc": False}

            try:
                # MX
                try:
                    mx = dns.resolver.resolve(domain.name, "MX")
                    checks["mx"] = any(
                        settings.MAIL_SERVER_HOSTNAME in str(r.exchange)
                        for r in mx
                    )
                except Exception:
                    pass

                # SPF
                try:
                    txt = dns.resolver.resolve(domain.name, "TXT")
                    checks["spf"] = any(
                        "v=spf1" in rdata.to_text() and settings.MAIL_SERVER_HOSTNAME in rdata.to_text()
                        for rdata in txt
                    )
                except Exception:
                    pass

                # DKIM
                try:
                    dkim_name = f"{domain.dkim_selector}._domainkey.{domain.name}"
                    dkim_txt = dns.resolver.resolve(dkim_name, "TXT")
                    checks["dkim"] = any("v=DKIM1" in rdata.to_text() for rdata in dkim_txt)
                except Exception:
                    pass

                # DMARC
                try:
                    dmarc_txt = dns.resolver.resolve(f"_dmarc.{domain.name}", "TXT")
                    checks["dmarc"] = any("v=DMARC1" in rdata.to_text() for rdata in dmarc_txt)
                except Exception:
                    pass

            except Exception:
                pass

            is_verified = checks["mx"] and checks["spf"]
            domain.is_verified = is_verified
            if hasattr(domain, "mx_verified"):
                domain.mx_verified = checks["mx"]
            if hasattr(domain, "spf_verified"):
                domain.spf_verified = checks["spf"]
            if hasattr(domain, "dkim_verified"):
                domain.dkim_verified = checks["dkim"]

            await db.commit()
            return {"status": "success", "verified": is_verified, "checks": checks}

    return asyncio.run(_verify())


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
    """
    Deliver an in-app notification to a user via Redis pub/sub.
    The WebSocket handler subscribes to the `notifications:{user_id}` channel.
    """
    import json
    from app.db.database import get_redis_sync

    try:
        redis = get_redis_sync()
        payload = json.dumps({
            "type": notification_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        })
        # Publish to per-user channel — WebSocket handler picks this up
        redis.publish(f"notifications:{user_id}", payload)
        # Also push to a persistent list (last 50) for reconnect replay
        redis.lpush(f"notif_history:{user_id}", payload)
        redis.ltrim(f"notif_history:{user_id}", 0, 49)
        return {"status": "success", "sent": True}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@celery_app.task
def send_email_digest(user_id: str) -> Dict[str, Any]:
    """
    Build and send a daily email digest to the user.
    Summarises unread inbox emails from the last 24h.
    """
    from app.db.database import AsyncSessionLocal
    from app.models.user import User
    from app.models.domain import Mailbox
    from app.models.email import Email, Folder
    from app.services.email_service import EmailService
    from sqlalchemy import and_
    from datetime import timedelta
    from uuid import UUID

    async def _digest():
        async with AsyncSessionLocal() as db:
            user = await db.get(User, UUID(user_id))
            if not user or not user.is_active:
                return {"status": "skip", "reason": "user not found or inactive"}

            # Get user's primary mailbox
            result = await db.execute(
                select(Mailbox).where(
                    and_(Mailbox.user_id == user.id, Mailbox.is_primary == True)
                )
            )
            mailbox = result.scalar_one_or_none()
            if not mailbox:
                return {"status": "skip", "reason": "no primary mailbox"}

            # Fetch unread inbox emails from the last 24h
            cutoff = datetime.utcnow() - timedelta(hours=24)
            inbox_result = await db.execute(
                select(Folder).where(
                    and_(Folder.mailbox_id == mailbox.id, Folder.type == "inbox")
                )
            )
            inbox = inbox_result.scalar_one_or_none()
            if not inbox:
                return {"status": "skip", "reason": "no inbox folder"}

            emails_result = await db.execute(
                select(Email)
                .where(
                    and_(
                        Email.folder_id == inbox.id,
                        Email.is_read == False,
                        Email.received_at >= cutoff,
                    )
                )
                .order_by(Email.date.desc())
                .limit(20)
            )
            unread = emails_result.scalars().all()

            if not unread:
                return {"status": "skip", "reason": "no unread emails"}

            # Build digest HTML
            rows = "".join(
                f"""
                <tr>
                  <td style='padding:8px;border-bottom:1px solid #eee;font-weight:bold'>
                    {e.from_name or e.from_address}
                  </td>
                  <td style='padding:8px;border-bottom:1px solid #eee'>{e.subject or '(no subject)'}</td>
                  <td style='padding:8px;border-bottom:1px solid #eee;color:#888;font-size:12px'>
                    {e.date.strftime('%H:%M')}
                  </td>
                </tr>
                """
                for e in unread
            )
            body_html = f"""
            <html><body style='font-family:sans-serif;max-width:600px;margin:auto'>
              <h2 style='color:#4f46e5'>Your Daily Email Digest</h2>
              <p>You have <strong>{len(unread)}</strong> unread message(s) from the last 24 hours.</p>
              <table width='100%' style='border-collapse:collapse'>
                <thead>
                  <tr style='background:#f5f5f5'>
                    <th style='padding:8px;text-align:left'>From</th>
                    <th style='padding:8px;text-align:left'>Subject</th>
                    <th style='padding:8px;text-align:left'>Time</th>
                  </tr>
                </thead>
                <tbody>{rows}</tbody>
              </table>
              <p style='color:#888;font-size:12px;margin-top:24px'>
                This digest was sent to {user.email}. Manage your notification settings in OpenMail.
              </p>
            </body></html>
            """
            body_text = (
                f"Your Daily Digest\n\nYou have {len(unread)} unread message(s) from the last 24 hours.\n\n"
                + "\n".join(
                    f"- {e.from_name or e.from_address}: {e.subject or '(no subject)'}"
                    for e in unread
                )
            )

            # Send digest via the mailbox SMTP
            svc = EmailService(db)
            await svc.send_email(
                mailbox=mailbox,
                to_addresses=[user.email],
                subject=f"Your Daily Digest — {len(unread)} unread messages",
                body_html=body_html,
                body_text=body_text,
            )

            return {"status": "success", "sent": True, "emails_summarised": len(unread)}

    return asyncio.run(_digest())
