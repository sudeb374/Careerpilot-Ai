from fastapi import HTTPException, status
from sqlalchemy import String, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.models.profile import (
    CareerPreference,
    Education,
    Experience,
    ExperienceSkill,
    Profile,
    ProfileSkill,
    Project,
    Skill,
    SkillAlias,
)
from app.schemas.profile import (
    CareerPreferenceUpsert,
    EducationCreate,
    EducationUpdate,
    ExperienceCreate,
    ExperienceSkillCreate,
    ExperienceSkillResponse,
    ExperienceUpdate,
    ProfileCreate,
    ProfileSkillCreate,
    ProfileSkillUpdate,
    ProfileUpdate,
    ProjectCreate,
    ProjectUpdate,
)


async def get_profile_by_user_id(db: AsyncSession, user_id: str) -> Profile | None:
    result = await db.execute(select(Profile).where(Profile.user_id == user_id))
    return result.scalars().first()


async def create_profile(
    db: AsyncSession, user_id: str, profile_in: ProfileCreate
) -> Profile:
    existing_profile = await get_profile_by_user_id(db, user_id)
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Profile already exists for this user",
        )

    db_profile = Profile(
        user_id=user_id,
        full_name=profile_in.full_name,
        headline=profile_in.headline,
        location=profile_in.location,
    )
    db.add(db_profile)
    await db.flush()  # DB session dependency handles commit/rollback
    return db_profile


async def update_profile(
    db: AsyncSession, user_id: str, profile_in: ProfileUpdate
) -> Profile:
    db_profile = await get_profile_by_user_id(db, user_id)
    if not db_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    update_data = profile_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_profile, field, value)

    db.add(db_profile)
    await db.flush()
    return db_profile


async def get_educations(db: AsyncSession, user_id: str) -> list[Education]:
    profile = await get_profile_by_user_id(db, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )

    result = await db.execute(
        select(Education)
        .where(Education.profile_id == profile.id)
        .order_by(Education.created_at.desc())
    )
    return list(result.scalars().all())


async def get_education_by_id(
    db: AsyncSession, user_id: str, education_id: str
) -> Education:
    profile = await get_profile_by_user_id(db, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )

    result = await db.execute(
        select(Education)
        .where(Education.profile_id == profile.id)
        .where(Education.id == education_id)
    )
    education = result.scalars().first()
    if not education:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Education record not found",
        )
    return education


async def create_education(
    db: AsyncSession, user_id: str, education_in: EducationCreate
) -> Education:
    profile = await get_profile_by_user_id(db, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Create a profile first.",
        )

    data = education_in.model_dump()

    db_education = Education(profile_id=profile.id, **data)
    db.add(db_education)
    await db.flush()
    return db_education


async def update_education(
    db: AsyncSession, user_id: str, education_id: str, education_in: EducationUpdate
) -> Education:
    education = await get_education_by_id(db, user_id, education_id)

    update_data = education_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(education, field, value)

    db.add(education)
    await db.flush()
    return education


async def delete_education(db: AsyncSession, user_id: str, education_id: str) -> None:
    education = await get_education_by_id(db, user_id, education_id)
    await db.delete(education)
    await db.flush()


async def get_profile_skills(db: AsyncSession, user_id: str):
    profile = await get_profile_by_user_id(db, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )

    result = await db.execute(
        select(ProfileSkill)
        .options(joinedload(ProfileSkill.skill))
        .where(ProfileSkill.profile_id == profile.id)
        .order_by(ProfileSkill.created_at.desc())
    )
    profile_skills = result.scalars().all()

    return [
        {
            "id": ps.id,
            "profile_id": ps.profile_id,
            "skill_id": ps.skill_id,
            "custom_skill_name": ps.custom_skill_name,
            "skill_name": ps.skill.name if ps.skill else ps.custom_skill_name,
            "proficiency": ps.proficiency,
            "created_at": ps.created_at,
        }
        for ps in profile_skills
    ]


async def get_profile_skill_by_id(
    db: AsyncSession, user_id: str, profile_skill_id: str
) -> ProfileSkill:
    profile = await get_profile_by_user_id(db, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )

    result = await db.execute(
        select(ProfileSkill)
        .options(joinedload(ProfileSkill.skill))
        .where(ProfileSkill.profile_id == profile.id)
        .where(ProfileSkill.id == profile_skill_id)
    )
    profile_skill = result.scalars().first()
    if not profile_skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Skill record not found"
        )
    return profile_skill


