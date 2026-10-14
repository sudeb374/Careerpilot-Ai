"""create_applications_and_history

Revision ID: e8c91a72d4f0
Revises: d5a71e8f2c3b
Create Date: 2026-10-14 21:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e8c91a72d4f0'
down_revision: str | Sequence[str] | None = 'd5a71e8f2c3b'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema: Create applications and application_status_history tables."""
    op.create_table(
        'applications',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('profile_id', sa.UUID(), nullable=False),
        sa.Column('opportunity_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='Applied', nullable=False),
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status_updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reminder_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reminder_note', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['profile_id'], ['profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('profile_id', 'opportunity_id', name='uix_profile_opportunity_application'),
        sa.CheckConstraint(
            "status IN ('Saved', 'Applied', 'Assessment', 'Interview', 'Offer', 'Rejected', 'Withdrawn')",
            name='chk_application_status',
        ),
    )
    op.create_index('ix_applications_profile_id', 'applications', ['profile_id'], unique=False)
    op.create_index('ix_applications_opportunity_id', 'applications', ['opportunity_id'], unique=False)
    op.create_index('ix_applications_status', 'applications', ['status'], unique=False)
    op.create_index('ix_applications_deadline', 'applications', ['deadline'], unique=False)
    op.create_index('ix_applications_reminder_at', 'applications', ['reminder_at'], unique=False)

    op.create_table(
        'application_status_history',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('application_id', sa.UUID(), nullable=False),
        sa.Column('from_status', sa.String(length=50), nullable=True),
        sa.Column('to_status', sa.String(length=50), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_application_status_history_application_id',
        'application_status_history',
        ['application_id'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema: Drop application_status_history and applications tables."""
    op.drop_index('ix_application_status_history_application_id', table_name='application_status_history')
    op.drop_table('application_status_history')

    op.drop_index('ix_applications_reminder_at', table_name='applications')
    op.drop_index('ix_applications_deadline', table_name='applications')
    op.drop_index('ix_applications_status', table_name='applications')
    op.drop_index('ix_applications_opportunity_id', table_name='applications')
    op.drop_index('ix_applications_profile_id', table_name='applications')
    op.drop_table('applications')
