from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SkillSource(str, Enum):
    PROFILE = "profile"
    RESUME = "resume"
    BOTH = "both"


class RequirementLevel(str, Enum):
    REQUIRED = "required"
    DESIRED = "desired"
    COMMON = "common"


class PriorityTier(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class JobEvidenceItem(BaseModel):
    opportunity_id: UUID
    title: str
    company_name: str
    is_required: bool

    model_config = ConfigDict(from_attributes=True)


class AcquiredSkillItem(BaseModel):
    skill_id: UUID | None = None
    name: str
    source: SkillSource
    proficiency: str | None = None
    resume_evidence: str | None = None
    is_saved_to_profile: bool = False
    category: str | None = None

    model_config = ConfigDict(from_attributes=True)


class MissingSkillItem(BaseModel):
    skill_id: UUID | None = None
    name: str
    priority_tier: PriorityTier
    demand_frequency: int
    demand_percentage: float
    requirement_level: RequirementLevel
    required_count: int
    desired_count: int
    evidence_jobs: list[JobEvidenceItem] = []
    rationale: str
    category: str | None = None

    model_config = ConfigDict(from_attributes=True)


class LearningSequenceStage(BaseModel):
    stage_number: int
    title: str
    description: str
    skills: list[MissingSkillItem] = []

    model_config = ConfigDict(from_attributes=True)


class SkillCoverageSummary(BaseModel):
    total_market_skills: int
    acquired_skills_count: int
    missing_skills_count: int
    coverage_percentage: float
    disclaimer: str = (
        "This metric measures observed skill overlap with published job listings. "
        "It is a heuristic readiness indicator and does not represent a probability of hiring or selection."
    )

    model_config = ConfigDict(from_attributes=True)


class InsufficientDataStatus(BaseModel):
    has_insufficient_profile: bool = False
    profile_message: str | None = None
    has_insufficient_jobs: bool = False
    jobs_message: str | None = None

    model_config = ConfigDict(from_attributes=True)


class SkillGapRoadmapResponse(BaseModel):
    target_role: str | None = None
    available_target_roles: list[str] = []
    total_analyzed_opportunities: int = 0
    coverage: SkillCoverageSummary
    data_status: InsufficientDataStatus
    acquired_skills: list[AcquiredSkillItem] = []
    missing_skills: list[MissingSkillItem] = []
    learning_sequence: list[LearningSequenceStage] = []

    model_config = ConfigDict(from_attributes=True)
