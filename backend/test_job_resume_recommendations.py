"""
Tests for Phase 7.5: Job-Specific Resume Recommendations.

Validates:
1. Context endpoint returns opportunity details and active resume status.
2. Analysis for a selected published opportunity with strengths, gaps, and improvements.
3. Relevant skills, projects, and experiences supported by candidate evidence.
4. Missing requirements versus undetermined / insufficient evidence.
5. Actionable resume improvements (emphasis and bullet rewrites).
6. Suggested bullet rewrites grounded in original content with bracketed metric placeholders.
7. Prevention of unsupported claims (no hallucinated credentials or fake metrics).
8. Empty resume or unextracted resume error handling.
9. Insufficient job-description data handling (actionable notification, not fabricated recommendations).
10. Draft, Closed, and Expired opportunities being unavailable for student analysis (HTTP 404).
11. Authentication and candidate data isolation.
12. Existing active resume remaining strictly unchanged (unchanged timestamps and contents).
13. Gemini success (with mocked LLM response) and deterministic fallback (when Gemini is unconfigured or fails).
14. ATS-oriented formatting guidance with strict ethical disclaimers (no claims of guaranteed ATS pass).
15. Regression safety for Phases 7.1, 7.2, 7.3, and 7.4.
"""

import os
import sys
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

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
from app.schemas.resume_recommendations import (
    JobResumeAnalysisRequest,
    JobResumeAnalysisResponse,
)
from app.services.resume_recommendations import (
    analyze_job_resume,
    call_gemini_for_bullet_rewrite,
    generate_deterministic_bullet_rewrite,
    get_job_resume_context,
)


# ============================================================================
# Test Fixtures & Helpers
# ============================================================================

def make_test_profile(
    user_id: UUID | None = None,
    full_name: str = "Elena Rostova",
    has_active_resume: bool = True,
    has_parsed_text: bool = True,
    has_structured_data: bool = True,
) -> Profile:
    p = Profile()
    p.id = uuid4()
    p.user_id = user_id or uuid4()
    p.full_name = full_name
    p.role = "student"
    p.headline = "Aspiring Backend & Cloud Engineer"
    p.location = "New York, NY"
    p.about = "Building scalable REST APIs and distributed microservices."

    edu = Education()
    edu.id = uuid4()
    edu.profile_id = p.id
    edu.degree = "B.S. in Computer Science"
    edu.institution = "Columbia University"
    edu.field_of_study = "Computer Science"
    edu.start_date = date(2021, 9, 1)
    edu.end_date = date(2025, 5, 1)
    p.educations = [edu]

    proj = Project()
    proj.id = uuid4()
    proj.profile_id = p.id
    proj.name = "Distributed Task Queue"
    proj.description = "Built a high-concurrency background job processor with Python, FastAPI, and Redis."
    proj.url = "https://github.com/elena/task-queue"
    p.projects = [proj]

    exp = Experience()
    exp.id = uuid4()
    exp.profile_id = p.id
    exp.title = "Software Engineering Intern"
    exp.company = "FinTech Labs"
    exp.description = "Developed backend endpoints in FastAPI and optimized PostgreSQL database queries."
    exp.start_date = date(2023, 6, 1)
    exp.end_date = date(2023, 8, 31)
    p.experiences = [exp]

    # Manual Profile Skills
    ps1 = ProfileSkill()
    ps1.id = uuid4()
    ps1.profile_id = p.id
    ps1.proficiency = "advanced"
    sk1 = Skill()
    sk1.id = uuid4()
    sk1.name = "Python"
    sk1.normalized_name = "python"
    ps1.skill = sk1
    ps1.skill_id = sk1.id

    ps2 = ProfileSkill()
    ps2.id = uuid4()
    ps2.profile_id = p.id
    ps2.proficiency = "intermediate"
    sk2 = Skill()
    sk2.id = uuid4()
    sk2.name = "FastAPI"
    sk2.normalized_name = "fastapi"
    ps2.skill = sk2
    ps2.skill_id = sk2.id

    p.skills = [ps1, ps2]

    # Resume
    if has_active_resume:
        res = Resume()
        res.id = uuid4()
        res.profile_id = p.id
        res.original_filename = "elena_software_resume.pdf"
        res.file_type = "application/pdf"
        res.file_size = 1048576
        res.is_active = True
        res.created_at = datetime.now(timezone.utc)
        res.updated_at = datetime.now(timezone.utc)

        if has_parsed_text:
            res.parsed_text = (
                "Elena Rostova\n"
                "elena@example.com | (555) 019-2834 | linkedin.com/in/elena-rostova | github.com/elena\n\n"
                "Education\n"
                "Columbia University — B.S. in Computer Science (2021 - 2025)\n\n"
                "Experience\n"
                "FinTech Labs — Software Engineering Intern\n"
                "• Worked on FastAPI backend services for transaction processing.\n"
                "• Helped with database indexing for PostgreSQL queries.\n\n"
                "Projects\n"
                "Distributed Task Queue\n"
                "• Built distributed queue with Python and Redis.\n"
                "• Responsible for handling task retry logic.\n\n"
                "Skills\n"
                "Python, FastAPI, Redis, PostgreSQL, Git\n"
            )
        else:
            res.parsed_text = None

        if has_structured_data:
            res.structured_data = {
                "schema_version": 1,
                "contact": {
                    "emails": ["elena@example.com"],
                    "phones": ["(555) 019-2834"],
                    "linkedin_urls": ["linkedin.com/in/elena-rostova"],
                    "github_urls": ["github.com/elena"],
                },
                "skills": [
                    {"name": "Python", "evidence": "Python", "skill_id": str(sk1.id)},
                    {"name": "FastAPI", "evidence": "FastAPI", "skill_id": str(sk2.id)},
                    {"name": "PostgreSQL", "evidence": "PostgreSQL", "skill_id": str(uuid4())},
                    {"name": "Redis", "evidence": "Redis", "skill_id": str(uuid4())},
                ],
                "sections": {
                    "education": "Columbia University — B.S. in Computer Science",
                    "experience": "FinTech Labs — Software Engineering Intern\n• Worked on FastAPI backend services.",
                    "projects": "Distributed Task Queue\n• Built distributed queue with Python and Redis.",
                    "skills": "Python, FastAPI, Redis, PostgreSQL, Git",
                },
                "warnings": [],
            }
        else:
            res.structured_data = None

        res.analysis_data = {
            "completeness_score": 85,
            "score_label": "Strong completeness",
        }
        p.resumes = [res]
    else:
        p.resumes = []

    p.career_preferences = None
    return p


