"""
OpenMail Platform - Webhook Endpoints for Mail Processing
"""
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Header
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
):
    """
    Webhook endpoint for email bounce notifications.
    
    Called when an email fails to deliver.
    """
    # Log bounce for analytics and potentially notify sender
    # In production, this would update the email status and possibly
    # add the address to a suppression list for hard bounces
    
    return {
        "status": "accepted",
        "bounce_type": data.bounce_type,
        "message_id": data.original_message_id,
    }


@router.post("/delivery")
async def receive_delivery_confirmation(
    data: DeliveryWebhook,
    background_tasks: BackgroundTasks,
):
    """
    Webhook endpoint for email delivery confirmations.
    
    Called when an email is successfully delivered.
    """
    # Update email status to "delivered"
    # Useful for tracking and analytics
    
    return {
        "status": "accepted",
        "message_id": data.message_id,
        "delivered_at": data.delivered_at,
    }


@router.post("/spam-report")
async def receive_spam_report(
    request: Request,
):
    """
    Webhook endpoint for spam reports (e.g., from SpamAssassin).
    
    Called when an email is flagged as spam by the filtering system.
    """
    data = await request.json()
    
    return {
        "status": "accepted",
        "action": "spam_filtered",
    }


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
