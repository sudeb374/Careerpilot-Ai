from datetime import date, datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)


class ProfileBase(BaseModel):
    full_name: str = Field(..., max_length=255)
    headline: str | None = Field(None, max_length=500)
    location: str | None = Field(None, max_length=255)
    about: str | None = Field(None, max_length=2000)
    phone: str | None = Field(None, max_length=30)
    linkedin_url: str | None = Field(None, max_length=500)
    github_url: str | None = Field(None, max_length=500)
    portfolio_url: str | None = Field(None, max_length=500)

    @field_validator("about", "phone", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str | None) -> str | None:
        if isinstance(v, str):
            return v.strip() or None
        return v

    @field_validator("linkedin_url", "github_url", "portfolio_url", mode="before")
    @classmethod
    def validate_and_format_url(cls, v: str | None) -> str | None:
        if not v:
            return None
        v = v.strip()
        if not v:
            return None
        # Validates and normalizes URL
        return str(HttpUrl(v))


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(None, max_length=255)
    headline: str | None = Field(None, max_length=500)
    location: str | None = Field(None, max_length=255)
    about: str | None = Field(None, max_length=2000)
    phone: str | None = Field(None, max_length=30)
    linkedin_url: str | None = Field(None, max_length=500)
    github_url: str | None = Field(None, max_length=500)
    portfolio_url: str | None = Field(None, max_length=500)

    @field_validator("about", "phone", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str | None) -> str | None:
        if isinstance(v, str):
            return v.strip() or None
        return v

    @field_validator("linkedin_url", "github_url", "portfolio_url", mode="before")
    @classmethod
    def validate_and_format_url(cls, v: str | None) -> str | None:
        if not v:
            return None
        v = v.strip()
        if not v:
            return None
        # Validates and normalizes URL
        return str(HttpUrl(v))


class ProfileResponse(ProfileBase):
    id: UUID
    user_id: UUID
    role: str
    profile_picture_path: str | None = None
    profile_picture_url: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EducationBase(BaseModel):
    institution: str = Field(..., max_length=255)
    degree: str = Field(..., max_length=255)
    field_of_study: str | None = Field(None, max_length=255)
    start_date: date | None = None
    end_date: date | None = None
    currently_studying: bool | None = False
    grade: str | None = Field(None, max_length=50)


class EducationCreate(EducationBase):
    pass


class EducationUpdate(BaseModel):
    institution: str | None = Field(None, max_length=255)
    degree: str | None = Field(None, max_length=255)
    field_of_study: str | None = Field(None, max_length=255)
    start_date: date | None = None
    end_date: date | None = None
    currently_studying: bool | None = None
    grade: str | None = Field(None, max_length=50)


class EducationResponse(EducationBase):
    id: UUID
    profile_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SkillCategoryResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


class SkillResponse(BaseModel):
    id: UUID
    name: str
    category: SkillCategoryResponse | None = None
    description: str | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class SkillSearchResponse(BaseModel):
    id: UUID
    name: str
    category: str | None = None
    matched_by: str  # "name" or "alias"

    model_config = ConfigDict(from_attributes=True)


class ProfileSkillBase(BaseModel):
    skill_name: str = Field(..., max_length=100)
    proficiency: str | None = Field(None, max_length=50)


class ProfileSkillCreate(ProfileSkillBase):
    pass


class ProfileSkillUpdate(BaseModel):
    proficiency: str | None = Field(None, max_length=50)


class ProfileSkillResponse(BaseModel):
    id: UUID
    profile_id: UUID
    skill_id: UUID | None = None
    custom_skill_name: str | None = None
    skill_name: str
    proficiency: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None
    url: str | None = Field(None, max_length=500)
    start_date: date | None = None
    end_date: date | None = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    url: str | None = Field(None, max_length=500)
    start_date: date | None = None
    end_date: date | None = None


class ProjectResponse(ProjectBase):
    id: UUID
    profile_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExperienceBase(BaseModel):
    title: str = Field(..., max_length=255)
    company: str = Field(..., max_length=255)
    location: str | None = Field(None, max_length=255)
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False


class ExperienceCreate(ExperienceBase):
    @model_validator(mode="after")
    def validate_dates(self) -> "ExperienceCreate":
        if self.is_current and self.end_date is not None:
            raise ValueError("If is_current is true, end_date must be null.")

        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValueError("end_date must not be earlier than start_date.")

        return self


class ExperienceUpdate(BaseModel):
    title: str | None = Field(None, max_length=255)
    company: str | None = Field(None, max_length=255)
    location: str | None = Field(None, max_length=255)
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool | None = None


class ExperienceResponse(ExperienceBase):
    id: UUID
    profile_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExperienceSkillCreate(BaseModel):
    profile_skill_id: UUID


class ExperienceSkillResponse(BaseModel):
    id: UUID
    profile_skill_id: UUID
    skill_id: UUID | None = None
    skill_name: str
    is_custom: bool
    proficiency: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


def normalize_string_list(
    v: list[str] | None, allowed_values: list[str] | None = None
) -> list[str]:
    if not v:
        return []
    seen = set()
    result = []
    for item in v:
        clean = item.strip()
        if not clean:
            continue
        clean_lower = clean.lower()
        if clean_lower not in seen:
            seen.add(clean_lower)
            if allowed_values:
                match = next(
                    (av for av in allowed_values if av.lower() == clean_lower), None
                )
                if match:
                    result.append(match)
                else:
                    raise ValueError(
                        f"Invalid value: {clean}. Allowed values: {', '.join(allowed_values)}"
                    )
            else:
                result.append(clean)
    return result


class CareerPreferenceUpsert(BaseModel):
    desired_roles: list[str] = Field(default_factory=list, max_length=20)
    locations: list[str] = Field(default_factory=list, max_length=20)
    job_type: list[str] = Field(default_factory=list, max_length=10)
    work_model: list[str] = Field(default_factory=list, max_length=10)
    preferred_domains: list[str] = Field(default_factory=list, max_length=20)
    sponsorship_needed: bool | None = None

    @field_validator("desired_roles", "locations", "preferred_domains", mode="before")
    @classmethod
    def validate_free_lists(cls, v: list[str] | None) -> list[str]:
        # Truncate individual strings to 100 chars
        normalized = normalize_string_list(v)
        return [item[:100] for item in normalized]

    @field_validator("job_type", mode="before")
    @classmethod
    def validate_job_type(cls, v: list[str] | None) -> list[str]:
        return normalize_string_list(
            v, ["Internship", "Full-Time", "Part-Time", "Contract"]
        )

    @field_validator("work_model", mode="before")
    @classmethod
    def validate_work_model(cls, v: list[str] | None) -> list[str]:
        return normalize_string_list(v, ["Remote", "Hybrid", "On-site"])


class CareerPreferenceResponse(BaseModel):
    id: UUID
    profile_id: UUID
    desired_roles: list[str] | None
    locations: list[str] | None
    job_type: list[str] | None
    work_model: list[str] | None
    preferred_domains: list[str] | None
    sponsorship_needed: bool | None
    created_at: datetime
    updated_at: datetime


# ==========================================
# Resume
# ==========================================


class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    profile_id: UUID
    original_filename: str
    file_type: str
    file_size: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ResumeDownloadResponse(BaseModel):
    signed_url: str
    original_filename: str
    file_type: str

# ==========================================
# Profile Picture
# ==========================================

class ProfilePictureResponse(BaseModel):
    signed_url: str
