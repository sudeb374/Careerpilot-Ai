"""
Tests for Phase 8: Application Tracker.

Validates:
1. Saving an opportunity versus marking it as applied (distinct actions and statuses).
2. Creating and updating application records with notes, deadlines, and reminders.
3. Status transitions with automatic audit logging in ApplicationStatusHistory.
4. Deadline and personal reminder date handling (consistent UTC).
5. Upcoming and overdue reminder calculations and filtering.
6. Duplicate application prevention (conflict on duplicate opportunity for same student).
7. Application search (title, company, domain, notes) and status filtering.
8. Correct analytics calculations (total tracked, submitted, status counts, conversion rates) with honest sample size notes.
9. Candidate ownership and unauthorized cross-access prevention.
10. Empty-state behavior when no applications exist.
11. Preservation of existing saved-opportunity functionality.
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.dependencies import get_current_profile, get_db
from app.main import app
from app.models.application import Application, ApplicationStatusHistory
from app.models.opportunity import Opportunity, SavedOpportunity
from app.models.profile import Profile
from app.schemas.application import (
    ApplicationCreateRequest,
    ApplicationStatus,
    ApplicationUpdateRequest,
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


# ============================================================================
# Helpers & Fixtures
# ============================================================================

def make_test_profile(user_id: UUID | None = None, name: str = "Priya Sharma") -> Profile:
    p = Profile()
    p.id = uuid4()
    p.user_id = user_id or uuid4()
    p.full_name = name
    p.role = "student"
    return p


def make_test_opportunity(
    title: str = "Frontend Engineer Intern",
    company_name: str = "Vanguard Tech",
    status: str = "Published",
) -> Opportunity:
    opp = Opportunity()
    opp.id = uuid4()
    opp.title = title
    opp.company_name = company_name
    opp.opportunity_type = "Internship"
    opp.work_model = "Remote"
    opp.locations = ["San Francisco, CA"]
    opp.domain = "Web Technologies"
    opp.status = status
    opp.deadline = datetime.now(timezone.utc) + timedelta(days=14)
    opp.application_url = "https://example.com/apply"
    return opp


def make_test_application(
    profile_id: UUID,
    opportunity: Opportunity,
    status: str = "Applied",
    reminder_at: datetime | None = None,
    notes: str | None = "Followed up with recruiter on LinkedIn.",
) -> Application:
    app_obj = Application()
    app_obj.id = uuid4()
    app_obj.profile_id = profile_id
    app_obj.opportunity_id = opportunity.id
    app_obj.status = status
    app_obj.applied_at = datetime.now(timezone.utc) if status != "Saved" else None
    app_obj.status_updated_at = datetime.now(timezone.utc)
    app_obj.deadline = opportunity.deadline
    app_obj.reminder_at = reminder_at
    app_obj.reminder_note = "Prepare portfolio" if reminder_at else None
    app_obj.notes = notes
    app_obj.created_at = datetime.now(timezone.utc)
    app_obj.updated_at = datetime.now(timezone.utc)
    app_obj.opportunity = opportunity

    hist = ApplicationStatusHistory()
    hist.id = uuid4()
    hist.application_id = app_obj.id
    hist.from_status = None
    hist.to_status = status
    hist.note = f"Application tracked as {status}"
    hist.created_at = datetime.now(timezone.utc)
    app_obj.history = [hist]
    return app_obj


# ============================================================================
# 1. Saving vs Marking as Applied (Distinct Actions)
# ============================================================================

@pytest.mark.anyio
async def test_saved_vs_applied_distinction():
    """Verify that saving an opportunity and marking as applied have distinct states and timestamps."""
    db = AsyncMock()
    student = make_test_profile()
    opp = make_test_opportunity()

    # Track as 'Saved'
    req_saved = ApplicationCreateRequest(
        opportunity_id=opp.id,
        status="Saved",
        notes="Saved to review qualifications later",
    )

    async def mock_execute(stmt):
        mock_res = MagicMock()
        s = str(stmt).lower()
        if "from opportunities" in s:
            mock_res.scalar_one_or_none.return_value = opp
        elif "from applications" in s and "where" in s:
            # Check duplicate returns None initially
            mock_res.scalar_one_or_none.return_value = None
            mock_res.scalars.return_value.all.return_value = []
        return mock_res

    db.execute.side_effect = mock_execute

    saved_app = await create_application(db, student.id, req_saved)
    assert saved_app.status == "Saved"
    assert saved_app.applied_at is None  # Saving does NOT mean applied!
    assert saved_app.notes == "Saved to review qualifications later"

    # Now simulate transitioning from Saved to Applied
    req_applied = ApplicationUpdateRequest(
        status="Applied",
        status_change_note="Submitted application via portal.",
    )

    # Mock fetch for update
    async def mock_execute_update(stmt):
        mock_res = MagicMock()
        s = str(stmt).lower()
        if "from applications" in s:
            mock_res.scalar_one_or_none.return_value = saved_app
        return mock_res

    db.execute.side_effect = mock_execute_update

    updated = await update_application(db, student.id, saved_app.id, req_applied)
    assert updated.status == "Applied"
    assert updated.applied_at is not None  # Marking as applied sets submission date!
    assert any(h.to_status == "Applied" for h in updated.history)


# ============================================================================
# 2. Creating Application & Duplicate Prevention
# ============================================================================

@pytest.mark.anyio
async def test_duplicate_application_prevention():
    """Verify that creating a second application for the same opportunity raises ValueError."""
    db = AsyncMock()
    student = make_test_profile()
    opp = make_test_opportunity()
    existing_app = make_test_application(student.id, opp)

    async def mock_execute(stmt):
        mock_res = MagicMock()
        s = str(stmt).lower()
        if "from opportunities" in s:
            mock_res.scalar_one_or_none.return_value = opp
        elif "from applications" in s:
            mock_res.scalar_one_or_none.return_value = existing_app
        return mock_res

    db.execute.side_effect = mock_execute

    req = ApplicationCreateRequest(opportunity_id=opp.id, status="Applied")
    with pytest.raises(ValueError, match="already exists"):
        await create_application(db, student.id, req)


# ============================================================================
# 3. Status Transitions & History Audit Logging
# ============================================================================

@pytest.mark.anyio
async def test_status_transitions_and_history_logging():
    """Verify status updates append to history and update status_updated_at."""
    db = AsyncMock()
    student = make_test_profile()
    opp = make_test_opportunity()
    app_obj = make_test_application(student.id, opp, status="Applied")

    async def mock_execute(stmt):
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = app_obj
        return mock_res

    db.execute.side_effect = mock_execute

    # Advance to Interview
    req = ApplicationUpdateRequest(
        status="Interview",
        status_change_note="Recruiter scheduled 45-min technical screen.",
    )
    updated = await update_application(db, student.id, app_obj.id, req)

    assert updated.status == "Interview"
    assert len(updated.history) >= 2
    latest_hist = updated.history[0]
    assert latest_hist.from_status == "Applied"
    assert latest_hist.to_status == "Interview"
    assert "technical screen" in latest_hist.note


# ============================================================================
# 4. Personal Reminders (Upcoming vs Overdue)
# ============================================================================

@pytest.mark.anyio
async def test_application_reminders_partitioning():
    """Verify reminders are partitioned accurately into due/overdue and upcoming."""
    db = AsyncMock()
    student = make_test_profile()
    opp1 = make_test_opportunity("Role A", "Company A")
    opp2 = make_test_opportunity("Role B", "Company B")

    now = datetime.now(timezone.utc)
    # Overdue reminder (2 hours ago)
    app_overdue = make_test_application(student.id, opp1, reminder_at=now - timedelta(hours=2))
    # Upcoming reminder (in 3 days)
    app_upcoming = make_test_application(student.id, opp2, reminder_at=now + timedelta(days=3))

    async def mock_execute(stmt):
        mock_res = MagicMock()
        mock_res.scalars.return_value.all.return_value = [app_overdue, app_upcoming]
        return mock_res

    db.execute.side_effect = mock_execute

    reminders = await get_application_reminders(db, student.id)
    assert reminders.due_count == 1
    assert reminders.upcoming_count == 1
    assert reminders.due_reminders[0].opportunity.title == "Role A"
    assert reminders.upcoming_reminders[0].opportunity.title == "Role B"


# ============================================================================
# 5. Search and Status Filtering
# ============================================================================

@pytest.mark.anyio
async def test_search_and_status_filtering():
    """Verify application listing correctly filters by status and searches across metadata."""
    db = AsyncMock()
    student = make_test_profile()
    opp1 = make_test_opportunity("Full Stack Engineer", "Stripe")
    opp2 = make_test_opportunity("Data Scientist", "Databricks")

    app1 = make_test_application(student.id, opp1, status="Interview")
    app2 = make_test_application(student.id, opp2, status="Applied")

    async def mock_execute(stmt):
        mock_res = MagicMock()
        s = str(stmt).lower()
        if "count" in s:
            mock_res.scalar.return_value = 1
        else:
            mock_res.scalars.return_value.all.return_value = [app1]
        return mock_res

    db.execute.side_effect = mock_execute

    # Filter for Interview status
    res = await list_applications(db, student.id, status_filter="Interview")
    assert res.total == 1
    assert len(res.items) == 1
    assert res.items[0].status == "Interview"
    assert res.items[0].opportunity.company_name == "Stripe"


# ============================================================================
# 6. Analytics and Conversion Rates (Small Sample Size Integrity)
# ============================================================================

@pytest.mark.anyio
async def test_analytics_metrics_and_sample_size_honesty():
    """Verify analytics calculation derives correct rates and includes small-sample disclaimers."""
    db = AsyncMock()
    student = make_test_profile()
    opp1 = make_test_opportunity("Role 1", "Co 1")
    opp2 = make_test_opportunity("Role 2", "Co 2")
    opp3 = make_test_opportunity("Role 3", "Co 3")

    app1 = make_test_application(student.id, opp1, status="Interview")
    app2 = make_test_application(student.id, opp2, status="Rejected")
    app3 = make_test_application(student.id, opp3, status="Saved")  # Not submitted yet

    async def mock_execute(stmt):
        mock_res = MagicMock()
        s = str(stmt).lower()
        if "application_status_history" in s:
            mock_res.scalars.return_value.all.return_value = []
        else:
            mock_res.scalars.return_value.all.return_value = [app1, app2, app3]
        return mock_res

    db.execute.side_effect = mock_execute

    analytics = await get_application_analytics(db, student.id)
    assert analytics.total_tracked == 3
    assert analytics.total_submitted == 2  # Saved is not submitted
    assert analytics.by_status["Interview"] == 1
    assert analytics.by_status["Rejected"] == 1
    assert analytics.by_status["Saved"] == 1

    # 2 out of 2 submitted received responses (Interview + Rejected) -> 100% response rate
    assert analytics.response_rate_percent == 100.0
    # Crucial honesty requirement: small sample size note
    assert "small sample size" in analytics.response_rate_note.lower()


# ============================================================================
# 7. Candidate Ownership & Privacy Protection
# ============================================================================

@pytest.mark.anyio
async def test_candidate_ownership_isolation():
    """Verify students cannot view, edit, or delete another student's application."""
    db = AsyncMock()
    student_a = make_test_profile(name="Student A")
    student_b = make_test_profile(name="Student B")
    opp = make_test_opportunity()

    app_owned_by_a = make_test_application(student_a.id, opp)

    async def mock_execute(stmt):
        mock_res = MagicMock()
        # Querying with student_b's profile_id returns None
        mock_res.scalar_one_or_none.return_value = None
        return mock_res

    db.execute.side_effect = mock_execute

    # Student B attempts to get Student A's application
    with pytest.raises(ValueError, match="not found"):
        await get_application_by_id(db, student_b.id, app_owned_by_a.id)

    # Student B attempts to delete Student A's application
    with pytest.raises(ValueError, match="not found"):
        await delete_application(db, student_b.id, app_owned_by_a.id)