async def create_profile_skill(
    db: AsyncSession, user_id: str, skill_in: ProfileSkillCreate
):
    profile = await get_profile_by_user_id(db, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )

    normalized_name = skill_in.skill_name.strip().lower()
    if not normalized_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Skill name cannot be empty",
        )

    # 1. Search canonical skills
    result = await db.execute(
        select(Skill).where(Skill.normalized_name == normalized_name)
    )
    skill = result.scalars().first()

    # 2. Search aliases
    if not skill:
        alias_result = await db.execute(
            select(SkillAlias)
            .options(joinedload(SkillAlias.skill))
            .where(SkillAlias.normalized_alias == normalized_name)
        )
        alias_match = alias_result.scalars().first()
        if alias_match:
            skill = alias_match.skill

    # 3. Check for duplicates and create ProfileSkill
    if skill:
        result = await db.execute(
            select(ProfileSkill)
            .where(ProfileSkill.profile_id == profile.id)
            .where(ProfileSkill.skill_id == skill.id)
        )
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Skill already exists in profile",
            )
        ps = ProfileSkill(
            profile_id=profile.id, skill_id=skill.id, proficiency=skill_in.proficiency
        )
        skill_name_response = skill.name
    else:
        result = await db.execute(
            select(ProfileSkill)
            .where(ProfileSkill.profile_id == profile.id)
            .where(func.lower(ProfileSkill.custom_skill_name) == normalized_name)
        )
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Skill already exists in profile",
            )
        ps = ProfileSkill(
            profile_id=profile.id,
            custom_skill_name=skill_in.skill_name.strip(),
            proficiency=skill_in.proficiency,
        )
        skill_name_response = skill_in.skill_name.strip()

    db.add(ps)

    try:
        async with db.begin_nested():
            await db.flush()
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Skill already exists in profile",
        )

    return {
        "id": ps.id,
        "profile_id": ps.profile_id,
        "skill_id": ps.skill_id,
        "custom_skill_name": ps.custom_skill_name,
        "skill_name": skill_name_response,
        "proficiency": ps.proficiency,
        "created_at": ps.created_at,
    }


async def update_profile_skill(
    db: AsyncSession, user_id: str, profile_skill_id: str, skill_in: ProfileSkillUpdate
):
    profile_skill = await get_profile_skill_by_id(db, user_id, profile_skill_id)

    update_data = skill_in.model_dump(exclude_unset=True)
    if "proficiency" in update_data:
        profile_skill.proficiency = update_data["proficiency"]
        db.add(profile_skill)
        await db.flush()

    return {
        "id": profile_skill.id,
        "profile_id": profile_skill.profile_id,
        "skill_id": profile_skill.skill_id,
        "custom_skill_name": profile_skill.custom_skill_name,
        "skill_name": profile_skill.skill.name
        if profile_skill.skill
        else profile_skill.custom_skill_name,
        "proficiency": profile_skill.proficiency,
        "created_at": profile_skill.created_at,
    }


async def delete_profile_skill(
    db: AsyncSession, user_id: str, profile_skill_id: str
) -> None:
    profile_skill = await get_profile_skill_by_id(db, user_id, profile_skill_id)
    await db.delete(profile_skill)
    await db.flush()


