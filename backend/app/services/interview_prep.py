"""
CareerPilot AI — Service Layer for Phase 7.4: Database-Driven Interview Preparation.

Features:
1. Database question selection with role, category, and difficulty filtering.
2. Graceful custom role fallback to general questions.
3. Deterministic local rubric-based evaluation (zero external API calls).
4. Explicit, optional Gemini feedback with graceful local fallback on quota/timeout/misconfig.
5. Strict privacy: candidate interview answers are never stored in the database.
"""

import logging
import random
import re
from typing import Any
from uuid import UUID, uuid4

import httpx
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.models.interview_question import InterviewQuestion
from app.models.opportunity import Opportunity
from app.schemas.interview_prep import (
    AIEvaluationRequest,
    AIEvaluationResponse,
    InterviewPrepConfigResponse,
    InterviewQuestionItem,
    InterviewSessionRequest,
    InterviewSessionResponse,
    LocalEvaluationRequest,
    LocalEvaluationResponse,
    PublishedOpportunitySummary,
)

logger = logging.getLogger(__name__)

STANDARD_ROLES: list[str] = [
    "General / Any Role",
    "Data Analyst",
    "Data Scientist",
    "AI/ML Engineer",
    "Full-Stack Developer",
    "General Software Engineering",
]

CATEGORIES: list[str] = [
    "All Categories",
    "Technical",
    "HR/Behavioural",
    "Project-Based",
]

DIFFICULTIES: list[str] = [
    "All Levels",
    "Beginner",
    "Intermediate",
    "Advanced",
]

QUESTION_COUNT_OPTIONS: list[int] = [3, 5, 10]

LOCAL_DISCLAIMER: str = (
    "Deterministic Rubric Evaluation: This feedback is generated locally using structured rubric "
    "criteria and key concept coverage. It does not reflect deep semantic understanding and does "
    "not predict interview or hiring outcomes."
)

AI_DISCLAIMER: str = (
    "AI-Assisted Interview Feedback: Evaluated using Google Gemini based on the question rubric. "
    "This guidance is intended for practice and self-reflection, and does not guarantee or predict "
    "actual hiring outcomes."
)


def get_gemini_api_url() -> str:
    model = getattr(settings, "gemini_model", "gemini-2.5-flash") or "gemini-2.5-flash"
    return f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


async def get_interview_prep_config(db: AsyncSession) -> InterviewPrepConfigResponse:
    """
    Fetch configuration metadata and active published opportunities for student selection.
    """
    stmt = (
        select(Opportunity)
        .where(Opportunity.status == "Published")
        .order_by(Opportunity.created_at.desc())
        .limit(20)
    )
    res = await db.execute(stmt)
    opps = res.scalars().all()

    opp_summaries = [
        PublishedOpportunitySummary(
            id=opp.id,
            title=opp.title,
            company_name=opp.company_name,
            work_model=opp.work_model,
            opportunity_type=opp.opportunity_type,
        )
        for opp in opps
    ]

    return InterviewPrepConfigResponse(
        roles=STANDARD_ROLES,
        categories=CATEGORIES,
        difficulties=DIFFICULTIES,
        count_options=QUESTION_COUNT_OPTIONS,
        published_opportunities=opp_summaries,
    )


