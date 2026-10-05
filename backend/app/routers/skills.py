from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.schemas.profile import SkillSearchResponse
from app.services import profile as profile_service

router = APIRouter(prefix="/api/v1/skills", tags=["Skills"])


@router.get("/search", response_model=list[SkillSearchResponse])
async def search_skills_endpoint(
    q: str = Query(..., min_length=1, description="Search query"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),  # Authenticated users only as requested
):
    """Search the global skill catalog."""
    return await profile_service.search_skills(db, q)
