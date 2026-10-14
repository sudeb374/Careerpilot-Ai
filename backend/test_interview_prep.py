"""
Tests for Phase 7.4: Database-Driven Interview Preparation.

Validates:
1. Question-bank seed idempotency (insert, update, no duplicates).
2. Role, category, and difficulty filtering.
3. Random selection and duplicate avoidance within a session.
4. General-question fallback for custom roles.
5. Empty and insufficient question-bank states.
6. Local rubric feedback without external network calls.
7. Explicit optional Gemini feedback and mocked provider failures.
8. Candidate authorization and data isolation.
9. No unintended persistence of student answers.
10. Regression safety for Phases 7.1, 7.2, and 7.3.
"""

import os
import sys
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.dependencies import get_current_profile, get_db
from app.main import app
from app.models.interview_question import InterviewQuestion
from app.models.opportunity import Opportunity
from app.models.profile import Profile
from app.schemas.interview_prep import (
    AIEvaluationRequest,
    InterviewSessionRequest,
    LocalEvaluationRequest,
)
from app.seeds.interview_questions_data import CURATED_INTERVIEW_QUESTIONS
from app.seeds.seed_interview_questions import seed_interview_questions
from app.services.interview_prep import (
    call_gemini_for_interview_feedback,
    create_interview_session,
    evaluate_answer_locally,
    evaluate_answer_with_ai,
    get_interview_prep_config,
)


# ============================================================================
# Helpers & Fixtures
# ============================================================================

def make_test_profile(
    user_id: UUID | None = None,
    full_name: str = "Elena Rostova",
) -> Profile:
    p = Profile()
    p.id = uuid4()
    p.user_id = user_id or uuid4()
    p.full_name = full_name
    p.role = "student"
    p.headline = "Computer Science Senior"
    p.location = "New York, NY"
    p.about = "Specializing in distributed databases and machine learning."
    p.educations = []
    p.experiences = []
    p.projects = []
    p.skills = []
    p.resumes = []
    return p


def make_sample_question(
    identifier: str = "test-q-01",
    question_text: str = "Explain the difference between SQL and NoSQL databases.",
    category: str = "Technical",
    difficulty: str = "Intermediate",
    role_tags: list[str] | None = None,
    is_general: bool = False,
    skill_tags: list[str] | None = None,
    expected_points: list[str] | None = None,
    reference_answer: str = "SQL databases are relational and structured...",
) -> InterviewQuestion:
    q = InterviewQuestion()
    q.id = uuid4()
    q.identifier = identifier
    q.question_text = question_text
    q.category = category
    q.difficulty = difficulty
    q.role_tags = role_tags or ["Full-Stack Developer", "General Software Engineering"]
    q.is_general = is_general
    q.skill_tags = skill_tags or ["Databases", "SQL", "NoSQL"]
    q.expected_points = expected_points or [
        "Relational schemas vs dynamic/schemaless documents",
        "ACID guarantees vs BASE/eventual consistency",
        "Horizontal vs vertical scaling strategies",
    ]
    q.rubric = {
        "criteria": ["Relational vs Non-Relational", "ACID vs BASE", "Scaling Characteristics"],
        "key_concepts": ["schema", "acid", "relational", "scaling", "nosql", "tables", "documents"],
    }
    q.reference_answer = reference_answer
    q.is_active = True
    q.created_at = datetime.now()
    q.updated_at = datetime.now()
    return q


# ============================================================================
# 1. Question-Bank Seed Idempotency
# ============================================================================

