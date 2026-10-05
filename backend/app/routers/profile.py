from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
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
    ProfileResponse,
    ProfileSkillCreate,
    ProfileSkillResponse,
    ProfileSkillUpdate,
    ProfileUpdate,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)
from app.services import profile as profile_service

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
    return profile


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_current_user_profile(
    profile_in: ProfileCreate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new profile for the authenticated user."""
    return await profile_service.create_profile(db, user_id, profile_in)


@router.patch("", response_model=ProfileResponse)
async def update_current_user_profile(
    profile_in: ProfileUpdate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the authenticated user's profile."""
    return await profile_service.update_profile(db, user_id, profile_in)


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
