"""
CareerPilot AI — FastAPI Dependencies

Reusable dependency functions for dependency injection.
"""

from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import verify_token
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


security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Validates the authorization header and returns the user UUID (subject).
    """
    token = credentials.credentials
    payload = verify_token(token)

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token does not contain user subject (sub)",
        )

    return user_id


async def get_current_profile(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Resolves the user's Profile using the verified JWT user_id.
    """
    from sqlalchemy import select

    from app.models.profile import Profile

    stmt = select(Profile).where(Profile.user_id == user_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    return profile


def require_admin(profile=Depends(get_current_profile)):
    """
    Ensures the current profile has the 'admin' role.
    """
    if profile.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return profile

