"""
OpenMail Platform - API v1 Router
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, emails, folders, labels, domains, mailboxes, contacts, filters, webhooks, stats

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(mailboxes.router, prefix="/mailboxes", tags=["Mailboxes"])
api_router.include_router(emails.router, prefix="/emails", tags=["Emails"])
api_router.include_router(folders.router, prefix="/folders", tags=["Folders"])
api_router.include_router(labels.router, prefix="/labels", tags=["Labels"])
api_router.include_router(domains.router, prefix="/domains", tags=["Domains"])
api_router.include_router(contacts.router, prefix="/contacts", tags=["Contacts"])
api_router.include_router(filters.router, prefix="/filters", tags=["Filters"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
api_router.include_router(stats.router, prefix="/stats", tags=["Statistics"])