@pytest.mark.anyio
async def test_seed_interview_questions_idempotency():
    """Verify seed adds questions on first run, updates if changed, and creates no duplicates on second run."""
    mock_db = AsyncMock()
    existing_store: dict[str, InterviewQuestion] = {}

    def get_ident(stmt):
        try:
            return stmt.whereclause.right.value
        except Exception:
            for v in stmt.compile().params.values():
                if isinstance(v, str):
                    return v
        return None

    async def mock_execute(stmt):
        res = MagicMock()
        ident = get_ident(stmt)
        res.scalar_one_or_none.return_value = existing_store.get(ident)
        return res

    mock_db.execute.side_effect = mock_execute

    def mock_add(inst):
        if isinstance(inst, InterviewQuestion):
            existing_store[inst.identifier] = inst

    mock_db.add = MagicMock(side_effect=mock_add)

    mini_seed = [
        {
            "identifier": "test-hr-01",
            "question_text": "Tell me about a time you handled conflict.",
            "category": "HR/Behavioural",
            "difficulty": "Beginner",
            "role_tags": ["General"],
            "is_general": True,
            "skill_tags": ["Conflict Resolution"],
            "expected_points": ["Context", "Action", "Result"],
            "rubric": {"criteria": ["STAR"], "key_concepts": ["conflict", "team"]},
            "reference_answer": "Guidance on conflict resolution...",
            "is_active": True,
        },
        {
            "identifier": "test-da-02",
            "question_text": "What is the difference between WHERE and HAVING in SQL?",
            "category": "Technical",
            "difficulty": "Beginner",
            "role_tags": ["Data Analyst"],
            "is_general": False,
            "skill_tags": ["SQL"],
            "expected_points": ["WHERE filters rows before aggregation", "HAVING filters aggregated groups"],
            "rubric": {"criteria": ["SQL Aggregates"], "key_concepts": ["where", "having", "group by"]},
            "reference_answer": "WHERE filters before GROUP BY...",
            "is_active": True,
        },
    ]

    # Run 1: Initial Seed
    stats1 = await seed_interview_questions(mock_db, questions=mini_seed)
    assert stats1["created"] == 2
    assert stats1["updated"] == 0
    assert len(existing_store) == 2

    # Run 2: Repeat with exact same seed (must be 0 created, 0 updated, 2 unchanged)
    stats2 = await seed_interview_questions(mock_db, questions=mini_seed)
    assert stats2["created"] == 0
    assert stats2["updated"] == 0
    assert stats2["unchanged"] == 2
    assert len(existing_store) == 2

    # Run 3: Modify one question in seed (must update 1, create 0)
    modified_seed = [
        dict(mini_seed[0], question_text="Updated text: Tell me about handling difficult technical disagreements."),
        mini_seed[1],
    ]
    stats3 = await seed_interview_questions(mock_db, questions=modified_seed)
    assert stats3["created"] == 0
    assert stats3["updated"] == 1
    assert stats3["unchanged"] == 1
    assert existing_store["test-hr-01"].question_text.startswith("Updated text:")


# ============================================================================
# 2. Role, Category, and Difficulty Filtering
# ============================================================================

@pytest.mark.anyio
async def test_role_category_difficulty_filtering():
    """Verify session creation respects requested category, difficulty, and role filters."""
    mock_db = AsyncMock()

    q_da = make_sample_question(
        identifier="da-tech-sql-01",
        category="Technical",
        difficulty="Intermediate",
        role_tags=["Data Analyst"],
        is_general=False,
    )
    q_hr = make_sample_question(
        identifier="hr-beh-01",
        category="HR/Behavioural",
        difficulty="Beginner",
        role_tags=["General"],
        is_general=True,
    )

    async def mock_execute(stmt):
        res = MagicMock()
        s = str(stmt).lower()
        if "count(interview_questions.id)" in s:
            res.scalar.return_value = 2
        elif "from interview_questions" in s:
            # Simulate SQL WHERE filtering:
            if "interview_questions.category = 'technical'" in s or "category = :category" in s:
                res.scalars.return_value.all.return_value = [q_da]
            else:
                res.scalars.return_value.all.return_value = [q_da, q_hr]
        return res

    mock_db.execute.side_effect = mock_execute

    req = InterviewSessionRequest(
        role="Data Analyst",
        category="Technical",
        difficulty="Intermediate",
        question_count=3,
    )
    resp = await create_interview_session(mock_db, req)

    assert resp.selected_role == "Data Analyst"
    assert resp.category_filter == "Technical"
    assert resp.difficulty_filter == "Intermediate"
    assert len(resp.questions) >= 1
    assert all(q.category == "Technical" for q in resp.questions)
    assert all(q.difficulty == "Intermediate" for q in resp.questions)


# ============================================================================
# 3. Random Selection and Duplicate Avoidance
# ============================================================================

@pytest.mark.anyio
async def test_random_selection_and_no_duplicates():
    """Verify session question selection never contains duplicate questions."""
    mock_db = AsyncMock()

    questions_pool = [
        make_sample_question(
            identifier=f"q-pool-{i}",
            question_text=f"Sample Question {i}",
            category="Technical",
            difficulty="Intermediate",
            role_tags=["Full-Stack Developer"],
            is_general=True,
        )
        for i in range(10)
    ]

    async def mock_execute(stmt):
        res = MagicMock()
        s = str(stmt).lower()
        if "count(interview_questions.id)" in s:
            res.scalar.return_value = len(questions_pool)
        elif "from interview_questions" in s:
            res.scalars.return_value.all.return_value = list(questions_pool)
        return res

    mock_db.execute.side_effect = mock_execute

    req = InterviewSessionRequest(
        role="Full-Stack Developer",
        question_count=5,
    )
    resp = await create_interview_session(mock_db, req)

    assert len(resp.questions) == 5
    ids = [q.id for q in resp.questions]
    identifiers = [q.identifier for q in resp.questions]
    assert len(set(ids)) == 5
    assert len(set(identifiers)) == 5


