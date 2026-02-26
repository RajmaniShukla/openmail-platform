"""
OpenMail Platform - Test Configuration
"""
import os
import sys
import pytest
from typing import AsyncGenerator

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://openmail:openmail@localhost:5432/openmail_test"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"


@pytest.fixture(scope="session")
def anyio_backend():
    """Specify async backend for pytest-anyio."""
    return "asyncio"


@pytest.fixture(scope="function")
async def db_session():
    """Create a test database session."""
    from app.db.database import async_session_maker
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
def auth_headers():
    """Get authentication headers for tests."""
    return {"Authorization": "Bearer test_token"}


@pytest.fixture(scope="function")
def sample_email_data():
    """Sample email data for tests."""
    return {
        "to_addresses": ["recipient@example.com"],
        "subject": "Test Email",
        "body_text": "This is a test email.",
        "body_html": "<p>This is a test email.</p>",
    }


@pytest.fixture(scope="function")
def sample_contact_data():
    """Sample contact data for tests."""
    return {
        "email": "contact@example.com",
        "name": "Test Contact",
        "first_name": "Test",
        "last_name": "Contact",
        "company": "Test Company",
    }


@pytest.fixture(scope="function")
def sample_filter_data():
    """Sample filter data for tests."""
    return {
        "name": "Test Filter",
        "conditions": [
            {"field": "from", "operator": "contains", "value": "newsletter"}
        ],
        "actions": [
            {"type": "move", "value": "archive"}
        ],
        "match_mode": "all",
        "is_active": True,
    }