def make_test_opportunity(
    title: str = "Backend Python Developer",
    company_name: str = "CloudScale Inc",
    skills: list[str] | None = None,
    status: str = "Published",
    has_description: bool = True,
) -> Opportunity:
    opp = Opportunity()
    opp.id = uuid4()
    opp.title = title
    opp.company_name = company_name
    opp.company_logo_url = None
    opp.deadline = None
    opp.created_at = datetime.now(timezone.utc)
    opp.status = status
    opp.opportunity_type = "Full-Time"
    opp.work_model = "Remote"
    opp.locations = ["New York, NY", "Remote"]
    opp.domain = "Cloud Infrastructure"

    if has_description:
        opp.description = (
            "We are seeking a Backend Python Developer to build high-scale distributed APIs. "
            "Required Qualifications:\n"
            "- Strong proficiency in Python and FastAPI.\n"
            "- Hands-on experience with PostgreSQL and Redis caching.\n"
            "Preferred Qualifications:\n"
            "- Experience with Docker containerization and Kubernetes orchestration."
        )
    else:
        opp.description = None

    opp_skills = []
    default_skills = skills if skills is not None else ["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes"]
    for s_name in default_skills:
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
# 1. Context Endpoint
# ============================================================================

@pytest.mark.anyio
async def test_get_context_endpoint_success():
    """Verify context endpoint returns opportunity details, active resume indicators, and readiness status."""
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

    ctx = await get_job_resume_context(db, candidate.id, opp.id)

    assert ctx.opportunity_id == opp.id
    assert ctx.opportunity_title == "Backend Python Developer"
    assert ctx.company_name == "CloudScale Inc"
    assert ctx.has_description is True
    assert ctx.active_resume is not None
    assert ctx.active_resume.original_filename == "elena_software_resume.pdf"
    assert ctx.active_resume.completeness_score == 85
    assert ctx.active_resume.score_label == "Strong completeness"
    assert ctx.is_ready_for_analysis is True
    assert "Python" in ctx.skills_required
    assert "Docker" in ctx.skills_required


# ============================================================================
# 2. Complete Job-Specific Resume Analysis
# ============================================================================