async def search_skills(db: AsyncSession, query: str):
    """
    Search skills by name or alias, case-insensitive.
    Returns canonical skills.
    """
    q = query.strip().lower()
    if not q:
        return []

    # Simple ILIKE search for now. Later can be upgraded to trigram.
    search_pattern = f"%{q}%"

    # Search canonical skills
    skills_query = (
        select(Skill, func.cast("name", String).label("matched_by"))
        .options(joinedload(Skill.category))
        .where(Skill.is_active, Skill.normalized_name.ilike(search_pattern))
    )

    # Search aliases
    aliases_query = (
        select(SkillAlias)
        .options(joinedload(SkillAlias.skill).joinedload(Skill.category))
        .where(SkillAlias.normalized_alias.ilike(search_pattern))
    )

    skills_res = await db.execute(skills_query)
    direct_skills = skills_res.all()

    aliases_res = await db.execute(aliases_query)
    alias_matches = aliases_res.scalars().all()

    results = []
    seen_ids = set()

    for skill, _ in direct_skills:
        if skill.id not in seen_ids:
            results.append(
                {
                    "id": skill.id,
                    "name": skill.name,
                    "category": skill.category.name if skill.category else None,
                    "matched_by": "name",
                }
            )
            seen_ids.add(skill.id)

    for alias in alias_matches:
        if alias.skill and alias.skill.id not in seen_ids and alias.skill.is_active:
            results.append(
                {
                    "id": alias.skill.id,
                    "name": alias.skill.name,
                    "category": alias.skill.category.name
                    if alias.skill.category
                    else None,
                    "matched_by": "alias",
                }
            )
            seen_ids.add(alias.skill.id)

    # Sort results to prefer exact matches or those starting with query
    def sort_key(item):
        name_lower = item["name"].lower()
        if name_lower == q:
            return 0
        if name_lower.startswith(q):
            return 1
        return 2

    results.sort(key=sort_key)
    return results[:15]


async def get_projects(db: AsyncSession, user_id: str) -> list[Project]:
    profile = await get_profile_by_user_id(db, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )

    result = await db.execute(
        select(Project)
        .where(Project.profile_id == profile.id)
        .order_by(Project.created_at.desc())
    )
    return list(result.scalars().all())


async def get_project_by_id(db: AsyncSession, user_id: str, project_id: str) -> Project:
    profile = await get_profile_by_user_id(db, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )

    result = await db.execute(
        select(Project)
        .where(Project.profile_id == profile.id)
        .where(Project.id == project_id)
    )
    project = result.scalars().first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project record not found",
        )
    return project


async def create_project(
    db: AsyncSession, user_id: str, project_in: ProjectCreate
) -> Project:
    profile = await get_profile_by_user_id(db, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Create a profile first.",
        )

    data = project_in.model_dump()

    db_project = Project(profile_id=profile.id, **data)
    db.add(db_project)
    await db.flush()
    return db_project


async def update_project(
    db: AsyncSession, user_id: str, project_id: str, project_in: ProjectUpdate
) -> Project:
    project = await get_project_by_id(db, user_id, project_id)

    update_data = project_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(project, field, value)

    db.add(project)
    await db.flush()
    return project


async def delete_project(db: AsyncSession, user_id: str, project_id: str) -> None:
    project = await get_project_by_id(db, user_id, project_id)
    await db.delete(project)
    await db.flush()


async def get_experiences(db: AsyncSession, user_id: str) -> list[Experience]:
    profile = await get_profile_by_user_id(db, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )

    result = await db.execute(
        select(Experience)
        .where(Experience.profile_id == profile.id)
        .order_by(
            Experience.is_current.desc(),
            Experience.start_date.desc().nulls_last(),
            Experience.created_at.desc(),
        )
    )
    return list(result.scalars().all())


async def get_experience_by_id(
    db: AsyncSession, user_id: str, experience_id: str
) -> Experience:
    profile = await get_profile_by_user_id(db, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )

    result = await db.execute(
        select(Experience)
        .where(Experience.profile_id == profile.id)
        .where(Experience.id == experience_id)
    )
    experience = result.scalars().first()
    if not experience:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experience record not found",
        )
    return experience


async def create_experience(
    db: AsyncSession, user_id: str, experience_in: ExperienceCreate
) -> Experience:
    profile = await get_profile_by_user_id(db, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Create a profile first.",
        )

    data = experience_in.model_dump()

    db_experience = Experience(profile_id=profile.id, **data)
    db.add(db_experience)
    await db.flush()
    return db_experience


# --- Experience Skills ---


async def get_experience_skills(
    db: AsyncSession, user_id: str, experience_id: str
) -> list[ExperienceSkillResponse]:
    experience = await get_experience_by_id(db, user_id, experience_id)

    result = await db.execute(
        select(ExperienceSkill)
        .options(
            joinedload(ExperienceSkill.profile_skill).joinedload(ProfileSkill.skill)
        )
        .where(ExperienceSkill.experience_id == experience.id)
        .order_by(ExperienceSkill.created_at)
    )
    experience_skills = result.scalars().all()

    response_list = []
    for es in experience_skills:
        ps = es.profile_skill
        if ps.skill:
            skill_name = ps.skill.name
            is_custom = False
        else:
            skill_name = ps.custom_skill_name
            is_custom = True

        response_list.append(
            ExperienceSkillResponse(
                id=es.id,
                profile_skill_id=es.profile_skill_id,
                skill_id=ps.skill_id,
                skill_name=skill_name,
                is_custom=is_custom,
                proficiency=ps.proficiency,
                created_at=es.created_at,
            )
        )
    return response_list


