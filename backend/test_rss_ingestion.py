import os
import sys
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.dependencies import get_current_user, get_db, require_admin
from app.main import app
from app.models.opportunity import Opportunity, OpportunitySkill
from app.models.profile import Profile, Skill
from app.schemas.ingestion import JobPreviewItem, MatchedSkillItem
from app.services.rss import (
    APPROVED_RSS_PRESETS,
    clean_html_text,
    normalize_rss_item,
    parse_rss_datetime,
    parse_xml_feed,
    validate_feed_url,
)

# ============================================================================
# Sample XML Fixtures
# ============================================================================

SAMPLE_RSS_2_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>We Work Remotely - Programming Jobs</title>
    <link>https://weworkremotely.com</link>
    <description>The largest remote work community in the world.</description>
    <item>
      <title>Acme Corp: Backend Software Engineer</title>
      <link>https://weworkremotely.com/jobs/12345-backend-engineer</link>
      <guid>wwr-12345</guid>
      <description>&lt;p&gt;We are looking for a &lt;strong&gt;Backend Engineer&lt;/strong&gt; proficient in Python and PostgreSQL. Remote worldwide.&lt;/p&gt;</description>
      <pubDate>Mon, 12 Oct 2026 14:30:00 GMT</pubDate>
      <category>Full-Time</category>
      <category>Python</category>
    </item>
    <item>
      <title>Frontend Intern at TechNova</title>
      <link>https://weworkremotely.com/jobs/12346-frontend-intern</link>
      <guid>wwr-12346</guid>
      <description>&lt;p&gt;Internship opportunity for junior developers interested in React and TypeScript.&lt;/p&gt;</description>
      <pubDate>Sun, 11 Oct 2026 09:00:00 GMT</pubDate>
      <category>Internship</category>
      <category>React</category>
    </item>
    <item>
      <title>CloudScale: Cloud Support Intern</title>
      <link>https://weworkremotely.com/jobs/12347-cloud-intern</link>
      <guid>wwr-12347</guid>
      <description>Work on Docker and Kubernetes infrastructure. Full-time position.</description>
      <pubDate>Sat, 10 Oct 2026 10:00:00 GMT</pubDate>
      <category>Full-Time</category>
    </item>
  </channel>
</rss>
"""

SAMPLE_ATOM_1_XML = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>RemoteOK Jobs</title>
  <link href="https://remoteok.com"/>
  <updated>2026-10-12T12:00:00Z</updated>
  <entry>
    <title>DevOps Specialist</title>
    <link href="https://remoteok.com/l/98765"/>
    <id>remoteok-98765</id>
    <author>
      <name>GlobalNet</name>
    </author>
    <summary>Remote role focusing on Linux and AWS automation.</summary>
    <published>2026-10-12T11:00:00Z</published>
    <category term="DevOps"/>
    <category term="Remote"/>
  </entry>
</feed>
"""


# ============================================================================
# Unit Tests: Parsing and Sanitization
# ============================================================================

def test_clean_html_text():
    """Verify HTML tags are stripped and entities properly unescaped without external scraping libs."""
    raw = "<p>Hello &amp; welcome to &lt;b&gt;CareerPilot&lt;/b&gt;!&#39;s job board.</p>"
    cleaned = clean_html_text(raw)
    assert cleaned == "Hello & welcome to CareerPilot!'s job board."

    multiline = "<p>Line 1</p>\n\n<br/>\n\n<p>Line 2</p>"
    cleaned_multi = clean_html_text(multiline)
    assert "Line 1" in cleaned_multi
    assert "Line 2" in cleaned_multi


def test_parse_rss_2_xml():
    """Verify standard RSS 2.0 channel and items extraction."""
    meta, items = parse_xml_feed(SAMPLE_RSS_2_XML)
    assert meta["title"] == "We Work Remotely - Programming Jobs"
    assert meta["link"] == "https://weworkremotely.com"
    assert len(items) == 3

    item1 = items[0]
    assert item1["title"] == "Acme Corp: Backend Software Engineer"
    assert item1["link"] == "https://weworkremotely.com/jobs/12345-backend-engineer"
    assert item1["guid"] == "wwr-12345"
    assert "Python and PostgreSQL" in item1["description"]
    assert "Full-Time" in item1["categories"]
    assert "Python" in item1["categories"]


