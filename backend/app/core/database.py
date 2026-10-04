"""
CareerPilot AI — Database Configuration

Sets up SQLAlchemy engine and session factory.
Actual database connections will be established when Phase 2 begins.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# Replace "postgresql+psycopg" with "postgresql+psycopg_async" for async support.
# For now, the engine is configured but not actively used until models are created.
_async_database_url = settings.database_url.replace(
    "postgresql+psycopg://",
    "postgresql+psycopg://",  # psycopg 3 supports async natively
)

engine = create_async_engine(
    _async_database_url,
    echo=settings.app_debug,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields a database session and ensures cleanup."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