async def create_interview_session(
    db: AsyncSession,
    request: InterviewSessionRequest,
) -> InterviewSessionResponse:
    """
    Create a practice interview session by querying the question bank matching requested filters.
    Stateless on backend: does not persist session or answers in the database.
    """
    session_id = uuid4()

    # 1. Check if question bank has any active questions at all
    count_stmt = select(func.count(InterviewQuestion.id)).where(InterviewQuestion.is_active == True)
    count_res = await db.execute(count_stmt)
    total_bank_questions = count_res.scalar() or 0

    if total_bank_questions == 0:
        return InterviewSessionResponse(
            session_id=session_id,
            questions=[],
            total_questions=0,
            selected_role=request.role,
            is_empty_bank=True,
            notice="The interview question bank has not been seeded yet. Please run the seed command to load curated interview questions.",
        )

    # 2. Resolve target role & opportunity context if opportunity_id is passed
    target_role = (request.role or "").strip()
    opp_title: str | None = None
    opp_company: str | None = None

    if request.opportunity_id:
        opp_stmt = select(Opportunity).where(Opportunity.id == request.opportunity_id)
        opp_res = await db.execute(opp_stmt)
        opp = opp_res.scalar_one_or_none()
        if not opp or opp.status != "Published":
            raise ValueError("Requested opportunity not found or not published.")
        opp_title = opp.title
        opp_company = opp.company_name
        if not target_role or target_role == "General / Any Role":
            target_role = opp.title

    # 3. Build query filters for category and difficulty
    category_filter = request.category if request.category and request.category != "All Categories" else None
    difficulty_filter = request.difficulty if request.difficulty and request.difficulty != "All Levels" else None

    # Fetch candidate questions from database
    query = select(InterviewQuestion).where(InterviewQuestion.is_active == True)
    if category_filter:
        query = query.where(InterviewQuestion.category == category_filter)
    if difficulty_filter:
        query = query.where(InterviewQuestion.difficulty == difficulty_filter)

    res = await db.execute(query)
    all_matched = res.scalars().all()

    if not all_matched:
        return InterviewSessionResponse(
            session_id=session_id,
            questions=[],
            total_questions=0,
            selected_role=target_role or None,
            opportunity_title=opp_title,
            opportunity_company=opp_company,
            category_filter=category_filter,
            difficulty_filter=difficulty_filter,
            insufficient_coverage=True,
            notice="No questions found matching the selected category and difficulty criteria. Try selecting 'All Categories' or 'All Levels'.",
        )

    # 4. Role Matching & General Fallback Logic
    role_norm = target_role.lower() if target_role and target_role != "general / any role" else ""
    
    role_specific: list[InterviewQuestion] = []
    general_pool: list[InterviewQuestion] = []

    for q in all_matched:
        # Check if question role_tags match the requested role
        q_role_tags_norm = [t.lower() for t in (q.role_tags or [])]
        is_role_match = False
        if role_norm:
            for tag in q_role_tags_norm:
                if tag in role_norm or role_norm in tag or tag == "all roles":
                    is_role_match = True
                    break

        if is_role_match:
            role_specific.append(q)
        elif q.is_general:
            general_pool.append(q)
        else:
            # Other questions that might be used if pool is small
            general_pool.append(q)

    # Combine questions: if role-specific questions exist, select up to ~70% from role-specific and 30% from general
    target_count = max(1, min(15, request.question_count))
    selected_set: list[InterviewQuestion] = []
    notice: str | None = None

    if role_specific:
        # Sample role-specific questions first
        needed_role = min(len(role_specific), max(1, int(target_count * 0.7)))
        sampled_role = random.sample(role_specific, needed_role)
        selected_set.extend(sampled_role)

        # Supplement with general questions if more are needed
        remaining_needed = target_count - len(selected_set)
        available_general = [q for q in general_pool if q.id not in {s.id for s in selected_set}]
        if remaining_needed > 0 and available_general:
            sampled_general = random.sample(available_general, min(remaining_needed, len(available_general)))
            selected_set.extend(sampled_general)

        # If still short, draw from remaining role questions if any
        remaining_role = [q for q in role_specific if q.id not in {s.id for s in selected_set}]
        if len(selected_set) < target_count and remaining_role:
            more_role = random.sample(remaining_role, min(target_count - len(selected_set), len(remaining_role)))
            selected_set.extend(more_role)
    else:
        # Custom role with no specific tag coverage: graceful fallback to general questions
        available = [q for q in all_matched if q.is_general] or all_matched
        sample_size = min(target_count, len(available))
        selected_set = random.sample(available, sample_size)
        if role_norm:
            notice = (
                f"No specific questions found for custom role '{target_role}'. "
                "Supplemented with general technical, problem-solving, and behavioural questions."
            )

    # Shuffle the final session questions so role and general questions are mixed naturally
    random.shuffle(selected_set)

    # Check for insufficient question coverage
    insufficient = len(selected_set) < target_count
    if insufficient and not notice:
        notice = (
            f"Found {len(selected_set)} questions matching your criteria (requested {target_count}). "
            "Supplemented with general questions where applicable."
        )

    # Format response items
    items = []
    for q in selected_set:
        rubric_criteria = []
        if isinstance(q.rubric, dict):
            rubric_criteria = q.rubric.get("criteria", [])
        
        items.append(
            InterviewQuestionItem(
                id=q.id,
                identifier=q.identifier,
                question_text=q.question_text,
                category=q.category,
                difficulty=q.difficulty,
                role_tags=q.role_tags or [],
                is_general=q.is_general,
                skill_tags=q.skill_tags or [],
                expected_points=q.expected_points or [],
                rubric_criteria=rubric_criteria,
                reference_answer=q.reference_answer,
            )
        )

    return InterviewSessionResponse(
        session_id=session_id,
        questions=items,
        total_questions=len(items),
        selected_role=target_role or None,
        opportunity_title=opp_title,
        opportunity_company=opp_company,
        category_filter=category_filter,
        difficulty_filter=difficulty_filter,
        insufficient_coverage=insufficient,
        notice=notice,
    )


