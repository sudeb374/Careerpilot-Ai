from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class AnswerStyle(str, Enum):
    PROFESSIONAL = "professional"
    CONCISE = "concise"
    DETAILED = "detailed"


class ApplicationQuestionRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="The job application question to answer.",
    )
    opportunity_id: UUID | None = Field(
        default=None,
        description="Optional published opportunity ID to tailor the response.",
    )
    style: AnswerStyle = Field(
        default=AnswerStyle.PROFESSIONAL,
        description="Desired style and tone of the generated answer.",
    )
    word_limit: int | None = Field(
        default=None,
        ge=30,
        le=1000,
        description="Optional target maximum word count constraint.",
    )
    additional_context: str | None = Field(
        default=None,
        max_length=500,
        description="Optional personal focus or context to emphasize.",
    )

    @field_validator("question", mode="before")
    @classmethod
    def validate_question(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Question cannot be empty or only whitespace.")
        return v.strip()

    @field_validator("additional_context", mode="before")
    @classmethod
    def validate_additional_context(cls, v: str | None) -> str | None:
        if v is None:
            return None
        clean = v.strip()
        return clean if clean else None


class QuestionEvidenceSummary(BaseModel):
    matched_skills: list[str] = Field(
        default_factory=list,
        description="Skills directly matching job requirements.",
    )
    verified_skills: list[str] = Field(
        default_factory=list,
        description="Candidate profile skills verified by student records.",
    )
    resume_skills: list[str] = Field(
        default_factory=list,
        description="Skills extracted from active resume (distinguished from manual profile skills).",
    )
    included_projects: list[str] = Field(
        default_factory=list,
        description="Candidate projects cited in the response.",
    )
    included_experiences: list[str] = Field(
        default_factory=list,
        description="Candidate work experiences cited in the response.",
    )
    included_education: list[str] = Field(
        default_factory=list,
        description="Candidate academic background cited in the response.",
    )
    missing_information_notes: list[str] = Field(
        default_factory=list,
        description="Identified gaps or candidate-confirmed items (e.g., work authorization, availability).",
    )


class ApplicationQuestionResponse(BaseModel):
    question: str
    opportunity_id: UUID | None = None
    opportunity_title: str | None = None
    company_name: str | None = None
    style: AnswerStyle
    word_limit: int | None = None
    answer_text: str
    provider: str  # "gemini" or "template_fallback"
    provider_model: str | None = None
    is_template_fallback: bool
    provider_note: str | None = None
    verified_evidence: QuestionEvidenceSummary
    data_warnings: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "This answer is an AI/template-assisted draft grounded in your verified records. "
        "Review and tailor all claims before submitting to an employer."
    )


class SuggestedQuestionItem(BaseModel):
    category: str
    question: str
    description: str


class SuggestedQuestionsResponse(BaseModel):
    suggested_questions: list[SuggestedQuestionItem]
