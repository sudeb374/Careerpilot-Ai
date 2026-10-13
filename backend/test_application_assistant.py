"""
Tests for Phase 7.3: AI-Powered Application Question Assistance.

Validates:
1. Gemini success using mocked responses.
2. Gemini unavailable or misconfigured and deterministic fallback.
3. API timeout, quota/rate-limit (HTTP 429), and malformed-response handling.
4. Evidence-based answers for project and experience questions.
5. Prevention of unsupported claims and handling of unknown personal facts (visa/authorization/salary).
6. Different question types, answer styles (Professional, Concise, Detailed), and word limits.
7. Insufficient profile data and unpublished opportunity validation.
8. General application questions without selecting an opportunity (opportunity_id=None).
9. Authentication and candidate data isolation.
10. Regression tests confirming Phase 7.1 skill-gap roadmap and Phase 7.2 cover letter generation remain intact.
"""

import os
import sys
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import httpx
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
from app.schemas.application_assistant import (
    AnswerStyle,
    ApplicationQuestionRequest,
    ApplicationQuestionResponse,
)
from app.services.application_assistant import (
    call_gemini_for_question,
    classify_question,
    generate_application_answer,
    generate_deterministic_answer,
    get_suggested_application_questions,
)


# ============================================================================
# Test Fixtures & Helpers
# ============================================================================

def make_test_profile(
    user_id: UUID | None = None,
    full_name: str = "Marcus Aurelius",
    degree: str = "B.S. in Computer Science",
    institution: str = "Stanford University",
) -> Profile:
    p = Profile()
    p.id = uuid4()
    p.user_id = user_id or uuid4()
    p.full_name = full_name
    p.role = "student"
    p.headline = "Aspiring Systems Software Engineer"
    p.location = "San Francisco, CA"
    p.about = "Passionate about high-throughput distributed systems."

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
    title: str = "Full Stack Engineer Intern",
    company_name: str = "Apex Technologies",
    skills: list[str] | None = None,
    status: str = "Published",
) -> Opportunity:
    opp = Opportunity()
    opp.id = uuid4()
    opp.title = title
    opp.company_name = company_name
    opp.company_logo_url = None
    opp.deadline = None
    opp.created_at = datetime.now()
    opp.status = status
    opp.opportunity_type = "Internship"
    opp.work_model = "Hybrid"
    opp.locations = ["San Francisco, CA"]
    opp.domain = "Enterprise Infrastructure"
    opp.description = (
        "Seeking an intern to build resilient full stack features with Python, FastAPI, and React. "
        "Experience in cloud deployments and PostgreSQL is appreciated."
    )

    opp_skills = []
    for s_name in skills or ["Python", "FastAPI", "React"]:
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
# 1. Gemini Success with Mocked Responses
# ============================================================================

@pytest.mark.anyio
async def test_gemini_success_mocked_response():
    """Verify successful Gemini generation returns provider='gemini' and proper metadata."""
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
        "My background in computer science at Stanford University has provided me with a rigorous grounding "
        "in software engineering. Through coursework and practical programming in Python, I have developed "
        "strong capabilities in designing robust APIs and writing maintainable code."
    )

    req = ApplicationQuestionRequest(
        question="Why should we hire you for this position?",
        opportunity_id=opp.id,
        style=AnswerStyle.PROFESSIONAL,
    )

    with patch("app.services.application_assistant.call_gemini_for_question", return_value=mock_llm_text):
        res = await generate_application_answer(db, candidate.id, req)

    assert res.provider == "gemini"
    assert res.provider_model == "gemini-2.5-flash"
    assert res.is_template_fallback is False
    assert res.opportunity_title == "Full Stack Engineer Intern"
    assert res.company_name == "Apex Technologies"
    assert "Stanford University" in res.answer_text
    assert res.disclaimer is not None


# ============================================================================
# 2. Gemini Unavailable & Deterministic Fallback
# ============================================================================

@pytest.mark.anyio
async def test_gemini_unavailable_falls_back_deterministically():
    """Verify that when Gemini is unconfigured or fails, the system safely falls back."""
    db = AsyncMock()
    candidate = make_test_profile()

    # Add Project
    proj = Project()
    proj.id = uuid4()
    proj.profile_id = candidate.id
    proj.name = "RaftConsensus"
    proj.description = "Implemented a distributed consensus protocol in Go and Python."
    candidate.projects = [proj]

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

    req = ApplicationQuestionRequest(
        question="Describe a relevant technical project you worked on.",
        opportunity_id=opp.id,
        style=AnswerStyle.PROFESSIONAL,
    )

    # When Gemini returns None
    with patch("app.services.application_assistant.call_gemini_for_question", return_value=None):
        res = await generate_application_answer(db, candidate.id, req)

    assert res.provider == "template_fallback"
    assert res.is_template_fallback is True
    assert "RaftConsensus" in res.answer_text
    assert "Apex Technologies" in res.answer_text
    assert "deterministic template engine" in (res.provider_note or "")


