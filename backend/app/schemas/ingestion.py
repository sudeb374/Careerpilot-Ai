from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class JSearchPreviewRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=200, description="Search keywords (e.g. 'Software Engineer Intern')")
    country: str = Field("in", min_length=2, max_length=2, description="2-letter ISO country code (default 'in')")
    date_posted: str = Field("all", description="Posting timeframe: all, today, 3days, week, month")
    employment_types: str | None = Field(None, description="Employment types filter (e.g. 'INTERN' or 'FULLTIME,INTERN')")
    remote_jobs_only: bool = Field(False, description="Filter remote positions only")
    page: int = Field(1, ge=1, le=10, description="Page number")
    num_pages: int = Field(1, ge=1, le=1, description="Bounded to 1 page to protect free-tier allowance")

    @field_validator("country")
    @classmethod
    def sanitize_country(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("date_posted")
    @classmethod
    def validate_date_posted(cls, v: str) -> str:
        allowed = {"all", "today", "3days", "week", "month"}
        val = v.strip().lower()
        if val not in allowed:
            return "all"
        return val


class MatchedSkillItem(BaseModel):
    id: UUID
    name: str

    model_config = ConfigDict(from_attributes=True)


class JobPreviewItem(BaseModel):
    job_id: str
    title: str
    company_name: str
    company_website: str | None = None
    company_logo_url: str | None = None
    description: str | None = None
    opportunity_type: str = "Internship"
    work_model: str = "On-site"
    locations: list[str] | None = None
    application_url: str | None = None
    publisher: str | None = None
    posted_at: datetime | None = None
    deadline: datetime | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    stipend_min: int | None = None
    stipend_max: int | None = None
    currency: str | None = None
    matched_skills: list[MatchedSkillItem] = []
    unmapped_skills: list[str] = []
    is_duplicate: bool = False
    review_required: bool = False
    warnings: list[str] = []
    errors: list[str] = []
    classification_conflict: bool = False
    raw_employment_types: list[str] = []

    model_config = ConfigDict(from_attributes=True)


class PreviewSummary(BaseModel):
    total_returned: int
    valid_count: int
    duplicate_count: int
    review_required_count: int


class JSearchPreviewResponse(BaseModel):
    jobs: list[JobPreviewItem]
    total_found: int
    cursor: str | None = None
    parameters: dict[str, Any] = {}
    summary: PreviewSummary


class JSearchImportRequest(BaseModel):
    selected_job_ids: list[str] = Field(..., min_length=1, description="IDs of jobs explicitly selected for import")
    jobs: list[JobPreviewItem] = Field(..., min_length=1, description="Previewed job objects")


class ImportDetailItem(BaseModel):
    job_id: str
    title: str
    status: str  # "imported", "duplicate", "skipped", "error"
    reason: str | None = None
    opportunity_id: UUID | None = None


class JSearchImportResponse(BaseModel):
    inserted_count: int
    skipped_count: int
    duplicate_count: int
    review_required_count: int
    details: list[ImportDetailItem]
