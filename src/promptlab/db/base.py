"""SQLAlchemy 2.0 async database configuration, engine, and session management.

This module provides the persistence foundation for PromptLab:
- DeclarativeBase for typed ORM mapping.
- AsyncEngine and AsyncSession lifecycle management.
- Schema creation utilities for testing and startup.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from promptlab.config import get_settings


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy 2.0 ORM models."""

    pass


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine(database_url: str | None = None) -> AsyncEngine:
    """Retrieve or create the global AsyncEngine singleton."""
    global _engine
    if _engine is None:
        url = database_url or get_settings().database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        _engine = create_async_engine(url, echo=False, future=True)
    return _engine


def get_session_factory(
    database_url: str | None = None,
) -> async_sessionmaker[AsyncSession]:
    """Retrieve or create the global sessionmaker instance."""
    global _session_factory
    if _session_factory is None:
        engine = get_engine(database_url)
        _session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


async def init_db(engine: AsyncEngine | None = None) -> None:
    """Create all database tables defined in metadata."""
    active_engine = engine or get_engine()
    async with active_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager yielding an AsyncSession with automated rollback on error."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
