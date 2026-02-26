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

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
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
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Sync session for Celery tasks
sync_database_url = settings.DATABASE_URL.replace("+asyncpg", "")
sync_engine = create_engine(sync_database_url, pool_pre_ping=True)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# Alias for Celery tasks
AsyncSessionLocal = async_session_maker


def get_db_sync():
    """Get synchronous database session (for Celery tasks)."""
    db = SyncSessionLocal()
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
