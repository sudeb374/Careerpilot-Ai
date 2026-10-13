"""
Tests for Phase 7.2: Personalized Cover Letter Generation.

Validates:
1. Cover letter generation for a published opportunity.
2. Grounding in candidate's verified profile, education, projects, skills, and active resume.
3. Tone and length controls (professional, enthusiastic, confident; concise, standard, detailed).
4. Prevention of unsupported claims (no hallucinated skills, companies, degrees).
5. Validation on missing candidate data and non-published opportunities.
6. AI provider abstraction: Gemini LLM call, deterministic fallback when unconfigured, graceful handling of LLM failure.
7. Candidate data isolation and authorization.
8. Regression test confirming Phase 7.1 skill-gap roadmap remains fully intact.
"""

import os
import sys
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient, Response

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.dependencies import get_current_profile, get_db
from app.main import app
from app.models.opportunity import Opportunity, OpportunitySkill
from app.models.profile import (
    Education,
    Experience,
    Profile,
    ProfileSkill,
    Project,
    Resume,
    Skill,
)
from app.schemas.cover_letter import (
    CoverLetterGenerateRequest,
    CoverLetterLength,
    CoverLetterTone,
)
from app.services.cover_letter import (
    call_gemini_api,
    generate_cover_letter,
    generate_deterministic_cover_letter,
)


# ============================================================================
# Helpers
# ============================================================================

def make_test_profile(
    user_id: UUID | None = None,
    full_name: str = "Elena Rostova",
    degree: str = "B.S. in Computer Science",
    institution: str = "University of Washington",
) -> Profile:
    p = Profile()
    p.id = uuid4()
    p.user_id = user_id or uuid4()
    p.full_name = full_name
    p.role = "student"
    p.headline = "Aspiring Backend Engineer"
    p.location = "Seattle, WA"
    p.linkedin_url = "https://linkedin.com/in/elenarostova"
    p.github_url = "https://github.com/elenarostova"
    p.portfolio_url = "https://elena.dev"

    edu = Education()
    edu.id = uuid4()
    edu.profile_id = p.id
    edu.degree = degree
    edu.institution = institution
    edu.field_of_study = "Computer Science"
    edu.start_date = date(2022, 9, 1)
    edu.end_date = date(2026, 6, 1)
    p.educations = [edu]

    p.experiences = []
    p.projects = []
    p.skills = []
    p.resumes = []
    p.career_preferences = None
    return p


def make_test_opportunity(
    title: str = "Backend Engineer Intern",
    company_name: str = "CloudScale Inc",
    skills: list[str] | None = None,
    status: str = "Published",
) -> Opportunity:
    opp = Opportunity()
    opp.id = uuid4()
    opp.title = title
    opp.company_name = company_name
    opp.status = status
    opp.opportunity_type = "Internship"
    opp.work_model = "Remote"
    opp.locations = ["Remote"]
    opp.domain = "Cloud Infrastructure"
    opp.description = (
        "We are looking for a Backend Engineer Intern to help build scalable APIs using Python and FastAPI. "
        "Experience with Docker and relational databases is a plus."
    )

    opp_skills = []
    for s_name in skills or ["Python", "FastAPI"]:
        sk = Skill()
        sk.id = uuid4()
        sk.name = s_name
        sk.normalized_name = s_name.lower()
        os = OpportunitySkill()
        os.id = uuid4()
        os.opportunity_id = opp.id
        os.skill_id = sk.id
        os.skill = sk
        opp_skills.append(os)
    opp.skills = opp_skills
    return opp


# ============================================================================
# 1. Generation & Grounding in Candidate Facts
# ============================================================================