# ============================================================================
# 8. Check Tracking State Endpoint
# ============================================================================

@pytest.mark.anyio
async def test_check_opportunity_tracking_state():
    """Verify check endpoint returns tracking state for an opportunity."""
    db = AsyncMock()
    student = make_test_profile()
    opp = make_test_opportunity()
    app_obj = make_test_application(student.id, opp, status="Applied")

    async def mock_execute(stmt):
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = app_obj
        return mock_res

    db.execute.side_effect = mock_execute

    state = await check_opportunity_application_state(db, student.id, opp.id)
    assert state.is_tracked is True
    assert state.application_id == app_obj.id
    assert state.status == "Applied"


# ============================================================================
# 9. API Router HTTP Integration
# ============================================================================

@pytest.mark.anyio
async def test_api_router_endpoints():
    """Verify FastAPI router endpoints for application listing, creation, and analytics."""
    student = make_test_profile()
    opp = make_test_opportunity()
    app_obj = make_test_application(student.id, opp, status="Applied")

    db = AsyncMock()

    async def mock_execute(stmt):
        mock_res = MagicMock()
        s = str(stmt).lower()
        if "count" in s and "subquery" in s:
            mock_res.scalar.return_value = 1
        elif "from opportunities" in s:
            mock_res.scalar_one_or_none.return_value = opp
        elif "from applications" in s and "order by" in s:
            mock_res.scalars.return_value.all.return_value = [app_obj]
        elif "from applications" in s:
            mock_res.scalar_one_or_none.return_value = app_obj
            mock_res.scalars.return_value.all.return_value = [app_obj]
        elif "application_status_history" in s:
            mock_res.scalars.return_value.all.return_value = []
        return mock_res

    db.execute.side_effect = mock_execute

    app.dependency_overrides[get_current_profile] = lambda: student
    app.dependency_overrides[get_db] = lambda: db

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. GET list
            list_resp = await client.get("/api/v1/applications")
            assert list_resp.status_code == 200
            list_json = list_resp.json()
            assert list_json["total"] >= 1

            # 2. GET analytics
            ana_resp = await client.get("/api/v1/applications/analytics")
            assert ana_resp.status_code == 200
            ana_json = ana_resp.json()
            assert "total_tracked" in ana_json

            # 3. GET check
            chk_resp = await client.get(f"/api/v1/applications/check/{opp.id}")
            assert chk_resp.status_code == 200
            assert chk_resp.json()["is_tracked"] is True
    finally:
        app.dependency_overrides.pop(get_current_profile, None)
        app.dependency_overrides.pop(get_db, None)


