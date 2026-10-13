from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CoverLetterTone(str, Enum):
    PROFESSIONAL = "professional"
    ENTHUSIASTIC = "enthusiastic"
    CONFIDENT = "confident"


class CoverLetterLength(str, Enum):
    CONCISE = "concise"
    STANDARD = "standard"
    DETAILED = "detailed"


class CoverLetterGenerateRequest(BaseModel):
    opportunity_id: UUID
    tone: CoverLetterTone = CoverLetterTone.PROFESSIONAL
    length: CoverLetterLength = CoverLetterLength.STANDARD
    additional_notes: str | None = Field(
        None,
        max_length=500,
        description="Optional angle or specific project to highlight",
    )

    model_config = ConfigDict(from_attributes=True)


class VerifiedEvidenceSummary(BaseModel):
    matched_skills: list[str] = []
    included_projects: list[str] = []
    included_experiences: list[str] = []
    included_education: list[str] = []
    resume_evidence_snippets: list[str] = []

    model_config = ConfigDict(from_attributes=True)


class CoverLetterGenerateResponse(BaseModel):
    opportunity_id: UUID
    opportunity_title: str
    company_name: str
    recipient_name: str = "Hiring Team"

    tone: CoverLetterTone
    length: CoverLetterLength

    subject_line: str
    cover_letter_text: str

    provider: str  # "gemini" or "template_fallback"
    provider_model: str | None = None
    is_template_fallback: bool = False
    provider_note: str | None = None

    verified_evidence: VerifiedEvidenceSummary
    data_warnings: list[str] = []

    disclaimer: str = (
        "This cover letter is an AI-assisted draft generated strictly from your verified profile and active resume. "
        "Review and personalize the draft before submitting it to an employer."
    )

    model_config = ConfigDict(from_attributes=True)


class OpportunityContextForLetter(BaseModel):
    opportunity_id: UUID
    title: str
    company_name: str
    opportunity_type: str
    work_model: str
    locations: list[str] = []
    domain: str | None = None
    skills_required: list[str] = []
    has_sufficient_candidate_data: bool = True
    candidate_matched_skills: list[str] = []
    validation_message: str | None = None

    model_config = ConfigDict(from_attributes=True)