async def add_experience_skill(
    db: AsyncSession, user_id: str, experience_id: str, skill_in: ExperienceSkillCreate
) -> ExperienceSkillResponse:
    experience = await get_experience_by_id(db, user_id, experience_id)

    # Verify ProfileSkill belongs to the same profile
    result = await db.execute(
        select(ProfileSkill)
        .options(joinedload(ProfileSkill.skill))
        .where(ProfileSkill.id == skill_in.profile_skill_id)
        .where(ProfileSkill.profile_id == experience.profile_id)
    )
    ps = result.scalars().first()
    if not ps:
        raise HTTPException(status_code=404, detail="Profile skill not found")

    db_es = ExperienceSkill(
        experience_id=experience.id,
        profile_skill_id=ps.id,
    )
    db.add(db_es)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Skill is already attached to this experience",
        )

    if ps.skill:
        skill_name = ps.skill.name
        is_custom = False
    else:
        skill_name = ps.custom_skill_name
        is_custom = True

    return ExperienceSkillResponse(
        id=db_es.id,
        profile_skill_id=db_es.profile_skill_id,
        skill_id=ps.skill_id,
        skill_name=skill_name,
        is_custom=is_custom,
        proficiency=ps.proficiency,
        created_at=db_es.created_at,
    )


async def remove_experience_skill(
    db: AsyncSession, user_id: str, experience_id: str, profile_skill_id: str
) -> None:
    experience = await get_experience_by_id(db, user_id, experience_id)

    result = await db.execute(
        select(ExperienceSkill)
        .where(ExperienceSkill.experience_id == experience.id)
        .where(ExperienceSkill.profile_skill_id == profile_skill_id)
    )
    es = result.scalars().first()
    if not es:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experience skill not found"
        )

    await db.delete(es)
    await db.flush()


async def update_experience(
    db: AsyncSession, user_id: str, experience_id: str, experience_in: ExperienceUpdate
) -> Experience:
    experience = await get_experience_by_id(db, user_id, experience_id)

    update_data = experience_in.model_dump(exclude_unset=True)

    # Perform partial cross-field validation
    new_is_current = update_data.get("is_current", experience.is_current)
    new_start_date = update_data.get("start_date", experience.start_date)

    # If explicitly updating end_date, we take it. Otherwise, if is_current becomes true, we must nullify it
    if "end_date" in update_data:
        new_end_date = update_data["end_date"]
    else:
        new_end_date = None if new_is_current else experience.end_date

    # Validate rules
    if new_is_current and new_end_date is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="If is_current is true, end_date must be null.",
        )

    if new_start_date and new_end_date:
        if new_end_date < new_start_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="end_date must not be earlier than start_date.",
            )

    for field, value in update_data.items():
        setattr(experience, field, value)

    # Explicitly enforce end_date rule if is_current was updated but end_date was omitted
    if "end_date" not in update_data and new_is_current:
        experience.end_date = None

    db.add(experience)
    await db.flush()
    return experience


async def delete_experience(db: AsyncSession, user_id: str, experience_id: str) -> None:
    experience = await get_experience_by_id(db, user_id, experience_id)
    await db.delete(experience)
    await db.flush()

async def get_career_preferences(session: AsyncSession, profile_id: str) -> CareerPreference | None:
    result = await session.execute(
        select(CareerPreference).where(CareerPreference.profile_id == profile_id)
    )
    return result.scalars().first()

async def upsert_career_preferences(
    session: AsyncSession, profile_id: str, prefs_in: CareerPreferenceUpsert
) -> CareerPreference:
    prefs = await get_career_preferences(session, profile_id)
    if prefs:
        for field, value in prefs_in.model_dump(exclude_unset=True).items():
            setattr(prefs, field, value)
    else:
        prefs = CareerPreference(
            profile_id=profile_id,
            **prefs_in.model_dump()
        )
        session.add(prefs)
    
    await session.commit()
    await session.refresh(prefs)
    return prefs
