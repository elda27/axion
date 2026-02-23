"""Database engine and session management"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from axion_lab_server.shared.libs.config import get_settings


def create_engine() -> AsyncEngine:
    """Create async database engine based on settings"""
    settings = get_settings()

    connect_args = {}
    if settings.database_type == "sqlite":
        connect_args["check_same_thread"] = False

    engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
        connect_args=connect_args,
    )
    return engine


# Global engine instance (lazy initialization)
_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    """Get or create the global engine instance"""
    global _engine
    if _engine is None:
        _engine = create_engine()
    return _engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """Get async session maker"""
    engine = get_engine()
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session as context manager"""
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session"""
    async with get_session() as session:
        yield session


async def close_db() -> None:
    """Close database connections"""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
