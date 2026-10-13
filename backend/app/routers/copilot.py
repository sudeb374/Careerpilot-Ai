from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_profile, get_db
from app.models.profile import Profile
from app.schemas.cover_letter import (
    CoverLetterGenerateRequest,
    CoverLetterGenerateResponse,
    OpportunityContextForLetter,
)
from app.schemas.skill_gap import SkillGapRoadmapResponse
from app.services.cover_letter import (
    generate_cover_letter,
    get_opportunity_context_for_candidate,
)
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


@router.get(
    "/cover-letter/context/{opportunity_id}",
    response_model=OpportunityContextForLetter,
    status_code=status.HTTP_200_OK,
    summary="Opportunity Context for Cover Letter",
)
async def get_cover_letter_context(
    opportunity_id: UUID,
    current_user: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch opportunity details and candidate readiness verification prior to cover letter generation.
    """
    try:
        return await get_opportunity_context_for_candidate(
            db=db,
            profile_id=current_user.id,
            opportunity_id=opportunity_id,
        )
    except ValueError as e:
        err_msg = str(e)
        if "not found" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)


@router.post(
    "/cover-letter/generate",
    response_model=CoverLetterGenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Personalized Cover Letter",
)
async def generate_cover_letter_endpoint(
    request: CoverLetterGenerateRequest,
    current_user: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a tailored cover letter grounded strictly in the authenticated candidate's verified profile and active resume.
    """
    try:
        return await generate_cover_letter(
            db=db,
            profile_id=current_user.id,
            request=request,
        )
    except ValueError as e:
        err_msg = str(e)
        if "not found" in err_msg.lower() or "not published" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cover letter generation encountered an unexpected error: {str(e)}",
        )
