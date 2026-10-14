from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ActiveResumeSummary(BaseModel):
    """Summary of the candidate's active resume and existing analysis indicators."""

    resume_id: UUID
    original_filename: str
    file_size: int
    file_type: str
    has_parsed_text: bool
    has_structured_data: bool
    has_analysis: bool
    completeness_score: int | None = None
    score_label: str | None = None
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobResumeContextResponse(BaseModel):
    """Context information for checking readiness before running job-specific resume analysis."""

    opportunity_id: UUID
    opportunity_title: str
    company_name: str
    opportunity_type: str
    work_model: str
    domain: str | None = None
    locations: list[str] = []
    deadline: datetime | None = None
    has_description: bool
    description_char_count: int
    skills_required: list[str] = []
    active_resume: ActiveResumeSummary | None = None
    is_ready_for_analysis: bool
    readiness_notes: list[str] = []


class JobResumeAnalysisRequest(BaseModel):
    """Request payload to initiate job-specific resume recommendations."""

    opportunity_id: UUID
    include_bullet_rewrites: bool = Field(
        default=True,
        description="Whether to generate enhanced wording suggestions for detected vague resume bullets.",
    )


class RelevantStrengthItem(BaseModel):
    """A factual strength supported by candidate's profile/resume that aligns with the target job."""

    category: str = Field(
        ...,
        description="Strength category: 'skill', 'project', 'experience', or 'education'.",
    )
    title: str = Field(..., description="Name or title of the strength.")
    source: str = Field(
        ...,
        description="Evidence source: 'profile' (manual verified), 'resume' (extracted), or 'both'.",
    )
    evidence: str = Field(
        ...,
        description="Verbatim or summarized factual proof from the candidate's records.",
    )
    relevance_explanation: str = Field(
        ...,
        description="Clear explanation of how this strength aligns with the target job requirements.",
    )


class RequirementGapItem(BaseModel):
    """A requirement in the job description that is missing or inconclusive in candidate records."""

    skill_name: str = Field(..., description="The required or desired competency.")
    requirement_level: str = Field(
        ...,
        description="'required' (core/minimum qualification) or 'desired' (preferred/bonus).",
    )
    gap_type: str = Field(
        ...,
        description="'missing_requirement' (not found anywhere in records) or 'undetermined_incomplete_info' (ambiguous or unevidenced).",
    )
    explanation: str = Field(
        ...,
        description="Objective explanation of the gap without assuming the candidate completely lacks the skill.",
    )
    student_guidance: str = Field(
        ...,
        description="Actionable advice for the student on how to address or verify this gap honestly.",
    )


class ActionableImprovementItem(BaseModel):
    """A concrete, prioritized recommendation for improving the resume for this opportunity."""

    category: str = Field(
        ...,
        description="Improvement category: 'emphasis', 'bullet_rewrite', 'keyword_alignment', or 'section_content'.",
    )
    priority: str = Field(..., description="'high', 'medium', or 'low'.")
    title: str = Field(..., description="Short summary of the recommendation.")
    original_content: str | None = Field(
        None,
        description="Exact snippet or bullet text from the candidate's resume being analyzed.",
    )
    suggested_wording: str | None = Field(
        None,
        description="Suggested wording with explicit bracketed placeholders for metrics or unverified facts.",
    )
    reason: str = Field(
        ...,
        description="Why this change improves relevance to the target job.",
    )
    evidence_support: str | None = Field(
        None,
        description="Factual candidate evidence supporting this improvement.",
    )
    is_gemini_assisted: bool = Field(
        default=False,
        description="Whether this suggested wording was drafted with Gemini LLM assistance.",
    )


class AtsGuidanceItem(BaseModel):
    """ATS-oriented structural and readability recommendation."""

    area: str = Field(
        ...,
        description="Focus area: 'headings', 'readability', 'keyword_placement', or 'section_structure'.",
    )
    status: str = Field(
        ...,
        description="'good' (adherent), 'improvement_needed' (action needed), or 'info' (guidance).",
    )
    title: str = Field(..., description="Guidance topic title.")
    recommendation: str = Field(..., description="Specific recommendation.")
    rationale: str = Field(
        ...,
        description="Technical rationale for why standard ATS parsers benefit from this formatting.",
    )


class DataSufficiencyInfo(BaseModel):
    """Status of available data used during the analysis."""

    has_active_resume: bool
    has_resume_text: bool
    has_job_description: bool
    has_job_skills: bool
    status: str = Field(..., description="'sufficient', 'partial', or 'insufficient'.")
    details: list[str] = []


class JobResumeAnalysisResponse(BaseModel):
    """Complete response payload for job-specific resume recommendations."""

    opportunity_id: UUID
    opportunity_title: str
    company_name: str
    resume_id: UUID | None = None
    resume_filename: str | None = None
    resume_completeness_score: int | None = None
    resume_completeness_label: str | None = None
    data_sufficiency: DataSufficiencyInfo
    strengths: list[RelevantStrengthItem] = []
    gaps: list[RequirementGapItem] = []
    improvements: list[ActionableImprovementItem] = []
    ats_guidance: list[AtsGuidanceItem] = []
    disclaimers: list[str] = []
    provider: str = Field(
        default="deterministic",
        description="'gemini' if LLM was used for rewrites, or 'deterministic'.",
    )
    provider_model: str | None = None
    created_at: datetime
