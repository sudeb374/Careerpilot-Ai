from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ApplicationStatus(str, Enum):
    SAVED = "Saved"
    APPLIED = "Applied"
    ASSESSMENT = "Assessment"
    INTERVIEW = "Interview"
    OFFER = "Offer"
    REJECTED = "Rejected"
    WITHDRAWN = "Withdrawn"


VALID_STATUSES = {s.value for s in ApplicationStatus}


class OpportunitySummaryForApp(BaseModel):
    """Summary of opportunity linked to an application record."""

    id: UUID
    title: str
    company_name: str
    company_logo_url: str | None = None
    opportunity_type: str
    work_model: str
    locations: list[str] | None = None
    domain: str | None = None
    deadline: datetime | None = None
    application_url: str | None = None
    status: str

    model_config = ConfigDict(from_attributes=True)


class ApplicationStatusHistoryItem(BaseModel):
    """Historical status transition audit record."""

    id: UUID
    application_id: UUID
    from_status: str | None = None
    to_status: str
    note: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationListItem(BaseModel):
    """Compact application record for listings, reminders, and filters."""

    id: UUID
    profile_id: UUID
    opportunity_id: UUID
    status: str
    applied_at: datetime | None = None
    status_updated_at: datetime
    deadline: datetime | None = None
    reminder_at: datetime | None = None
    reminder_note: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    opportunity: OpportunitySummaryForApp

    model_config = ConfigDict(from_attributes=True)


class ApplicationResponse(BaseModel):
    """Complete application details with full status history and linked opportunity."""

    id: UUID
    profile_id: UUID
    opportunity_id: UUID
    status: str
    applied_at: datetime | None = None
    status_updated_at: datetime
    deadline: datetime | None = None
    reminder_at: datetime | None = None
    reminder_note: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    opportunity: OpportunitySummaryForApp
    history: list[ApplicationStatusHistoryItem] = []

    model_config = ConfigDict(from_attributes=True)


class PaginatedApplicationsResponse(BaseModel):
    """Paginated list of applications with metadata."""

    items: list[ApplicationListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class ApplicationCreateRequest(BaseModel):
    """Payload to track a new job application."""

    opportunity_id: UUID
    status: str = Field(default="Applied", description="Initial application status")
    applied_at: datetime | None = Field(
        default=None,
        description="Submission timestamp. If status is Applied and omitted, defaults to now.",
    )
    deadline: datetime | None = Field(
        default=None,
        description="Optional personal or job deadline override.",
    )
    reminder_at: datetime | None = Field(
        default=None,
        description="Optional personal reminder date and time (UTC).",
    )
    reminder_note: str | None = Field(
        default=None,
        max_length=255,
        description="Optional short label for reminder purpose (e.g. Follow up on assessment).",
    )
    notes: str | None = Field(
        default=None,
        description="Personal notes for recruiter contacts, interview prep, or follow-ups.",
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        clean = v.strip().title()
        if clean not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status '{v}'. Allowed statuses: {', '.join(sorted(VALID_STATUSES))}"
            )
        return clean


class ApplicationUpdateRequest(BaseModel):
    """Payload to update an existing application's status, notes, deadline, or reminders."""

    status: str | None = None
    applied_at: datetime | None = None
    deadline: datetime | None = None
    reminder_at: datetime | None = None
    reminder_note: str | None = None
    notes: str | None = None
    status_change_note: str | None = Field(
        default=None,
        description="Optional note recorded in status history explaining this transition.",
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is None:
            return None
        clean = v.strip().title()
        if clean not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status '{v}'. Allowed statuses: {', '.join(sorted(VALID_STATUSES))}"
            )
        return clean


class ApplicationActivityItem(BaseModel):
    """Timeline entry for recent activity in the tracker."""

    id: UUID
    application_id: UUID
    opportunity_id: UUID
    opportunity_title: str
    company_name: str
    from_status: str | None = None
    to_status: str
    note: str | None = None
    timestamp: datetime


class ApplicationAnalyticsResponse(BaseModel):
    """Summary metrics and conversion statistics scoped to candidate records."""

    total_tracked: int
    total_submitted: int
    by_status: dict[str, int]
    active_interviews_count: int
    upcoming_deadlines_count: int
    active_reminders_count: int
    overdue_reminders_count: int
    response_rate_percent: float | None = None
    response_rate_note: str
    interview_rate_percent: float | None = None
    interview_rate_note: str
    recent_activity: list[ApplicationActivityItem] = []


class RemindersSummaryResponse(BaseModel):
    """Due and upcoming personal reminders for the authenticated student."""

    due_count: int
    upcoming_count: int
    due_reminders: list[ApplicationListItem] = []
    upcoming_reminders: list[ApplicationListItem] = []


class ApplicationCheckStateResponse(BaseModel):
    """Check if an opportunity is already tracked by the authenticated student."""

    is_tracked: bool
    application_id: UUID | None = None
    status: str | None = None
    applied_at: datetime | None = None
