"""
OpenMail Platform - Database Configuration
"""
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
import redis.asyncio as aioredis
import redis

from app.core.config import settings

# Redis clients
_redis_client: Optional[aioredis.Redis] = None
_redis_sync_client: Optional[redis.Redis] = None

# Base class for models
Base = declarative_base()

# ---------------------------------------------------------------------------
# Lazy engine & session factory
# Engine is NOT created at module import time so tests can override DATABASE_URL
# via env vars before the first import of this module.
# ---------------------------------------------------------------------------
_engine = None
_async_session_maker_instance = None


def _build_engine():
    global _engine
    if _engine is not None:
        return _engine

    url = settings.DATABASE_URL
    if url.startswith("sqlite"):
        from sqlalchemy.pool import StaticPool
        _engine = create_async_engine(
            url,
            echo=settings.DEBUG,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        _engine = create_async_engine(
            url,
            echo=settings.DEBUG,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_pre_ping=True,
        )
    return _engine


def _build_session_maker():
    global _async_session_maker_instance
    if _async_session_maker_instance is None:
        _async_session_maker_instance = async_sessionmaker(
            _build_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _async_session_maker_instance


class _SessionMakerProxy:
    """Acts like async_sessionmaker: calling it returns an AsyncSession context manager."""
    def __call__(self):
        return _build_session_maker()()

    def __getattr__(self, name):
        return getattr(_build_session_maker(), name)


# Public name used throughout the codebase
async_session_maker = _SessionMakerProxy()


class _EngineProxy:
    """Forwards all attribute access + async context managers to the lazy engine."""
    def begin(self):
        return _build_engine().begin()

    def connect(self):
        return _build_engine().connect()

    def __getattr__(self, name):
        return getattr(_build_engine(), name)


engine = _EngineProxy()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    Usage: db: AsyncSession = Depends(get_db)
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    async with _build_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Sync session for Celery tasks
def _get_sync_engine():
    url = settings.DATABASE_URL
    if url.startswith("sqlite+aiosqlite"):
        sync_url = url.replace("sqlite+aiosqlite", "sqlite")
    else:
        sync_url = url.replace("+asyncpg", "")
    return create_engine(sync_url, pool_pre_ping=True)


_sync_engine = None
_sync_session_local = None


def _get_sync_session_local():
    global _sync_engine, _sync_session_local
    if _sync_session_local is None:
        _sync_engine = _get_sync_engine()
        _sync_session_local = sessionmaker(
            autocommit=False, autoflush=False, bind=_sync_engine
        )
    return _sync_session_local


SyncSessionLocal = _get_sync_session_local  # callable proxy
AsyncSessionLocal = async_session_maker      # alias for Celery tasks


def get_db_sync():
    """Get synchronous database session (for Celery tasks)."""
    maker = _get_sync_session_local()
    db = maker()
    try:
        return db
    finally:
        db.close()


async def get_redis() -> aioredis.Redis:
    """Get async Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


def get_redis_sync() -> redis.Redis:
    """Get sync Redis client (for Celery tasks)."""
    global _redis_sync_client
    if _redis_sync_client is None:
        _redis_sync_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_sync_client


async def close_redis():
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


# For testing
def create_test_engine(database_url: str):
    """Create a test engine with NullPool."""
    return create_async_engine(
        database_url,
        echo=True,
        poolclass=NullPool,
    )
