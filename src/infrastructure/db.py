"""Database engine/session setup (TASK_04)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from src.settings import settings


def create_engine(database_url: str | None = None) -> AsyncEngine:
    """Create async SQLAlchemy engine using configured DATABASE_URL."""
    return create_async_engine(database_url or settings.database_url, future=True)


engine = create_engine()
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)