def test_parse_atom_1_xml():
    """Verify Atom 1.0 feed and entry extraction."""
    meta, items = parse_xml_feed(SAMPLE_ATOM_1_XML)
    assert meta["title"] == "RemoteOK Jobs"
    assert meta["link"] == "https://remoteok.com"
    assert len(items) == 1

    item1 = items[0]
    assert item1["title"] == "DevOps Specialist"
    assert item1["link"] == "https://remoteok.com/l/98765"
    assert item1["guid"] == "remoteok-98765"
    assert item1["author"] == "GlobalNet"
    assert "DevOps" in item1["categories"]


def test_parse_rss_datetime():
    """Verify RFC 2822 and ISO 8601 timestamps parse to timezone-aware UTC."""
    rfc_date = "Mon, 12 Oct 2026 14:30:00 GMT"
    dt = parse_rss_datetime(rfc_date)
    assert dt is not None
    assert dt.tzinfo is not None
    assert dt.year == 2026
    assert dt.month == 10
    assert dt.day == 12

    iso_date = "2026-10-12T11:00:00Z"
    dt_iso = parse_rss_datetime(iso_date)
    assert dt_iso is not None
    assert dt_iso.hour == 11


def test_ssrf_prohibited_hosts():
    """Verify SSRF validation rejects localhost, private subnets, and non-HTTP schemes."""
    # 1. Scheme checks
    with pytest.raises(Exception) as exc1:
        validate_feed_url("file:///etc/passwd")
    assert "scheme" in str(exc1.value).lower()

    # 2. Localhost strings
    with pytest.raises(Exception) as exc2:
        validate_feed_url("http://localhost:8000/feed.xml")
    assert "prohibited feed host" in str(exc2.value).lower()

    with pytest.raises(Exception) as exc3:
        validate_feed_url("http://127.0.0.1/rss")
    assert "prohibited feed host" in str(exc3.value).lower()

    # 3. Private IP resolution
    with patch("socket.getaddrinfo") as mock_dns:
        mock_dns.return_value = [(2, 1, 6, "", ("192.168.1.50", 80))]
        with pytest.raises(Exception) as exc4:
            validate_feed_url("http://internal-feed.corp/jobs.rss")
        assert "private or restricted network" in str(exc4.value).lower()


# ============================================================================
# Unit Tests: Normalization and Deduplication
# ============================================================================

def test_normalize_rss_title_and_company_conventions():
    """Extract company and title from common RSS title formats."""
    skill_py = Skill(id=uuid4(), name="Python", normalized_name="python")
    skills_map = {"python": skill_py}

    # Case 1: "Company: Title"
    item1 = {
        "title": "Stripe: Senior Software Engineer",
        "link": "https://stripe.com/jobs/1",
        "guid": "guid-1",
        "description": "Python backend role.",
    }
    norm1 = normalize_rss_item(item1, set(), set(), set(), skills_map)
    assert norm1.company_name == "Stripe"
    assert norm1.title == "Senior Software Engineer"

    # Case 2: "Title at Company"
    item2 = {
        "title": "Machine Learning Intern at DeepTech Labs",
        "link": "https://deeptech.ai/jobs/2",
        "guid": "guid-2",
        "description": "Internship in Python ML.",
    }
    norm2 = normalize_rss_item(item2, set(), set(), set(), skills_map)
    assert norm2.company_name == "DeepTech Labs"
    assert norm2.title == "Machine Learning Intern"
    assert norm2.opportunity_type == "Internship"


def test_normalize_rss_classification_conflict():
    """Detect conflict when title says Intern but category declares Full-Time."""
    item = {
        "title": "CloudScale: Cloud Support Intern",
        "link": "https://cloudscale.io/jobs/3",
        "guid": "guid-3",
        "description": "Full-time position for junior cloud engineers.",
        "categories": ["Full-Time"],
    }
    norm = normalize_rss_item(item, set(), set(), set(), {})
    assert norm.classification_conflict is True
    assert norm.opportunity_type == "Internship"
    assert any("classification conflict" in w.lower() for w in norm.warnings)


