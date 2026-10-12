from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from httpx import (
    ASGITransport,
    AsyncClient,
    ConnectTimeout,
    ReadTimeout,
    Response,
)

from app.core.config import settings
from app.core.dependencies import get_db, require_admin
from app.main import app
from app.models.profile import Profile, Skill
from app.schemas.ingestion import JobPreviewItem, MatchedSkillItem
from app.services.jsearch import (
    fetch_jsearch_jobs,
    normalize_job_record,
    parse_jsearch_payload,
    sanitize_external_id,
    validate_url,
)

# ============================================================================
# 1. Unit Tests: Response Parsing
# ============================================================================

def test_parse_jsearch_payload_observed_format():
    """Observed format: status OK, parameters object, data.jobs array with cursor."""
    raw = {
        "status": "OK",
        "request_id": "req-123",
        "parameters": {"query": "python intern", "country": "in"},
        "data": {
            "jobs": [
                {"job_id": "j1", "job_title": "Backend Intern", "employer_name": "Tech Corp"},
                {"job_id": "j2", "job_title": "Data Intern", "employer_name": "Data Corp"},
            ],
            "cursor": "cursor_page_2",
        },
    }
    jobs, cursor, params = parse_jsearch_payload(raw)
    assert len(jobs) == 2
    assert jobs[0]["job_id"] == "j1"
    assert cursor == "cursor_page_2"
    assert params["query"] == "python intern"


def test_parse_jsearch_payload_array_format():
    """Alternative format: data is a list directly."""
    raw = {
        "status": "OK",
        "parameters": {},
        "data": [
            {"job_id": "j10", "job_title": "Software Engineer", "employer_name": "Global Corp"}
        ],
        "cursor": "c_direct",
    }
    jobs, cursor, _params = parse_jsearch_payload(raw)
    assert len(jobs) == 1
    assert jobs[0]["job_id"] == "j10"
    assert cursor == "c_direct"


def test_parse_jsearch_payload_empty_and_malformed():
    """Handles empty or unexpected types gracefully."""
    jobs, cursor, params = parse_jsearch_payload({})
    assert jobs == []
    assert cursor is None
    assert params == {}

    jobs, cursor, params = parse_jsearch_payload("invalid string")
    assert jobs == []

    jobs, cursor, params = parse_jsearch_payload(None)
    assert jobs == []


def test_parse_jsearch_payload_error_status():
    """Raises HTTPException on provider ERROR status."""
    raw = {"status": "ERROR", "error": "Invalid country parameter"}
    with pytest.raises(HTTPException) as exc_info:
        parse_jsearch_payload(raw)
    assert exc_info.value.status_code == 502
    assert "Invalid country parameter" in exc_info.value.detail


# ============================================================================
# 2. Unit Tests: Normalization, Conflict Detection, and Validation
# ============================================================================

def test_normalize_classification_conflict():
    """
    When title includes 'Intern' but provider reports FULLTIME,
    flag classification conflict and mark review_required.
    """
    raw_job = {
        "job_id": "job_conflict_1",
        "job_title": "Software Engineer Intern",
        "employer_name": "Acme Inc",
        "job_employment_types": ["FULLTIME"],
        "job_employment_type": "FULLTIME",
        "job_apply_link": "https://example.com/apply",
    }
    item = normalize_job_record(raw_job, existing_external_ids=set(), skills_map={})

    assert item.job_id == "job_conflict_1"
    assert item.classification_conflict is True
    assert item.opportunity_type == "Internship"
    assert item.review_required is True
    assert any("Classification conflict" in w for w in item.warnings)


def test_normalize_standard_internship():
    """Title without conflict where provider says INTERN."""
    raw_job = {
        "job_id": "job_intern_1",
        "job_title": "Frontend Developer",
        "employer_name": "Acme Inc",
        "job_employment_types": ["INTERN"],
        "job_apply_link": "https://example.com/apply",
    }
    item = normalize_job_record(raw_job, existing_external_ids=set(), skills_map={})

    assert item.classification_conflict is False
    assert item.opportunity_type == "Internship"