async def evaluate_answer_locally(
    db: AsyncSession,
    request: LocalEvaluationRequest,
) -> LocalEvaluationResponse:
    """
    Perform deterministic, local rubric-based feedback.
    Evaluates word count, sentence structure, coverage of expected points, and key concepts.
    Does NOT call Gemini or external network APIs. Does NOT persist student answers.
    """
    stmt = select(InterviewQuestion).where(InterviewQuestion.id == request.question_id)
    res = await db.execute(stmt)
    question = res.scalar_one_or_none()
    if not question:
        raise ValueError("Interview question not found.")

    answer_clean = request.answer_text.strip()
    words = answer_clean.split()
    word_count = len(words)
    sentences = [s.strip() for s in re.split(r"[.!?]+", answer_clean) if s.strip()]
    sentence_count = len(sentences)

    # Completeness Level
    if word_count < 30:
        completeness_level = "Initial Draft (Too Brief)"
    elif word_count < 80:
        completeness_level = "Developing (Needs Examples)"
    elif word_count < 220:
        completeness_level = "Proficient (Good Interview Depth)"
    else:
        completeness_level = "Comprehensive (Detailed Response)"

    # Rubric Key Concepts & Expected Points Evaluation
    expected_points = question.expected_points or []
    rubric_dict = question.rubric if isinstance(question.rubric, dict) else {}
    key_concepts = [c.lower() for c in rubric_dict.get("key_concepts", [])]

    addressed_points: list[str] = []
    points_to_elaborate: list[str] = []

    answer_lower = answer_clean.lower()

    # Heuristic match: check if key words from each expected point appear in answer
    for pt in expected_points:
        pt_words = [w.lower() for w in re.findall(r"\b[a-zA-Z]{4,}\b", pt)]
        matched_words = [w for w in pt_words if w in answer_lower]
        # If at least 2 distinct significant words or key concepts match, consider touched upon
        has_concept_overlap = any(kc in answer_lower for kc in key_concepts if kc in pt.lower())
        if len(matched_words) >= 2 or has_concept_overlap:
            addressed_points.append(pt)
        else:
            points_to_elaborate.append(pt)

    # If all points ended in points_to_elaborate but answer is substantial (>80 words) and has key concepts
    concept_hits = sum(1 for kc in key_concepts if kc in answer_lower)
    if not addressed_points and concept_hits >= 2 and expected_points:
        addressed_points.append(expected_points[0])
        points_to_elaborate = expected_points[1:]

    # Structure feedback
    structure_feedback: list[str] = []
    suggestions: list[str] = []

    if question.category == "HR/Behavioural":
        # Check STAR indicators
        has_situation = any(k in answer_lower for k in ["situation", "when i", "during my", "at my", "project", "team"])
        has_action = any(k in answer_lower for k in ["i decided", "i built", "i initiated", "my role", "i spoke", "i focused"])
        has_result = any(k in answer_lower for k in ["result", "outcome", "learned", "impact", "delivered", "successful", "metric"])

        if has_situation and has_action and has_result:
            structure_feedback.append("Strong adherence to the STAR framework (Situation, Task, Action, Result).")
        else:
            missing_star = []
            if not has_situation:
                missing_star.append("clear initial context/situation")
            if not has_action:
                missing_star.append("specific personal actions taken ('I' rather than just 'we')")
            if not has_result:
                missing_star.append("measurable results, impact, or key learnings")
            if missing_star:
                structure_feedback.append(f"Consider structuring with STAR: add {', '.join(missing_star)}.")

    elif question.category == "Technical":
        has_tradeoffs = any(k in answer_lower for k in ["trade-off", "tradeoff", "versus", "vs", "instead of", "because", "advantage"])
        if has_tradeoffs:
            structure_feedback.append("Excellent inclusion of engineering trade-offs and rationale.")
        else:
            suggestions.append("Consider discussing architectural trade-offs (e.g. speed vs memory, or why you chose this tool over an alternative).")

    # Length and pacing suggestions
    if word_count < 40:
        suggestions.append("Your response is quite short for a spoken interview. Aim for roughly 100-180 words to give the interviewer adequate technical substance.")
    elif word_count > 300:
        suggestions.append("Your answer is very detailed. In a live interview, ensure you can deliver the core message in under 2 minutes without losing the interviewer's attention.")

    if points_to_elaborate:
        suggestions.append(f"Try to touch upon: '{points_to_elaborate[0]}'.")

    return LocalEvaluationResponse(
        question_id=question.id,
        addressed_points=addressed_points,
        points_to_elaborate=points_to_elaborate,
        word_count=word_count,
        sentence_count=sentence_count,
        completeness_level=completeness_level,
        structure_feedback=structure_feedback,
        suggestions=suggestions,
        reference_answer_guidance=question.reference_answer,
        provider="local_rubric",
        disclaimer=LOCAL_DISCLAIMER,
    )