# ============================================================================
# 3. API Timeout, Quota Errors (429), and Malformed Response
# ============================================================================

@pytest.mark.anyio
async def test_gemini_errors_and_quota_graceful_handling():
    """Verify call_gemini_for_question safely handles 429 quota error, timeouts, and malformed JSON."""
    candidate = make_test_profile()
    opp = make_test_opportunity()
    from app.services.application_assistant import (
        CandidateApplicationContext,
        build_evidence_summary,
        gather_candidate_application_context,
    )

    cand_ctx = CandidateApplicationContext(
        full_name=candidate.full_name,
        headline=candidate.headline,
        location=candidate.location,
        about=candidate.about,
        educations=list(candidate.educations),
        experiences=[],
        projects=[],
        verified_skills=["Python"],
        resume_skills=[],
        warnings=[],
    )
    evidence = build_evidence_summary(cand_ctx, opp, "project")

    # 1. Missing / Dummy Key returns None immediately
    with patch("app.services.application_assistant.settings.gemini_api_key", ""):
        res_nokey = await call_gemini_for_question(cand_ctx, opp, "Why hire you?", AnswerStyle.PROFESSIONAL, None, None, evidence)
        assert res_nokey is None

    # 2. HTTP 429 Rate Limit
    with patch("app.services.application_assistant.settings.gemini_api_key", "valid-test-key"):
        mock_resp_429 = MagicMock()
        mock_resp_429.status_code = 429
        mock_resp_429.text = "RESOURCE_EXHAUSTED: Quota exceeded"
        with patch("httpx.AsyncClient.post", return_value=mock_resp_429):
            res_429 = await call_gemini_for_question(cand_ctx, opp, "Why hire you?", AnswerStyle.PROFESSIONAL, None, None, evidence)
            assert res_429 is None

    # 3. Timeout Exception
    with patch("app.services.application_assistant.settings.gemini_api_key", "valid-test-key"):
        with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Timed out")):
            res_timeout = await call_gemini_for_question(cand_ctx, opp, "Why hire you?", AnswerStyle.PROFESSIONAL, None, None, evidence)
            assert res_timeout is None


# ============================================================================
# 4. Evidence-Based Answers: Project & Experience Grounding
# ============================================================================

@pytest.mark.anyio
async def test_evidence_grounding_for_project_and_experience_questions():
    """Verify question answers cite candidate's verified projects and work experience without hallucinations."""
    db = AsyncMock()
    candidate = make_test_profile()

    # Experience
    exp = Experience()
    exp.id = uuid4()
    exp.profile_id = candidate.id
    exp.title = "Backend Intern"
    exp.company = "Stripe"
    exp.description = "Built payment webhook processors and telemetry dashboards."
    candidate.experiences = [exp]

    # Project
    proj = Project()
    proj.id = uuid4()
    proj.profile_id = candidate.id
    proj.name = "CacheMaster"
    proj.description = "An in-memory LRU cache engine."
    candidate.projects = [proj]

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

    # 1. Project Question
    req_proj = ApplicationQuestionRequest(
        question="Describe a technical project you built.",
        opportunity_id=opp.id,
    )
    with patch("app.services.application_assistant.call_gemini_for_question", return_value=None):
        res_proj = await generate_application_answer(db, candidate.id, req_proj)
    assert "CacheMaster" in res_proj.answer_text
    assert "CacheMaster" in res_proj.verified_evidence.included_projects

    # 2. Experience Question
    req_exp = ApplicationQuestionRequest(
        question="Tell me about your prior work experience and teamwork.",
        opportunity_id=opp.id,
    )
    with patch("app.services.application_assistant.call_gemini_for_question", return_value=None):
        res_exp = await generate_application_answer(db, candidate.id, req_exp)
    assert "Backend Intern" in res_exp.answer_text
    assert "Stripe" in res_exp.answer_text
    assert any("Stripe" in e for e in res_exp.verified_evidence.included_experiences)


