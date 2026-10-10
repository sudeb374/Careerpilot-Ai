from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_profile, get_current_user, get_db
from app.models.opportunity import Opportunity, OpportunitySkill, SavedOpportunity
from app.schemas.matching import OpportunityMatchItem, PaginatedOpportunityMatchResponse
from app.schemas.opportunity import PaginatedSavedOpportunityResponse
from app.schemas.profile import (
    CareerPreferenceResponse,
    CareerPreferenceUpsert,
    EducationCreate,
    EducationResponse,
    EducationUpdate,
    ExperienceCreate,
    ExperienceResponse,
    ExperienceSkillCreate,
    ExperienceSkillResponse,
    ExperienceUpdate,
    ProfileCreate,
    ProfilePictureResponse,
    ProfileResponse,
    ProfileSkillCreate,
    ProfileSkillResponse,
    ProfileSkillUpdate,
    ProfileUpdate,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    ResumeAnalysisResponse,
    ResumeDownloadResponse,
    ResumeParseResponse,
    ResumeResponse,
    ResumeStructureResponse,
)
from app.services import profile as profile_service
from app.services import profile_picture as picture_service
from app.services import resume as resume_service
from app.services.matching import calculate_match_with_evidence, get_candidate_evidence
from app.services.opportunity import expire_overdue_opportunities
from app.services.resume_analyzer import (
    ResumeAnalyzerError,
    analyze_resume,
    get_resume_analysis,
)

router = APIRouter(prefix="/api/v1/profile", tags=["Profile"])


