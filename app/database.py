"""
database.py – Async SQLAlchemy engine, session factory, and base model.

Uses aiosqlite for async SQLite access (default).
Tables are auto-created on startup.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from app.config import settings
import logging

logger = logging.getLogger(__name__)

from sqlalchemy.pool import NullPool, StaticPool

# ─── Engine ───────────────────────────────────────────────────────────────────
_db_url = settings.DATABASE_URL

# aiosqlite requires NullPool; in-memory SQLite (tests) needs StaticPool
if ":memory:" in _db_url:
    _pool_cls = StaticPool
    _connect_args = {"check_same_thread": False}
else:
    _pool_cls = NullPool
    _connect_args = {}

engine = create_async_engine(
    _db_url,
    echo=settings.DEBUG,
    poolclass=_pool_cls,
    connect_args=_connect_args,
)

# ─── Session factory ──────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ─── Base class ───────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """All ORM models inherit from this base."""
    pass


# ─── Dependency ───────────────────────────────────────────────────────────────
from typing import AsyncGenerator

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an async DB session.
    Automatically commits on success and rolls back on error.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ─── Table creation ───────────────────────────────────────────────────────────
async def init_db():
    """Create all tables if they do not already exist."""
    # Import models here so SQLAlchemy registers them with the Base metadata
    from app.models import user, daily_log, task, habit, analytics  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database tables initialised (MSSQL).")