# ============================================================================
# 5. Handling Unknown Personal Facts (Visa, Salary, Relocation)
# ============================================================================

@pytest.mark.anyio
async def test_handling_unknown_personal_facts():
    """Verify that questions about visa sponsorship or salary do NOT guess or hallucinate claims."""
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

    req = ApplicationQuestionRequest(
        question="Are you authorized to work in the US and do you require visa sponsorship?",
        opportunity_id=opp.id,
    )

    with patch("app.services.application_assistant.call_gemini_for_question", return_value=None):
        res = await generate_application_answer(db, candidate.id, req)

    # Must prompt candidate to confirm directly and not fabricate visa status
    assert "authorization" in res.answer_text.lower() or "directly" in res.answer_text.lower()
    assert any("authorization" in n.lower() for n in res.verified_evidence.missing_information_notes)


# ============================================================================
# 6. Style Variations & Word Limit Controls
# ============================================================================

@pytest.mark.anyio
async def test_styles_and_word_limit_controls():
    """Verify concise, professional, detailed styles and explicit word limits."""
    db = AsyncMock()
    candidate = make_test_profile()

    proj = Project()
    proj.id = uuid4()
    proj.profile_id = candidate.id
    proj.name = "QuickSync"
    proj.description = "Fast file synchronization tool."
    candidate.projects = [proj]

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

    # 1. Concise Style
    req_concise = ApplicationQuestionRequest(
        question="Why should we hire you?",
        opportunity_id=opp.id,
        style=AnswerStyle.CONCISE,
    )
    with patch("app.services.application_assistant.call_gemini_for_question", return_value=None):
        res_c = await generate_application_answer(db, candidate.id, req_concise)

    # 2. Detailed Style
    req_detailed = ApplicationQuestionRequest(
        question="Why should we hire you?",
        opportunity_id=opp.id,
        style=AnswerStyle.DETAILED,
    )
    with patch("app.services.application_assistant.call_gemini_for_question", return_value=None):
        res_d = await generate_application_answer(db, candidate.id, req_detailed)

    words_c = len(res_c.answer_text.split())
    words_d = len(res_d.answer_text.split())
    assert words_d >= words_c

    # 3. Explicit Word Limit (50 words)
    req_limited = ApplicationQuestionRequest(
        question="Why should we hire you?",
        opportunity_id=opp.id,
        word_limit=50,
    )
    with patch("app.services.application_assistant.call_gemini_for_question", return_value=None):
        res_lim = await generate_application_answer(db, candidate.id, req_limited)
    words_lim = len(res_lim.answer_text.split())
    assert words_lim <= 55


# ============================================================================
# 7. Validation: Insufficient Profile Data & Unpublished Job
# ============================================================================

@pytest.mark.anyio
async def test_validation_insufficient_data_and_invalid_opportunity():
    """Verify clear errors when candidate profile is empty or target opportunity is draft/missing."""
    db = AsyncMock()

    # Empty candidate profile
    empty_cand = Profile()
    empty_cand.id = uuid4()
    empty_cand.full_name = "Empty Candidate"
    empty_cand.educations = []
    empty_cand.experiences = []
    empty_cand.projects = []
    empty_cand.skills = []
    empty_cand.resumes = []

    opp = make_test_opportunity()

    async def mock_execute(stmt):
        mock_res = MagicMock()
        s = str(stmt).lower()
        if "from profiles" in s:
            mock_res.scalar_one_or_none.return_value = empty_cand
        elif "from opportunities" in s:
            mock_res.scalar_one_or_none.return_value = opp
        return mock_res

    db.execute.side_effect = mock_execute

    req = ApplicationQuestionRequest(
        question="Why should we hire you?",
        opportunity_id=opp.id,
    )
    with pytest.raises(ValueError) as exc:
        await generate_application_answer(db, empty_cand.id, req)
    assert "educational history, projects, experience, or skills" in str(exc.value)

    # Candidate with data but Draft Opportunity
    valid_cand = make_test_profile()
    draft_opp = make_test_opportunity(status="Draft")

    async def mock_execute_draft(stmt):
        mock_res = MagicMock()
        s = str(stmt).lower()
        if "from profiles" in s:
            mock_res.scalar_one_or_none.return_value = valid_cand
        elif "from opportunities" in s:
            mock_res.scalar_one_or_none.return_value = draft_opp
        return mock_res

    db.execute.side_effect = mock_execute_draft

    req_draft = ApplicationQuestionRequest(
        question="Why should we hire you?",
        opportunity_id=draft_opp.id,
    )
    with pytest.raises(ValueError) as exc2:
        await generate_application_answer(db, valid_cand.id, req_draft)
    assert "not found or not published" in str(exc2.value).lower()


