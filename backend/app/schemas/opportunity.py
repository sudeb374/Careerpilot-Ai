from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)
from typing_extensions import Self


class OpportunitySkillResponse(BaseModel):
    id: UUID
    name: str

    model_config = ConfigDict(from_attributes=True)

class OpportunityBase(BaseModel):
    title: str = Field(..., max_length=255)
    company_name: str = Field(..., max_length=255)
    company_website: str | None = Field(None, max_length=500)
    company_logo_url: str | None = Field(None, max_length=500)
    
    description: str | None = None
    
    opportunity_type: str = Field(..., description="Internship or Full-Time")
    work_model: str = Field(..., description="Remote, Hybrid, or On-site")
    
    locations: list[str] | None = Field(default=None, max_length=20)
    domain: str | None = Field(None, max_length=255)
    
    required_experience_min: int = Field(0, ge=0)
    required_experience_max: int | None = Field(None, ge=0)
    
    education_requirements: str | None = None
    eligibility: str | None = None
    
    application_url: str | None = Field(None, max_length=500)
    deadline: datetime | None = None
    
    stipend_min: int | None = Field(None, ge=0)
    stipend_max: int | None = Field(None, ge=0)
    salary_min: int | None = Field(None, ge=0)
    salary_max: int | None = Field(None, ge=0)
    currency: str | None = Field(None, max_length=10)
    
    source_name: str | None = Field(None, max_length=100)
    source_url: str | None = Field(None, max_length=500)
    external_id: str | None = Field(None, max_length=255)
    
    status: str = Field("Draft", description="Draft, Published, Closed, or Expired")

    @field_validator("company_website", "company_logo_url", "application_url", "source_url", mode="before")
    @classmethod
    def validate_and_format_url(cls, v: str | None) -> str | None:
        if not v:
            return None
        v = v.strip()
        if not v:
            return None
        return str(HttpUrl(v))

    @field_validator("locations", mode="before")
    @classmethod
    def sanitize_locations(cls, v: list[str] | None) -> list[str] | None:
        if not v:
            return v
        seen = set()
        result = []
        for loc in v:
            if isinstance(loc, str):
                cleaned = loc.strip()
                if cleaned:
                    lower_cleaned = cleaned.lower()
                    if lower_cleaned not in seen:
                        seen.add(lower_cleaned)
                        result.append(cleaned)
        return result

    @field_validator("opportunity_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ["Internship", "Full-Time"]:
            raise ValueError("opportunity_type must be Internship or Full-Time")
        return v

    @field_validator("work_model")
    @classmethod
    def validate_work_model(cls, v: str) -> str:
        if v not in ["Remote", "Hybrid", "On-site"]:
            raise ValueError("work_model must be Remote, Hybrid, or On-site")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ["Draft", "Published", "Closed", "Expired"]:
            raise ValueError("status must be Draft, Published, Closed, or Expired")
        return v

    @model_validator(mode="after")
    def validate_ranges(self) -> Self:
        if self.required_experience_max is not None and self.required_experience_min is not None:
            if self.required_experience_max < self.required_experience_min:
                raise ValueError("required_experience_max cannot be less than required_experience_min")
        
        if self.stipend_max is not None and self.stipend_min is not None:
            if self.stipend_max < self.stipend_min:
                raise ValueError("stipend_max cannot be less than stipend_min")
                
        if self.salary_max is not None and self.salary_min is not None:
            if self.salary_max < self.salary_min:
                raise ValueError("salary_max cannot be less than salary_min")
                
        return self


class OpportunityCreate(OpportunityBase):
    required_skill_ids: list[UUID] | None = Field(default_factory=list)

    @field_validator("required_skill_ids", mode="before")
    @classmethod
    def deduplicate_skills(cls, v: list[Any] | None) -> list[Any]:
        if not v:
            return []
        # Convert to string and deduplicate, preserving order
        seen = set()
        result = []
        for x in v:
            s = str(x)
            if s not in seen:
                seen.add(s)
                result.append(x)
        return result


class OpportunityUpdate(BaseModel):
    title: str | None = Field(None, max_length=255)
    company_name: str | None = Field(None, max_length=255)
    company_website: str | None = Field(None, max_length=500)
    company_logo_url: str | None = Field(None, max_length=500)
    description: str | None = None
    opportunity_type: str | None = None
    work_model: str | None = None
    locations: list[str] | None = Field(None, max_length=20)
    domain: str | None = Field(None, max_length=255)
    required_experience_min: int | None = Field(None, ge=0)
    required_experience_max: int | None = Field(None, ge=0)
    education_requirements: str | None = None
    eligibility: str | None = None
    application_url: str | None = Field(None, max_length=500)
    deadline: datetime | None = None
    stipend_min: int | None = Field(None, ge=0)
    stipend_max: int | None = Field(None, ge=0)
    salary_min: int | None = Field(None, ge=0)
    salary_max: int | None = Field(None, ge=0)
    currency: str | None = Field(None, max_length=10)
    source_name: str | None = Field(None, max_length=100)
    source_url: str | None = Field(None, max_length=500)
    external_id: str | None = Field(None, max_length=255)
    status: str | None = None
    required_skill_ids: list[UUID] | None = None

    @field_validator("company_website", "company_logo_url", "application_url", "source_url", mode="before")
    @classmethod
    def validate_and_format_url(cls, v: str | None) -> str | None:
        if not v:
            return None
        v = v.strip()
        if not v:
            return None
        return str(HttpUrl(v))

    @field_validator("locations", mode="before")
    @classmethod
    def sanitize_locations(cls, v: list[str] | None) -> list[str] | None:
        if not v:
            return v
        seen = set()
        result = []
        for loc in v:
            if isinstance(loc, str):
                cleaned = loc.strip()
                if cleaned:
                    lower_cleaned = cleaned.lower()
                    if lower_cleaned not in seen:
                        seen.add(lower_cleaned)
                        result.append(cleaned)
        return result

    @field_validator("opportunity_type")
    @classmethod
    def validate_type(cls, v: str | None) -> str | None:
        if v is not None and v not in ["Internship", "Full-Time"]:
            raise ValueError("opportunity_type must be Internship or Full-Time")
        return v

    @field_validator("work_model")
    @classmethod
    def validate_work_model(cls, v: str | None) -> str | None:
        if v is not None and v not in ["Remote", "Hybrid", "On-site"]:
            raise ValueError("work_model must be Remote, Hybrid, or On-site")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is not None and v not in ["Draft", "Published", "Closed", "Expired"]:
            raise ValueError("status must be Draft, Published, Closed, or Expired")
        return v

    @field_validator("required_skill_ids", mode="before")
    @classmethod
    def deduplicate_skills(cls, v: list[Any] | None) -> list[Any] | None:
        if v is None:
            return v
        seen = set()
        result = []
        for x in v:
            s = str(x)
            if s not in seen:
                seen.add(s)
                result.append(x)
        return result


class OpportunityResponse(OpportunityBase):
    id: UUID
    created_by_profile_id: UUID | None = None
    created_at: datetime
    updated_at: datetime
    
    skills: list[OpportunitySkillResponse] = []

    model_config = ConfigDict(from_attributes=True)


class OpportunityListItem(BaseModel):
    id: UUID
    title: str
    company_name: str
    company_logo_url: str | None = None
    opportunity_type: str
    work_model: str
    locations: list[str] | None = None
    domain: str | None = None
    deadline: datetime | None = None
    status: str
    created_at: datetime
    
    skills: list[OpportunitySkillResponse] = []

    model_config = ConfigDict(from_attributes=True)


class PaginatedOpportunityResponse(BaseModel):
    items: list[OpportunityListItem]
    page: int
    page_size: int
    total: int
    total_pages: int


class SavedOpportunityState(BaseModel):
    saved: bool


class SavedOpportunityItem(OpportunityListItem):
    saved_at: datetime


class PaginatedSavedOpportunityResponse(BaseModel):
    items: list[SavedOpportunityItem]
    page: int
    page_size: int
    total: int
    total_pages: int