async def call_gemini_for_interview_feedback(
    question_text: str,
    category: str,
    difficulty: str,
    expected_points: list[str],
    rubric_criteria: list[str],
    student_answer: str,
) -> str | None:
    """
    Call Gemini API with minimal necessary context for optional interview feedback.
    Sends only the question, rubric, and student answer.
    """
    api_key = getattr(settings, "gemini_api_key", "")
    if not api_key or not api_key.strip():
        logger.warning("Gemini API key is not configured.")
        return None

    rubric_str = "\n".join(f"- {pt}" for pt in expected_points)
    criteria_str = ", ".join(rubric_criteria) if rubric_criteria else "General Clarity & Depth"

    prompt = f"""You are an expert technical and behavioural interview coach evaluating a candidate's practice interview response.
Provide constructive, actionable feedback strictly based on the question and rubric criteria below.

INTERVIEW QUESTION:
- Question: {question_text}
- Category: {category}
- Difficulty: {difficulty}

EVALUATION RUBRIC / EXPECTED POINTS:
{rubric_str}
- Criteria: {criteria_str}

CANDIDATE'S PRACTICE ANSWER:
\"\"\"
{student_answer}
\"\"\"

Provide your evaluation in clear markdown with these exact sections:
### Strengths
(2-3 bullet points identifying specific strong points, relevant concepts, or good structure)

### Areas for Improvement
(2-3 actionable bullet points on what was missing, vague, or could be explained better)

### Delivery & Coaching Tips
(1-2 practical tips for live interview delivery)
"""

    url = f"{get_gemini_api_url()}?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 800,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        raw_text = parts[0]["text"].strip()
                        clean_text = re.sub(r"^```(?:markdown)?\s*", "", raw_text)
                        clean_text = re.sub(r"\s*```$", "", clean_text).strip()
                        return clean_text
            else:
                logger.warning("Gemini API call returned status %s: %s", resp.status_code, resp.text[:200])
    except Exception as exc:
        logger.warning("Gemini API call encountered exception: %s", str(exc))

    return None