def test_normalize_work_models():
    """Validates work_model determination: Remote, Hybrid, On-site."""
    # Remote
    r1 = normalize_job_record(
        {"job_id": "1", "job_title": "Dev", "employer_name": "A", "job_is_remote": True},
        set(), {},
    )
    assert r1.work_model == "Remote"

    # Hybrid
    r2 = normalize_job_record(
        {"job_id": "2", "job_title": "Dev (Hybrid)", "employer_name": "A", "job_is_remote": False},
        set(), {},
    )
    assert r2.work_model == "Hybrid"

    # On-site
    r3 = normalize_job_record(
        {"job_id": "3", "job_title": "Dev in Office", "employer_name": "A", "job_is_remote": False},
        set(), {},
    )
    assert r3.work_model == "On-site"


def test_normalize_url_validation():
    """Invalid or unsafe URLs are discarded and flagged."""
    assert validate_url("https://example.com/jobs/1") == "https://example.com/jobs/1"
    assert validate_url("http://example.com") == "http://example.com"
    assert validate_url("javascript:alert(1)") is None
    assert validate_url("file:///etc/passwd") is None
    assert validate_url("not-a-url") is None
    assert validate_url(None) is None

    raw_job = {
        "job_id": "url_test",
        "job_title": "Engineer",
        "employer_name": "Company",
        "job_apply_link": "unsafe://bad-link",
    }
    item = normalize_job_record(raw_job, set(), {})
    assert item.application_url is None
    assert any("Missing or invalid application URL" in w for w in item.warnings)


def test_normalize_salary_validation():
    """Validates salary range correction, negative rejection, and monthly stipend mapping."""
    # Inverted range corrected
    raw_job = {
        "job_id": "sal_1",
        "job_title": "Engineer",
        "employer_name": "Company",
        "job_min_salary": 900000,
        "job_max_salary": 500000,
        "job_salary_currency": "INR",
        "job_salary_period": "YEAR",
    }
    item = normalize_job_record(raw_job, set(), {})
    assert item.salary_min == 500000
    assert item.salary_max == 900000
    assert item.currency == "INR"

    # Monthly stipend for internship
    raw_job_intern = {
        "job_id": "sal_2",
        "job_title": "Engineering Intern",
        "employer_name": "Company",
        "job_min_salary": 25000,
        "job_max_salary": 30000,
        "job_salary_period": "MONTH",
    }
    item2 = normalize_job_record(raw_job_intern, set(), {})
    assert item2.stipend_min == 25000
    assert item2.stipend_max == 30000


def test_normalize_canonical_skill_catalog_matching():
    """
    Matches existing canonical skills by name/alias,
    keeps unmatched skills as unmapped suggestions,
    never creates new Skill database records automatically.
    """
    skill_py_id = uuid4()
    mock_skill_py = Skill(id=skill_py_id, name="Python", normalized_name="python")

    skills_map = {
        "python": mock_skill_py,
    }

    raw_job = {
        "job_id": "skill_test",
        "job_title": "Python Developer Intern",
        "employer_name": "Tech Corp",
        "job_required_skills": ["Python", "Rust", "FastAPI"],
    }

    item = normalize_job_record(raw_job, set(), skills_map)
    matched_names = [m.name for m in item.matched_skills]
    assert "Python" in matched_names
    assert item.matched_skills[0].id == skill_py_id

    # Unmapped skills suggestions
    assert "Rust" in item.unmapped_skills
    assert "FastAPI" in item.unmapped_skills