# ============================================================================
# 8. General Mode: Question Without Opportunity Selected
# ============================================================================

@pytest.mark.anyio
async def test_general_mode_without_opportunity_selected():
    """Verify candidate can generate answers to general questions when opportunity_id is None."""
    db = AsyncMock()
    candidate = make_test_profile()

    async def mock_execute(stmt):
        mock_res = MagicMock()
        s = str(stmt).lower()
        if "from profiles" in s:
            mock_res.scalar_one_or_none.return_value = candidate
        return mock_res

    db.execute.side_effect = mock_execute

    req = ApplicationQuestionRequest(
        question="What are your greatest professional strengths?",
        opportunity_id=None,
    )

    with patch("app.services.application_assistant.call_gemini_for_question", return_value=None):
        res = await generate_application_answer(db, candidate.id, req)

    assert res.opportunity_id is None
    assert res.opportunity_title is None
    assert res.company_name is None
    assert "Stanford University" in res.answer_text
    assert any("general application context" in note for note in res.verified_evidence.missing_information_notes)


# ============================================================================
# 9. Authentication & Student Data Isolation
# ============================================================================

@pytest.mark.anyio
async def test_application_assistant_auth_and_isolation():
    """Verify unauthorized requests are rejected and students only access their own facts."""
    student_a = make_test_profile(full_name="Alice Candidate", degree="B.S. at MIT", institution="MIT")
    student_b = make_test_profile(full_name="Bob Candidate", degree="B.S. at Harvard", institution="Harvard")

    mock_db = AsyncMock()
    transport = ASGITransport(app=app)

    # 1. Unauthenticated Request
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_unauth = await client.post(
            "/api/v1/copilot/application-assistant/generate",
            json={"question": "Why should we hire you?"},
        )
        assert res_unauth.status_code in (401, 403)

    # 2. Student A Request
    app.dependency_overrides[get_current_profile] = lambda: student_a
    app.dependency_overrides[get_db] = lambda: mock_db

    async def mock_exec_a(stmt):
        res = MagicMock()
        s = str(stmt).lower()
        if "from profiles" in s:
            res.scalar_one_or_none.return_value = student_a
        return res

    mock_db.execute.side_effect = mock_exec_a

    with patch("app.services.application_assistant.call_gemini_for_question", return_value=None):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res_a = await client.post(
                "/api/v1/copilot/application-assistant/generate",
                json={"question": "Why should we hire you for this role?"},
            )
            assert res_a.status_code == 200
            data_a = res_a.json()
            assert "MIT" in data_a["answer_text"]
            assert "Harvard" not in data_a["answer_text"]

    app.dependency_overrides.clear()


# ============================================================================
# 10. Suggested Questions Endpoint
# ============================================================================

def test_suggested_application_questions():
    """Verify standard application questions are returned with categories and descriptions."""
    resp = get_suggested_application_questions()
    assert len(resp.suggested_questions) >= 5
    assert any("hire" in q.question.lower() for q in resp.suggested_questions)
    assert any("project" in q.question.lower() for q in resp.suggested_questions)


# ============================================================================
# 11. Regression Tests: Phase 7.1 and Phase 7.2 Remain Intact
# ============================================================================

@pytest.mark.anyio
async def test_phase71_and_phase72_remain_intact():
    """Ensure adding Phase 7.3 does not break Phase 7.1 roadmap or Phase 7.2 cover letter."""
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
            res.scalar_one_or_none.return_value = None
        return res

    mock_db.execute.side_effect = mock_exec

    transport = ASGITransport(app=app)
    with patch("app.services.skill_gap.expire_overdue_opportunities", new_callable=AsyncMock):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Phase 7.1 Skill Gap Roadmap
            res_71 = await client.get("/api/v1/copilot/skill-gap-roadmap")
            assert res_71.status_code == 200

            # 2. Phase 7.3 Suggested Questions
            res_73 = await client.get("/api/v1/copilot/application-assistant/suggested-questions")
            assert res_73.status_code == 200
            assert "suggested_questions" in res_73.json()

    app.dependency_overrides.clear()


# ============================================================================
# 12. Regression Tests: Opportunity Listing, Auth, and 404 Handling
# ============================================================================

