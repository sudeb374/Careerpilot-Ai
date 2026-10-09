import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_profile, get_db
from app.models.opportunity import Opportunity, OpportunitySkill, SavedOpportunity
from app.models.profile import Profile, Skill
from app.schemas.opportunity import (
    OpportunityListItem,
    OpportunityResponse,
    PaginatedOpportunityResponse,
    SavedOpportunityState,
)
from app.services.opportunity import expire_overdue_opportunities


router = APIRouter(
    prefix="/api/v1/opportunities",
    tags=["Opportunities"],
)

@router.get("", response_model=PaginatedOpportunityResponse)
async def list_opportunities(
    q: str | None = None,
    opportunity_type: str | None = None,
    work_model: str | None = None,
    location: str | None = None,
    domain: str | None = None,
    skill_id: UUID | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_profile),
):
    """
    List active opportunities for students.
    """
    await expire_overdue_opportunities(db)

    stmt = select(Opportunity).where(Opportunity.status == "Published")

    if q:
        terms = [term.strip() for term in q.split() if term.strip()]
        if terms:
            term_conditions = []
            for term in terms:
                search_pattern = f"%{term}%"
                term_conditions.append(
                    or_(
                        Opportunity.title.ilike(search_pattern),
                        Opportunity.company_name.ilike(search_pattern),
                        Opportunity.domain.ilike(search_pattern),
                        Opportunity.description.ilike(search_pattern),
                        Opportunity.education_requirements.ilike(search_pattern),
                        Opportunity.eligibility.ilike(search_pattern),
                        Opportunity.skills.any(OpportunitySkill.skill.has(Skill.name.ilike(search_pattern)))
                    )
                )
            stmt = stmt.where(or_(*term_conditions))
    
    if opportunity_type:
        stmt = stmt.where(Opportunity.opportunity_type == opportunity_type)
        
    if work_model:
        stmt = stmt.where(Opportunity.work_model == work_model)
        
    if domain:
        stmt = stmt.where(Opportunity.domain.ilike(f"%{domain}%"))
        
    if location:
        import re
        loc_terms = [term for term in re.split(r'[,\s]+', location) if term]
        for term in loc_terms:
            stmt = stmt.where(func.array_to_string(Opportunity.locations, ",").ilike(f"%{term}%"))
        
    if skill_id:
        stmt = stmt.join(Opportunity.skills).where(OpportunitySkill.skill_id == skill_id)

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    # Order and paginate
    stmt = stmt.options(selectinload(Opportunity.skills).joinedload(OpportunitySkill.skill))
    # Order by deadline asc nulls last, then created_at desc
    stmt = stmt.order_by(
        Opportunity.deadline.asc().nulls_last(),
        Opportunity.created_at.desc()
    )
    
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    opportunities = result.scalars().all()

    # Format skills for response
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

@router.get("/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(
    opportunity_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_profile),
):
    """
    Get details of a specific published opportunity.
    """
    await expire_overdue_opportunities(db)

    stmt = select(Opportunity).options(
        selectinload(Opportunity.skills).joinedload(OpportunitySkill.skill)
    ).where(
        Opportunity.id == opportunity_id,
        Opportunity.status == "Published"
    )
    result = await db.execute(stmt)
    opp = result.scalar_one_or_none()
    
    if not opp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found or not published"
        )
        
    skills_resp = [{"id": os.skill.id, "name": os.skill.name} for os in opp.skills]
    opp_dict = {
        c.name: getattr(opp, c.name) for c in opp.__table__.columns
    }
    opp_dict["skills"] = skills_resp
    return OpportunityResponse(**opp_dict)


@router.post("/{opportunity_id}/save", status_code=status.HTTP_201_CREATED)
async def save_opportunity(
    opportunity_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_profile),
):
    """
    Save an opportunity for the current user.
    """
    await expire_overdue_opportunities(db)

    stmt = select(Opportunity).where(
        Opportunity.id == opportunity_id,
        Opportunity.status == "Published"
    )
    result = await db.execute(stmt)
    opp = result.scalar_one_or_none()
    
    if not opp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found or not published"
        )
        
    try:
        saved_opp = SavedOpportunity(
            profile_id=current_user.id,
            opportunity_id=opportunity_id
        )
        db.add(saved_opp)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Opportunity already saved"
        )
        
    return {"message": "Opportunity saved successfully"}


@router.delete("/{opportunity_id}/save", status_code=status.HTTP_204_NO_CONTENT)
async def unsave_opportunity(
    opportunity_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_profile),
):
    """
    Remove a saved opportunity for the current user.
    """
    stmt = select(SavedOpportunity).where(
        SavedOpportunity.profile_id == current_user.id,
        SavedOpportunity.opportunity_id == opportunity_id
    )
    result = await db.execute(stmt)
    saved_opp = result.scalar_one_or_none()
    
    if not saved_opp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved opportunity not found"
        )
        
    await db.delete(saved_opp)
    await db.commit()


@router.get("/{opportunity_id}/saved", response_model=SavedOpportunityState)
async def check_saved_state(
    opportunity_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_profile),
):
    """
    Check if the current user has saved this opportunity.
    """
    stmt = select(SavedOpportunity).where(
        SavedOpportunity.profile_id == current_user.id,
        SavedOpportunity.opportunity_id == opportunity_id
    )
    result = await db.execute(stmt)
    saved_opp = result.scalar_one_or_none()
    
    return SavedOpportunityState(saved=saved_opp is not None)
