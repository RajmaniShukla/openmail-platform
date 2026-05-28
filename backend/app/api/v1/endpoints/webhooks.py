"""
OpenMail Platform - Webhook Endpoints for Mail Processing
"""
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Header, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from pydantic import BaseModel
import hmac
import hashlib
import json

from app.core.config import settings
from app.services.celery_tasks import process_incoming_email

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class IncomingEmailWebhook(BaseModel):
    """Schema for incoming email webhook from Postfix/mail server."""
    sender: str
    recipient: str
    subject: str = ""
    raw_email: str
    timestamp: str
    size: int = 0
    spam_score: float = 0.0
    headers: Dict[str, str] = {}


class BounceWebhook(BaseModel):
    """Schema for email bounce notification."""
    original_recipient: str
    original_message_id: str
    bounce_type: str  # hard, soft, block
    bounce_reason: str
    timestamp: str


class DeliveryWebhook(BaseModel):
    """Schema for email delivery confirmation."""
    recipient: str
    message_id: str
    delivered_at: str
    smtp_response: str = ""


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str = settings.WEBHOOK_SECRET if hasattr(settings, 'WEBHOOK_SECRET') else ''
) -> bool:
    """Verify webhook signature for authenticity."""
    if not secret:
        return True  # Skip verification if no secret configured
    
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)


@router.post("/incoming")
async def receive_incoming_email(
    data: IncomingEmailWebhook,
    background_tasks: BackgroundTasks,
    x_webhook_signature: str = Header(None),
):
    """
    Webhook endpoint for receiving incoming emails from Postfix.
    
    This endpoint is called by the mail server when a new email arrives.
    The email is queued for processing in the background.
    """
    # Process email in background
    background_tasks.add_task(
        process_incoming_email.delay,
        data.raw_email,
        data.recipient
    )
    
    return {
        "status": "accepted",
        "message": "Email queued for processing",
        "recipient": data.recipient,
    }


@router.post("/bounce")
async def receive_bounce(
    data: BounceWebhook,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Webhook endpoint for email bounce notifications.
    Updates the email record with bounce status and logs to Redis.
    """
    from sqlalchemy import select, update
    from app.models.email import Email
    from app.db.database import get_redis

    # Find the original email by message-id and mark it as bounced
    result = await db.execute(
        select(Email).where(Email.message_id == data.original_message_id)
    )
    original_email = result.scalar_one_or_none()

    if original_email:
        # Store bounce info in the email's headers JSON field
        headers = dict(original_email.headers or {})
        headers["X-Bounce-Type"] = data.bounce_type
        headers["X-Bounce-Reason"] = data.bounce_reason
        headers["X-Bounce-Recipient"] = data.original_recipient
        headers["X-Bounce-Timestamp"] = data.timestamp
        original_email.headers = headers
        await db.commit()

    # Log to Redis for analytics
    try:
        redis = await get_redis()
        await redis.lpush(
            "bounces",
            f"{data.bounce_type}|{data.original_recipient}|{data.original_message_id}|{data.timestamp}",
        )
        # Hard bounces: add to suppression list
        if data.bounce_type == "hard":
            await redis.sadd("suppressed_addresses", data.original_recipient)
    except Exception:
        pass

    return {
        "status": "accepted",
        "bounce_type": data.bounce_type,
        "message_id": data.original_message_id,
    }


@router.post("/delivery")
async def receive_delivery_confirmation(
    data: DeliveryWebhook,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Webhook endpoint for email delivery confirmations.
    Stamps the email record with delivery info.
    """
    from sqlalchemy import select
    from app.models.email import Email
    from app.db.database import get_redis

    result = await db.execute(
        select(Email).where(Email.message_id == data.message_id)
    )
    email = result.scalar_one_or_none()

    if email:
        headers = dict(email.headers or {})
        headers["X-Delivered-To"] = data.recipient
        headers["X-Delivered-At"] = data.delivered_at
        headers["X-SMTP-Response"] = data.smtp_response
        email.headers = headers
        await db.commit()

    # Log to Redis for analytics
    try:
        redis = await get_redis()
        await redis.lpush(
            "deliveries",
            f"{data.recipient}|{data.message_id}|{data.delivered_at}",
        )
        await redis.ltrim("deliveries", 0, 9999)  # Keep last 10k
    except Exception:
        pass

    return {
        "status": "accepted",
        "message_id": data.message_id,
        "delivered_at": data.delivered_at,
    }


@router.post("/spam-report")
async def receive_spam_report(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Webhook endpoint for spam reports.
    Moves the flagged email to spam folder and updates its spam score.
    """
    from sqlalchemy import select
    from app.models.email import Email, Folder

    data = await request.json()
    message_id = data.get("message_id")
    spam_score = float(data.get("spam_score", 1.0))

    if message_id:
        result = await db.execute(
            select(Email).where(Email.message_id == message_id)
        )
        email = result.scalar_one_or_none()

        if email:
            # Move to spam folder
            spam_folder_result = await db.execute(
                select(Folder).where(
                    Folder.mailbox_id == email.mailbox_id,
                    Folder.type == "spam",
                )
            )
            spam_folder = spam_folder_result.scalar_one_or_none()
            if spam_folder:
                email.folder_id = spam_folder.id
            email.is_spam = True
            email.spam_score = spam_score
            await db.commit()

    return {"status": "accepted", "action": "spam_filtered"}


@router.get("/health")
async def webhook_health():
    """Health check endpoint for webhook processing."""
    return {
        "status": "healthy",
        "service": "webhooks",
        "endpoints": [
            "/incoming",
            "/bounce",
            "/delivery",
            "/spam-report",
        ]
    }
