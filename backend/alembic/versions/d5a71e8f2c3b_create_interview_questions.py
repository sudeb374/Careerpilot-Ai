"""create_interview_questions

Revision ID: d5a71e8f2c3b
Revises: a9c850dac4bc
Create Date: 2026-10-14 11:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd5a71e8f2c3b'
down_revision: str | Sequence[str] | None = 'a9c850dac4bc'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'interview_questions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('identifier', sa.String(length=100), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('difficulty', sa.String(length=50), nullable=False),
        sa.Column('role_tags', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('is_general', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('skill_tags', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('expected_points', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('rubric', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('reference_answer', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "category IN ('Technical', 'HR/Behavioural', 'Project-Based')",
            name='chk_interview_question_category'
        ),
        sa.CheckConstraint(
            "difficulty IN ('Beginner', 'Intermediate', 'Advanced')",
            name='chk_interview_question_difficulty'
        ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        op.f('ix_interview_questions_identifier'),
        'interview_questions',
        ['identifier'],
        unique=True
    )
    op.create_index(
        op.f('ix_interview_questions_category'),
        'interview_questions',
        ['category'],
        unique=False
    )
    op.create_index(
        op.f('ix_interview_questions_difficulty'),
        'interview_questions',
        ['difficulty'],
        unique=False
    )
    op.create_index(
        op.f('ix_interview_questions_is_general'),
        'interview_questions',
        ['is_general'],
        unique=False
    )
    op.create_index(
        op.f('ix_interview_questions_is_active'),
        'interview_questions',
        ['is_active'],
        unique=False
    )
    op.create_index(
        'ix_interview_questions_category_diff',
        'interview_questions',
        ['category', 'difficulty'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_interview_questions_category_diff', table_name='interview_questions')
    op.drop_index(op.f('ix_interview_questions_is_active'), table_name='interview_questions')
    op.drop_index(op.f('ix_interview_questions_is_general'), table_name='interview_questions')
    op.drop_index(op.f('ix_interview_questions_difficulty'), table_name='interview_questions')
    op.drop_index(op.f('ix_interview_questions_category'), table_name='interview_questions')
    op.drop_index(op.f('ix_interview_questions_identifier'), table_name='interview_questions')
    op.drop_table('interview_questions')
