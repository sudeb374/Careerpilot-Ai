"""
CareerPilot AI — FastAPI Dependencies

Reusable dependency functions for dependency injection.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional database session to route handlers."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
