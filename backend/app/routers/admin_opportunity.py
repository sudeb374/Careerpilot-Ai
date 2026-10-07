import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_db, require_admin
from app.models.opportunity import Opportunity, OpportunitySkill
from app.models.profile import Profile, Skill
from app.schemas.opportunity import (
    OpportunityCreate,
    OpportunityListItem,
    OpportunityResponse,
    OpportunityUpdate,
    PaginatedOpportunityResponse,
)

router = APIRouter(
    prefix="/api/v1/admin/opportunities",
    tags=["Admin Opportunities"],
)

@router.get("", response_model=PaginatedOpportunityResponse)
async def admin_list_opportunities(
    q: str | None = None,
    opportunity_type: str | None = None,
    work_model: str | None = None,
    status: str | None = None,
    company_name: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    admin_user: Profile = Depends(require_admin),
):
    """
    List all opportunities for admins, including Drafts and Expired.
    """
    stmt = select(Opportunity)

    if q:
        search_pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                Opportunity.title.ilike(search_pattern),
                Opportunity.company_name.ilike(search_pattern),
                Opportunity.domain.ilike(search_pattern),
                Opportunity.description.ilike(search_pattern),
            )
        )
    
    if opportunity_type:
        stmt = stmt.where(Opportunity.opportunity_type == opportunity_type)
        
    if work_model:
        stmt = stmt.where(Opportunity.work_model == work_model)
        
    if status:
        stmt = stmt.where(Opportunity.status == status)

    if company_name:
        stmt = stmt.where(Opportunity.company_name.ilike(f"%{company_name}%"))

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    # Order and paginate
    stmt = stmt.options(selectinload(Opportunity.skills).joinedload(OpportunitySkill.skill))
    stmt = stmt.order_by(
        Opportunity.created_at.desc()
    )
    
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    opportunities = result.scalars().all()

    items = []
    for opp in opportunities:
        skills_resp = [{"id": os.skill.id, "name": os.skill.name} for os in opp.skills]
        opp_dict = {
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
        items.append(OpportunityListItem(**opp_dict))

    return PaginatedOpportunityResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages
    )


@router.post("", response_model=OpportunityResponse, status_code=status.HTTP_201_CREATED)
async def create_opportunity(
    data: OpportunityCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: Profile = Depends(require_admin),
):
    """
    Create a new opportunity as an admin.
    """
    opp_dict = data.model_dump(exclude={"required_skill_ids"})
    opp_dict["created_by_profile_id"] = admin_user.id
    
    # Validation against global skills
    required_skill_ids = data.required_skill_ids
    if required_skill_ids:
        skills_result = await db.execute(select(Skill).where(Skill.id.in_(required_skill_ids)))
        found_skills = skills_result.scalars().all()
        if len(found_skills) != len(required_skill_ids):
            raise HTTPException(status_code=422, detail="One or more skill IDs are invalid.")

    opp = Opportunity(**opp_dict)
    db.add(opp)
    
    try:
        await db.flush() # flush to get opp.id
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Duplicate source_name and external_id")

    for skill_id in required_skill_ids:
        db.add(OpportunitySkill(opportunity_id=opp.id, skill_id=skill_id))
        
    await db.commit()
    
    # Reload with skills
    stmt = select(Opportunity).options(
        selectinload(Opportunity.skills).joinedload(OpportunitySkill.skill)
    ).where(Opportunity.id == opp.id).execution_options(populate_existing=True)
    result = await db.execute(stmt)
    opp_loaded = result.scalar_one()

    skills_resp = [{"id": os.skill.id, "name": os.skill.name} for os in opp_loaded.skills]
    resp_dict = {c.name: getattr(opp_loaded, c.name) for c in opp_loaded.__table__.columns}
    resp_dict["skills"] = skills_resp
    return OpportunityResponse(**resp_dict)