def test_normalize_duplicate_detection():
    """Existing external_id in database marks is_duplicate=True."""
    raw_job = {
        "job_id": "existing_job_1",
        "job_title": "Dev",
        "employer_name": "Comp",
    }
    item = normalize_job_record(raw_job, existing_external_ids={"existing_job_1"}, skills_map={})
    assert item.is_duplicate is True
    assert any("already been imported" in w for w in item.warnings)


def test_sanitize_external_id():
    """Sanitizes external_id to fit within VARCHAR(255) deterministically without collisions."""
    assert sanitize_external_id("short_job_123") == "short_job_123"
    assert sanitize_external_id("") == ""
    assert sanitize_external_id(None) == ""

    # Real JSearch v2 IDs often exceed 300 characters
    long_id = "jsearch_v2_" + ("abc123xyz_" * 35)
    assert len(long_id) > 300
    sanitized = sanitize_external_id(long_id)
    assert len(sanitized) <= 255
    assert len(sanitized) == 233
    assert sanitized.startswith(long_id[:200])

    # Determinism
    assert sanitize_external_id(long_id) == sanitize_external_id(long_id)
    # Different inputs produce different hashes
    assert sanitize_external_id(long_id) != sanitize_external_id(long_id + "_different")


# ============================================================================
# 3. Provider Fetching & Error Handling Tests
# ============================================================================

@pytest.mark.anyio
async def test_fetch_missing_api_key():
    """Raises HTTP 400 when JSEARCH_API_KEY is not configured."""
    with patch.object(settings, "jsearch_api_key", ""):
        with pytest.raises(HTTPException) as exc_info:
            await fetch_jsearch_jobs("python developer")
        assert exc_info.value.status_code == 400
        assert "JSearch API key is not configured" in exc_info.value.detail


