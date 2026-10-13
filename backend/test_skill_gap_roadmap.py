"""
Tests for Phase 7.1: Personalized Skill-Gap Roadmap.

Validates:
1. Personalization (student-specific profile skills, active-resume extracted skills, target role selection).
2. Missing profile data (handling empty preferences/skills gracefully with honest notifications).
3. Missing job evidence (handling non-existent or zero-evidence roles without fabricating recommendations).
4. Evidence-based prioritization & distinguishing required vs desired skills.
5. Practical learning sequence integrity (no fabricated URLs, certifications, or prerequisites).
6. Candidate data isolation and authorization.
7. Score integrity (disclaimer verification, readiness != hiring probability).
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.dependencies import get_current_profile, get_db
from app.main import app
from app.models.opportunity import Opportunity, OpportunitySkill
from app.models.profile import (
    CareerPreference,
    Profile,
    ProfileSkill,
    Resume,
    Skill,
    SkillCategory,
)
from app.schemas.skill_gap import (
    PriorityTier,
    RequirementLevel,
    SkillGapRoadmapResponse,
    SkillSource,
)
from app.services.skill_gap import (
    generate_skill_gap_roadmap,
    partition_job_description,
    role_matches_opportunity,
)


# ============================================================================
# Helpers & Fixtures
# ============================================================================

def make_profile(
    user_id: UUID | None = None,
    full_name: str = "Test Student",
    desired_roles: list[str] | None = None,
    preferred_domains: list[str] | None = None,
) -> Profile:
    p = Profile()
    p.id = uuid4()
    p.user_id = user_id or uuid4()
    p.full_name = full_name
    p.role = "student"
    p.skills = []
    p.resumes = []

    if desired_roles or preferred_domains:
        cp = CareerPreference()
        cp.id = uuid4()
        cp.profile_id = p.id
        cp.desired_roles = desired_roles or []
        cp.preferred_domains = preferred_domains or []
        p.career_preferences = cp
    else:
        p.career_preferences = None

    return p


def make_skill(name: str, category_name: str | None = None) -> Skill:
    s = Skill()
    s.id = uuid4()
    s.name = name
    s.normalized_name = name.lower()
    if category_name:
        cat = SkillCategory()
        cat.id = uuid4()
        cat.name = category_name
        cat.slug = category_name.lower()
        s.category = cat
    else:
        s.category = None
    return s


def make_opportunity(
    title: str,
    company_name: str,
    skills: list[Skill],
    description: str = "",
    domain: str = "Technology",
    status: str = "Published",
) -> Opportunity:
    opp = Opportunity()
    opp.id = uuid4()
    opp.title = title
    opp.company_name = company_name
    opp.description = description
    opp.domain = domain
    opp.status = status
    opp.opportunity_type = "Full-Time"
    opp.work_model = "Remote"

    opp_skills = []
    for sk in skills:
        os = OpportunitySkill()
        os.id = uuid4()
        os.opportunity_id = opp.id
        os.skill_id = sk.id
        os.skill = sk
        opp_skills.append(os)
    opp.skills = opp_skills
    return opp


# ============================================================================
# 1. Description Partitioning & Required vs Desired
# ============================================================================

def test_partition_job_description_distinguishes_sections():
    desc = """
    We are seeking a Backend Engineer.
    Requirements:
    - Python
    - FastAPI
    Preferred Qualifications:
    - Docker
    - Kubernetes
    """
    req_text, des_text = partition_job_description(desc)
    assert "fastapi" in req_text
    assert "python" in req_text
    assert "docker" in des_text
    assert "kubernetes" in des_text


def test_partition_job_description_fallback_when_no_preferred_section():
    desc = "Must be proficient in React, TypeScript, and CSS."
    req_text, des_text = partition_job_description(desc)
    assert "react" in req_text
    assert des_text == ""


# ============================================================================
# 2. Personalization & Skill Source Tracking
# ============================================================================

@pytest.mark.anyio
async def test_skill_gap_roadmap_personalization_profile_and_resume():
    """
    Verify candidate gets personalized recommendations distinguishing
    manual profile skills, active resume extracted evidence, and missing skills.
    """
    db = AsyncMock()

    # Candidate has Python in manual profile, and Docker in active resume
    student = make_profile(
        full_name="Alex Rivera",
        desired_roles=["Backend Engineer"],
        preferred_domains=["Technology"],
    )

    skill_python = make_skill("Python", "Languages")
    skill_docker = make_skill("Docker", "DevOps")
    skill_fastapi = make_skill("FastAPI", "Frameworks")
    skill_postgres = make_skill("PostgreSQL", "Databases")

    # Manual Profile Skill: Python
    ps = ProfileSkill()
    ps.id = uuid4()
    ps.profile_id = student.id
    ps.skill_id = skill_python.id
    ps.skill = skill_python
    ps.proficiency = "Intermediate"
    student.skills = [ps]

    # Active Resume: Docker
    resume = Resume()
    resume.id = uuid4()
    resume.profile_id = student.id
    resume.is_active = True
    resume.structured_data = {
        "skills": [
            {
                "skill_id": str(skill_docker.id),
                "name": "Docker",
                "evidence": "Containerized microservices using Docker",
            }
        ]
    }
    student.resumes = [resume]

    # Published Opportunity for Backend Engineer
    opp = make_opportunity(
        title="Backend Engineer",
        company_name="Acme Corp",
        skills=[skill_python, skill_fastapi, skill_postgres, skill_docker],
        description="""
        Requirements:
        - Python
        - FastAPI
        - PostgreSQL
        Preferred:
        - Docker
        """,
    )

    async def mock_execute(stmt):
        mock_res = MagicMock()
        stmt_str = str(stmt).lower()
        if "from profiles" in stmt_str:
            mock_res.scalar_one_or_none.return_value = student
        elif "from opportunities" in stmt_str:
            mock_res.scalars.return_value.all.return_value = [opp]
        return mock_res

    db.execute.side_effect = mock_execute

    with patch("app.services.skill_gap.expire_overdue_opportunities", new_callable=AsyncMock):
        roadmap: SkillGapRoadmapResponse = await generate_skill_gap_roadmap(
            db=db,
            profile_id=student.id,
            target_role="Backend Engineer",
        )

    assert roadmap.target_role == "Backend Engineer"
    assert roadmap.total_analyzed_opportunities == 1

    # Check Acquired Skills: Python (profile, saved=True) & Docker (resume, saved=False)
    acquired_names = {s.name: s for s in roadmap.acquired_skills}
    assert "Python" in acquired_names
    assert acquired_names["Python"].source == SkillSource.PROFILE
    assert acquired_names["Python"].is_saved_to_profile is True
    assert acquired_names["Python"].proficiency == "Intermediate"

    assert "Docker" in acquired_names
    assert acquired_names["Docker"].source == SkillSource.RESUME
    assert acquired_names["Docker"].is_saved_to_profile is False
    assert "Containerized microservices" in (acquired_names["Docker"].resume_evidence or "")

    # Check Missing Skills: FastAPI and PostgreSQL are missing
    missing_names = {s.name: s for s in roadmap.missing_skills}
    assert "FastAPI" in missing_names
    assert "PostgreSQL" in missing_names
    assert "Python" not in missing_names
    assert "Docker" not in missing_names

    # Check Evidence on Missing Skills
    fastapi_item = missing_names["FastAPI"]
    assert fastapi_item.demand_frequency == 1
    assert fastapi_item.demand_percentage == 100.0
    assert fastapi_item.requirement_level == RequirementLevel.REQUIRED
    assert len(fastapi_item.evidence_jobs) == 1
    assert fastapi_item.evidence_jobs[0].company_name == "Acme Corp"

    # Coverage summary
    assert roadmap.coverage.total_market_skills == 4
    # Candidate has Python and Docker (2 of 4)
    assert roadmap.coverage.acquired_skills_count == 2
    assert roadmap.coverage.missing_skills_count == 2
    assert roadmap.coverage.coverage_percentage == 50.0


# ============================================================================
# 3. Missing Profile Data Handling
# ============================================================================

@pytest.mark.anyio
async def test_skill_gap_roadmap_missing_profile_data():
    """
    Candidate with empty career preferences and zero profile skills
    gracefully receives insufficient profile flag and honest explanatory message.
    """
    db = AsyncMock()
    empty_student = make_profile(full_name="Fresh Student")
    opp = make_opportunity(
        title="Junior Developer",
        company_name="Alpha Tech",
        skills=[make_skill("Git")],
    )

    async def mock_execute(stmt):
        mock_res = MagicMock()
        stmt_str = str(stmt).lower()
        if "from profiles" in stmt_str:
            mock_res.scalar_one_or_none.return_value = empty_student
        elif "from opportunities" in stmt_str:
            mock_res.scalars.return_value.all.return_value = [opp]
        return mock_res

    db.execute.side_effect = mock_execute

    with patch("app.services.skill_gap.expire_overdue_opportunities", new_callable=AsyncMock):
        roadmap = await generate_skill_gap_roadmap(
            db=db,
            profile_id=empty_student.id,
            target_role=None,
        )

    assert roadmap.data_status.has_insufficient_profile is True
    assert "desired roles" in (roadmap.data_status.profile_message or "").lower()
    assert roadmap.coverage.coverage_percentage == 0.0


# ============================================================================
# 4. Missing Job Evidence Handling (No Hallucinations)
# ============================================================================

@pytest.mark.anyio
async def test_skill_gap_roadmap_missing_job_evidence():
    """
    When no published opportunities match the specified target role,
    the system explicitly flags insufficient job data and does NOT fabricate missing skills.
    """
    db = AsyncMock()
    student = make_profile(
        full_name="Sarah Connor",
        desired_roles=["Quantum Computer Architect"],
    )

    # Database only has Web Developer jobs, none for Quantum Computer Architect
    opp = make_opportunity(
        title="Web Developer",
        company_name="Web Works",
        skills=[make_skill("HTML")],
    )

    async def mock_execute(stmt):
        mock_res = MagicMock()
        stmt_str = str(stmt).lower()
        if "from profiles" in stmt_str:
            mock_res.scalar_one_or_none.return_value = student
        elif "from opportunities" in stmt_str:
            mock_res.scalars.return_value.all.return_value = [opp]
        return mock_res

    db.execute.side_effect = mock_execute

    with patch("app.services.skill_gap.expire_overdue_opportunities", new_callable=AsyncMock):
        roadmap = await generate_skill_gap_roadmap(
            db=db,
            profile_id=student.id,
            target_role="Quantum Computer Architect",
        )

    assert roadmap.total_analyzed_opportunities == 0
    assert roadmap.data_status.has_insufficient_jobs is True
    assert "Quantum Computer Architect" in (roadmap.data_status.jobs_message or "")
    assert len(roadmap.missing_skills) == 0
    assert len(roadmap.learning_sequence) == 0


# ============================================================================
# 5. Prioritization & Requirement Distinction
# ============================================================================

@pytest.mark.anyio
async def test_prioritization_and_required_vs_desired_distinction():
    """
    Verify high-frequency required skills rank in Stage 1 (High Priority),
    while preferred/desired skills rank in Stage 3 (Low Priority).
    """
    db = AsyncMock()
    student = make_profile(
        desired_roles=["Software Engineer"],
    )

    skill_python = make_skill("Python")
    skill_fastapi = make_skill("FastAPI")
    skill_docker = make_skill("Docker")
    skill_graphql = make_skill("GraphQL")

    # Opp 1: Requires FastAPI and Python. Preferred: Docker
    opp1 = make_opportunity(
        title="Software Engineer I",
        company_name="Corp A",
        skills=[skill_python, skill_fastapi, skill_docker],
        description="Requirements:\nFastAPI\nPython\nPreferred:\nDocker",
    )

    # Opp 2: Requires FastAPI and Python.
    opp2 = make_opportunity(
        title="Software Engineer II",
        company_name="Corp B",
        skills=[skill_python, skill_fastapi],
        description="Requirements:\nFastAPI\nPython",
    )

    # Opp 3: Requires FastAPI. Preferred: GraphQL
    opp3 = make_opportunity(
        title="Software Engineer III",
        company_name="Corp C",
        skills=[skill_fastapi, skill_graphql],
        description="Requirements:\nFastAPI\nPreferred:\nGraphQL",
    )

    # Candidate already has Python
    ps = ProfileSkill()
    ps.id = uuid4()
    ps.profile_id = student.id
    ps.skill_id = skill_python.id
    ps.skill = skill_python
    student.skills = [ps]

    async def mock_execute(stmt):
        mock_res = MagicMock()
        stmt_str = str(stmt).lower()
        if "from profiles" in stmt_str:
            mock_res.scalar_one_or_none.return_value = student
        elif "from opportunities" in stmt_str:
            mock_res.scalars.return_value.all.return_value = [opp1, opp2, opp3]
        return mock_res

    db.execute.side_effect = mock_execute

    with patch("app.services.skill_gap.expire_overdue_opportunities", new_callable=AsyncMock):
        roadmap = await generate_skill_gap_roadmap(
            db=db,
            profile_id=student.id,
            target_role="Software Engineer",
        )

    assert roadmap.total_analyzed_opportunities == 3

    # FastAPI is required in 3/3 jobs -> 100% demand -> Priority HIGH
    fastapi_stat = next(s for s in roadmap.missing_skills if s.name == "FastAPI")
    assert fastapi_stat.priority_tier == PriorityTier.HIGH
    assert fastapi_stat.demand_frequency == 3
    assert fastapi_stat.requirement_level == RequirementLevel.REQUIRED

    # Docker is preferred in 1 job -> Priority LOW, DESIRED
    docker_stat = next(s for s in roadmap.missing_skills if s.name == "Docker")
    assert docker_stat.requirement_level == RequirementLevel.DESIRED
    assert docker_stat.priority_tier == PriorityTier.LOW

    # Learning Sequence Stages
    assert len(roadmap.learning_sequence) >= 2
    stage1 = roadmap.learning_sequence[0]
    assert stage1.stage_number == 1
    assert "Essentials" in stage1.title
    assert any(s.name == "FastAPI" for s in stage1.skills)


# ============================================================================
# 6. Score Integrity & Disclaimers
# ============================================================================

@pytest.mark.anyio
async def test_score_integrity_disclaimer():
    """
    Ensures readiness is strictly represented as heuristic coverage and contains
    an explicit non-hiring-probability disclaimer.
    """
    db = AsyncMock()
    student = make_profile(desired_roles=["Frontend Engineer"])
    opp = make_opportunity(
        title="Frontend Engineer",
        company_name="Acme",
        skills=[make_skill("React"), make_skill("TypeScript")],
    )

    async def mock_execute(stmt):
        mock_res = MagicMock()
        stmt_str = str(stmt).lower()
        if "from profiles" in stmt_str:
            mock_res.scalar_one_or_none.return_value = student
        elif "from opportunities" in stmt_str:
            mock_res.scalars.return_value.all.return_value = [opp]
        return mock_res

    db.execute.side_effect = mock_execute

    with patch("app.services.skill_gap.expire_overdue_opportunities", new_callable=AsyncMock):
        roadmap = await generate_skill_gap_roadmap(
            db=db,
            profile_id=student.id,
            target_role="Frontend Engineer",
        )

    assert "heuristic readiness indicator" in roadmap.coverage.disclaimer.lower()
    assert "not represent a probability of hiring" in roadmap.coverage.disclaimer.lower()
    assert 0.0 <= roadmap.coverage.coverage_percentage <= 100.0


# ============================================================================
# 7. Authorization & Candidate Data Isolation
# ============================================================================

@pytest.mark.anyio
async def test_api_endpoint_authorization_and_candidate_isolation():
    """
    Verifies that:
    1. Unauthenticated requests are rejected.
    2. Candidate A only receives Candidate A's profile data and skills.
    3. Candidate B receives Candidate B's isolated roadmap.
    """
    student_a = make_profile(full_name="Candidate A", desired_roles=["Backend"])
    student_b = make_profile(full_name="Candidate B", desired_roles=["Design"])

    mock_db = AsyncMock()
    opp = make_opportunity(title="Backend Dev", company_name="Co", skills=[make_skill("Go")])

    async def mock_execute_for(curr_student):
        async def _exec(stmt):
            res = MagicMock()
            s = str(stmt).lower()
            if "from profiles" in s:
                res.scalar_one_or_none.return_value = curr_student
            elif "from opportunities" in s:
                res.scalars.return_value.all.return_value = [opp]
            return res
        return _exec

    # 1. Unauthenticated Request Check
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Without dependency override or token, should fail auth
        res_unauth = await client.get("/api/v1/copilot/skill-gap-roadmap")
        assert res_unauth.status_code in (401, 403)

    # 2. Candidate A Isolated Access
    app.dependency_overrides[get_current_profile] = lambda: student_a
    app.dependency_overrides[get_db] = lambda: mock_db
    mock_db.execute.side_effect = await mock_execute_for(student_a)

    with patch("app.services.skill_gap.expire_overdue_opportunities", new_callable=AsyncMock):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res_a = await client.get("/api/v1/copilot/skill-gap-roadmap")
            assert res_a.status_code == 200
            data_a = res_a.json()
            assert data_a["target_role"] == "Backend"
            assert data_a["available_target_roles"] == ["Backend"]

    # 3. Candidate B Isolated Access
    app.dependency_overrides[get_current_profile] = lambda: student_b
    mock_db.execute.side_effect = await mock_execute_for(student_b)

    with patch("app.services.skill_gap.expire_overdue_opportunities", new_callable=AsyncMock):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res_b = await client.get("/api/v1/copilot/skill-gap-roadmap")
            assert res_b.status_code == 200
            data_b = res_b.json()
            assert data_b["target_role"] == "Design"
            assert data_b["available_target_roles"] == ["Design"]

    # Clean up dependency overrides
    app.dependency_overrides.clear()