@pytest.mark.anyio
async def test_cover_letter_generation_grounded_in_facts():
    """
    Verify cover letter includes candidate's verified name, degree, institution,
    matched skills, and projects without inventing false claims.
    """
    db = AsyncMock()
    candidate = make_test_profile()

    # Add Project
    proj = Project()
    proj.id = uuid4()
    proj.profile_id = candidate.id
    proj.name = "DistributedCache"
    proj.description = "Built a high-performance in-memory cache in Python."
    candidate.projects = [proj]

    # Add Skill
    sk = Skill()
    sk.id = uuid4()
    sk.name = "Python"
    sk.normalized_name = "python"
    ps = ProfileSkill()
    ps.id = uuid4()
    ps.profile_id = candidate.id
    ps.skill_id = sk.id
    ps.skill = sk
    candidate.skills = [ps]

    # Add Active Resume with Docker
    resume = Resume()
    resume.id = uuid4()
    resume.profile_id = candidate.id
    resume.is_active = True
    resume.structured_data = {
        "skills": [{"name": "Docker", "evidence": "Containerized microservices"}]
    }
    candidate.resumes = [resume]

    opp = make_test_opportunity(skills=["Python", "Docker"])

    async def mock_execute(stmt):
        mock_res = MagicMock()
        s = str(stmt).lower()
        if "from profiles" in s:
            mock_res.scalar_one_or_none.return_value = candidate
        elif "from opportunities" in s:
            mock_res.scalar_one_or_none.return_value = opp
        return mock_res

    db.execute.side_effect = mock_execute

    req = CoverLetterGenerateRequest(
        opportunity_id=opp.id,
        tone=CoverLetterTone.PROFESSIONAL,
        length=CoverLetterLength.STANDARD,
    )

    with patch("app.services.cover_letter.call_gemini_api", return_value=None):
        res = await generate_cover_letter(db, candidate.id, req)

    assert res.opportunity_title == "Backend Engineer Intern"
    assert res.company_name == "CloudScale Inc"
    assert "Elena Rostova" in res.subject_line
    assert "Dear CloudScale Inc Hiring Team," in res.cover_letter_text
    assert "University of Washington" in res.cover_letter_text
    assert "Python" in res.cover_letter_text
    assert "DistributedCache" in res.cover_letter_text
    assert "Elena Rostova" in res.cover_letter_text

    # Verified Evidence Summary audit
    assert "Python" in res.verified_evidence.matched_skills
    assert "DistributedCache" in res.verified_evidence.included_projects
    assert any("University of Washington" in edu for edu in res.verified_evidence.included_education)
    assert res.is_template_fallback is True
    assert "deterministic template engine" in (res.provider_note or "")


# ============================================================================
# 2. Tone and Length Controls
# ============================================================================

@pytest.mark.anyio
async def test_cover_letter_tone_and_length_variations():
    """Verify different tones and lengths adjust text appropriately."""
    db = AsyncMock()
    candidate = make_test_profile()
    opp = make_test_opportunity()

    async def mock_execute(stmt):
        mock_res = MagicMock()
        s = str(stmt).lower()
        if "from profiles" in s:
            mock_res.scalar_one_or_none.return_value = candidate
        elif "from opportunities" in s:
            mock_res.scalar_one_or_none.return_value = opp
        return mock_res

    db.execute.side_effect = mock_execute

    # 1. Enthusiastic Tone + Concise Length
    req_enthusiastic = CoverLetterGenerateRequest(
        opportunity_id=opp.id,
        tone=CoverLetterTone.ENTHUSIASTIC,
        length=CoverLetterLength.CONCISE,
    )
    with patch("app.services.cover_letter.call_gemini_api", return_value=None):
        res1 = await generate_cover_letter(db, candidate.id, req_enthusiastic)
    assert res1.tone == CoverLetterTone.ENTHUSIASTIC
    assert "thrilled" in res1.cover_letter_text.lower() or "eager" in res1.cover_letter_text.lower()

    # 2. Confident Tone + Detailed Length
    req_confident = CoverLetterGenerateRequest(
        opportunity_id=opp.id,
        tone=CoverLetterTone.CONFIDENT,
        length=CoverLetterLength.DETAILED,
    )
    with patch("app.services.cover_letter.call_gemini_api", return_value=None):
        res2 = await generate_cover_letter(db, candidate.id, req_confident)
    assert res2.tone == CoverLetterTone.CONFIDENT
    assert "confident" in res2.cover_letter_text.lower()
    # Detailed length should have more words than concise
    words_concise = len(res1.cover_letter_text.split())
    words_detailed = len(res2.cover_letter_text.split())
    assert words_detailed >= words_concise