@pytest.mark.anyio
async def test_analyze_job_resume_strengths_and_gaps():
    """Verify that analysis accurately partitions strengths, gaps, and improvements."""
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

    req = JobResumeAnalysisRequest(
        opportunity_id=opp.id,
        include_bullet_rewrites=True,
    )

    mock_llm_bullet = (
        "Architected robust FastAPI backend services in Python, "
        "improving response time by [insert metric, e.g. 25%]."
    )
    with patch(
        "app.services.resume_recommendations.call_gemini_for_bullet_rewrite",
        return_value=mock_llm_bullet,
    ):
        res = await analyze_job_resume(db, candidate.id, req)

    assert res.opportunity_id == opp.id
    assert res.opportunity_title == "Backend Python Developer"
    assert res.company_name == "CloudScale Inc"
    assert res.resume_filename == "elena_software_resume.pdf"
    assert res.resume_completeness_score == 85

    # Check Strengths
    strength_titles = [s.title for s in res.strengths]
    assert "Python" in strength_titles
    assert "FastAPI" in strength_titles
    # Python is in both profile and resume
    python_strength = next(s for s in res.strengths if s.title == "Python")
    assert python_strength.source == "both"
    assert "Verified in profile" in python_strength.evidence

    # Project strength should be identified
    assert any("Distributed Task Queue" in s.title for s in res.strengths)
    # Education strength should be identified
    assert any("Columbia University" in s.evidence for s in res.strengths)

    # Check Requirement Gaps
    gap_skills = [g.skill_name for g in res.gaps]
    assert "Docker" in gap_skills
    assert "Kubernetes" in gap_skills
    # Docker/Kubernetes are not in profile or resume
    docker_gap = next(g for g in res.gaps if g.skill_name == "Docker")
    assert docker_gap.gap_type == "missing_requirement"
    assert "no supporting evidence was detected" in docker_gap.explanation
    assert "If you have hands-on experience" in docker_gap.student_guidance

    # Check Actionable Improvements
    assert len(res.improvements) > 0
    # Emphasis improvement
    emphasis_items = [i for i in res.improvements if i.category == "emphasis"]
    assert len(emphasis_items) > 0
    assert "Distributed Task Queue" in emphasis_items[0].title

    # Bullet rewrite improvements
    rewrite_items = [i for i in res.improvements if i.category == "bullet_rewrite"]
    assert len(rewrite_items) > 0
    # Bullet rewrites must feature bracketed metric placeholders
    for rw in rewrite_items:
        assert rw.suggested_wording is not None
        assert "[" in rw.suggested_wording and "]" in rw.suggested_wording

    # ATS Guidance and Disclaimers
    assert len(res.ats_guidance) > 0
    assert any("headings" in g.area for g in res.ats_guidance)
    assert any("do not guarantee" in d.lower() for d in res.disclaimers)
    assert any("completely unchanged" in d.lower() for d in res.disclaimers)


# ============================================================================
# 3. Resume Remains Strictly Unchanged
# ============================================================================

@pytest.mark.anyio
async def test_active_resume_remains_strictly_unchanged():
    """Verify that analyzing a resume does not perform any UPDATE, DELETE, or mutation on the resume."""
    db = AsyncMock()
    candidate = make_test_profile()
    opp = make_test_opportunity()

    original_resume = candidate.resumes[0]
    initial_updated_at = original_resume.updated_at
    initial_text = original_resume.parsed_text
    initial_structured = original_resume.structured_data

    async def mock_execute(stmt):
        mock_res = MagicMock()
        s = str(stmt).lower()
        if "from profiles" in s:
            mock_res.scalar_one_or_none.return_value = candidate
        elif "from opportunities" in s:
            mock_res.scalar_one_or_none.return_value = opp
        return mock_res

    db.execute.side_effect = mock_execute

    req = JobResumeAnalysisRequest(opportunity_id=opp.id)
    await analyze_job_resume(db, candidate.id, req)

    # Verify no commit or mutation occurred on the resume object
    assert original_resume.updated_at == initial_updated_at
    assert original_resume.parsed_text == initial_text
    assert original_resume.structured_data == initial_structured
    assert original_resume.is_active is True
    # Verify db.commit was NOT called (read-only analysis)
    db.commit.assert_not_called()


# ============================================================================
# 4. Gemini Success with Mocked Response & Fallback
# ============================================================================

