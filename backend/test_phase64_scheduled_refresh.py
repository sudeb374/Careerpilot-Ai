"""
CareerPilot AI — Phase 6.4 Automated Test Suite

Tests:
1. Part A: Scheduled Refresh Orchestrator, Concurrency Lock, Safe Updates, Error Isolation, CLI.
2. Part B: Idempotent Deadline-Based Expiration, Timezone Boundaries, Draft/Closed Preservation.
3. Part C: Admin Bulk Upload (CSV/JSON), Schema Boundaries, HTML Sanitization, URL Security, Savepoints.
4. Admin Ingestion Endpoints (Bulk Upload Preview/Import, Refresh Trigger/Status, Authorization).
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import IntegrityError

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.config import settings
from app.core.dependencies import get_current_user, get_db, require_admin
from app.main import app
from app.models.opportunity import Opportunity, OpportunitySkill
from app.models.profile import Profile, Skill
from app.schemas.ingestion import (
    BulkUploadImportRequest,
    JobPreviewItem,
    MatchedSkillItem,
)
from app.services.bulk_upload import (
    MAX_BULK_UPLOAD_BYTES,
    import_bulk_upload_jobs,
    normalize_bulk_row,
    parse_csv_rows,
    parse_json_rows,
    preview_bulk_upload,
    validate_upload_file_metadata,
)
from app.services.opportunity import expire_overdue_opportunities
from app.services.scheduled_refresh import (
    _refresh_lock,
    execute_scheduled_refresh,
    get_last_refresh_summary,
    is_refresh_running,
)


def make_test_profile(role: str = "admin") -> Profile:
    p = Profile()
    p.id = uuid4()
    p.email = f"{role}_{uuid4().hex[:6]}@example.com"
    p.role = role
    p.full_name = f"Test {role.capitalize()}"
    return p


# ============================================================================
# PART B: Deadline-Based Expiration Tests
# ============================================================================

@pytest.mark.anyio
async def test_expire_overdue_opportunities_published_past_deadline():
    """Verify Published opportunity with past deadline transitions to Expired."""
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.rowcount = 3
    mock_db.execute.return_value = mock_result
    mock_db.commit = AsyncMock()

    past_time = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    count = await expire_overdue_opportunities(mock_db, now=past_time)

    assert count == 3
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_called_once()


@pytest.mark.anyio
async def test_expire_overdue_opportunities_idempotent():
    """Verify repeated calls transition zero additional rows and are idempotent."""
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.rowcount = 0  # No matching rows on second call
    mock_db.execute.return_value = mock_result

    count = await expire_overdue_opportunities(mock_db)
    assert count == 0
    mock_db.commit.assert_not_called()


@pytest.mark.anyio
async def test_expire_overdue_opportunities_timezone_naive_coercion():
    """Verify timezone-naive datetime is safely converted to UTC-aware without errors."""
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.rowcount = 1
    mock_db.execute.return_value = mock_result

    naive_now = datetime(2026, 10, 15, 10, 0, 0)  # No tzinfo
    count = await expire_overdue_opportunities(mock_db, now=naive_now)
    assert count == 1


# ============================================================================
# PART C: Admin Bulk Upload (CSV & JSON) Tests
# ============================================================================

def test_validate_upload_file_metadata_bounds():
    """Verify file size bounds and extension whitelist."""
    # Oversized file
    big_bytes = b"x" * (MAX_BULK_UPLOAD_BYTES + 1)
    with pytest.raises(Exception) as exc:
        validate_upload_file_metadata("large.csv", big_bytes)
    assert "exceeds maximum allowed size" in str(exc.value.detail)

    # Invalid extension
    with pytest.raises(Exception) as exc:
        validate_upload_file_metadata("malware.exe", b"test")
    assert "Unsupported file format" in str(exc.value.detail)

    # Valid extensions
    assert validate_upload_file_metadata("jobs.csv", b"123") == ".csv"
    assert validate_upload_file_metadata("data.json", b"{}") == ".json"


def test_parse_csv_rows_clean():
    """Verify CSV header trimming and row dictionary parsing."""
    csv_text = """Title , Company Name , Opportunity Type , Application URL
