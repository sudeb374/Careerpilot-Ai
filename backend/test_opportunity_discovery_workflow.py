import os
import sys
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.dependencies import get_current_profile, get_current_user, get_db, require_admin
from app.main import app
from app.models.opportunity import Opportunity, OpportunitySkill
from app.models.profile import CareerPreference, Profile, ProfileSkill, Skill
from app.services.matching import calculate_opportunity_match, get_candidate_evidence


# ============================================================================
# Helpers & Mock Models
# ============================================================================

def make_test_profile(role="student"):
    uid = uuid4()
    pid = uuid4()
    return Profile(id=pid, user_id=uid, full_name=f"User {role.capitalize()}", role=role)


def make_test_skill(name="Python"):
    return Skill(id=uuid4(), name=name, normalized_name=name.lower())


def make_imported_opportunity(
    status="Draft",
    source_name="JSearch",
    external_id="jsearch_ext_123",
    opportunity_type="Internship",
    work_model="On-site",
    application_url="https://example.com/jobs/apply",
    eligibility=None,
    skills=None,
):
    opp = Opportunity(
        id=uuid4(),
        title="SDE- Intern- Embedded Linux & Yocto",
        company_name="Todaywalkin Com",
        company_website="https://todaywalkin.com",
        company_logo_url="https://example.com/logo.png",
        description="SDE Intern role in Embedded Linux and Yocto.",
        opportunity_type=opportunity_type,
        work_model=work_model,
        locations=["Noida, Uttar Pradesh, IN"],
        domain="Engineering",
        required_experience_min=0,
        required_experience_max=1,
        education_requirements="B.Tech in CS/EC",
        eligibility=eligibility,
        application_url=application_url,
        deadline=None,
        currency="INR",
        source_name=source_name,
        source_url=application_url,
        external_id=external_id,
        status=status,
        created_by_profile_id=uuid4(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    opp.skills = []
    if skills:
        for sk in skills:
            os_rel = OpportunitySkill(id=uuid4(), opportunity_id=opp.id, skill_id=sk.id)
            os_rel.skill = sk
            opp.skills.append(os_rel)
    return opp


# ============================================================================
# Tests: Discovery & Access Control
# ============================================================================

@pytest.mark.anyio
async def test_draft_opportunity_hidden_from_students():
    """Draft opportunities are hidden from student listings and direct detail routes."""
    student = make_test_profile("student")
    draft_opp = make_imported_opportunity(status="Draft")

    mock_db = AsyncMock()
    expire_res = MagicMock(rowcount=0)
    count_res = MagicMock()
    count_res.scalar.return_value = 0
    list_res = MagicMock()
    list_res.scalars.return_value.all.return_value = []
    # Detail query
    detail_res = MagicMock()
    detail_res.scalar_one_or_none.return_value = None

    mock_db.execute.side_effect = [expire_res, count_res, list_res, expire_res, detail_res]

    app.dependency_overrides[get_current_user] = lambda: str(student.user_id)
    app.dependency_overrides[get_current_profile] = lambda: student
    app.dependency_overrides[get_db] = lambda: mock_db

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Listing should not contain Draft
            res = await client.get("/api/v1/opportunities")
            assert res.status_code == 200
            data = res.json()
            assert len(data["items"]) == 0

            # 2. Direct get on Draft should return 404
            res = await client.get(f"/api/v1/opportunities/{draft_opp.id}")
            assert res.status_code == 404
            assert "not published" in res.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_published_imported_opportunity_appears_in_discovery():
    """Published imported opportunity appears in student discovery with human-readable skill names."""
    student = make_test_profile("student")
    skill_python = make_test_skill("Python")
    skill_c = make_test_skill("C")
    pub_opp = make_imported_opportunity(status="Published", skills=[skill_python, skill_c])

    mock_db = AsyncMock()
    expire_res = MagicMock(rowcount=0)
    count_res = MagicMock()
    count_res.scalar.return_value = 1
    list_res = MagicMock()
    list_res.scalars.return_value.all.return_value = [pub_opp]
    detail_res = MagicMock()
    detail_res.scalar_one_or_none.return_value = pub_opp

    mock_db.execute.side_effect = [expire_res, count_res, list_res, expire_res, detail_res]

    app.dependency_overrides[get_current_user] = lambda: str(student.user_id)
    app.dependency_overrides[get_current_profile] = lambda: student
    app.dependency_overrides[get_db] = lambda: mock_db

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Listing
            res = await client.get("/api/v1/opportunities")
            assert res.status_code == 200
            items = res.json()["items"]
            assert len(items) == 1
            item = items[0]
            assert item["id"] == str(pub_opp.id)
            assert item["title"] == pub_opp.title
            assert item["company_name"] == pub_opp.company_name
            assert item["status"] == "Published"

            # Verify skill labels are human-readable strings, not raw UUIDs
            assert len(item["skills"]) == 2
            skill_names = [s["name"] for s in item["skills"]]
            assert "Python" in skill_names
            assert "C" in skill_names
            # Make sure names don't look like UUIDs
            for name in skill_names:
                assert "-" not in name or len(name) < 20

            # Detail
            res_detail = await client.get(f"/api/v1/opportunities/{pub_opp.id}")
            assert res_detail.status_code == 200
            detail_data = res_detail.json()
            assert detail_data["application_url"] == pub_opp.application_url
            assert detail_data["source_name"] == "JSearch"
    finally:
        app.dependency_overrides.clear()


# ============================================================================
# Tests: Admin Publishing & Conflict Validation
# ============================================================================

@pytest.mark.anyio
async def test_admin_only_publication_authorization():
    """Only authorized admins can publish or patch opportunities."""
    student = make_test_profile("student")
    opp_id = uuid4()

    transport = ASGITransport(app=app)

    # 1. Unauthenticated -> 401
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.patch(f"/api/v1/admin/opportunities/{opp_id}", json={"status": "Published"})
        assert res.status_code == 401

    # 2. Student user -> 403 Forbidden
    app.dependency_overrides[get_current_user] = lambda: str(student.user_id)
    app.dependency_overrides[get_current_profile] = lambda: student
    mock_db = AsyncMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.patch(f"/api/v1/admin/opportunities/{opp_id}", json={"status": "Published"})
            assert res.status_code == 403
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_unresolved_employment_type_conflict_cannot_be_published_as_internship():
    """An imported draft with a classification conflict cannot be published as an Internship without review."""
    admin = make_test_profile("admin")
    conflict_opp = make_imported_opportunity(
        status="Draft",
        opportunity_type="Internship",
        eligibility="[Classification Conflict: Job title includes 'Intern', but provider reports 'FULLTIME' employment type. Flagged for review.]",
    )

    mock_db = AsyncMock()
    opp_res = MagicMock()
    opp_res.scalar_one_or_none.return_value = conflict_opp
    mock_db.execute.return_value = opp_res

    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Attempt to publish as Internship with unresolved conflict
            res = await client.patch(
                f"/api/v1/admin/opportunities/{conflict_opp.id}",
                json={"status": "Published", "opportunity_type": "Internship"},
            )
            assert res.status_code == 422
            assert "employment-type conflict" in res.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_reviewed_and_corrected_conflict_can_be_published():
    """Once reviewed and corrected (e.g. type changed to Full-Time, or conflict note cleared), publishing succeeds."""
    admin = make_test_profile("admin")
    conflict_opp = make_imported_opportunity(
        status="Draft",
        opportunity_type="Internship",
        eligibility="[Classification Conflict: Job title includes 'Intern', but provider reports 'FULLTIME' employment type. Flagged for review.]",
    )

    mock_db = AsyncMock()
    mock_db.commit = AsyncMock()
    opp_res = MagicMock()
    opp_res.scalar_one_or_none.return_value = conflict_opp
    # Second execute for reload
    reload_res = MagicMock()
    reload_res.scalar_one.return_value = conflict_opp
    mock_db.execute.side_effect = [opp_res, reload_res]

    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Admin reviews and corrects: changes type to Full-Time
            res = await client.patch(
                f"/api/v1/admin/opportunities/{conflict_opp.id}",
                json={"status": "Published", "opportunity_type": "Full-Time"},
            )
            assert res.status_code == 200
            assert res.json()["status"] == "Published"
            assert res.json()["opportunity_type"] == "Full-Time"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_imported_opportunity_requires_valid_application_url_to_publish():
    """Publishing an imported listing requires a valid HTTP/HTTPS application URL."""
    admin = make_test_profile("admin")
    opp_without_url = make_imported_opportunity(status="Draft", application_url=None)

    mock_db = AsyncMock()
    opp_res = MagicMock()
    opp_res.scalar_one_or_none.return_value = opp_without_url
    mock_db.execute.return_value = opp_res

    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Missing URL rejected
            res = await client.patch(
                f"/api/v1/admin/opportunities/{opp_without_url.id}",
                json={"status": "Published"},
            )
            assert res.status_code == 422
            assert "application url is required" in res.json()["detail"].lower()

            # 2. Invalid non-HTTP scheme rejected
            res_bad_scheme = await client.patch(
                f"/api/v1/admin/opportunities/{opp_without_url.id}",
                json={"status": "Published", "application_url": "javascript:alert(1)"},
            )
            assert res_bad_scheme.status_code == 422
    finally:
        app.dependency_overrides.clear()


# ============================================================================
# Tests: Matching Integration for Published Imported Listing
# ============================================================================

@pytest.mark.anyio
async def test_published_imported_listing_eligible_for_matching():
    """A published imported listing is matched using existing scoring system without weight changes."""
    student = make_test_profile("student")
    skill_python = make_test_skill("Python")
    skill_c = make_test_skill("C")
    pub_opp = make_imported_opportunity(status="Published", skills=[skill_python, skill_c])

    # Configure candidate profile skills: student has Python but lacks C
    ps = ProfileSkill(id=uuid4(), profile_id=student.id, skill_id=skill_python.id)
    ps.skill = skill_python
    student.skills = [ps]
    student.career_preferences = CareerPreference(
        profile_id=student.id,
        desired_roles=["Software Engineer Intern"],
        work_model=["On-site"],
        locations=["Noida"],
        preferred_domains=["Engineering"],
    )
    student.experiences = []
    student.educations = []
    student.resumes = []

    mock_db = AsyncMock()
    opp_res = MagicMock()
    opp_res.scalar_one_or_none.return_value = pub_opp
    prof_res = MagicMock()
    prof_res.scalar_one_or_none.return_value = student

    # calculate_opportunity_match queries opportunity then profile
    mock_db.execute.side_effect = [opp_res, prof_res]

    match_result = await calculate_opportunity_match(mock_db, student.id, pub_opp.id)

    # 1. Verify match score computed
    assert match_result.score is not None
    assert 0 <= match_result.score <= 100

    # 2. Verify skills are human-readable names and NOT UUIDs
    assert "Python" in match_result.matched_skills
    assert "C" in match_result.missing_required_skills
    for s in match_result.matched_skills + match_result.missing_required_skills:
        assert "-" not in s or len(s) < 20

    # 3. Verify component scores are intact (Phase 5 weights: Skills 40, Role 20, Model/Loc 15, Exp/Edu 15, Domain 10)
    component_names = [c.component for c in match_result.component_scores]
    assert "Required Skills" in component_names
    assert "Desired Role" in component_names
    assert "Work Model & Location" in component_names
    assert "Preferred Domain" in component_names

    # 4. Verify disclaimer and explanation exist
    assert match_result.explanation.summary != ""
    assert match_result.data_coverage in ("High", "Moderate", "Limited")


@pytest.mark.anyio
async def test_duplicate_source_identifiers_protected():
    """Duplicate (source_name, external_id) is rejected with 409 Conflict."""
    from sqlalchemy.exc import IntegrityError

    admin = make_test_profile("admin")

    mock_db = AsyncMock()
    mock_db.flush.side_effect = IntegrityError("statement", {}, Exception("uix_opportunity_source_external_id"))

    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post(
                "/api/v1/admin/opportunities",
                json={
                    "title": "Another Job",
                    "company_name": "Another Co",
                    "opportunity_type": "Full-Time",
                    "work_model": "Remote",
                    "source_name": "JSearch",
                    "external_id": "dup_ext_id_999",
                    "status": "Draft",
                },
            )
            assert res.status_code == 409
            assert "duplicate source_name and external_id" in res.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_candidate_specific_matching_data_isolated_between_users():
    """Candidate match results are strictly user-scoped and never leak candidate data between users."""
    student_a = make_test_profile("student")
    student_b = make_test_profile("student")

    skill_python = make_test_skill("Python")
    pub_opp = make_imported_opportunity(status="Published", skills=[skill_python])

    # Candidate A has Python
    ps_a = ProfileSkill(id=uuid4(), profile_id=student_a.id, skill_id=skill_python.id)
    ps_a.skill = skill_python
    student_a.skills = [ps_a]
    student_a.career_preferences = CareerPreference(
        profile_id=student_a.id,
        desired_roles=["Software Engineer Intern"],
        work_model=["On-site"],
        locations=["Noida"],
        preferred_domains=["Engineering"],
    )
    student_a.experiences = []
    student_a.educations = []
    student_a.resumes = []

    # Candidate B has no matching skills and different preference
    student_b.skills = []
    student_b.career_preferences = CareerPreference(
        profile_id=student_b.id,
        desired_roles=["Marketing Specialist"],
        work_model=["Remote"],
        locations=["Mumbai"],
        preferred_domains=["Marketing"],
    )
    student_b.experiences = []
    student_b.educations = []
    student_b.resumes = []

    mock_db = AsyncMock()
    expire_res = MagicMock(rowcount=0)
    opps_res = MagicMock()
    opps_res.scalars.return_value.all.return_value = [pub_opp]

    prof_res_a = MagicMock()
    prof_res_a.scalar_one_or_none.return_value = student_a

    prof_res_b = MagicMock()
    prof_res_b.scalar_one_or_none.return_value = student_b

    transport = ASGITransport(app=app)

    # 1. Query matching for Candidate A
    app.dependency_overrides[get_current_user] = lambda: str(student_a.user_id)
    app.dependency_overrides[get_current_profile] = lambda: student_a

    mock_db.execute.side_effect = [
        expire_res,  # expire_overdue_opportunities
        prof_res_a,  # get_candidate_evidence
        opps_res,    # select opportunities
    ]
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_a = await client.get("/api/v1/profile/opportunity-matches")
        assert res_a.status_code == 200
        matches_a = res_a.json()["items"]
        assert len(matches_a) == 1
        match_a = matches_a[0]["match"]
        assert "Python" in match_a["matched_skills"]
        score_a = match_a["score"]

    # 2. Query matching for Candidate B
    app.dependency_overrides[get_current_user] = lambda: str(student_b.user_id)
    app.dependency_overrides[get_current_profile] = lambda: student_b

    mock_db.execute.side_effect = [
        expire_res,
        prof_res_b,
        opps_res,
    ]

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_b = await client.get("/api/v1/profile/opportunity-matches")
        assert res_b.status_code == 200
        matches_b = res_b.json()["items"]
        assert len(matches_b) == 1
        match_b = matches_b[0]["match"]
        assert "Python" in match_b["missing_required_skills"]
        assert "Python" not in match_b["matched_skills"]
        score_b = match_b["score"]

    app.dependency_overrides.clear()

    # Scores and candidate results must differ and reflect individual candidate profiles
    assert score_a > score_b