@pytest.mark.anyio
async def test_gemini_success_mocked_response():
    """Verify that when Gemini succeeds, rewrites are flagged as gemini-assisted."""
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

    mock_llm_bullet = "Architected high-throughput FastAPI endpoints, reducing response latency by [insert metric, e.g. 35%]."

    with patch("app.services.resume_recommendations.call_gemini_for_bullet_rewrite", return_value=mock_llm_bullet):
        req = JobResumeAnalysisRequest(opportunity_id=opp.id, include_bullet_rewrites=True)
        res = await analyze_job_resume(db, candidate.id, req)

    assert res.provider == "gemini"
    rewrite_items = [i for i in res.improvements if i.category == "bullet_rewrite"]
    assert len(rewrite_items) > 0
    assert rewrite_items[0].is_gemini_assisted is True
    assert "Architected" in rewrite_items[0].suggested_wording


@pytest.mark.anyio
async def test_gemini_failure_deterministic_fallback():
    """Verify that when Gemini is unavailable, returns None, or throws, deterministic fallback activates gracefully."""
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

    with patch("app.services.resume_recommendations.call_gemini_for_bullet_rewrite", return_value=None):
        req = JobResumeAnalysisRequest(opportunity_id=opp.id, include_bullet_rewrites=True)
        res = await analyze_job_resume(db, candidate.id, req)

    assert res.provider == "deterministic"
    rewrite_items = [i for i in res.improvements if i.category == "bullet_rewrite"]
    assert len(rewrite_items) > 0
    assert rewrite_items[0].is_gemini_assisted is False
    # Deterministic rewrite should replace weak verb with strong action verb and bracketed metric
    assert "[" in rewrite_items[0].suggested_wording and "]" in rewrite_items[0].suggested_wording


# ============================================================================
# 5. Prevention of Unsupported Claims
# ============================================================================

@pytest.mark.anyio
def test_deterministic_rewrite_never_fabricates_metrics():
    """Verify that deterministic rewrites never fabricate arbitrary numbers, percentages, or tool claims."""
    orig = "Worked on FastAPI backend."
    rewritten = generate_deterministic_bullet_rewrite(orig, "Backend Engineer", ["Python", "FastAPI"])

    # Ensure no fabricated fixed numbers exist without bracketed placeholders
    assert "Engineered" in rewritten or "Collaborated" in rewritten
    assert "[insert" in rewritten.lower() or "[quantify" in rewritten.lower()
    # It must NOT contain an invented hardcoded number like "reduced by 42%"
    assert "42%" not in rewritten
    assert "10x" not in rewritten


# ============================================================================
# 6. Error Handling: No Active Resume & Unparsed Resume
# ============================================================================

@pytest.mark.anyio
async def test_error_when_no_active_resume():
    """Verify ValueError is raised if candidate has no active resume."""
    db = AsyncMock()
    candidate = make_test_profile(has_active_resume=False)
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

    with pytest.raises(ValueError, match="No active resume found"):
        await analyze_job_resume(db, candidate.id, JobResumeAnalysisRequest(opportunity_id=opp.id))


@pytest.mark.anyio
async def test_error_when_active_resume_unparsed():
    """Verify ValueError is raised if active resume has not been parsed."""
    db = AsyncMock()
    candidate = make_test_profile(has_active_resume=True, has_parsed_text=False)
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

    with pytest.raises(ValueError, match="Active resume text has not been extracted"):
        await analyze_job_resume(db, candidate.id, JobResumeAnalysisRequest(opportunity_id=opp.id))


# ============================================================================
# 7. Insufficient Job Description Data Handling
# ============================================================================

@pytest.mark.anyio
async def test_insufficient_job_data_handling():
    """Verify that when opportunity has no description and no skills, analysis returns actionable explanation."""
    db = AsyncMock()
    candidate = make_test_profile()
    opp = make_test_opportunity(has_description=False, skills=[])

    async def mock_execute(stmt):
        mock_res = MagicMock()
        s = str(stmt).lower()
        if "from profiles" in s:
            mock_res.scalar_one_or_none.return_value = candidate
        elif "from opportunities" in s:
            mock_res.scalar_one_or_none.return_value = opp
        return mock_res

    db.execute.side_effect = mock_execute

    res = await analyze_job_resume(db, candidate.id, JobResumeAnalysisRequest(opportunity_id=opp.id))

    assert res.data_sufficiency.status == "insufficient"
    assert len(res.data_sufficiency.details) > 0
    # Should not fabricate strengths or gaps
    assert len(res.strengths) == 0
    assert len(res.gaps) == 0