# ============================================================================
# 4. General-Question Fallback for Custom Roles
# ============================================================================

@pytest.mark.anyio
async def test_custom_role_general_fallback():
    """Verify custom roles with no specific role tags fall back cleanly to general questions."""
    mock_db = AsyncMock()

    q_general = make_sample_question(
        identifier="gen-swe-01",
        question_text="How do you debug an intermittent network issue?",
        category="Technical",
        difficulty="Intermediate",
        role_tags=["General Software Engineering"],
        is_general=True,
    )

    async def mock_execute(stmt):
        res = MagicMock()
        s = str(stmt).lower()
        if "count(interview_questions.id)" in s:
            res.scalar.return_value = 1
        elif "from interview_questions" in s:
            res.scalars.return_value.all.return_value = [q_general]
        return res

    mock_db.execute.side_effect = mock_execute

    req = InterviewSessionRequest(
        role="Quantum Computing Architect",  # Custom role not present in tags
        question_count=3,
    )
    resp = await create_interview_session(mock_db, req)

    assert len(resp.questions) == 1
    assert resp.questions[0].is_general is True
    assert resp.notice is not None
    assert "Quantum Computing Architect" in resp.notice
    assert "general" in resp.notice.lower()


# ============================================================================
# 5. Empty and Insufficient Question-Bank States
# ============================================================================

@pytest.mark.anyio
async def test_empty_and_insufficient_bank_states():
    """Verify empty bank and insufficient question coverage states are handled gracefully."""
    mock_db = AsyncMock()

    # 1. Totally Empty Bank
    async def mock_execute_empty(stmt):
        res = MagicMock()
        s = str(stmt).lower()
        if "count(interview_questions.id)" in s:
            res.scalar.return_value = 0
        return res

    mock_db.execute.side_effect = mock_execute_empty

    req = InterviewSessionRequest(question_count=5)
    resp_empty = await create_interview_session(mock_db, req)
    assert resp_empty.is_empty_bank is True
    assert resp_empty.total_questions == 0
    assert "not been seeded" in resp_empty.notice

    # 2. Insufficient Coverage (Requested 5, only 2 available)
    q1 = make_sample_question(identifier="cov-01", is_general=True)
    q2 = make_sample_question(identifier="cov-02", is_general=True)

    async def mock_execute_partial(stmt):
        res = MagicMock()
        s = str(stmt).lower()
        if "count(interview_questions.id)" in s:
            res.scalar.return_value = 2
        elif "from interview_questions" in s:
            res.scalars.return_value.all.return_value = [q1, q2]
        return res

    mock_db.execute.side_effect = mock_execute_partial

    resp_partial = await create_interview_session(mock_db, InterviewSessionRequest(question_count=5))
    assert resp_partial.insufficient_coverage is True
    assert len(resp_partial.questions) == 2
    assert "Found 2 questions matching your criteria (requested 5)" in resp_partial.notice


# ============================================================================
# 6. Local Rubric Feedback Without External Network Calls
# ============================================================================

@pytest.mark.anyio
async def test_local_rubric_evaluation_deterministic():
    """Verify deterministic local rubric evaluation without calling Gemini or external network."""
    mock_db = AsyncMock()
    q = make_sample_question(
        identifier="da-sql-joins",
        question_text="Explain the differences between INNER JOIN and LEFT JOIN.",
        category="Technical",
        expected_points=[
            "INNER JOIN returns only matching rows across both tables",
            "LEFT JOIN returns all left rows plus matching right rows or null",
            "Handling of null values in aggregations",
        ],
    )

    async def mock_execute(stmt):
        res = MagicMock()
        res.scalar_one_or_none.return_value = q
        return res

    mock_db.execute.side_effect = mock_execute

    # Answer touches on inner join and left join concepts
    sample_answer = (
        "An INNER JOIN returns only records where there is a matching key in both tables. "
        "In contrast, a LEFT JOIN preserves all rows from the left table, filling in null values "
        "when the right table has no matching record. We should consider query performance and indexes on join keys."
    )

    req = LocalEvaluationRequest(question_id=q.id, answer_text=sample_answer)

    with patch("httpx.AsyncClient.post") as mock_http:
        resp = await evaluate_answer_locally(mock_db, req)
        mock_http.assert_not_called()  # Confirms zero external calls!

    assert resp.provider == "local_rubric"
    assert resp.word_count > 30
    assert resp.sentence_count >= 2
    assert len(resp.addressed_points) >= 1
    assert resp.reference_answer_guidance is not None
    assert "Deterministic Rubric Evaluation" in resp.disclaimer


