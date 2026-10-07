import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    and_,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


def utcnow():
    return datetime.now(timezone.utc)


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=False, index=True)
    company_website = Column(String(500), nullable=True)
    company_logo_url = Column(String(500), nullable=True)
    
    description = Column(Text, nullable=True)

    opportunity_type = Column(String(50), nullable=False, index=True)
    work_model = Column(String(50), nullable=False)
    
    locations = Column(ARRAY(String), nullable=True)
    domain = Column(String(255), nullable=True)
    
    required_experience_min = Column(Integer, default=0, nullable=False)
    required_experience_max = Column(Integer, nullable=True)
    
    education_requirements = Column(Text, nullable=True)
    eligibility = Column(Text, nullable=True)
    
    application_url = Column(String(500), nullable=True)
    deadline = Column(DateTime(timezone=True), nullable=True, index=True)
    
    stipend_min = Column(Integer, nullable=True)
    stipend_max = Column(Integer, nullable=True)
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    currency = Column(String(10), nullable=True)
    
    source_name = Column(String(100), nullable=True)
    source_url = Column(String(500), nullable=True)
    external_id = Column(String(255), nullable=True)
    
    status = Column(String(50), nullable=False, index=True, server_default="Draft")
    
    created_by_profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    # Relationships
    creator = relationship("Profile", foreign_keys=[created_by_profile_id])
    skills = relationship(
        "OpportunitySkill", back_populates="opportunity", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "opportunity_type IN ('Internship', 'Full-Time')", 
            name="chk_opportunity_type"
        ),
        CheckConstraint(
            "work_model IN ('Remote', 'Hybrid', 'On-site')", 
            name="chk_work_model"
        ),
        CheckConstraint(
            "status IN ('Draft', 'Published', 'Closed', 'Expired')", 
            name="chk_opportunity_status"
        ),
        CheckConstraint(
            "required_experience_min >= 0", 
            name="chk_req_exp_min_positive"
        ),
        CheckConstraint(
            "required_experience_max IS NULL OR required_experience_max >= required_experience_min", 
            name="chk_req_exp_max_valid"
        ),
        CheckConstraint(
            "stipend_min IS NULL OR stipend_min >= 0", 
            name="chk_stipend_min_positive"
        ),
        CheckConstraint(
            "stipend_max IS NULL OR stipend_min IS NULL OR stipend_max >= stipend_min", 
            name="chk_stipend_max_valid"
        ),
        CheckConstraint(
            "salary_min IS NULL OR salary_min >= 0", 
            name="chk_salary_min_positive"
        ),
        CheckConstraint(
            "salary_max IS NULL OR salary_min IS NULL OR salary_max >= salary_min", 
            name="chk_salary_max_valid"
        ),
        # Unique constraint for external_id per source
        Index(
            "uix_opportunity_source_external_id",
            "source_name",
            "external_id",
            unique=True,
            postgresql_where=and_(external_id.isnot(None), source_name.isnot(None))
        ),
    )


class OpportunitySkill(Base):
    __tablename__ = "opportunity_skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opportunity_id = Column(
        UUID(as_uuid=True),
        ForeignKey("opportunities.id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_id = Column(
        UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    opportunity = relationship("Opportunity", back_populates="skills")
    skill = relationship("Skill")

    __table_args__ = (
        UniqueConstraint("opportunity_id", "skill_id", name="uix_opportunity_skill"),
    )


class SavedOpportunity(Base):
    __tablename__ = "saved_opportunities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    opportunity_id = Column(
        UUID(as_uuid=True),
        ForeignKey("opportunities.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    profile = relationship("Profile")
    opportunity = relationship("Opportunity")

    __table_args__ = (
        UniqueConstraint("profile_id", "opportunity_id", name="uix_profile_saved_opportunity"),
    )
