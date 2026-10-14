"""
CareerPilot AI — Schemas for Phase 7.4: Database-Driven Interview Preparation.
"""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class PublishedOpportunitySummary(BaseModel):
    id: UUID
    title: str
    company_name: str
    work_model: str
    opportunity_type: str


class InterviewPrepConfigResponse(BaseModel):
    roles: list[str]
    categories: list[str]
    difficulties: list[str]
    count_options: list[int]
    published_opportunities: list[PublishedOpportunitySummary]


class InterviewSessionRequest(BaseModel):
    role: str | None = Field(default=None, description="Target role name or custom role")
    opportunity_id: UUID | None = Field(default=None, description="Optional published opportunity ID")
    category: str | None = Field(default=None, description="Technical, HR/Behavioural, Project-Based, or None")
    difficulty: str | None = Field(default=None, description="Beginner, Intermediate, Advanced, or None")
    question_count: int = Field(default=5, ge=1, le=15, description="Number of practice questions (1-15)")


class InterviewQuestionItem(BaseModel):
    id: UUID
    identifier: str
    question_text: str
    category: str
    difficulty: str
    role_tags: list[str]
    is_general: bool
    skill_tags: list[str]
    expected_points: list[str]
    rubric_criteria: list[str] = Field(default_factory=list)
    reference_answer: str | None = None


class InterviewSessionResponse(BaseModel):
    session_id: UUID
    questions: list[InterviewQuestionItem]
    total_questions: int
    selected_role: str | None = None
    opportunity_title: str | None = None
    opportunity_company: str | None = None
    category_filter: str | None = None
    difficulty_filter: str | None = None
    is_empty_bank: bool = False
    insufficient_coverage: bool = False
    notice: str | None = None


class LocalEvaluationRequest(BaseModel):
    question_id: UUID
    answer_text: str = Field(..., min_length=1, description="Student's practice answer")


class LocalEvaluationResponse(BaseModel):
    question_id: UUID
    addressed_points: list[str]
    points_to_elaborate: list[str]
    word_count: int
    sentence_count: int
    completeness_level: str
    structure_feedback: list[str]
    suggestions: list[str]
    reference_answer_guidance: str | None = None
    provider: str = "local_rubric"
    disclaimer: str


class AIEvaluationRequest(BaseModel):
    question_id: UUID
    answer_text: str = Field(..., min_length=1, description="Student's practice answer")


class AIEvaluationResponse(BaseModel):
    question_id: UUID
    feedback_markdown: str
    strengths: list[str]
    areas_for_improvement: list[str]
    delivery_tips: list[str]
    provider: str
    provider_model: str | None = None
    is_fallback: bool = False
    fallback_reason: str | None = None
    disclaimer: str