Python Intern , Acme Corp , Internship , https://acme.com/apply
Frontend Dev , Beta LLC , Full-Time , https://beta.com/jobs
"""
    rows = parse_csv_rows(csv_text)
    assert len(rows) == 2
    assert rows[0]["title"] == "Python Intern"
    assert rows[0]["company name"] == "Acme Corp"
    assert rows[1]["title"] == "Frontend Dev"


def test_parse_json_rows_array_and_wrapped():
    """Verify JSON parsing for direct arrays and wrapped object formats."""
    json_direct = '[{"title": "Dev", "company_name": "Acme"}]'
    assert len(parse_json_rows(json_direct)) == 1

    json_wrapped = '{"jobs": [{"title": "Dev", "company_name": "Acme"}]}'
    assert len(parse_json_rows(json_wrapped)) == 1

    # Malformed JSON
    with pytest.raises(Exception):
        parse_json_rows("not valid json")


def test_normalize_bulk_row_sanitization_and_url_security():
    """Verify HTML stripping, URL scheme safety, and canonical skill matching."""
    skill_uuid = uuid4()
    skills_map = {"python": skill_uuid}

    row = {
        "title": "<script>alert('xss')</script>Backend Engineer",
        "company_name": "<b>Acme Software</b>",
        "opportunity_type": "Full-Time",
        "application_url": "javascript:stealToken()",  # Insecure URL
        "skills": "Python, GoLang",
        "deadline": "2026-12-31T23:59:59Z",
        "stipend_min": "1500",
        "stipend_max": "2000",
    }

    item = normalize_bulk_row(
        row=row,
        row_index=1,
        existing_external_ids=set(),
        existing_urls=set(),
        existing_signatures=set(),
        skills_map=skills_map,
    )

    # HTML stripped
    assert item.title == "Backend Engineer"
    assert item.company_name == "Acme Software"
    assert "<script>" not in item.title
    assert "<b>" not in item.company_name

    # Insecure URL rejected
    assert any("Invalid application URL scheme" in err for err in item.errors)

    # Canonical skill mapped
    assert len(item.matched_skills) == 1
    assert item.matched_skills[0].id == skill_uuid
    assert "GoLang" in item.unmapped_skills

    # Numeric fields parsed
    assert item.stipend_min == 1500
    assert item.stipend_max == 2000


def test_normalize_bulk_row_classification_conflict():
    """Verify conflict warning when title contains 'intern' but type is Full-Time."""
    item = normalize_bulk_row(
        row={
            "title": "Machine Learning Intern",
            "company_name": "AI Corp",
            "opportunity_type": "Full-Time",
        },
        row_index=1,
        existing_external_ids=set(),
        existing_urls=set(),
        existing_signatures=set(),
        skills_map={},
    )
    assert any("Classification conflict" in w for w in item.warnings)


def test_normalize_bulk_row_cross_source_duplicate_detection():
    """Verify deduplication detects existing external ID, URL, or title::company signature."""
    existing_ext = {"bulk-dup-01"}
    existing_url = {"https://dup.com/apply"}
    existing_sig = {"test engineer::acme corp"}

    item1 = normalize_bulk_row(
        row={"title": "New Title", "company_name": "New Corp", "external_id": "bulk-dup-01"},
        row_index=1,
        existing_external_ids=existing_ext,
        existing_urls=set(),
        existing_signatures=set(),
        skills_map={},
    )
    assert item1.is_duplicate is True

    item2 = normalize_bulk_row(
        row={"title": "Other", "company_name": "Other", "application_url": "https://dup.com/apply"},
        row_index=2,
        existing_external_ids=set(),
        existing_urls=existing_url,
        existing_signatures=set(),
        skills_map={},
    )
    assert item2.is_duplicate is True

    item3 = normalize_bulk_row(
        row={"title": "Test Engineer", "company_name": "Acme Corp"},
        row_index=3,
        existing_external_ids=set(),
        existing_urls=set(),
        existing_signatures=existing_sig,
        skills_map={},
    )
    assert item3.is_duplicate is True


@pytest.mark.anyio
async def test_import_bulk_upload_jobs_isolated_savepoints():
    """Verify savepoints isolate duplicate IntegrityError while importing valid items."""
    admin_id = uuid4()
    item1 = JobPreviewItem(
        job_id="bulk-ok-1",
        title="Valid Job 1",
        company_name="Acme",
        opportunity_type="Internship",
        work_model="Remote",
    )
    item2 = JobPreviewItem(
        job_id="bulk-dup-2",
        title="Duplicate Job 2",
        company_name="Beta",
        opportunity_type="Internship",
        work_model="Remote",
    )

    mock_db = AsyncMock()
    # 1. Existing external IDs -> empty
    dup_res = MagicMock()
    dup_res.scalars.return_value.all.return_value = []
    # 2. Existing skills -> empty
    skills_res = MagicMock()
    skills_res.scalars.return_value.all.return_value = []
    mock_db.execute.side_effect = [dup_res, skills_res]

    # First flush succeeds, second flush raises IntegrityError
    mock_db.flush.side_effect = [None, IntegrityError("stmt", {}, Exception("uix_opportunity_source_external_id"))]
    mock_db.add = MagicMock()
    mock_db.begin_nested = MagicMock(return_value=AsyncMock())
    mock_db.commit = AsyncMock()

    resp = await import_bulk_upload_jobs(
        db=mock_db,
        selected_job_ids=["bulk-ok-1", "bulk-dup-2"],
        jobs=[item1, item2],
        admin_profile_id=admin_id,
    )

    assert resp.inserted_count == 1
    assert resp.duplicate_count == 1
    assert resp.details[0].status == "imported"
    assert resp.details[1].status == "duplicate"


# ============================================================================
# PART A: Scheduled Refresh Orchestrator Tests
# ============================================================================

@pytest.mark.anyio
async def test_scheduled_refresh_disabled_returns_skipped():
    """Verify refresh without force flag exits immediately with status='skipped' when disabled."""
    mock_db = AsyncMock()
    with patch.object(settings, "scheduled_refresh_enabled", False):
        summary = await execute_scheduled_refresh(mock_db, force=False)
        assert summary.status == "skipped"


@pytest.mark.anyio
async def test_scheduled_refresh_concurrency_lock():
    """Verify that when a refresh is running, concurrent runs return already_running."""
    mock_db = AsyncMock()
    with patch("app.services.scheduled_refresh._is_refresh_running", True):
        summary = await execute_scheduled_refresh(mock_db, force=True)
        assert summary.status == "already_running"


@pytest.mark.anyio
async def test_scheduled_refresh_safe_updates_preserve_admin_fields():
    """Verify scheduled refresh updates deadline and URL but preserves status and classifications."""
    mock_db = AsyncMock()

    # Mock active skills query
    skills_res = MagicMock()
    skills_res.scalars.return_value.all.return_value = []
    mock_db.execute.side_effect = [skills_res]

    # Existing published opportunity
    existing_opp = Opportunity(
        title="Admin Curated Title",
        company_name="Acme Corp",
        opportunity_type="Internship",
        status="Published",  # Admin published! Must NOT revert to Draft
        deadline=datetime(2026, 6, 1, tzinfo=timezone.utc),
        application_url="https://acme.com/apply-v1",
        source_name="RSS",
        external_id="rss-job-123",
    )

    # Mock finding this existing opportunity in DB
    existing_opp_res = MagicMock()
    existing_opp_res.scalars.return_value.first.return_value = existing_opp

    # We add existing_opp_res to side_effect after skills query
    mock_db.execute.side_effect = [skills_res, existing_opp_res]
    mock_db.commit = AsyncMock()

    # Mock RSS feed fetch returning updated deadline & URL
    sample_xml = """<?xml version="1.0"?>
    <rss version="2.0">
      <channel>
        <title>Jobs</title>
        <item>
          <title>Provider Raw Title</title>
          <guid>rss-job-123</guid>
          <link>https://acme.com/apply-v2</link>
          <pubDate>Mon, 15 Jun 2026 12:00:00 GMT</pubDate>
          <description>Proficient in Python</description>
        </item>
      </channel>
    </rss>"""

    with (
        patch.object(settings, "scheduled_refresh_rss_enabled", True),
        patch.object(settings, "scheduled_refresh_jsearch_enabled", False),
        patch.object(settings, "scheduled_refresh_auto_expire", False),
        patch.object(settings, "scheduled_refresh_rss_feed_urls", "https://example.com/feed.xml"),
        patch("app.services.scheduled_refresh.validate_feed_url", return_value="https://example.com/feed.xml"),
        patch("app.services.scheduled_refresh.fetch_feed_content", AsyncMock(return_value=sample_xml)),
    ):
        summary = await execute_scheduled_refresh(mock_db, force=True)

        assert summary.status == "success"
        assert summary.total_updated == 1
        # Preserved status and admin title!
        assert existing_opp.status == "Published"
        assert existing_opp.title == "Admin Curated Title"
        # Updated allowed fields
        assert existing_opp.application_url == "https://acme.com/apply-v2"


@pytest.mark.anyio
async def test_scheduled_refresh_jsearch_quota_and_error_isolation():
    """Verify JSearch error does not crash the refresh and RSS feed proceeds safely."""
    mock_db = AsyncMock()

    # Active skills query
    skills_res = MagicMock()
    skills_res.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = skills_res
    mock_db.commit = AsyncMock()

    # Mock RSS feed
    sample_rss = """<?xml version="1.0"?>
    <rss version="2.0">
      <channel>
        <title>Jobs</title>
        <item>
          <title>DevOps Engineer</title>
          <guid>rss-devops-01</guid>
          <link>https://example.com/devops</link>
          <description>Kubernetes</description>
        </item>
      </channel>
    </rss>"""

    # Existing opp query returns None (new item)
    new_opp_res = MagicMock()
    new_opp_res.scalars.return_value.first.return_value = None
    mock_db.execute.side_effect = [skills_res, new_opp_res]
    mock_db.begin_nested = MagicMock(return_value=AsyncMock())
    mock_db.add = MagicMock()

    with (
        patch.object(settings, "scheduled_refresh_rss_enabled", True),
        patch.object(settings, "scheduled_refresh_jsearch_enabled", True),
        patch.object(settings, "jsearch_api_key", "valid-key"),
        patch.object(settings, "scheduled_refresh_auto_expire", True),
        patch("app.services.scheduled_refresh.validate_feed_url", return_value="https://example.com/feed.xml"),
        patch("app.services.scheduled_refresh.fetch_feed_content", AsyncMock(return_value=sample_rss)),
        # JSearch raises 429 rate limit or timeout error
        patch("app.services.scheduled_refresh.fetch_jsearch_jobs", AsyncMock(side_effect=Exception("RapidAPI 429 Rate Limit"))),
        patch("app.services.scheduled_refresh.expire_overdue_opportunities", AsyncMock(return_value=2)),
    ):
        summary = await execute_scheduled_refresh(mock_db, force=True)

        # RSS inserted 1 item despite JSearch 429 error
        assert summary.total_inserted == 1
        assert summary.total_expired == 2
        assert summary.status == "partial_failure"
        assert any("429 Rate Limit" in err for err in summary.errors)


# ============================================================================
# API Endpoints & Authorization Tests
# ============================================================================

@pytest.mark.anyio
async def test_endpoints_unauthenticated():
    """Verify bulk upload and refresh endpoints reject unauthenticated requests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res1 = await client.post("/api/v1/admin/ingestion/bulk-upload/preview")
        assert res1.status_code == 401

        res2 = await client.get("/api/v1/admin/ingestion/refresh/status")
        assert res2.status_code == 401

        res3 = await client.post("/api/v1/admin/ingestion/refresh/trigger")
        assert res3.status_code == 401


