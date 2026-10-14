from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_profile, get_db
from app.models.profile import Profile
from app.schemas.application import (
    ApplicationAnalyticsResponse,
    ApplicationCheckStateResponse,
    ApplicationCreateRequest,
    ApplicationResponse,
    ApplicationUpdateRequest,
    PaginatedApplicationsResponse,
    RemindersSummaryResponse,
)
from app.services.application import (
    check_opportunity_application_state,
    create_application,
    delete_application,
    get_application_analytics,
    get_application_by_id,
    get_application_reminders,
    list_applications,
    update_application,
)

router = APIRouter(
    prefix="/api/v1/applications",
    tags=["Application Tracker"],
)


@router.get(
    "",
    response_model=PaginatedApplicationsResponse,
    status_code=status.HTTP_200_OK,
    summary="List Tracked Applications",
)
async def list_applications_endpoint(
    status_filter: str | None = Query(
        None, alias="status", description="Filter by status (e.g. Applied, Interview)"
    ),
    search: str | None = Query(
        None, description="Search by title, company, domain, or notes"
    ),
    sort_by: str = Query(
        "created_at",
        description="Sort by created_at, applied_at, status_updated_at, deadline, reminder_at",
    ),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    """
    List tracked job applications for the authenticated candidate with search, status filtering, and sorting.
    """
    return await list_applications(
        db=db,
        profile_id=current_user.id,
        status_filter=status_filter,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/analytics",
    response_model=ApplicationAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Application Tracker Analytics",
)
async def get_analytics_endpoint(
    current_user: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate summary statistics, status counts, response rates, and recent activity scoped to the student.
    """
    return await get_application_analytics(db=db, profile_id=current_user.id)


@router.get(
    "/reminders",
    response_model=RemindersSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Upcoming & Due Reminders",
)
async def get_reminders_endpoint(
    current_user: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch personal reminders that are due or upcoming for the authenticated candidate.
    """
    return await get_application_reminders(db=db, profile_id=current_user.id)


@router.get(
    "/check/{opportunity_id}",
    response_model=ApplicationCheckStateResponse,
    status_code=status.HTTP_200_OK,
    summary="Check Opportunity Tracking State",
)
async def check_opportunity_state_endpoint(
    opportunity_id: UUID,
    current_user: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    """
    Check if the current candidate is already tracking an application for a specific opportunity.
    """
    return await check_opportunity_application_state(
        db=db,
        profile_id=current_user.id,
        opportunity_id=opportunity_id,
    )


@router.post(
    "",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Track New Job Application",
)
async def create_application_endpoint(
    request: ApplicationCreateRequest,
    current_user: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    """
    Add an application record linking the candidate to an opportunity.
    Prevents duplicate application records for the same student and opportunity.
    """
    try:
        return await create_application(
            db=db,
            profile_id=current_user.id,
            request=request,
        )
    except ValueError as e:
        err_msg = str(e)
        if "already exists" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=err_msg)
        if "not found" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)


@router.get(
    "/{application_id}",
    response_model=ApplicationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Application Details & History",
)
async def get_application_endpoint(
    application_id: UUID,
    current_user: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve application details, personal notes, reminders, and full status history.
    Enforces candidate ownership.
    """
    try:
        return await get_application_by_id(
            db=db,
            profile_id=current_user.id,
            application_id=application_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.patch(
    "/{application_id}",
    response_model=ApplicationResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Application Status, Notes, or Reminders",
)
async def update_application_endpoint(
    application_id: UUID,
    request: ApplicationUpdateRequest,
    current_user: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    """
    Update status, deadlines, reminder settings, or notes for an application.
    Logs status changes in the audit history.
    """
    try:
        return await update_application(
            db=db,
            profile_id=current_user.id,
            application_id=application_id,
            request=request,
        )
    except ValueError as e:
        err_msg = str(e)
        if "not found" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)


@router.delete(
    "/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Tracked Application",
)
async def delete_application_endpoint(
    application_id: UUID,
    current_user: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove an application from tracking.
    Enforces candidate ownership.
    """
    try:
        await delete_application(
            db=db,
            profile_id=current_user.id,
            application_id=application_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
