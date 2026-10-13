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
    eligibility: str | None = None
    domain: str | None = None
    required_experience_min: int = 0
    required_experience_max: int | None = None
    education_requirements: str | None = None
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


class RssPresetFeed(BaseModel):
    id: str
    name: str
    url: str
    description: str


class RssPreviewRequest(BaseModel):
    feed_url: str = Field(..., min_length=10, max_length=1000, description="Authorized RSS or Atom feed URL")
    max_items: int = Field(20, ge=1, le=50, description="Max items to parse (bounded to 50)")
    filter_keywords: str | None = Field(None, max_length=200, description="Optional keyword filter on title or description")


class RssPreviewResponse(BaseModel):
    feed_title: str | None = None
    feed_link: str | None = None
    feed_description: str | None = None
    jobs: list[JobPreviewItem]
    total_found: int
    summary: PreviewSummary


class RssImportRequest(BaseModel):
    selected_job_ids: list[str] = Field(..., min_length=1, description="IDs of RSS jobs explicitly selected for import")
    jobs: list[JobPreviewItem] = Field(..., min_length=1, description="Previewed job objects")


class RssImportResponse(BaseModel):
    inserted_count: int
    skipped_count: int
    duplicate_count: int
    review_required_count: int
    details: list[ImportDetailItem]


# -----------------------------------------------------------------------------
# Bulk Upload Fallback Schemas (Phase 6.4)
# -----------------------------------------------------------------------------

class BulkUploadPreviewResponse(BaseModel):
    filename: str
    total_rows: int
    valid_count: int
    invalid_count: int
    duplicate_count: int
    review_required_count: int
    jobs: list[JobPreviewItem]
    summary: PreviewSummary


class BulkUploadImportRequest(BaseModel):
    selected_job_ids: list[str] = Field(..., min_length=1, description="IDs of rows selected for import")
    jobs: list[JobPreviewItem] = Field(..., min_length=1, description="Previewed job objects")


class BulkUploadImportResponse(BaseModel):
    inserted_count: int
    skipped_count: int
    duplicate_count: int
    review_required_count: int
    details: list[ImportDetailItem]


# -----------------------------------------------------------------------------
# Scheduled Refresh Schemas (Phase 6.4)
# -----------------------------------------------------------------------------

class RefreshSourceDetail(BaseModel):
    source: str
    target: str
    status: str  # "success", "skipped", "error"
    items_found: int = 0
    items_inserted: int = 0
    items_updated: int = 0
    items_duplicate: int = 0
    error: str | None = None


class RefreshSummary(BaseModel):
    last_run_at: datetime | None = None
    duration_seconds: float = 0.0
    status: str = "idle"  # "idle", "running", "success", "partial_failure", "failed"
    is_running: bool = False
    total_inserted: int = 0
    total_updated: int = 0
    total_duplicates: int = 0
    total_expired: int = 0
    sources: list[RefreshSourceDetail] = []
    errors: list[str] = []


class RefreshTriggerResponse(BaseModel):
    message: str
    status: str
    summary: RefreshSummary | None = None


class RefreshStatusResponse(BaseModel):
    enabled: bool
    interval_minutes: int
    jsearch_enabled: bool
    jsearch_query: str
    jsearch_max_pages: int
    rss_enabled: bool
    rss_feed_urls: list[str]
    rss_max_items: int
    auto_expire: bool
    last_summary: RefreshSummary