@pytest.mark.anyio
async def test_endpoints_forbidden_for_students():
    """Verify bulk upload and refresh endpoints return 403 Forbidden for non-admin students."""
    student = make_test_profile("student")
    app.dependency_overrides[require_admin] = lambda: (_ for _ in ()).throw(
        pytest.importorskip("fastapi").HTTPException(status_code=403, detail="Forbidden")
    )

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res1 = await client.get("/api/v1/admin/ingestion/refresh/status")
            assert res1.status_code == 403

            res2 = await client.post("/api/v1/admin/ingestion/refresh/trigger")
            assert res2.status_code == 403
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_admin_bulk_upload_preview_endpoint_success():
    """Verify admin bulk upload preview endpoint parses uploaded CSV."""
    admin = make_test_profile("admin")
    app.dependency_overrides[require_admin] = lambda: admin

    mock_db = AsyncMock()
    # Mock deduplication queries
    res_ext = MagicMock()
    res_ext.scalars.return_value.all.return_value = []
    res_url = MagicMock()
    res_url.scalars.return_value.all.return_value = []
    res_sig = MagicMock()
    res_sig.all.return_value = []
    res_skills = MagicMock()
    res_skills.all.return_value = [(uuid4(), "python")]

    mock_db.execute.side_effect = [res_ext, res_url, res_sig, res_skills]
    app.dependency_overrides[get_db] = lambda: mock_db

    csv_data = b"title,company_name,application_url\nBackend Engineer,Acme,https://acme.com/apply\n"

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post(
                "/api/v1/admin/ingestion/bulk-upload/preview",
                files={"file": ("upload.csv", csv_data, "text/csv")},
            )
            assert res.status_code == 200
            data = res.json()
            assert data["total_rows"] == 1
            assert data["valid_count"] == 1
            assert data["jobs"][0]["title"] == "Backend Engineer"
            assert data["jobs"][0]["opportunity_type"] == "Internship"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_admin_refresh_status_and_trigger_endpoints():
    """Verify admin refresh status and trigger endpoints return valid payloads."""
    admin = make_test_profile("admin")
    app.dependency_overrides[require_admin] = lambda: admin
    mock_db = AsyncMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Status endpoint
            res = await client.get("/api/v1/admin/ingestion/refresh/status")
            assert res.status_code == 200
            data = res.json()
            assert "enabled" in data
            assert "last_summary" in data

            # 2. Trigger endpoint (mock execute_scheduled_refresh)
            with patch(
                "app.routers.admin_ingestion.execute_scheduled_refresh",
                AsyncMock(return_value=get_last_refresh_summary()),
            ):
                res_trig = await client.post("/api/v1/admin/ingestion/refresh/trigger?force=true")
                assert res_trig.status_code == 200
                assert res_trig.json()["message"] == "Refresh execution completed."
    finally:
        app.dependency_overrides.clear()