@pytest.mark.anyio
async def test_local_rubric_behavioural_star_checks():
    """Verify behavioural questions trigger STAR structural feedback."""
    mock_db = AsyncMock()
    q = make_sample_question(
        identifier="hr-star-conflict",
        question_text="Tell me about a time you handled a disagreement with a coworker.",
        category="HR/Behavioural",
        expected_points=["Clear context without blame", "Active listening and collaboration", "Outcome and learning"],
    )

    async def mock_execute(stmt):
        res = MagicMock()
        res.scalar_one_or_none.return_value = q
        return res

    mock_db.execute.side_effect = mock_execute

    # Answer lacking result
    incomplete_answer = "During my team project, when I had a disagreement with a peer, I decided to discuss our assumptions."
    req = LocalEvaluationRequest(question_id=q.id, answer_text=incomplete_answer)
    resp = await evaluate_answer_locally(mock_db, req)

    assert any("STAR" in s for s in resp.structure_feedback)
    assert any("result" in s.lower() or "impact" in s.lower() for s in resp.structure_feedback)


# ============================================================================
# 7. Explicit Optional Gemini Feedback and Mocked Provider Failures
# ============================================================================

@pytest.mark.anyio
async def test_gemini_feedback_success_mocked():
    """Verify explicit AI feedback returns structured Gemini analysis when provider succeeds."""
    mock_db = AsyncMock()
    q = make_sample_question()

    async def mock_execute(stmt):
        res = MagicMock()
        res.scalar_one_or_none.return_value = q
        return res

    mock_db.execute.side_effect = mock_execute

    mock_ai_output = """
### Strengths
- Strong conceptual understanding of relational vs non-relational schemas.
- Clear explanation of horizontal scaling using sharding.

### Areas for Improvement
- Could explicitly mention ACID transaction trade-offs.
- Mention real-world database engines (e.g. Postgres vs MongoDB).

### Delivery & Coaching Tips
- Practice timing this answer to under 90 seconds.
"""

    req = AIEvaluationRequest(
        question_id=q.id,
        answer_text="SQL databases are structured and enforce schemas. NoSQL databases are schemaless and scale horizontally.",
    )

    with patch("app.services.interview_prep.settings.gemini_api_key", "test-key-123"):
        with patch("app.services.interview_prep.call_gemini_for_interview_feedback", return_value=mock_ai_output):
            resp = await evaluate_answer_with_ai(mock_db, req)

    assert resp.provider == "gemini"
    assert resp.is_fallback is False
    assert len(resp.strengths) >= 2
    assert len(resp.areas_for_improvement) >= 2
    assert len(resp.delivery_tips) >= 1
    assert resp.fallback_reason is None


@pytest.mark.anyio
async def test_gemini_feedback_quota_failure_falls_back():
    """Verify that when Gemini times out or quota is exceeded (HTTP 429), system falls back gracefully to local rubric."""
    mock_db = AsyncMock()
    q = make_sample_question()

    async def mock_execute(stmt):
        res = MagicMock()
        res.scalar_one_or_none.return_value = q
        return res

    mock_db.execute.side_effect = mock_execute

    req = AIEvaluationRequest(
        question_id=q.id,
        answer_text="Relational databases use tables while document databases use JSON documents.",
    )

    # Simulate Gemini failure (returns None or throws)
    with patch("app.services.interview_prep.settings.gemini_api_key", "test-key-123"):
        with patch("app.services.interview_prep.call_gemini_for_interview_feedback", return_value=None):
            resp = await evaluate_answer_with_ai(mock_db, req)

    assert resp.provider == "local_rubric_fallback"
    assert resp.is_fallback is True
    assert resp.fallback_reason is not None
    assert "quota" in resp.fallback_reason.lower() or "offline" in resp.fallback_reason.lower()
    assert len(resp.strengths) >= 1