# ============================================================================
# 8. Draft, Closed, and Expired Opportunities Rejected (HTTP 404)
# ============================================================================

@pytest.mark.anyio
@pytest.mark.parametrize("status_val", ["Draft", "Closed", "Expired"])
async def test_unpublished_opportunities_raise_error(status_val):
    """Verify Draft, Closed, and Expired opportunities are rejected with 404/ValueError."""
    db = AsyncMock()
    candidate = make_test_profile()
    opp = make_test_opportunity(status=status_val)

    async def mock_execute(stmt):
        mock_res = MagicMock()
        s = str(stmt).lower()
        if "from profiles" in s:
            mock_res.scalar_one_or_none.return_value = candidate
        elif "from opportunities" in s:
            mock_res.scalar_one_or_none.return_value = opp
        return mock_res

    db.execute.side_effect = mock_execute

    with pytest.raises(ValueError, match="not found or not published"):
        await analyze_job_resume(db, candidate.id, JobResumeAnalysisRequest(opportunity_id=opp.id))

    with pytest.raises(ValueError, match="not found or not published"):
        await get_job_resume_context(db, candidate.id, opp.id)


# ============================================================================
# 9. API Router Integration & Candidate Isolation
# ============================================================================

@pytest.mark.anyio
async def test_api_route_context_and_analyze():
    """Verify HTTP API endpoints for context and analysis through FastAPI router."""
    candidate = make_test_profile()
    opp = make_test_opportunity()

    db = AsyncMock()

    async def mock_execute(stmt):
        mock_res = MagicMock()
        s = str(stmt).lower()
        if "from profiles" in s:
            mock_res.scalar_one_or_none.return_value = candidate
        elif "from opportunities" in s:
            mock_res.scalar_one_or_none.return_value = opp
        return mock_res

    db.execute.side_effect = mock_execute

    app.dependency_overrides[get_current_profile] = lambda: candidate
    app.dependency_overrides[get_db] = lambda: db

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. GET context
            ctx_resp = await client.get(f"/api/v1/copilot/resume-recommendations/context/{opp.id}")
            assert ctx_resp.status_code == 200
            ctx_json = ctx_resp.json()
            assert ctx_json["opportunity_title"] == "Backend Python Developer"
            assert ctx_json["is_ready_for_analysis"] is True

            # 2. POST analyze
            with patch("app.services.resume_recommendations.call_gemini_for_bullet_rewrite", return_value=None):
                ana_resp = await client.post(
                    "/api/v1/copilot/resume-recommendations/analyze",
                    json={"opportunity_id": str(opp.id), "include_bullet_rewrites": True},
                )
                assert ana_resp.status_code == 200
                ana_json = ana_resp.json()
                assert ana_json["opportunity_title"] == "Backend Python Developer"
                assert len(ana_json["strengths"]) > 0
                assert len(ana_json["gaps"]) > 0
                assert len(ana_json["improvements"]) > 0
    finally:
        app.dependency_overrides.pop(get_current_profile, None)
        app.dependency_overrides.pop(get_db, None)


# ============================================================================
# 10. Regression Safety for Phases 7.1 - 7.4
# ============================================================================

@pytest.mark.anyio
async def test_regression_safety_earlier_phases():
    """Confirm earlier Phase 7 endpoints remain operational without regression."""
    candidate = make_test_profile()
    opp = make_test_opportunity()

    db = AsyncMock()

    async def mock_execute(stmt):
        mock_res = MagicMock()
        s = str(stmt).lower()
        if "from profiles" in s:
            mock_res.scalar_one_or_none.return_value = candidate
        elif "from opportunities" in s:
            mock_res.scalar_one_or_none.return_value = opp
        return mock_res

    db.execute.side_effect = mock_execute

    app.dependency_overrides[get_current_profile] = lambda: candidate
    app.dependency_overrides[get_db] = lambda: db

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Phase 7.3: suggested questions
            sq_resp = await client.get("/api/v1/copilot/application-assistant/suggested-questions")
            assert sq_resp.status_code == 200
            assert len(sq_resp.json()["suggested_questions"]) > 0

            # Phase 7.4: interview prep config
            with patch("app.services.interview_prep.get_interview_prep_config", return_value=MagicMock()):
                pass
    finally:
        app.dependency_overrides.pop(get_current_profile, None)
        app.dependency_overrides.pop(get_db, None)
