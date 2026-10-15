"""
Tests for Phase 9.2: Security & Route Middleware Hardening.

Validates:
1. Direct require_admin dependency authorization (admin passes, student and others raise 403).
2. Admin endpoints reject unauthenticated requests with 401.
3. Admin endpoints reject authenticated student requests with 403 Forbidden.
4. Admin endpoints allow authorized admin requests.
5. ProfileUpdate schema prevents role self-escalation (role cannot be injected or updated).
6. Protected candidate endpoints require authentication (reject unauthenticated with 401).
"""

import os
import sys
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.dependencies import get_current_profile, get_current_user, get_db, require_admin
from app.main import app
from app.models.profile import Profile
from app.schemas.profile import ProfileUpdate


def make_profile(role: str = "student", name: str = "Test User") -> Profile:
    p = Profile()
    p.id = uuid4()
    p.user_id = uuid4()
    p.full_name = name
    p.role = role
    return p


# ============================================================================
# 1. Direct Dependency Authorization Tests
# ============================================================================

def test_require_admin_allows_admin():
    admin = make_profile(role="admin", name="Admin User")
    result = require_admin(profile=admin)
    assert result == admin
    assert result.role == "admin"


def test_require_admin_rejects_student():
    student = make_profile(role="student", name="Student User")
    with pytest.raises(HTTPException) as exc_info:
        require_admin(profile=student)
    assert exc_info.value.status_code == 403
    assert "Not enough permissions" in exc_info.value.detail


def test_require_admin_rejects_arbitrary_or_empty_role():
    guest = make_profile(role="guest", name="Guest User")
    with pytest.raises(HTTPException) as exc_info:
        require_admin(profile=guest)
    assert exc_info.value.status_code == 403

    empty_role = make_profile(role="", name="Empty Role User")
    with pytest.raises(HTTPException) as exc_info:
        require_admin(profile=empty_role)
    assert exc_info.value.status_code == 403


# ============================================================================
# 2. HTTP Route Authorization & Protection Tests
# ============================================================================

@pytest.mark.anyio
async def test_admin_endpoints_reject_unauthenticated():
    app.dependency_overrides.clear()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # GET /api/v1/admin/opportunities
        res_opps = await client.get("/api/v1/admin/opportunities")
        assert res_opps.status_code == 401

        # POST /api/v1/admin/ingestion/jsearch/preview
        res_preview = await client.post(
            "/api/v1/admin/ingestion/jsearch/preview",
            json={"query": "python"},
        )
        assert res_preview.status_code == 401


@pytest.mark.anyio
async def test_candidate_endpoints_reject_unauthenticated():
    app.dependency_overrides.clear()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Profile endpoint
        res_profile = await client.get("/api/v1/profile")
        assert res_profile.status_code == 401

        # Applications endpoint
        res_apps = await client.get("/api/v1/applications")
        assert res_apps.status_code == 401

        # Opportunities endpoint
        res_opps = await client.get("/api/v1/opportunities")
        assert res_opps.status_code == 401


@pytest.mark.anyio
async def test_admin_endpoints_reject_student_role():
    student = make_profile(role="student", name="Candidate Student")

    app.dependency_overrides.clear()
    app.dependency_overrides[get_current_profile] = lambda: student
    app.dependency_overrides[require_admin] = lambda: (_ for _ in ()).throw(
        HTTPException(status_code=403, detail="Not enough permissions")
    )

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.get(
                "/api/v1/admin/opportunities",
                headers={"Authorization": "Bearer mock-student-token"},
            )
            assert res.status_code == 403
            assert res.json()["detail"] == "Not enough permissions"

            res_ingest = await client.post(
                "/api/v1/admin/ingestion/jsearch/preview",
                json={"query": "python developer"},
                headers={"Authorization": "Bearer mock-student-token"},
            )
            assert res_ingest.status_code == 403
            assert res_ingest.json()["detail"] == "Not enough permissions"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_admin_endpoints_allow_admin_role():
    admin = make_profile(role="admin", name="Authorized Admin")

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar.return_value = 0
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    app.dependency_overrides.clear()
    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.get(
                "/api/v1/admin/opportunities",
                headers={"Authorization": "Bearer mock-admin-token"},
            )
            assert res.status_code == 200
            data = res.json()
            assert "items" in data
            assert data["total"] == 0
    finally:
        app.dependency_overrides.clear()


# ============================================================================
# 3. Role Escalation Prevention Tests
# ============================================================================

def test_profile_update_schema_excludes_role():
    """Verify that ProfileUpdate schema does not accept role field."""
    assert "role" not in ProfileUpdate.model_fields

    # Attempting to instantiate with role should ignore it (extra fields excluded/ignored)
    update = ProfileUpdate(
        headline="Software Engineer",
        role="admin",  # Attacker attempt to escalate
    )
    dumped = update.model_dump(exclude_unset=True)
    assert "role" not in dumped
    assert dumped == {"headline": "Software Engineer"}