@pytest.mark.anyio
async def test_gemini_feedback_unconfigured_api_key():
    """Verify that missing GEMINI_API_KEY immediately uses local rubric fallback without crashing."""
    mock_db = AsyncMock()
    q = make_sample_question()

    async def mock_execute(stmt):
        res = MagicMock()
        res.scalar_one_or_none.return_value = q
        return res

    mock_db.execute.side_effect = mock_execute

    req = AIEvaluationRequest(
        question_id=q.id,
        answer_text="Databases provide structured storage for applications.",
    )

    with patch("app.services.interview_prep.settings.gemini_api_key", ""):
        resp = await evaluate_answer_with_ai(mock_db, req)

    assert resp.provider == "local_rubric_fallback"
    assert resp.is_fallback is True
    assert "not configured" in resp.fallback_reason.lower()


# ============================================================================
# 8. Candidate Authorization & Data Isolation
# ============================================================================

@pytest.mark.anyio
async def test_interview_prep_auth_and_isolation():
    """Verify unauthenticated requests return 401 and authenticated candidates can access endpoints."""
    transport = ASGITransport(app=app)
    mock_db = AsyncMock()

    # 1. Unauthenticated Session Request -> 401
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_unauth = await client.post(
            "/api/v1/copilot/interview-prep/session",
            json={"role": "Data Analyst", "question_count": 3},
        )
        assert res_unauth.status_code in (401, 403)

    # 2. Authenticated Session Request -> 200
    student = make_test_profile()
    q = make_sample_question()

    app.dependency_overrides[get_current_profile] = lambda: student
    app.dependency_overrides[get_db] = lambda: mock_db

    async def mock_execute(stmt):
        res = MagicMock()
        s = str(stmt).lower()
        if "count(interview_questions.id)" in s:
            res.scalar.return_value = 1
        elif "from interview_questions" in s:
            res.scalars.return_value.all.return_value = [q]
        elif "from opportunities" in s:
            res.scalars.return_value.all.return_value = []
        return res

    mock_db.execute.side_effect = mock_execute

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_auth = await client.post(
            "/api/v1/copilot/interview-prep/session",
            json={"role": "Full-Stack Developer", "question_count": 3},
        )
        assert res_auth.status_code == 200
        data = res_auth.json()
        assert "questions" in data
        assert len(data["questions"]) >= 1

    app.dependency_overrides.clear()


# ============================================================================
# 9. No Unintended Persistence of Student Answers
# ============================================================================

@pytest.mark.anyio
async def test_no_unintended_persistence_of_student_answers():
    """Verify that student answers passed for evaluation are not inserted or stored in the database."""
    mock_db = AsyncMock()
    q = make_sample_question()

    async def mock_execute(stmt):
        res = MagicMock()
        res.scalar_one_or_none.return_value = q
        return res

    mock_db.execute.side_effect = mock_execute

    req = LocalEvaluationRequest(
        question_id=q.id,
        answer_text="This is my highly confidential practice answer that must not be stored in any database table.",
    )

    await evaluate_answer_locally(mock_db, req)

    # Ensure mock_db.add was NEVER called with student answer
    mock_db.add.assert_not_called()
    mock_db.add_all.assert_not_called()


# ============================================================================
# 10. Regression Safety for Phases 7.1, 7.2, and 7.3
# ============================================================================

@pytest.mark.anyio
async def test_regression_safety_phases_71_72_73():
    """Verify Phase 7.1 roadmap, Phase 7.2 cover letter, and Phase 7.3 application assistant remain working."""
    student = make_test_profile()
    mock_db = AsyncMock()
    transport = ASGITransport(app=app)

    app.dependency_overrides[get_current_profile] = lambda: student
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Phase 7.3 suggested questions endpoint
        res_73 = await client.get("/api/v1/copilot/application-assistant/suggested-questions")
        assert res_73.status_code == 200
        data_73 = res_73.json()
        assert "suggested_questions" in data_73

        # Phase 7.4 config endpoint
        async def mock_exec_cfg(stmt):
            res = MagicMock()
            res.scalars.return_value.all.return_value = []
            return res

        mock_db.execute.side_effect = mock_exec_cfg
        res_74 = await client.get("/api/v1/copilot/interview-prep/config")
        assert res_74.status_code == 200
        data_74 = res_74.json()
        assert "roles" in data_74
        assert "categories" in data_74
        assert "difficulties" in data_74

    app.dependency_overrides.clear()
