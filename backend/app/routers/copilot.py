from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_profile, get_db
from app.models.profile import Profile
from app.schemas.skill_gap import SkillGapRoadmapResponse
from app.services.skill_gap import generate_skill_gap_roadmap

router = APIRouter(
    prefix="/api/v1/copilot",
    tags=["Career Copilot"],
)


@router.get(
    "/skill-gap-roadmap",
    response_model=SkillGapRoadmapResponse,
    status_code=status.HTTP_200_OK,
    summary="Personalized Skill-Gap Roadmap",
)
async def get_skill_gap_roadmap(
    target_role: str | None = Query(
        None, description="Optional target job title to focus the roadmap on"
    ),
    current_user: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate an evidence-based skill gap roadmap personalized to the authenticated student.
    Analyzes student manual profile skills, active resume extracted skills, and published opportunities.
    """
    return await generate_skill_gap_roadmap(
        db=db,
        profile_id=current_user.id,
        target_role=target_role,
    )
