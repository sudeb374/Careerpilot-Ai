from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_profile, get_db
from app.models.profile import Profile
from app.schemas.application_assistant import (
    ApplicationQuestionRequest,
    ApplicationQuestionResponse,
    SuggestedQuestionsResponse,
)
from app.schemas.cover_letter import (
    CoverLetterGenerateRequest,
    CoverLetterGenerateResponse,
    OpportunityContextForLetter,
)
from app.schemas.interview_prep import (
    AIEvaluationRequest,
    AIEvaluationResponse,
    InterviewPrepConfigResponse,
    InterviewSessionRequest,
    InterviewSessionResponse,
    LocalEvaluationRequest,
    LocalEvaluationResponse,
)
from app.schemas.resume_recommendations import (
    JobResumeAnalysisRequest,
    JobResumeAnalysisResponse,
    JobResumeContextResponse,
)
from app.schemas.skill_gap import SkillGapRoadmapResponse
from app.services.application_assistant import (
    generate_application_answer,
    get_suggested_application_questions,
)
from app.services.cover_letter import (
    generate_cover_letter,
    get_opportunity_context_for_candidate,
)
from app.services.interview_prep import (
    create_interview_session,
    evaluate_answer_locally,
    evaluate_answer_with_ai,
    get_interview_prep_config,
)
from app.services.resume_recommendations import (
    analyze_job_resume,
    get_job_resume_context,
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


@router.get(
    "/application-assistant/suggested-questions",
    response_model=SuggestedQuestionsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Suggested Application Questions",
)
async def get_suggested_questions_endpoint(
    current_user: Profile = Depends(get_current_profile),
):
    """
    Fetch curated standard job application questions with category tags.
    """
    return get_suggested_application_questions()


@router.post(
    "/application-assistant/generate",
    response_model=ApplicationQuestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Application Question Answer",
)
async def generate_application_answer_endpoint(
    request: ApplicationQuestionRequest,
    current_user: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a tailored answer for an application question grounded strictly in candidate facts,
    with Gemini AI assistance or deterministic fallback.
    """
    try:
        return await generate_application_answer(
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
            detail=f"Application assistant encountered an unexpected error: {str(e)}",
        )


@router.get(
    "/interview-prep/config",
    response_model=InterviewPrepConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Interview Prep Options & Published Opportunities",
)
async def get_interview_prep_config_endpoint(
    current_user: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch configuration filters and published opportunities for setting up practice sessions.
    """
    return await get_interview_prep_config(db)


@router.post(
    "/interview-prep/session",
    response_model=InterviewSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Create Practice Interview Session",
)
async def create_interview_session_endpoint(
    request: InterviewSessionRequest,
    current_user: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    """
    Select practice questions randomly matching requested role, category, and difficulty filters.
    Stateless on backend: questions are selected directly from the question bank without calling Gemini.
    """
    try:
        return await create_interview_session(db, request)
    except ValueError as e:
        err_msg = str(e)
        if "not found" in err_msg.lower() or "not published" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create interview practice session: {str(e)}",
        )


@router.post(
    "/interview-prep/evaluate-local",
    response_model=LocalEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate Answer with Local Rubric Engine",
)
async def evaluate_local_endpoint(
    request: LocalEvaluationRequest,
    current_user: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    """
    Evaluate student's practice answer using deterministic, local rubric logic.
    Does NOT call Gemini or external network APIs. Candidate answers are not persisted.
    """
    try:
        return await evaluate_answer_locally(db, request)
    except ValueError as e:
        err_msg = str(e)
        if "not found" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Local evaluation encountered an unexpected error: {str(e)}",
        )


@router.post(
    "/interview-prep/evaluate-ai",
    response_model=AIEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Optional AI Feedback (Uses Gemini Quota)",
)
async def evaluate_ai_endpoint(
    request: AIEvaluationRequest,
    current_user: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    """
    Explicit action: request AI-assisted interview feedback using Gemini.
    Falls back gracefully to local rubric evaluation if Gemini is rate-limited, timed out, or unconfigured.
    """
    try:
        return await evaluate_answer_with_ai(db, request)
    except ValueError as e:
        err_msg = str(e)
        if "not found" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI evaluation encountered an unexpected error: {str(e)}",
        )


@router.get(
    "/resume-recommendations/context/{opportunity_id}",
    response_model=JobResumeContextResponse,
    status_code=status.HTTP_200_OK,
    summary="Opportunity & Active Resume Context for Recommendations",
)
async def get_resume_recommendations_context_endpoint(
    opportunity_id: UUID,
    current_user: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch target opportunity details and candidate's active resume status before initiating recommendations.
    Validates published opportunity status and active resume indicators.
    """
    try:
        return await get_job_resume_context(
            db=db,
            profile_id=current_user.id,
            opportunity_id=opportunity_id,
        )
    except ValueError as e:
        err_msg = str(e)
        if "not found" in err_msg.lower() or "not published" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch resume recommendations context: {str(e)}",
        )


@router.post(
    "/resume-recommendations/analyze",
    response_model=JobResumeAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Job-Specific Resume Recommendations",
)
async def analyze_job_resume_endpoint(
    request: JobResumeAnalysisRequest,
    current_user: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate evidence-based, job-specific resume recommendations comparing the authenticated student's
    active resume against the selected published opportunity.
    Strictly preserves the existing active resume without modification.
    """
    try:
        return await analyze_job_resume(
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
            detail=f"Job-specific resume analysis encountered an unexpected error: {str(e)}",
        )