def test_cross_source_duplicate_detection():
    """Flag duplicate if identical application_url or title+company signature exists in DB."""
    item = {
        "title": "Databricks: Data Engineer",
        "link": "https://databricks.com/jobs/de-101",
        "guid": "guid-rss-new",
        "description": "Data engineering opening.",
    }

    # 1. New item: not duplicate
    norm_new = normalize_rss_item(item, set(), set(), set(), {})
    assert norm_new.is_duplicate is False

    # 2. Existing URL from another source (e.g., imported via JSearch earlier)
    norm_dup_url = normalize_rss_item(
        item,
        existing_external_ids=set(),
        existing_urls={"https://databricks.com/jobs/de-101"},
        existing_signatures=set(),
        skills_map={},
    )
    assert norm_dup_url.is_duplicate is True
    assert any("cross-source duplicate detected by url" in w.lower() for w in norm_dup_url.warnings)

    # 3. Existing title + company signature from manual entry
    norm_dup_sig = normalize_rss_item(
        item,
        existing_external_ids=set(),
        existing_urls=set(),
        existing_signatures={"data engineer::databricks"},
        skills_map={},
    )
    assert norm_dup_sig.is_duplicate is True
    assert any("cross-source duplicate detected by title and company" in w.lower() for w in norm_dup_sig.warnings)


# ============================================================================
# API Endpoints & Authorization Tests
# ============================================================================

def make_test_profile(role="admin"):
    uid = uuid4()
    pid = uuid4()
    return Profile(id=pid, user_id=uid, full_name=f"User {role.capitalize()}", role=role)