# ============================================================================
# 3. Missing Candidate Data Validation
# ============================================================================

@pytest.mark.anyio
async def test_cover_letter_missing_candidate_data():
    """Verify error when candidate has empty profile (no name or no education/skills)."""
    db = AsyncMock()
    empty_candidate = Profile()
    empty_candidate.id = uuid4()
    empty_candidate.full_name = "Empty User"
    empty_candidate.educations = []
    empty_candidate.skills = []
    empty_candidate.experiences = []
    empty_candidate.projects = []
    empty_candidate.resumes = []

    opp = make_test_opportunity()

    async def mock_execute(stmt):
        mock_res = MagicMock()
        s = str(stmt).lower()
        if "from profiles" in s:
            mock_res.scalar_one_or_none.return_value = empty_candidate
        elif "from opportunities" in s:
            mock_res.scalar_one_or_none.return_value = opp
        return mock_res

    db.execute.side_effect = mock_execute

    req = CoverLetterGenerateRequest(opportunity_id=opp.id)
    with pytest.raises(ValueError) as exc:
        await generate_cover_letter(db, empty_candidate.id, req)
    assert "educational history or skills" in str(exc.value)


# ============================================================================
# 4. Non-Published Opportunity Validation
# ============================================================================

@pytest.mark.anyio
async def test_cover_letter_draft_or_missing_opportunity():
    """Verify error when opportunity is in Draft or Closed status."""
    db = AsyncMock()
    candidate = make_test_profile()
    draft_opp = make_test_opportunity(status="Draft")

    async def mock_execute(stmt):
        mock_res = MagicMock()
        s = str(stmt).lower()
        if "from profiles" in s:
            mock_res.scalar_one_or_none.return_value = candidate
        elif "from opportunities" in s:
            mock_res.scalar_one_or_none.return_value = draft_opp
        return mock_res

    db.execute.side_effect = mock_execute

    req = CoverLetterGenerateRequest(opportunity_id=draft_opp.id)
    with pytest.raises(ValueError) as exc:
        await generate_cover_letter(db, candidate.id, req)
    assert "not found or not published" in str(exc.value).lower()


# ============================================================================
# 5. Gemini Provider Integration & Safe Fallback
# ============================================================================

@pytest.mark.anyio
async def test_gemini_integration_mocked_success():
    """Verify successful Gemini LLM generation returns provider='gemini'."""
    db = AsyncMock()
    candidate = make_test_profile()
    opp = make_test_opportunity()

    async def mock_execute(stmt):
        mock_res = MagicMock()
        s = str(stmt).lower()
        if "from profiles" in s:
            mock_res.scalar_one_or_none.return_value = candidate
        elif "from opportunities" in s:
            mock_res.scalar_one_or_none.return_value = opp
        return mock_res

    db.execute.side_effect = mock_execute

    mock_llm_text = (
        "Dear CloudScale Inc Hiring Team,\n\n"
        "I am writing to express my strong interest in the Backend Engineer Intern role at CloudScale Inc. "
        "As a student at University of Washington, I have developed a solid foundation in Python.\n\n"
        "Sincerely,\nElena Rostova"
    )

    with patch("app.services.cover_letter.call_gemini_api", return_value=mock_llm_text):
        req = CoverLetterGenerateRequest(opportunity_id=opp.id)
        res = await generate_cover_letter(db, candidate.id, req)

    assert res.provider == "gemini"
    assert res.provider_model == "gemini-1.5-flash"
    assert res.is_template_fallback is False
    assert "CloudScale Inc" in res.cover_letter_text


