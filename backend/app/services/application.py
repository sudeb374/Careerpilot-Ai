import math
import uuid
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import delete, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.application import Application, ApplicationStatusHistory
from app.models.opportunity import Opportunity, SavedOpportunity
from app.schemas.application import (
    ApplicationActivityItem,
    ApplicationAnalyticsResponse,
    ApplicationCheckStateResponse,
    ApplicationCreateRequest,
    ApplicationListItem,
    ApplicationResponse,
    ApplicationStatus,
    ApplicationStatusHistoryItem,
    ApplicationUpdateRequest,
    OpportunitySummaryForApp,
    PaginatedApplicationsResponse,
    RemindersSummaryResponse,
    VALID_STATUSES,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def list_applications(
    db: AsyncSession,
    profile_id: UUID,
    status_filter: str | None = None,
    search: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    page: int = 1,
    page_size: int = 20,
) -> PaginatedApplicationsResponse:
    """
    List tracked applications for the authenticated candidate with optional filtering, search, and sorting.
    """
    page = max(1, page)
    page_size = max(1, min(page_size, 100))

    query = (
        select(Application)
        .options(selectinload(Application.opportunity))
        .where(Application.profile_id == profile_id)
    )

    if status_filter:
        clean_status = status_filter.strip().title()
        if clean_status in VALID_STATUSES:
            query = query.where(Application.status == clean_status)

    if search and search.strip():
        term = f"%{search.strip().lower()}%"
        query = query.join(Application.opportunity).where(
            or_(
                func.lower(Opportunity.title).ilike(term),
                func.lower(Opportunity.company_name).ilike(term),
                func.lower(func.coalesce(Opportunity.domain, "")).ilike(term),
                func.lower(func.coalesce(Application.notes, "")).ilike(term),
                func.lower(func.coalesce(Application.reminder_note, "")).ilike(term),
            )
        )

    # Count total items
    count_stmt = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Sort
    sort_column_map = {
        "created_at": Application.created_at,
        "applied_at": Application.applied_at,
        "status_updated_at": Application.status_updated_at,
        "deadline": Application.deadline,
        "reminder_at": Application.reminder_at,
    }
    sort_col = sort_column_map.get(sort_by, Application.created_at)
    if sort_order.lower() == "asc":
        query = query.order_by(sort_col.asc().nullslast())
    else:
        query = query.order_by(sort_col.desc().nullslast())

    # Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    res = await db.execute(query)
    apps = res.scalars().all()

    items = [
        ApplicationListItem(
            id=app.id,
            profile_id=app.profile_id,
            opportunity_id=app.opportunity_id,
            status=app.status,
            applied_at=app.applied_at,
            status_updated_at=app.status_updated_at,
            deadline=app.deadline,
            reminder_at=app.reminder_at,
            reminder_note=app.reminder_note,
            notes=app.notes,
            created_at=app.created_at,
            updated_at=app.updated_at,
            opportunity=OpportunitySummaryForApp.model_validate(app.opportunity),
        )
        for app in apps
    ]

    try:
        total_int = int(total)
    except (TypeError, ValueError):
        total_int = len(items)

    total_pages = max(1, math.ceil(total_int / page_size))

    return PaginatedApplicationsResponse(
        items=items,
        total=total_int,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


async def get_application_by_id(
    db: AsyncSession,
    profile_id: UUID,
    application_id: UUID,
) -> ApplicationResponse:
    """
    Fetch a single application record with its full status history and opportunity details.
    Enforces candidate ownership.
    """
    stmt = (
        select(Application)
        .options(
            selectinload(Application.opportunity),
            selectinload(Application.history),
        )
        .where(
            Application.id == application_id,
            Application.profile_id == profile_id,
        )
    )
    res = await db.execute(stmt)
    app = res.scalar_one_or_none()

    if not app:
        raise ValueError("Application not found.")

    sorted_history = sorted(app.history, key=lambda h: h.created_at, reverse=True)

    return ApplicationResponse(
        id=app.id,
        profile_id=app.profile_id,
        opportunity_id=app.opportunity_id,
        status=app.status,
        applied_at=app.applied_at,
        status_updated_at=app.status_updated_at,
        deadline=app.deadline,
        reminder_at=app.reminder_at,
        reminder_note=app.reminder_note,
        notes=app.notes,
        created_at=app.created_at,
        updated_at=app.updated_at,
        opportunity=OpportunitySummaryForApp.model_validate(app.opportunity),
        history=[
            ApplicationStatusHistoryItem.model_validate(h) for h in sorted_history
        ],
    )


async def create_application(
    db: AsyncSession,
    profile_id: UUID,
    request: ApplicationCreateRequest,
) -> ApplicationResponse:
    """
    Create a new application tracking record.
    Prevents duplicate applications for the same candidate and opportunity.
    Automatically populates initial status history.
    """
    # 1. Verify opportunity exists
    opp_stmt = select(Opportunity).where(Opportunity.id == request.opportunity_id)
    opp_res = await db.execute(opp_stmt)
    opp = opp_res.scalar_one_or_none()

    if not opp:
        raise ValueError("Opportunity not found.")

    # 2. Check duplicate application
    dup_stmt = select(Application).where(
        Application.profile_id == profile_id,
        Application.opportunity_id == request.opportunity_id,
    )
    dup_res = await db.execute(dup_stmt)
    if dup_res.scalar_one_or_none():
        raise ValueError("An application record already exists for this opportunity.")

    now = utcnow()
    initial_status = request.status.strip().title()

    # Determine applied_at
    applied_at = request.applied_at
    if initial_status != ApplicationStatus.SAVED.value and applied_at is None:
        applied_at = now

    # Determine deadline: fallback to opportunity deadline if not explicitly provided
    deadline = request.deadline if request.deadline is not None else opp.deadline

    # Create application
    app = Application(
        id=uuid.uuid4(),
        profile_id=profile_id,
        opportunity_id=request.opportunity_id,
        status=initial_status,
        applied_at=applied_at,
        status_updated_at=now,
        deadline=deadline,
        reminder_at=request.reminder_at,
        reminder_note=request.reminder_note,
        notes=request.notes,
        created_at=now,
        updated_at=now,
    )
    db.add(app)
    await db.flush()

    # Create initial status history entry
    hist = ApplicationStatusHistory(
        id=uuid.uuid4(),
        application_id=app.id,
        from_status=None,
        to_status=initial_status,
        note=f"Application tracked as {initial_status}.",
        created_at=now,
    )
    db.add(hist)
    await db.commit()
    await db.refresh(app)

    app.opportunity = opp
    return ApplicationResponse(
        id=app.id,
        profile_id=app.profile_id,
        opportunity_id=app.opportunity_id,
        status=app.status,
        applied_at=app.applied_at,
        status_updated_at=app.status_updated_at,
        deadline=app.deadline,
        reminder_at=app.reminder_at,
        reminder_note=app.reminder_note,
        notes=app.notes,
        created_at=app.created_at,
        updated_at=app.updated_at,
        opportunity=OpportunitySummaryForApp.model_validate(app.opportunity),
        history=[ApplicationStatusHistoryItem.model_validate(hist)],
    )


async def update_application(
    db: AsyncSession,
    profile_id: UUID,
    application_id: UUID,
    request: ApplicationUpdateRequest,
) -> ApplicationResponse:
    """
    Update an application record's status, notes, deadlines, or reminder settings.
    Logs status transitions in application_status_history.
    """
    stmt = (
        select(Application)
        .options(
            selectinload(Application.opportunity),
            selectinload(Application.history),
        )
        .where(
            Application.id == application_id,
            Application.profile_id == profile_id,
        )
    )
    res = await db.execute(stmt)
    app = res.scalar_one_or_none()

    if not app:
        raise ValueError("Application not found.")

    now = utcnow()
    new_hist = None

    # Status transition
    if request.status and request.status != app.status:
        old_status = app.status
        new_status = request.status
        app.status = new_status
        app.status_updated_at = now

        # If transitioning to Applied or later from Saved and applied_at is empty, set applied_at
        if new_status != ApplicationStatus.SAVED.value and app.applied_at is None:
            app.applied_at = request.applied_at or now

        note_text = request.status_change_note or f"Status updated from {old_status} to {new_status}."
        new_hist = ApplicationStatusHistory(
            id=uuid.uuid4(),
            application_id=app.id,
            from_status=old_status,
            to_status=new_status,
            note=note_text,
            created_at=now,
        )
        db.add(new_hist)
    elif request.status_change_note:
        # Note logged without status change
        new_hist = ApplicationStatusHistory(
            id=uuid.uuid4(),
            application_id=app.id,
            from_status=app.status,
            to_status=app.status,
            note=request.status_change_note,
            created_at=now,
        )
        db.add(new_hist)

    if request.applied_at is not None:
        app.applied_at = request.applied_at

    if request.deadline is not None:
        app.deadline = request.deadline

    # Allow setting or updating reminder
    if "reminder_at" in request.model_fields_set:
        app.reminder_at = request.reminder_at

    if "reminder_note" in request.model_fields_set:
        app.reminder_note = request.reminder_note

    if "notes" in request.model_fields_set:
        app.notes = request.notes

    app.updated_at = now
    await db.commit()

    if not hasattr(app, "history") or app.history is None:
        app.history = []
    if new_hist and new_hist not in app.history:
        app.history.append(new_hist)

    sorted_history = sorted(app.history, key=lambda h: h.created_at, reverse=True)

    return ApplicationResponse(
        id=app.id,
        profile_id=app.profile_id,
        opportunity_id=app.opportunity_id,
        status=app.status,
        applied_at=app.applied_at,
        status_updated_at=app.status_updated_at,
        deadline=app.deadline,
        reminder_at=app.reminder_at,
        reminder_note=app.reminder_note,
        notes=app.notes,
        created_at=app.created_at,
        updated_at=app.updated_at,
        opportunity=OpportunitySummaryForApp.model_validate(app.opportunity),
        history=[
            ApplicationStatusHistoryItem.model_validate(h) for h in sorted_history
        ],
    )


async def delete_application(
    db: AsyncSession,
    profile_id: UUID,
    application_id: UUID,
) -> None:
    """
    Remove an application from tracking.
    Enforces candidate ownership.
    """
    stmt = select(Application).where(
        Application.id == application_id,
        Application.profile_id == profile_id,
    )
    res = await db.execute(stmt)
    app = res.scalar_one_or_none()

    if not app:
        raise ValueError("Application not found.")

    await db.delete(app)
    await db.commit()


async def get_application_analytics(
    db: AsyncSession,
    profile_id: UUID,
) -> ApplicationAnalyticsResponse:
    """
    Generate candidate-scoped summary counts, status breakdowns, and ethical response analytics.
    """
    apps_stmt = select(Application).where(Application.profile_id == profile_id)
    apps_res = await db.execute(apps_stmt)
    apps = apps_res.scalars().all()

    now = utcnow()
    total_tracked = len(apps)

    # Status breakdown
    by_status = {s.value: 0 for s in ApplicationStatus}
    for a in apps:
        if a.status in by_status:
            by_status[a.status] += 1
        else:
            by_status[a.status] = 1

    # Total submitted = all applications that are not just "Saved"
    submitted_apps = [a for a in apps if a.status != ApplicationStatus.SAVED.value]
    total_submitted = len(submitted_apps)

    active_interviews_count = by_status.get(ApplicationStatus.INTERVIEW.value, 0)

    # Upcoming deadlines: active applications with deadline in future
    active_statuses = {
        ApplicationStatus.SAVED.value,
        ApplicationStatus.APPLIED.value,
        ApplicationStatus.ASSESSMENT.value,
        ApplicationStatus.INTERVIEW.value,
    }
    upcoming_deadlines_count = sum(
        1 for a in apps if a.deadline and a.deadline >= now and a.status in active_statuses
    )

    # Reminders: due vs upcoming
    terminal_statuses = {
        ApplicationStatus.OFFER.value,
        ApplicationStatus.REJECTED.value,
        ApplicationStatus.WITHDRAWN.value,
    }
    active_reminders_count = sum(
        1
        for a in apps
        if a.reminder_at and a.reminder_at > now and a.status not in terminal_statuses
    )
    overdue_reminders_count = sum(
        1
        for a in apps
        if a.reminder_at and a.reminder_at <= now and a.status not in terminal_statuses
    )

    # Response Rate calculation (Assessment, Interview, Offer, Rejected)
    responded_statuses = {
        ApplicationStatus.ASSESSMENT.value,
        ApplicationStatus.INTERVIEW.value,
        ApplicationStatus.OFFER.value,
        ApplicationStatus.REJECTED.value,
    }
    responded_count = sum(1 for a in submitted_apps if a.status in responded_statuses)

    response_rate: float | None = None
    if total_submitted > 0:
        response_rate = round((responded_count / total_submitted) * 100, 1)

    if total_submitted == 0:
        response_rate_note = "No applications submitted yet."
    elif total_submitted < 5:
        response_rate_note = f"Based on {total_submitted} submitted application(s). Small sample size — indicative only."
    else:
        response_rate_note = f"Calculated across {total_submitted} submitted applications."

    # Interview Conversion Rate (Interview, Offer)
    interview_count = sum(
        1
        for a in submitted_apps
        if a.status in {ApplicationStatus.INTERVIEW.value, ApplicationStatus.OFFER.value}
    )
    interview_rate: float | None = None
    if total_submitted > 0:
        interview_rate = round((interview_count / total_submitted) * 100, 1)

    if total_submitted == 0:
        interview_rate_note = "No applications submitted yet."
    elif total_submitted < 5:
        interview_rate_note = f"Based on {total_submitted} submitted application(s). Small sample size — indicative only."
    else:
        interview_rate_note = f"Percentage of submissions advancing to interview stages ({interview_count}/{total_submitted})."

    # Recent Activity: latest 8 status changes
    recent_activity: list[ApplicationActivityItem] = []
    hist_stmt = (
        select(ApplicationStatusHistory)
        .join(ApplicationStatusHistory.application)
        .options(
            selectinload(ApplicationStatusHistory.application).selectinload(
                Application.opportunity
            )
        )
        .where(Application.profile_id == profile_id)
        .order_by(ApplicationStatusHistory.created_at.desc())
        .limit(8)
    )
    hist_res = await db.execute(hist_stmt)
    histories = hist_res.scalars().all()

    for h in histories:
        if h.application and h.application.opportunity:
            recent_activity.append(
                ApplicationActivityItem(
                    id=h.id,
                    application_id=h.application_id,
                    opportunity_id=h.application.opportunity_id,
                    opportunity_title=h.application.opportunity.title,
                    company_name=h.application.opportunity.company_name,
                    from_status=h.from_status,
                    to_status=h.to_status,
                    note=h.note,
                    timestamp=h.created_at,
                )
            )

    return ApplicationAnalyticsResponse(
        total_tracked=total_tracked,
        total_submitted=total_submitted,
        by_status=by_status,
        active_interviews_count=active_interviews_count,
        upcoming_deadlines_count=upcoming_deadlines_count,
        active_reminders_count=active_reminders_count,
        overdue_reminders_count=overdue_reminders_count,
        response_rate_percent=response_rate,
        response_rate_note=response_rate_note,
        interview_rate_percent=interview_rate,
        interview_rate_note=interview_rate_note,
        recent_activity=recent_activity,
    )


async def get_application_reminders(
    db: AsyncSession,
    profile_id: UUID,
) -> RemindersSummaryResponse:
    """
    Fetch upcoming and due reminders for the student's active applications.
    """
    now = utcnow()
    terminal_statuses = {
        ApplicationStatus.OFFER.value,
        ApplicationStatus.REJECTED.value,
        ApplicationStatus.WITHDRAWN.value,
    }

    stmt = (
        select(Application)
        .options(selectinload(Application.opportunity))
        .where(
            Application.profile_id == profile_id,
            Application.reminder_at.is_not(None),
            Application.status.not_in(terminal_statuses),
        )
        .order_by(Application.reminder_at.asc())
    )
    res = await db.execute(stmt)
    apps = res.scalars().all()

    due_items: list[ApplicationListItem] = []
    upcoming_items: list[ApplicationListItem] = []

    for a in apps:
        item = ApplicationListItem(
            id=a.id,
            profile_id=a.profile_id,
            opportunity_id=a.opportunity_id,
            status=a.status,
            applied_at=a.applied_at,
            status_updated_at=a.status_updated_at,
            deadline=a.deadline,
            reminder_at=a.reminder_at,
            reminder_note=a.reminder_note,
            notes=a.notes,
            created_at=a.created_at,
            updated_at=a.updated_at,
            opportunity=OpportunitySummaryForApp.model_validate(a.opportunity),
        )
        if a.reminder_at and a.reminder_at <= now:
            due_items.append(item)
        else:
            upcoming_items.append(item)

    return RemindersSummaryResponse(
        due_count=len(due_items),
        upcoming_count=len(upcoming_items),
        due_reminders=due_items,
        upcoming_reminders=upcoming_items,
    )


async def check_opportunity_application_state(
    db: AsyncSession,
    profile_id: UUID,
    opportunity_id: UUID,
) -> ApplicationCheckStateResponse:
    """
    Check whether a candidate is currently tracking a specific opportunity.
    """
    stmt = select(Application).where(
        Application.profile_id == profile_id,
        Application.opportunity_id == opportunity_id,
    )
    res = await db.execute(stmt)
    app = res.scalar_one_or_none()

    if not app:
        return ApplicationCheckStateResponse(is_tracked=False)

    return ApplicationCheckStateResponse(
        is_tracked=True,
        application_id=app.id,
        status=app.status,
        applied_at=app.applied_at,
    )
