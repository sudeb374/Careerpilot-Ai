import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


def utcnow():
    return datetime.now(timezone.utc)


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # References Supabase auth.users.id
    user_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    headline = Column(String(500), nullable=True)
    location = Column(String(255), nullable=True)
    about = Column(Text, nullable=True)
    phone = Column(String(30), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    github_url = Column(String(500), nullable=True)
    portfolio_url = Column(String(500), nullable=True)
    profile_picture_path = Column(String(500), nullable=True)
    role = Column(String(50), nullable=False, server_default="student")
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    __table_args__ = (
        CheckConstraint("role IN ('student', 'admin')", name="chk_profile_role"),
    )

    # Relationships
    educations = relationship(
        "Education", back_populates="profile", cascade="all, delete-orphan"
    )
    projects = relationship(
        "Project", back_populates="profile", cascade="all, delete-orphan"
    )
    experiences = relationship(
        "Experience", back_populates="profile", cascade="all, delete-orphan"
    )
    career_preferences = relationship(
        "CareerPreference",
        uselist=False,
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    skills = relationship(
        "ProfileSkill", back_populates="profile", cascade="all, delete-orphan"
    )
    resumes = relationship(
        "Resume", back_populates="profile", cascade="all, delete-orphan"
    )


class Education(Base):
    __tablename__ = "educations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    institution = Column(String(255), nullable=False)
    degree = Column(String(255), nullable=False)
    field_of_study = Column(String(255), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    grade = Column(String(50), nullable=True)
    currently_studying = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    profile = relationship("Profile", back_populates="educations")


class SkillCategory(Base):
    __tablename__ = "skill_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    skills = relationship("Skill", back_populates="category")


class Skill(Base):
    """Global list of skills to avoid duplication."""

    __tablename__ = "skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    normalized_name = Column(String(100), unique=True, nullable=False, index=True)
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("skill_categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    category = relationship("SkillCategory", back_populates="skills")
    aliases = relationship(
        "SkillAlias", back_populates="skill", cascade="all, delete-orphan"
    )
    profile_skills = relationship(
        "ProfileSkill", back_populates="skill", cascade="all, delete-orphan"
    )


class SkillAlias(Base):
    __tablename__ = "skill_aliases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    skill_id = Column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False
    )
    alias = Column(String(100), nullable=False)
    normalized_alias = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    skill = relationship("Skill", back_populates="aliases")


class ProfileSkill(Base):
    """Link table between Profile and Skill with proficiency."""

    __tablename__ = "profile_skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_id = Column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=True
    )
    custom_skill_name = Column(String(100), nullable=True)
    proficiency = Column(
        String(50), nullable=True
    )  # e.g., beginner, intermediate, advanced
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    profile = relationship("Profile", back_populates="skills")
    skill = relationship("Skill", back_populates="profile_skills")
    experience_skills = relationship(
        "ExperienceSkill", back_populates="profile_skill", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("profile_id", "skill_id", name="uix_profile_skill"),
        Index(
            "uix_profile_custom_skill",
            "profile_id",
            func.lower(custom_skill_name),
            unique=True,
            postgresql_where=custom_skill_name.isnot(None),
        ),
        CheckConstraint(
            "(skill_id IS NOT NULL AND custom_skill_name IS NULL) OR (skill_id IS NULL AND custom_skill_name IS NOT NULL)",
            name="chk_skill_or_custom",
        ),
    )


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    profile = relationship("Profile", back_populates="projects")


class Experience(Base):
    __tablename__ = "experiences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    is_current = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    profile = relationship("Profile", back_populates="experiences")
    skills = relationship(
        "ExperienceSkill", back_populates="experience", cascade="all, delete-orphan"
    )


class CareerPreference(Base):
    __tablename__ = "career_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    desired_roles = Column(ARRAY(String), nullable=True)
    locations = Column(ARRAY(String), nullable=True)
    job_type = Column(ARRAY(String), nullable=True)
    work_model = Column(ARRAY(String), nullable=True)
    preferred_domains = Column(ARRAY(String), nullable=True)
    sponsorship_needed = Column(Boolean, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    profile = relationship("Profile", back_populates="career_preferences")


class ExperienceSkill(Base):
    __tablename__ = "experience_skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experience_id = Column(
        UUID(as_uuid=True),
        ForeignKey("experiences.id", ondelete="CASCADE"),
        nullable=False,
    )
    profile_skill_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profile_skills.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    experience = relationship("Experience", back_populates="skills")
    profile_skill = relationship("ProfileSkill", back_populates="experience_skills")

    __table_args__ = (
        UniqueConstraint(
            "experience_id", "profile_skill_id", name="uix_exp_profile_skill"
        ),
    )


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False, unique=True)
    file_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    parsed_text = Column(Text, nullable=True)
    structured_data = Column(JSONB, nullable=True)
    analysis_data = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    profile = relationship("Profile", back_populates="resumes")

    __table_args__ = (
        CheckConstraint("file_size > 0", name="chk_resume_file_size_positive"),
    )

    @property
    def has_parsed_text(self) -> bool:
        return self.parsed_text is not None

    @property
    def has_structured_data(self) -> bool:
        return self.structured_data is not None

    @property
    def has_analysis(self) -> bool:
        return self.analysis_data is not None