async def evaluate_answer_with_ai(
    db: AsyncSession,
    request: AIEvaluationRequest,
) -> AIEvaluationResponse:
    """
    Orchestrate optional Gemini feedback.
    Falls back gracefully to local rubric evaluation if Gemini is unavailable, rate-limited, or unconfigured.
    Does NOT store student answers in the database.
    """
    stmt = select(InterviewQuestion).where(InterviewQuestion.id == request.question_id)
    res = await db.execute(stmt)
    question = res.scalar_one_or_none()
    if not question:
        raise ValueError("Interview question not found.")

    rubric_criteria = []
    if isinstance(question.rubric, dict):
        rubric_criteria = question.rubric.get("criteria", [])

    # Check if Gemini is configured
    api_key = getattr(settings, "gemini_api_key", "")
    if not api_key or not api_key.strip():
        # Transparent fallback to local rubric
        local_res = await evaluate_answer_locally(
            db, LocalEvaluationRequest(question_id=request.question_id, answer_text=request.answer_text)
        )
        return AIEvaluationResponse(
            question_id=question.id,
            feedback_markdown=(
                "**Local Rubric Fallback**: Gemini API key is not configured on the backend. "
                "Here is your automated rubric evaluation:\n\n"
                f"- **Completeness**: {local_res.completeness_level} ({local_res.word_count} words)\n"
                f"- **Points Addressed**: {len(local_res.addressed_points)} of {len(question.expected_points or [])}\n"
                + "\n".join(f"  - ✓ {p}" for p in local_res.addressed_points)
                + ("\n- **Points to Elaborate**:\n" + "\n".join(f"  - • {p}" for p in local_res.points_to_elaborate) if local_res.points_to_elaborate else "")
            ),
            strengths=local_res.addressed_points or ["Demonstrated initial familiarity with the core topic."],
            areas_for_improvement=local_res.points_to_elaborate or local_res.suggestions,
            delivery_tips=local_res.structure_feedback or ["Practice answering with a timer to simulate real interview pressure."],
            provider="local_rubric_fallback",
            provider_model=None,
            is_fallback=True,
            fallback_reason="Gemini API key is not configured. Evaluated deterministically with local rubric engine.",
            disclaimer=LOCAL_DISCLAIMER,
        )

    # Call Gemini
    ai_text = await call_gemini_for_interview_feedback(
        question_text=question.question_text,
        category=question.category,
        difficulty=question.difficulty,
        expected_points=question.expected_points or [],
        rubric_criteria=rubric_criteria,
        student_answer=request.answer_text,
    )

    if ai_text:
        # Parse sections from markdown
        strengths = []
        improvements = []
        delivery_tips = []

        # Simple section extraction
        sections = re.split(r"###\s+", ai_text)
        for sec in sections:
            sec_lower = sec.lower()
            lines = [l.strip().lstrip("-*• ") for l in sec.splitlines() if l.strip() and not l.startswith("#")]
            if "strength" in sec_lower:
                strengths.extend(lines[1:] if len(lines) > 1 else lines)
            elif "improvement" in sec_lower or "missing" in sec_lower:
                improvements.extend(lines[1:] if len(lines) > 1 else lines)
            elif "delivery" in sec_lower or "tip" in sec_lower or "coaching" in sec_lower:
                delivery_tips.extend(lines[1:] if len(lines) > 1 else lines)

        model_name = getattr(settings, "gemini_model", "gemini-2.5-flash") or "gemini-2.5-flash"
        return AIEvaluationResponse(
            question_id=question.id,
            feedback_markdown=ai_text,
            strengths=strengths or ["Addressed key aspects of the question."],
            areas_for_improvement=improvements or ["Could incorporate more specific metrics or trade-offs."],
            delivery_tips=delivery_tips or ["Speak concisely and pause for interviewer confirmation."],
            provider="gemini",
            provider_model=model_name,
            is_fallback=False,
            fallback_reason=None,
            disclaimer=AI_DISCLAIMER,
        )

    # If Gemini call failed (timeout / quota / error)
    local_res = await evaluate_answer_locally(
        db, LocalEvaluationRequest(question_id=request.question_id, answer_text=request.answer_text)
    )
    return AIEvaluationResponse(
        question_id=question.id,
        feedback_markdown=(
            "**Gemini Quota / Service Fallback**: Gemini AI was temporarily unavailable or rate-limited. "
            "Evaluated seamlessly with the local rubric engine:\n\n"
            f"- **Completeness**: {local_res.completeness_level} ({local_res.word_count} words)\n"
            f"- **Rubric Points Addressed**: {len(local_res.addressed_points)} of {len(question.expected_points or [])}\n"
            + "\n".join(f"  - ✓ {p}" for p in local_res.addressed_points)
        ),
        strengths=local_res.addressed_points or ["Addressed core technical themes."],
        areas_for_improvement=local_res.points_to_elaborate or local_res.suggestions,
        delivery_tips=local_res.structure_feedback or ["Structure your thoughts before speaking."],
        provider="local_rubric_fallback",
        provider_model=None,
        is_fallback=True,
        fallback_reason="Gemini service timed out or quota exceeded. Showing offline rubric feedback.",
        disclaimer=LOCAL_DISCLAIMER,
    )