@pytest.mark.anyio
async def test_rss_endpoints_unauthenticated():
    """Unauthenticated requests to RSS preview, import, or presets receive 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res1 = await client.get("/api/v1/admin/ingestion/rss/presets")
        assert res1.status_code == 401

        res2 = await client.post("/api/v1/admin/ingestion/rss/preview", json={"feed_url": "https://example.com/feed.rss"})
        assert res2.status_code == 401

        res3 = await client.post("/api/v1/admin/ingestion/rss/import", json={"selected_job_ids": ["1"], "jobs": []})
        assert res3.status_code == 401


@pytest.mark.anyio
async def test_rss_endpoints_forbidden_for_students():
    """Students receive 403 Forbidden on RSS endpoints."""
    student = make_test_profile("student")
    app.dependency_overrides[get_current_user] = lambda: str(student.user_id)
    app.dependency_overrides[require_admin] = lambda: (_ for _ in ()).throw(
        __import__("fastapi").HTTPException(status_code=403, detail="Forbidden")
    )

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.get("/api/v1/admin/ingestion/rss/presets")
            assert res.status_code == 403

            res_prev = await client.post(
                "/api/v1/admin/ingestion/rss/preview",
                json={"feed_url": "https://example.com/feed.rss"},
            )
            assert res_prev.status_code == 403
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_admin_rss_presets_endpoint():
    """Admin can fetch approved preset feeds."""
    admin = make_test_profile("admin")
    app.dependency_overrides[require_admin] = lambda: admin

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.get("/api/v1/admin/ingestion/rss/presets")
            assert res.status_code == 200
            presets = res.json()
            assert len(presets) >= 2
            preset_ids = [p["id"] for p in presets]
            assert "weworkremotely-programming" in preset_ids
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_admin_rss_preview_endpoint_success():
    """Admin preview fetches and normalizes RSS items with cross-source deduplication."""
    admin = make_test_profile("admin")
    app.dependency_overrides[require_admin] = lambda: admin

    mock_db = AsyncMock()
    # Mock skills map query
    skill_py = Skill(id=uuid4(), name="Python", normalized_name="python")
    skill_py.aliases = []
    skills_res = MagicMock()
    skills_res.scalars.return_value.all.return_value = [skill_py]

    # Mock existing opportunities query (one existing listing matching Acme Corp URL)
    dup_res = MagicMock()
    dup_res.all.return_value = [
        ("other-ext-id", "https://weworkremotely.com/jobs/12345-backend-engineer", "Backend Software Engineer", "Acme Corp")
    ]

    mock_db.execute.side_effect = [skills_res, dup_res]
    app.dependency_overrides[get_db] = lambda: mock_db

    # Mock HTTP response from feed provider
    mock_http_resp = MagicMock()
    mock_http_resp.status_code = 200
    mock_http_resp.text = SAMPLE_RSS_2_XML

    transport = ASGITransport(app=app)
    try:
        with (
            patch("app.services.rss.validate_feed_url", return_value="https://weworkremotely.com/feed.rss"),
            patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_http_resp),
        ):
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                res = await client.post(
                    "/api/v1/admin/ingestion/rss/preview",
                    json={"feed_url": "https://weworkremotely.com/feed.rss", "max_items": 10},
                )
                assert res.status_code == 200
                data = res.json()
                assert data["feed_title"] == "We Work Remotely - Programming Jobs"
                assert len(data["jobs"]) == 3

                # First job was in dup_res -> should be flagged duplicate
                job1 = data["jobs"][0]
                assert job1["title"] == "Backend Software Engineer"
                assert job1["company_name"] == "Acme Corp"
                assert job1["is_duplicate"] is True

                # Second job is an intern role
                job2 = data["jobs"][1]
                assert job2["title"] == "Frontend Intern"
                assert job2["company_name"] == "TechNova"
                assert job2["opportunity_type"] == "Internship"
                assert job2["is_duplicate"] is False

                # Summary
                summary = data["summary"]
                assert summary["total_returned"] == 3
                assert summary["duplicate_count"] == 1
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_admin_rss_import_endpoint_success():
    """Admin import saves selected RSS jobs into database as Draft with savepoints."""
    admin = make_test_profile("admin")
    app.dependency_overrides[require_admin] = lambda: admin

    py_skill_id = uuid4()
    preview_item = JobPreviewItem(
        job_id="wwr-rss-001",
        title="Python Software Intern",
        company_name="CloudNine",
        opportunity_type="Internship",
        work_model="Remote",
        locations=["Remote"],
        application_url="https://cloudnine.com/apply/1",
        matched_skills=[MatchedSkillItem(id=py_skill_id, name="Python")],
        status="Draft",
    )

    mock_db = AsyncMock()
    # 1. Existing external IDs query -> returns empty set
    dup_res = MagicMock()
    dup_res.scalars.return_value.all.return_value = []
    # 2. Valid skills query -> returns py_skill_id
    skills_res = MagicMock()
    skills_res.scalars.return_value.all.return_value = [py_skill_id]

    mock_db.execute.side_effect = [dup_res, skills_res]
    mock_db.add = MagicMock()
    mock_db.begin_nested = MagicMock(return_value=AsyncMock())
    mock_db.commit = AsyncMock()

    app.dependency_overrides[get_db] = lambda: mock_db

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post(
                "/api/v1/admin/ingestion/rss/import",
                json={
                    "selected_job_ids": ["wwr-rss-001"],
                    "jobs": [preview_item.model_dump(mode="json")],
                },
            )
            assert res.status_code == 200
            data = res.json()
            assert data["inserted_count"] == 1
            assert data["duplicate_count"] == 0
            assert data["skipped_count"] == 0
            detail = data["details"][0]
            assert detail["job_id"] == "wwr-rss-001"
            assert detail["status"] == "imported"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_admin_rss_import_duplicate_savepoint_rollback():
    """Verify IntegrityError inside nested savepoint is caught and counted as duplicate."""
    admin = make_test_profile("admin")
    app.dependency_overrides[require_admin] = lambda: admin

    preview_item = JobPreviewItem(
        job_id="wwr-rss-dup",
        title="Duplicate Job",
        company_name="Acme",
        opportunity_type="Full-Time",
        work_model="Remote",
        application_url="https://acme.com/apply",
        status="Draft",
    )

    mock_db = AsyncMock()
    # 1. Existing external IDs query -> returns empty set
    dup_res = MagicMock()
    dup_res.scalars.return_value.all.return_value = []
    # 2. Valid skills query -> empty
    skills_res = MagicMock()
    skills_res.scalars.return_value.all.return_value = []

    mock_db.execute.side_effect = [dup_res, skills_res]

    # Mock flush to raise IntegrityError on insert
    from sqlalchemy.exc import IntegrityError
    mock_db.flush.side_effect = IntegrityError("statement", {}, Exception("uix_opportunity_source_external_id"))

    # begin_nested returns async context manager
    mock_nested = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.begin_nested = MagicMock(return_value=mock_nested)
    mock_db.commit = AsyncMock()

    app.dependency_overrides[get_db] = lambda: mock_db

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post(
                "/api/v1/admin/ingestion/rss/import",
                json={
                    "selected_job_ids": ["wwr-rss-dup"],
                    "jobs": [preview_item.model_dump(mode="json")],
                },
            )
            assert res.status_code == 200
            data = res.json()
            assert data["inserted_count"] == 0
            assert data["duplicate_count"] == 1
            detail = data["details"][0]
            assert detail["status"] == "duplicate"
    finally:
        app.dependency_overrides.clear()