@router.get("/{opportunity_id}", response_model=OpportunityResponse)
async def admin_get_opportunity(
    opportunity_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin_user: Profile = Depends(require_admin),
):
    """
    Get any opportunity details by ID for admin.
    """
    stmt = select(Opportunity).options(
        selectinload(Opportunity.skills).joinedload(OpportunitySkill.skill)
    ).where(Opportunity.id == opportunity_id)
    result = await db.execute(stmt)
    opp = result.scalar_one_or_none()
    
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
        
    skills_resp = [{"id": os.skill.id, "name": os.skill.name} for os in opp.skills]
    opp_dict = {c.name: getattr(opp, c.name) for c in opp.__table__.columns}
    opp_dict["skills"] = skills_resp
    return OpportunityResponse(**opp_dict)


@router.patch("/{opportunity_id}", response_model=OpportunityResponse)
async def update_opportunity(
    opportunity_id: UUID,
    data: OpportunityUpdate,
    db: AsyncSession = Depends(get_db),
    admin_user: Profile = Depends(require_admin),
):
    """
    Update an opportunity.
    """
    stmt = select(Opportunity).options(
        selectinload(Opportunity.skills)
    ).where(Opportunity.id == opportunity_id)
    result = await db.execute(stmt)
    opp = result.scalar_one_or_none()
    
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    update_data = data.model_dump(exclude_unset=True)
    
    # Validation logic for min/max relationships if only one is updated
    new_exp_min = update_data.get("required_experience_min", opp.required_experience_min)
    new_exp_max = update_data.get("required_experience_max", opp.required_experience_max)
    if new_exp_min is not None and new_exp_max is not None and new_exp_max < new_exp_min:
        raise HTTPException(status_code=422, detail="required_experience_max cannot be less than required_experience_min")
        
    new_stipend_min = update_data.get("stipend_min", opp.stipend_min)
    new_stipend_max = update_data.get("stipend_max", opp.stipend_max)
    if new_stipend_min is not None and new_stipend_max is not None and new_stipend_max < new_stipend_min:
        raise HTTPException(status_code=422, detail="stipend_max cannot be less than stipend_min")

    new_salary_min = update_data.get("salary_min", opp.salary_min)
    new_salary_max = update_data.get("salary_max", opp.salary_max)
    if new_salary_min is not None and new_salary_max is not None and new_salary_max < new_salary_min:
        raise HTTPException(status_code=422, detail="salary_max cannot be less than salary_min")

    required_skill_ids = update_data.pop("required_skill_ids", None)

    for field, value in update_data.items():
        setattr(opp, field, value)

    if required_skill_ids is not None:
        # Validate skills
        if required_skill_ids:
            skills_result = await db.execute(select(Skill).where(Skill.id.in_(required_skill_ids)))
            found_skills = skills_result.scalars().all()
            if len(found_skills) != len(required_skill_ids):
                raise HTTPException(status_code=422, detail="One or more skill IDs are invalid.")

        # Atomic replacement: Delete existing and add new
        await db.execute(OpportunitySkill.__table__.delete().where(OpportunitySkill.opportunity_id == opp.id))
        
        for skill_id in required_skill_ids:
            db.add(OpportunitySkill(opportunity_id=opp.id, skill_id=skill_id))

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Duplicate source_name and external_id")

    # Reload
    stmt = select(Opportunity).options(
        selectinload(Opportunity.skills).joinedload(OpportunitySkill.skill)
    ).where(Opportunity.id == opp.id).execution_options(populate_existing=True)
    result = await db.execute(stmt)
    opp_loaded = result.scalar_one()

    skills_resp = [{"id": os.skill.id, "name": os.skill.name} for os in opp_loaded.skills]
    resp_dict = {c.name: getattr(opp_loaded, c.name) for c in opp_loaded.__table__.columns}
    resp_dict["skills"] = skills_resp
    return OpportunityResponse(**resp_dict)


@router.delete("/{opportunity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_opportunity(
    opportunity_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin_user: Profile = Depends(require_admin),
):
    """
    Delete an opportunity.
    """
    result = await db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
    opp = result.scalar_one_or_none()
    
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
        
    await db.delete(opp)
    await db.commit()
