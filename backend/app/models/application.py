import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


def utcnow():
    return datetime.now(timezone.utc)


class Application(Base):
    """
    Application tracking record for an authenticated student candidate.
    Links candidate profile to an opportunity with workflow lifecycle status,
    deadlines, personal notes, and reminders.
    """

    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    opportunity_id = Column(
        UUID(as_uuid=True),
        ForeignKey("opportunities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(
        String(50),
        nullable=False,
        default="Applied",
        index=True,
    )
    applied_at = Column(DateTime(timezone=True), nullable=True)
    status_updated_at = Column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )
    deadline = Column(DateTime(timezone=True), nullable=True, index=True)
    reminder_at = Column(DateTime(timezone=True), nullable=True, index=True)
    reminder_note = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    # Relationships
    profile = relationship("Profile")
    opportunity = relationship("Opportunity")
    history = relationship(
        "ApplicationStatusHistory",
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="ApplicationStatusHistory.created_at.desc()",
    )

    __table_args__ = (
        UniqueConstraint(
            "profile_id",
            "opportunity_id",
            name="uix_profile_opportunity_application",
        ),
        CheckConstraint(
            "status IN ('Saved', 'Applied', 'Assessment', 'Interview', 'Offer', 'Rejected', 'Withdrawn')",
            name="chk_application_status",
        ),
    )


class ApplicationStatusHistory(Base):
    """
    Audit log of status changes and milestones for an application.
    """

    __tablename__ = "application_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_status = Column(String(50), nullable=True)
    to_status = Column(String(50), nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    application = relationship("Application", back_populates="history")
