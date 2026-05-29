"""
OpenMail Platform - Test Configuration
Sets env vars BEFORE any app import so DATABASE_URL resolves to SQLite.
"""
import os
import sys

# ── Must happen before app modules are imported ─────────────────────────────
import tempfile as _tempfile
_db_file = _tempfile.mktemp(suffix="_openmail_test.db")
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{_db_file}")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("ENVIRONMENT", "test")

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

# Clear pydantic-settings lru_cache so env overrides above take effect
try:
    from app.core.config import get_settings
    get_settings.cache_clear()
except Exception:
    pass
# ─────────────────────────────────────────────────────────────────────────────

import pytest
from uuid import uuid4
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """Create SQLite tables once before all tests (session-scoped, autouse)."""
    mock_redis = AsyncMock()
    with patch("app.db.database.aioredis.from_url", return_value=mock_redis):
        from app.db.database import init_db
        await init_db()
    yield
    # Cleanup temp DB file after session
    import os as _os
    try:
        _os.remove(_db_file)
    except Exception:
        pass


@pytest.fixture
def test_user():
    return {
        "email": f"test_{uuid4().hex[:8]}@example.com",
        "password": "TestPass123!",
        "first_name": "Test",
        "last_name": "User",
    }


# Alias used by test_auth.py + test_emails.py
@pytest.fixture
def test_user_data():
    return {
        "email": f"user_{uuid4().hex[:8]}@example.com",
        "password": "TestPass123!",
        "first_name": "Test",
        "last_name": "User",
    }


@pytest.fixture
def sample_email_data():
    return {
        "to_addresses": ["recipient@example.com"],
        "subject": "Test Email",
        "body_text": "This is a test email.",
        "body_html": "<p>This is a test email.</p>",
    }


@pytest.fixture
def sample_contact_data():
    return {
        "email": "contact@example.com",
        "name": "Test Contact",
        "first_name": "Test",
        "last_name": "Contact",
        "company": "Test Company",
    }


@pytest.fixture
def sample_filter_data():
    return {
        "name": "Test Filter",
        "conditions": [{"field": "from", "operator": "contains", "value": "newsletter"}],
        "actions": [{"type": "move", "value": "archive"}],
        "match_mode": "all",
        "is_active": True,
    }


@pytest.fixture
async def client():
    """Async test client — patches Redis, creates SQLite tables."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=1)

    with patch("app.db.database.aioredis.from_url", return_value=mock_redis):
        from app.main import app
        from app.db.database import init_db
        # Create tables in SQLite in-memory DB
        await init_db()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac


@pytest.fixture(scope="function")
async def db_session():
    """Create a test database session."""
    from app.db.database import async_session_maker
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
def auth_headers():
    return {"Authorization": "Bearer test_token"}