@pytest.mark.anyio
async def test_fetch_rate_limit_429():
    """Handles HTTP 429 rate limit with actionable error."""
    mock_response = Response(status_code=429, text="Rate limit exceeded")

    with (
        patch.object(settings, "jsearch_api_key", "test-key"),
        patch("httpx.AsyncClient.get", AsyncMock(return_value=mock_response)),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await fetch_jsearch_jobs("python")
        assert exc_info.value.status_code == 429
        assert "rate limit or monthly credit allowance exceeded" in exc_info.value.detail

@pytest.mark.anyio
async def test_fetch_read_timeout_504():
    """Handles HTTPX ReadTimeout gracefully with 504 Gateway Timeout."""
    mock_get = AsyncMock(side_effect=ReadTimeout("Read timed out after 30 seconds"))

    with (
        patch.object(settings, "jsearch_api_key", "test-key"),
        patch("httpx.AsyncClient.get", mock_get),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await fetch_jsearch_jobs("python")
        assert exc_info.value.status_code == 504
        assert "timed out" in exc_info.value.detail
        assert "waiting for response data" in exc_info.value.detail


@pytest.mark.anyio
async def test_fetch_connect_timeout_504():
    """Handles HTTPX ConnectTimeout gracefully with 504 Gateway Timeout."""
    mock_get = AsyncMock(side_effect=ConnectTimeout("Connection timed out"))

    with (
        patch.object(settings, "jsearch_api_key", "test-key"),
        patch("httpx.AsyncClient.get", mock_get),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await fetch_jsearch_jobs("python")
        assert exc_info.value.status_code == 504
        assert "connection timed out" in exc_info.value.detail
        assert "unreachable" in exc_info.value.detail


@pytest.mark.anyio
async def test_fetch_auth_error_403():
    """Handles HTTP 403 provider authentication error."""
    mock_response = Response(status_code=403, text="Forbidden")

    with (
        patch.object(settings, "jsearch_api_key", "invalid-key"),
        patch("httpx.AsyncClient.get", AsyncMock(return_value=mock_response)),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await fetch_jsearch_jobs("python")
        assert exc_info.value.status_code == 502
        assert "authentication failed" in exc_info.value.detail


@pytest.mark.anyio
async def test_fetch_provider_endpoint_not_found_404():
    """Handles HTTP 404 RapidAPI gateway response with escaped slash pattern."""
    mock_response = Response(
        status_code=404,
        text='{"message":"Endpoint \'\\/search\' does not exist"}',
    )

    with (
        patch.object(settings, "jsearch_api_key", "test-key"),
        patch("httpx.AsyncClient.get", AsyncMock(return_value=mock_response)),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await fetch_jsearch_jobs("python")
        assert exc_info.value.status_code == 502
        assert "404" in exc_info.value.detail
        assert "Endpoint" in exc_info.value.detail


@pytest.mark.anyio
async def test_fetch_exact_endpoint_url_and_headers():
    """
    Asserts exact RapidAPI JSearch URL construction:
    - Base URL: https://jsearch.p.rapidapi.com
    - Path: strictly /search-v2
    - Headers: X-RapidAPI-Key and X-RapidAPI-Host
    - Response: parses observed data.jobs structure correctly
    """
    mock_payload = {
        "status": "OK",
        "data": {
            "jobs": [
                {"job_id": "job_v2_1", "job_title": "React Intern", "employer_name": "Tech Corp"}
            ]
        },
    }
    mock_response = Response(
        status_code=200,
        json=mock_payload,
    )
    mock_get = AsyncMock(return_value=mock_response)

    with (
        patch.object(settings, "jsearch_api_key", "secret-test-key"),
        patch.object(settings, "jsearch_api_host", "jsearch.p.rapidapi.com"),
        patch.object(settings, "jsearch_api_base_url", "https://jsearch.p.rapidapi.com"),
        patch("httpx.AsyncClient.get", mock_get),
    ):
        result = await fetch_jsearch_jobs(
            query="react intern in delhi",
            country="in",
            date_posted="week",
            employment_types="INTERN",
            remote_jobs_only=True,
            page=1,
            num_pages=1,
        )

        assert mock_get.called
        called_url, = mock_get.call_args[0]
        called_headers = mock_get.call_args[1]["headers"]
        called_params = mock_get.call_args[1]["params"]

        # Exact URL assertions matching RapidAPI Playground
        assert str(called_url) == "https://jsearch.p.rapidapi.com/search-v2"
        assert str(called_url).endswith("/search-v2")
        assert repr(str(called_url)) == "'https://jsearch.p.rapidapi.com/search-v2'"
        assert not any(ord(c) < 32 or ord(c) == 127 for c in str(called_url))

        from urllib.parse import urlparse
        p = urlparse(str(called_url))
        assert p.scheme == "https"
        assert p.netloc == "jsearch.p.rapidapi.com"
        assert p.path == "/search-v2"

        # Headers assertions
        assert called_headers["X-RapidAPI-Host"] == "jsearch.p.rapidapi.com"
        assert called_headers["X-RapidAPI-Key"] == "secret-test-key"

        # Parameters assertions
        assert called_params["query"] == "react intern in delhi"
        assert called_params["country"] == "in"
        assert called_params["date_posted"] == "week"
        assert called_params["employment_types"] == "INTERN"
        assert called_params["remote_jobs_only"] == "true"
        assert called_params["page"] == "1"
        assert called_params["num_pages"] == "1"

        # Data.jobs payload parsing verification
        jobs, _cursor, _params = parse_jsearch_payload(result)
        assert len(jobs) == 1
        assert jobs[0]["job_id"] == "job_v2_1"
        assert jobs[0]["job_title"] == "React Intern"


@pytest.mark.anyio
async def test_fetch_url_resilience_to_malformed_base_urls():
    """
    Ensures URL construction eliminates trailing slashes or malformed prefixes,
    always guaranteeing canonical endpoint https://jsearch.p.rapidapi.com/search-v2.
    """
    mock_response = Response(
        status_code=200,
        json={"status": "OK", "data": {"jobs": []}},
    )

    malformed_variations = [
        ("jsearch.p.rapidapi.com", "https://jsearch.p.rapidapi.com/v2"),
        ("jsearch.p.rapidapi.com", "https://jsearch.p.rapidapi.com/search"),
        ("https://jsearch.p.rapidapi.com/", "https://jsearch.p.rapidapi.com/"),
        ("jsearch.p.rapidapi.com", "http://jsearch.p.rapidapi.com"),
    ]

    for host_val, base_val in malformed_variations:
        mock_get = AsyncMock(return_value=mock_response)
        with (
            patch.object(settings, "jsearch_api_key", "test-key"),
            patch.object(settings, "jsearch_api_host", host_val),
            patch.object(settings, "jsearch_api_base_url", base_val),
            patch("httpx.AsyncClient.get", mock_get),
        ):
            await fetch_jsearch_jobs("python")
            called_url, = mock_get.call_args[0]
            assert str(called_url) == "https://jsearch.p.rapidapi.com/search-v2"
            assert str(called_url).endswith("/search-v2")
            assert not any(ord(c) < 32 or ord(c) == 127 for c in str(called_url))


@pytest.mark.anyio
async def test_fetch_url_rejects_control_characters_and_invalid_endpoints():
    """
    Ensures outgoing URL validation catches control characters (e.g. \\v)
    or malformed endpoints before dispatching requests.
    """
    mock_get = AsyncMock()

    # Attempting to supply base URL containing vertical tab or control character
    with (
        patch.object(settings, "jsearch_api_key", "test-key"),
        patch.object(
            type(settings),
            "clean_jsearch_base_url",
            new_callable=PropertyMock,
            return_value="https://custom.api.internal/\vsearch",
        ),
        patch("httpx.AsyncClient.get", mock_get),
    ):
        with pytest.raises(ValueError, match="JSearch endpoint path must strictly be|Control characters"):
            await fetch_jsearch_jobs("python")
        assert not mock_get.called


# ============================================================================
# 4. API Endpoints Authorization & Mocked Ingestion Tests
# ============================================================================

@pytest.mark.anyio
async def test_endpoints_unauthenticated():
    """Unauthenticated requests are rejected with 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/v1/admin/ingestion/jsearch/preview", json={"query": "python"})
        assert res.status_code == 401

        res_import = await client.post(
            "/api/v1/admin/ingestion/jsearch/import",
            json={"selected_job_ids": ["1"], "jobs": []},
        )
        assert res_import.status_code == 401


@pytest.mark.anyio
async def test_endpoints_forbidden_for_students():
    """Student profiles receive 403 Forbidden on ingestion endpoints."""
    app.dependency_overrides[require_admin] = lambda: (_ for _ in ()).throw(
        HTTPException(status_code=403, detail="Not enough permissions")
    )

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post(
                "/api/v1/admin/ingestion/jsearch/preview",
                json={"query": "python"},
                headers={"Authorization": "Bearer mock-token"},
            )
            assert res.status_code == 403

            res_import = await client.post(
                "/api/v1/admin/ingestion/jsearch/import",
                json={"selected_job_ids": ["1"], "jobs": []},
                headers={"Authorization": "Bearer mock-token"},
            )
            assert res_import.status_code == 403
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_admin_preview_endpoint_success():
    """Admin preview returns parsed and normalized preview records with summary."""
    admin_profile = Profile(id=uuid4(), user_id=uuid4(), full_name="Admin", role="admin")
    app.dependency_overrides[require_admin] = lambda: admin_profile

    # Mock DB dependency
    mock_db = AsyncMock()
    mock_db_res = MagicMock()
    mock_db_res.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_db_res
    app.dependency_overrides[get_db] = lambda: mock_db

    mock_jsearch_response = {
        "status": "OK",
        "parameters": {"query": "python intern in bangalore"},
        "data": {
            "jobs": [
                {
                    "job_id": "mock_jsearch_1",
                    "job_title": "Python Intern",
                    "employer_name": "Infosys",
                    "job_employment_types": ["INTERN"],
                    "job_city": "Bengaluru",
                    "job_country": "IN",
                    "job_apply_link": "https://infosys.com/careers/1",
                    "job_required_skills": ["Python", "Django"],
                    "job_is_remote": False,
                },
                {
                    "job_id": "mock_jsearch_2",
                    "job_title": "React Developer Intern",
                    "employer_name": "Wipro",
                    "job_employment_types": ["FULLTIME"],  # conflict!
                    "job_city": "Pune",
                    "job_country": "IN",
                    "job_apply_link": "https://wipro.com/careers/2",
                    "job_is_remote": True,
                },
            ],
            "cursor": "cursor_next",
        },
    }

    transport = ASGITransport(app=app)
    try:
        with patch("app.services.jsearch.fetch_jsearch_jobs", AsyncMock(return_value=mock_jsearch_response)):
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                res = await client.post(
                    "/api/v1/admin/ingestion/jsearch/preview",
                    json={"query": "python intern in bangalore", "country": "in"},
                    headers={"Authorization": "Bearer mock-token"},
                )
                assert res.status_code == 200
                data = res.json()

                assert len(data["jobs"]) == 2
                assert data["total_found"] == 2
                assert data["cursor"] == "cursor_next"

                j1 = data["jobs"][0]
                assert j1["job_id"] == "mock_jsearch_1"
                assert j1["opportunity_type"] == "Internship"
                assert j1["company_name"] == "Infosys"
                assert j1["work_model"] == "On-site"

                j2 = data["jobs"][1]
                assert j2["job_id"] == "mock_jsearch_2"
                assert j2["classification_conflict"] is True
                assert j2["opportunity_type"] == "Internship"
                assert j2["work_model"] == "Remote"
                assert j2["review_required"] is True

                assert data["summary"]["total_returned"] == 2
                assert data["summary"]["review_required_count"] >= 1
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_admin_import_endpoint_success():
    """Admin import saves selected jobs into Opportunity as Draft and connects canonical skills."""
    admin_id = uuid4()
    admin_profile = Profile(id=admin_id, user_id=uuid4(), full_name="Admin", role="admin")
    app.dependency_overrides[require_admin] = lambda: admin_profile

    skill_id = uuid4()
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.begin_nested = MagicMock(return_value=AsyncMock())

    # Configure mock responses for duplicates check and skill check
    dup_res = MagicMock()
    dup_res.scalars.return_value.all.return_value = []  # no existing duplicates

    skill_res = MagicMock()
    skill_res.scalars.return_value.all.return_value = [skill_id]

    mock_db.execute.side_effect = [dup_res, skill_res]
    app.dependency_overrides[get_db] = lambda: mock_db

    preview_item = JobPreviewItem(
        job_id="imp_1",
        title="Software Engineer Intern",
        company_name="Google",
        opportunity_type="Internship",
        work_model="Remote",
        locations=["Bengaluru, IN"],
        application_url="https://careers.google.com/jobs/1",
        matched_skills=[MatchedSkillItem(id=skill_id, name="Python")],
        unmapped_skills=["Bazel"],
        status="Draft",
    )

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            payload = {
                "selected_job_ids": ["imp_1"],
                "jobs": [preview_item.model_dump(mode="json")],
            }
            res = await client.post(
                "/api/v1/admin/ingestion/jsearch/import",
                json=payload,
                headers={"Authorization": "Bearer mock-token"},
            )
            assert res.status_code == 200
            data = res.json()

            assert data["inserted_count"] == 1
            assert data["duplicate_count"] == 0
            assert data["skipped_count"] == 0
            assert len(data["details"]) == 1
            assert data["details"][0]["status"] == "imported"

            # Verify Opportunity was added with status="Draft"
            added_opp = mock_db.add.call_args_list[0][0][0]
            assert added_opp.title == "Software Engineer Intern"
            assert added_opp.company_name == "Google"
            assert added_opp.status == "Draft"
            assert added_opp.source_name == "JSearch"
            assert added_opp.external_id == "imp_1"
            assert added_opp.created_by_profile_id == admin_id
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_admin_import_handles_duplicate_safely():
    """Repeated or already-imported jobs are recorded as duplicate and skipped safely."""
    admin_profile = Profile(id=uuid4(), user_id=uuid4(), full_name="Admin", role="admin")
    app.dependency_overrides[require_admin] = lambda: admin_profile

    mock_db = AsyncMock()
    dup_res = MagicMock()
    dup_res.scalars.return_value.all.return_value = ["imp_dup_1"]  # already in DB!
    mock_db.execute.return_value = dup_res
    app.dependency_overrides[get_db] = lambda: mock_db

    preview_item = JobPreviewItem(
        job_id="imp_dup_1",
        title="Frontend Intern",
        company_name="Microsoft",
        opportunity_type="Internship",
        work_model="Hybrid",
    )

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            payload = {
                "selected_job_ids": ["imp_dup_1"],
                "jobs": [preview_item.model_dump(mode="json")],
            }
            res = await client.post(
                "/api/v1/admin/ingestion/jsearch/import",
                json=payload,
                headers={"Authorization": "Bearer mock-token"},
            )
            assert res.status_code == 200
            data = res.json()

            assert data["inserted_count"] == 0
            assert data["duplicate_count"] == 1
            assert data["skipped_count"] == 0
            assert data["details"][0]["status"] == "duplicate"
            # mock_db.add was not called for the duplicate opportunity
            assert mock_db.add.call_count == 0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_admin_import_handles_oversized_external_id_and_urls():
    """
    Jobs with oversized base64 job_id (>300 chars) and long Google tracking URLs (>500 chars)
    are safely sanitized to database schema constraints and saved as Draft.
    """
    admin_id = uuid4()
    admin_profile = Profile(id=admin_id, user_id=uuid4(), full_name="Admin", role="admin")
    app.dependency_overrides[require_admin] = lambda: admin_profile

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.begin_nested = MagicMock(return_value=AsyncMock())

    dup_res = MagicMock()
    dup_res.scalars.return_value.all.return_value = []

    mock_db.execute.side_effect = [dup_res]
    app.dependency_overrides[get_db] = lambda: mock_db

    oversized_job_id = "jsearch_base64_" + ("x" * 320)
    oversized_url = "https://www.google.com/search?q=jobs&ibp=htiv2&sa=X&ved=2ahUKEwj" + ("y" * 600)
    oversized_company = "Tech Corp " + ("c" * 300)

    preview_item = JobPreviewItem(
        job_id=oversized_job_id,
        title="Oversized Job Engineer",
        company_name=oversized_company,
        opportunity_type="Internship",
        work_model="Remote",
        locations=["Global"],
        application_url=oversized_url,
        status="Draft",
    )

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            payload = {
                "selected_job_ids": [oversized_job_id],
                "jobs": [preview_item.model_dump(mode="json")],
            }
            res = await client.post(
                "/api/v1/admin/ingestion/jsearch/import",
                json=payload,
                headers={"Authorization": "Bearer mock-token"},
            )
            assert res.status_code == 200
            data = res.json()

            assert data["inserted_count"] == 1
            assert data["duplicate_count"] == 0
            assert data["skipped_count"] == 0

            # Verify sanitized database values
            added_opp = mock_db.add.call_args_list[0][0][0]
            assert len(added_opp.external_id) <= 255
            assert added_opp.external_id == sanitize_external_id(oversized_job_id)
            assert len(added_opp.company_name) <= 255
            assert len(added_opp.application_url) <= 500
            assert added_opp.status == "Draft"
    finally:
        app.dependency_overrides.clear()