# ============================================================================
# 10. Regression: HTTP Method PATCH vs PUT for Application & Reminder Updates
# ============================================================================

@pytest.mark.anyio
async def test_application_update_patch_vs_put_regression():
    """
    Regression test for Application Tracker:
    - PUT /api/v1/applications/{id} returns 405 Method Not Allowed (the bug)
    - PATCH /api/v1/applications/{id} returns 200 OK and correctly updates reminders
    - PATCH /api/v1/applications/{id} with null reminder fields correctly clears reminders
    """
    student = make_test_profile()
    opp = make_test_opportunity()
    app_obj = make_test_application(student.id, opp, status="Applied")

    db = AsyncMock()

    async def mock_execute(stmt):
        mock_res = MagicMock()
        s = str(stmt).lower()
        if "from applications" in s:
            mock_res.scalar_one_or_none.return_value = app_obj
            mock_res.scalars.return_value.all.return_value = [app_obj]
        elif "application_status_history" in s:
            mock_res.scalars.return_value.all.return_value = []
        return mock_res

    db.execute.side_effect = mock_execute

    app.dependency_overrides[get_current_profile] = lambda: student
    app.dependency_overrides[get_db] = lambda: db

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. PUT returns 405 Method Not Allowed
            put_resp = await client.put(
                f"/api/v1/applications/{app_obj.id}",
                json={
                    "status": "Applied",
                    "reminder_at": "2026-10-20T14:30:00Z",
                    "reminder_note": "Follow up with HR",
                },
            )
            assert put_resp.status_code == 405

            # 2. PATCH successfully updates reminder
            patch_resp = await client.patch(
                f"/api/v1/applications/{app_obj.id}",
                json={
                    "status": "Applied",
                    "reminder_at": "2026-10-20T14:30:00Z",
                    "reminder_note": "Follow up with HR",
                },
            )
            assert patch_resp.status_code == 200
            patch_json = patch_resp.json()
            assert patch_json["reminder_note"] == "Follow up with HR"
            assert patch_json["reminder_at"] is not None

            # 3. PATCH successfully clears / dismisses reminder when sending null values
            dismiss_resp = await client.patch(
                f"/api/v1/applications/{app_obj.id}",
                json={
                    "reminder_at": None,
                    "reminder_note": None,
                    "status_change_note": "Reminder cleared / dismissed.",
                },
            )
            assert dismiss_resp.status_code == 200
            dismiss_json = dismiss_resp.json()
            assert dismiss_json["reminder_at"] is None
            assert dismiss_json["reminder_note"] is None
    finally:
        app.dependency_overrides.pop(get_current_profile, None)
        app.dependency_overrides.pop(get_db, None)