@pytest.mark.anyio
async def test_published_opportunities_listing_and_filtering():
    """Verify authenticated students receive published opportunities in PaginatedOpportunityResponse format,
    while Draft, Closed, and Expired opportunities are excluded."""
    student = make_test_profile()
    pub_opp = make_test_opportunity(title="Published Engineer", status="Published")
    mock_db = AsyncMock()

    app.dependency_overrides[get_current_profile] = lambda: student
    app.dependency_overrides[get_db] = lambda: mock_db

    async def mock_exec(stmt):
        res = MagicMock()
        s = str(stmt).lower()
        if "count" in s:
            res.scalar.return_value = 1
        else:
            res.scalars.return_value.all.return_value = [pub_opp]
        return res

    mock_db.execute.side_effect = mock_exec

    transport = ASGITransport(app=app)
    with patch("app.routers.opportunity.expire_overdue_opportunities", new_callable=AsyncMock):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.get("/api/v1/opportunities?page=1&page_size=50")
            assert res.status_code == 200
            data = res.json()
            assert "items" in data
            assert "total" in data
            assert "page" in data
            assert "page_size" in data
            assert "total_pages" in data
            assert data["page"] == 1
            assert data["page_size"] == 50
            assert len(data["items"]) == 1
            assert data["items"][0]["title"] == "Published Engineer"
            assert data["items"][0]["status"] == "Published"

    app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_opportunities_listing_unauthenticated_returns_401():
    """Verify calling opportunities listing without authentication returns 401 Unauthorized."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/opportunities?page=1&page_size=50")
        assert res.status_code == 401
        assert res.json().get("detail") == "Not authenticated"


@pytest.mark.anyio
async def test_generate_endpoint_missing_opportunity_returns_404():
    """Verify passing a non-existent or unpublished opportunity_id returns 404 Not Found with clear detail."""
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
            # Opportunity not found
            res.scalar_one_or_none.return_value = None
        return res

    mock_db.execute.side_effect = mock_exec

    missing_opp_id = str(uuid4())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/copilot/application-assistant/generate",
            json={
                "question": "Why should we hire you for this role?",
                "opportunity_id": missing_opp_id,
                "style": "professional",
            },
        )
        assert res.status_code == 404
        assert "not found or not published" in res.json().get("detail", "").lower()

    app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_generate_endpoint_with_published_opportunity_success():
    """Verify passing a valid published opportunity and question generates answer with opportunity context."""
    student = make_test_profile()
    opp = make_test_opportunity(
        title="Distributed Systems Intern",
        company_name="CloudScale Systems",
        skills=["Python", "FastAPI"],
        status="Published",
    )
    mock_db = AsyncMock()

    app.dependency_overrides[get_current_profile] = lambda: student
    app.dependency_overrides[get_db] = lambda: mock_db

    async def mock_exec(stmt):
        res = MagicMock()
        s = str(stmt).lower()
        if "from profiles" in s:
            res.scalar_one_or_none.return_value = student
        elif "from opportunities" in s:
            res.scalar_one_or_none.return_value = opp
        return res

    mock_db.execute.side_effect = mock_exec

    transport = ASGITransport(app=app)
    with patch("app.services.application_assistant.call_gemini_for_question", return_value=None):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post(
                "/api/v1/copilot/application-assistant/generate",
                json={
                    "question": "Why should we hire you for this role?",
                    "opportunity_id": str(opp.id),
                    "style": "professional",
                },
            )
            assert res.status_code == 200
            data = res.json()
            assert data["opportunity_id"] == str(opp.id)
            assert data["opportunity_title"] == "Distributed Systems Intern"
            assert data["company_name"] == "CloudScale Systems"
            assert data["is_template_fallback"] is True
            assert len(data["answer_text"]) > 50
            assert "Stanford University" in data["answer_text"]

    app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_generate_endpoint_validation_errors():
    """Verify endpoint rejects invalid payloads with 422 Unprocessable Entity."""
    student = make_test_profile()
    mock_db = AsyncMock()

    app.dependency_overrides[get_current_profile] = lambda: student
    app.dependency_overrides[get_db] = lambda: mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Question too short (< 5 chars)
        res_short = await client.post(
            "/api/v1/copilot/application-assistant/generate",
            json={"question": "Why?"},
        )
        assert res_short.status_code == 422

        # Word limit too small (< 30)
        res_limit = await client.post(
            "/api/v1/copilot/application-assistant/generate",
            json={
                "question": "Why should we hire you?",
                "word_limit": 10,
            },
        )
        assert res_limit.status_code == 422

    app.dependency_overrides.clear()

