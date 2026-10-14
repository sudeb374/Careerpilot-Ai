import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

from app.models.base import Base


def utcnow():
    return datetime.now(timezone.utc)


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    identifier = Column(String(100), unique=True, nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, index=True)
    difficulty = Column(String(50), nullable=False, index=True)
    role_tags = Column(ARRAY(String), nullable=False, default=list)
    is_general = Column(Boolean, nullable=False, default=False, index=True)
    skill_tags = Column(ARRAY(String), nullable=False, default=list)
    expected_points = Column(JSONB, nullable=False, default=list)
    rubric = Column(JSONB, nullable=True)
    reference_answer = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "category IN ('Technical', 'HR/Behavioural', 'Project-Based')",
            name="chk_interview_question_category",
        ),
        CheckConstraint(
            "difficulty IN ('Beginner', 'Intermediate', 'Advanced')",
            name="chk_interview_question_difficulty",
        ),
        Index("ix_interview_questions_category_diff", "category", "difficulty"),
        Index("ix_interview_questions_is_general", "is_general"),
    )