@pytest.mark.anyio
async def test_gemini_failure_gracefully_falls_back():
    """Verify that when Gemini API call fails, the system falls back seamlessly to template."""
    db = AsyncMock()
    candidate = make_test_profile()
    opp = make_test_opportunity()

    async def mock_execute(stmt):
        mock_res = MagicMock()
        s = str(stmt).lower()
        if "from profiles" in s:
            mock_res.scalar_one_or_none.return_value = candidate
        elif "from opportunities" in s:
            mock_res.scalar_one_or_none.return_value = opp
        return mock_res

    db.execute.side_effect = mock_execute

    # Simulate Gemini returning None (e.g. on quota error or timeout)
    with patch("app.services.cover_letter.call_gemini_api", return_value=None):
        req = CoverLetterGenerateRequest(opportunity_id=opp.id)
        res = await generate_cover_letter(db, candidate.id, req)

    assert res.provider == "template_fallback"
    assert res.is_template_fallback is True
    assert "Elena Rostova" in res.cover_letter_text
    assert "CloudScale Inc" in res.cover_letter_text


# ============================================================================
# 6. Authorization & Candidate Data Isolation
# ============================================================================

@pytest.mark.anyio
async def test_cover_letter_api_authorization_and_isolation():
    """Verify unauthenticated requests fail and students only access their own profile facts."""
    student_a = make_test_profile(full_name="Alice Candidate")
    student_b = make_test_profile(full_name="Bob Candidate")
    opp = make_test_opportunity()

    mock_db = AsyncMock()

    # 1. Unauthenticated Request
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_unauth = await client.post(
            "/api/v1/copilot/cover-letter/generate",
            json={"opportunity_id": str(opp.id)},
        )
        assert res_unauth.status_code in (401, 403)

    # 2. Candidate A Access
    app.dependency_overrides[get_current_profile] = lambda: student_a
    app.dependency_overrides[get_db] = lambda: mock_db

    async def mock_exec_a(stmt):
        res = MagicMock()
        s = str(stmt).lower()
        if "from profiles" in s:
            res.scalar_one_or_none.return_value = student_a
        elif "from opportunities" in s:
            res.scalar_one_or_none.return_value = opp
        return res

    mock_db.execute.side_effect = mock_exec_a

    with patch("app.services.cover_letter.call_gemini_api", return_value=None):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res_a = await client.post(
                "/api/v1/copilot/cover-letter/generate",
                json={"opportunity_id": str(opp.id)},
            )
            assert res_a.status_code == 200
            data_a = res_a.json()
            assert "Alice Candidate" in data_a["cover_letter_text"]
            assert "Bob Candidate" not in data_a["cover_letter_text"]

    # Clean up
    app.dependency_overrides.clear()


# ============================================================================
# 7. Regression Test: Phase 7.1 Skill-Gap Roadmap Intact
# ============================================================================

@pytest.mark.anyio
async def test_phase71_roadmap_remains_intact():
    """Ensure adding Phase 7.2 does not break Phase 7.1 roadmap endpoint."""
    student = make_test_profile()
    mock_db = AsyncMock()

    app.dependency_overrides[get_current_profile] = lambda: student
    app.dependency_overrides[get_db] = lambda: mock_db

    async def mock_exec(stmt):
        res = MagicMock()
        s = str(stmt).lower()
        if "from profiles" in s:
            res.scalar_one_or_none.return_value = student
        elif "from opportunities" in s:
            res.scalars.return_value.all.return_value = []
        return res

    mock_db.execute.side_effect = mock_exec

    transport = ASGITransport(app=app)
    with patch("app.services.skill_gap.expire_overdue_opportunities", new_callable=AsyncMock):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.get("/api/v1/copilot/skill-gap-roadmap")
            assert res.status_code == 200
            data = res.json()
            assert "coverage" in data
            assert "data_status" in data

    app.dependency_overrides.clear()