@router.get("", response_model=ProfileResponse)
async def get_current_user_profile(
    user_id: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Get the authenticated user's profile."""
    profile = await profile_service.get_profile_by_user_id(db, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )
    return await picture_service.inject_profile_picture_url(profile)


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_current_user_profile(
    profile_in: ProfileCreate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new profile for the authenticated user."""
    profile = await profile_service.create_profile(db, user_id, profile_in)
    return await picture_service.inject_profile_picture_url(profile)


@router.patch("", response_model=ProfileResponse)
async def update_current_user_profile(
    profile_in: ProfileUpdate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the authenticated user's profile."""
    profile = await profile_service.update_profile(db, user_id, profile_in)
    return await picture_service.inject_profile_picture_url(profile)


@router.get("/education", response_model=list[EducationResponse])
async def get_educations(
    user_id: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Get all education records for the authenticated user."""
    return await profile_service.get_educations(db, user_id)


@router.post(
    "/education", response_model=EducationResponse, status_code=status.HTTP_201_CREATED
)
async def create_education(
    education_in: EducationCreate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a new education record for the authenticated user."""
    return await profile_service.create_education(db, user_id, education_in)


@router.patch("/education/{education_id}", response_model=EducationResponse)
async def update_education(
    education_id: str,
    education_in: EducationUpdate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing education record."""
    return await profile_service.update_education(
        db, user_id, education_id, education_in
    )


@router.delete("/education/{education_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_education(
    education_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an education record."""
    await profile_service.delete_education(db, user_id, education_id)


@router.get("/skills", response_model=list[ProfileSkillResponse])
async def get_profile_skills(
    user_id: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Get all skills for the authenticated user's profile."""
    return await profile_service.get_profile_skills(db, user_id)


@router.post(
    "/skills", response_model=ProfileSkillResponse, status_code=status.HTTP_201_CREATED
)
async def create_profile_skill(
    skill_in: ProfileSkillCreate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a new skill to the authenticated user's profile."""
    return await profile_service.create_profile_skill(db, user_id, skill_in)


@router.patch("/skills/{profile_skill_id}", response_model=ProfileSkillResponse)
async def update_profile_skill(
    profile_skill_id: str,
    skill_in: ProfileSkillUpdate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a skill's proficiency on the user's profile."""
    return await profile_service.update_profile_skill(
        db, user_id, profile_skill_id, skill_in
    )


@router.delete("/skills/{profile_skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile_skill(
    profile_skill_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a skill from the user's profile."""
    await profile_service.delete_profile_skill(db, user_id, profile_skill_id)


@router.get("/projects", response_model=list[ProjectResponse])
async def get_projects(
    user_id: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Get all projects for the authenticated user."""
    return await profile_service.get_projects(db, user_id)


@router.post(
    "/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED
)
async def create_project(
    project_in: ProjectCreate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a new project for the authenticated user."""
    return await profile_service.create_project(db, user_id, project_in)


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_in: ProjectUpdate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing project."""
    return await profile_service.update_project(db, user_id, project_id, project_in)


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a project."""
    await profile_service.delete_project(db, user_id, project_id)


@router.get("/experience", response_model=list[ExperienceResponse])
async def get_experiences(
    user_id: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Get all experiences for the authenticated user."""
    return await profile_service.get_experiences(db, user_id)


@router.post(
    "/experience",
    response_model=ExperienceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_experience(
    experience_in: ExperienceCreate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a new experience record for the authenticated user."""
    return await profile_service.create_experience(db, user_id, experience_in)


@router.patch("/experience/{experience_id}", response_model=ExperienceResponse)
async def update_experience(
    experience_id: str,
    experience_in: ExperienceUpdate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing experience record."""
    return await profile_service.update_experience(
        db, user_id, experience_id, experience_in
    )


@router.delete("/experience/{experience_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_experience(
    experience_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an experience record."""
    await profile_service.delete_experience(db, user_id, experience_id)


# --- Experience Skills ---


@router.get(
    "/experience/{experience_id}/skills",
    response_model=list[ExperienceSkillResponse],
)
async def get_experience_skills(
    experience_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all skills attached to a specific experience."""
    return await profile_service.get_experience_skills(db, user_id, experience_id)


@router.post(
    "/experience/{experience_id}/skills",
    response_model=ExperienceSkillResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_experience_skill(
    experience_id: str,
    skill_in: ExperienceSkillCreate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Attach a profile skill to a specific experience."""
    return await profile_service.add_experience_skill(
        db, user_id, experience_id, skill_in
    )


@router.delete(
    "/experience/{experience_id}/skills/{profile_skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_experience_skill(
    experience_id: str,
    profile_skill_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a skill from a specific experience."""
    await profile_service.remove_experience_skill(
        db, user_id, experience_id, profile_skill_id
    )


# ==========================================
# Career Preferences
# ==========================================


@router.get("/preferences", response_model=CareerPreferenceResponse)
async def get_career_preferences(
    user_id: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Get the authenticated user's career preferences."""
    profile = await profile_service.get_profile_by_user_id(db, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )
    prefs = await profile_service.get_career_preferences(db, str(profile.id))
    if not prefs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Career preferences not found"
        )
    return prefs


@router.put("/preferences", response_model=CareerPreferenceResponse)
async def upsert_career_preferences(
    prefs_in: CareerPreferenceUpsert,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upsert the authenticated user's career preferences."""
    profile = await profile_service.get_profile_by_user_id(db, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )
    prefs = await profile_service.upsert_career_preferences(
        db, str(profile.id), prefs_in
    )
    return prefs


# ==========================================
# Resumes
# ==========================================


@router.get("/resumes", response_model=list[ResumeResponse])
async def list_resumes(
    profile=Depends(get_current_profile), db: AsyncSession = Depends(get_db)
):
    """Get all resumes for the authenticated user."""
    return await resume_service.list_resumes(db, profile.id)


@router.post(
    "/resumes", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED
)
async def upload_resume(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
    profile=Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    """Upload a new resume for the authenticated user."""
    return await resume_service.upload_resume(db, user_id, profile, file)


@router.patch("/resumes/{resume_id}/activate", response_model=ResumeResponse)
async def activate_resume(
    resume_id: str,
    profile=Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    """Set a specific resume as the active resume."""
    return await resume_service.activate_resume(db, profile.id, resume_id)


@router.get("/resumes/{resume_id}/download", response_model=ResumeDownloadResponse)
async def download_resume(
    resume_id: str,
    profile=Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    """Get a signed URL to download the resume."""
    return await resume_service.create_download_url(db, profile.id, resume_id)


@router.delete("/resumes/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: str,
    profile=Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    """Delete a resume."""
    await resume_service.delete_resume(db, profile.id, resume_id)


@router.post("/resumes/{resume_id}/parse", response_model=ResumeParseResponse)
async def parse_resume(
    resume_id: str,
    profile=Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    """Parse resume text from storage and save it."""
    return await resume_service.parse_resume(db, profile.id, resume_id)

@router.get("/resumes/{resume_id}/parsed-text", response_model=ResumeParseResponse)
async def get_parsed_resume(
    resume_id: str,
    profile=Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    """Get previously parsed resume text."""
    resume = await resume_service.get_resume_by_id(db, profile.id, resume_id)
    if not resume.parsed_text:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume has not been parsed yet."
        )
    return {
        "id": resume.id,
        "status": "success",
        "character_count": len(resume.parsed_text),
        "extracted_text": resume.parsed_text,
        "message": "Retrieved previously parsed text."
    }

@router.post("/resumes/{resume_id}/structure", response_model=ResumeStructureResponse)
async def structure_resume(
    resume_id: str,
    profile=Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    """Run structured extraction on the resume text."""
    return await resume_service.structure_resume(db, profile.id, resume_id)

@router.get("/resumes/{resume_id}/structured-data", response_model=ResumeStructureResponse)
async def get_structured_resume(
    resume_id: str,
    profile=Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    """Get previously saved structured resume data."""
    resume = await resume_service.get_resume_by_id(db, profile.id, resume_id)
    if not resume.structured_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Structured data not found. Please extract structure first."
        )
    return {
        "id": resume.id,
        "status": "success",
        "structured_data": resume.structured_data,
        "message": "Retrieved previously structured data."
    }

# ==========================================
# Profile Picture Endpoints
# ==========================================

@router.post("/picture", response_model=ProfileResponse)
async def upload_profile_picture(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
    profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db)
):
    """Upload or replace profile picture."""
    await picture_service.upload_profile_picture(db, str(profile.id), user_id, file)
    # Refresh and return profile
    await db.refresh(profile)
    return await picture_service.inject_profile_picture_url(profile)

@router.get("/picture", response_model=ProfilePictureResponse)
async def get_profile_picture(
    profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db)
):
    """Get signed URL for profile picture."""
    url = await picture_service.get_profile_picture_url(db, str(profile.id))
    return {"signed_url": url}

@router.delete("/picture", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile_picture(
    profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db)
):
    """Delete profile picture."""
    await picture_service.delete_profile_picture(db, str(profile.id))


@router.get("/saved-opportunities", response_model=PaginatedSavedOpportunityResponse)
async def get_saved_opportunities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_profile),
):
    """
    Get saved opportunities for the current user.
    """
    import math
    await expire_overdue_opportunities(db)
    stmt = select(SavedOpportunity).where(
        SavedOpportunity.profile_id == current_user.id
    )
    
    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    # Order and paginate
    stmt = stmt.order_by(SavedOpportunity.created_at.desc())
    stmt = stmt.options(
        selectinload(SavedOpportunity.opportunity).selectinload(Opportunity.skills).joinedload(OpportunitySkill.skill)
    )
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(stmt)
    saved_opps = result.scalars().all()

    items = []
    for saved in saved_opps:
        opp = saved.opportunity
        skills_resp = [{"id": os.skill.id, "name": os.skill.name} for os in opp.skills]
        items.append({
            "id": opp.id,
            "title": opp.title,
            "company_name": opp.company_name,
            "company_logo_url": opp.company_logo_url,
            "opportunity_type": opp.opportunity_type,
            "work_model": opp.work_model,
            "locations": opp.locations,
            "domain": opp.domain,
            "deadline": opp.deadline,
            "status": opp.status,
            "created_at": opp.created_at,
            "skills": skills_resp,
            "saved_at": saved.created_at
        })
        
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages
    }

@router.post("/resumes/{resume_id}/analyze", response_model=ResumeAnalysisResponse)
async def analyze_resume_endpoint(
    resume_id: str,
    profile=Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await analyze_resume(db, profile.id, resume_id)
    except ResumeAnalyzerError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/resumes/{resume_id}/analysis", response_model=ResumeAnalysisResponse)
async def get_resume_analysis_endpoint(
    resume_id: str,
    profile=Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await get_resume_analysis(db, profile.id, resume_id)
    except ResumeAnalyzerError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/opportunity-matches", response_model=PaginatedOpportunityMatchResponse)
async def get_opportunity_matches(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_profile),
):
    """
    Get ranked opportunity matches for the current user.
    """
    import math
    await expire_overdue_opportunities(db)
    
    # 1. Load candidate evidence once
    evidence = await get_candidate_evidence(db, current_user.id)
    
    # 2. Get all eligible Published opportunities
    stmt = select(Opportunity).where(Opportunity.status == "Published")
    stmt = stmt.options(selectinload(Opportunity.skills).selectinload(OpportunitySkill.skill))
    res = await db.execute(stmt)
    opportunities = res.scalars().all()
    
    # 3. Calculate matches deterministically
    match_items = []
    for opp in opportunities:
        match_result = calculate_match_with_evidence(opp, evidence)
        
        # Compose OpportunityListItem
        skills_resp = [{"id": os.skill.id, "name": os.skill.name} for os in opp.skills]
        opp_item = {
            "id": opp.id,
            "title": opp.title,
            "company_name": opp.company_name,
            "company_logo_url": opp.company_logo_url,
            "opportunity_type": opp.opportunity_type,
            "work_model": opp.work_model,
            "locations": opp.locations,
            "domain": opp.domain,
            "deadline": opp.deadline,
            "status": opp.status,
            "created_at": opp.created_at,
            "skills": skills_resp
        }
        
        match_items.append(
            OpportunityMatchItem(
                opportunity=opp_item,
                match=match_result
            )
        )
        
    # 4. Sort results
    def sort_key(item: OpportunityMatchItem):
        score = item.match.score if item.match.score is not None else -1
        timestamp = item.opportunity.created_at.timestamp()
        return (score, timestamp, str(item.opportunity.id))

    match_items.sort(key=sort_key, reverse=True)
    
    # 5. Apply pagination
    total = len(match_items)
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    start = (page - 1) * page_size
    end = start + page_size
    items = match_items[start:end]
    
    return PaginatedOpportunityMatchResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages
    )
