"""Update Skills architecture

Revision ID: a91ce669d065
Revises: 7996515e0884
Create Date: 2026-10-05 19:08:41.912530

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a91ce669d065"
down_revision: str | Sequence[str] | None = "7996515e0884"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "skill_categories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_skill_categories_slug"), "skill_categories", ["slug"], unique=True
    )
    op.create_table(
        "skill_aliases",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("skill_id", sa.UUID(), nullable=False),
        sa.Column("alias", sa.String(length=100), nullable=False),
        sa.Column("normalized_alias", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_skill_aliases_normalized_alias"),
        "skill_aliases",
        ["normalized_alias"],
        unique=True,
    )
    op.add_column(
        "profile_skills",
        sa.Column("custom_skill_name", sa.String(length=100), nullable=True),
    )
    op.alter_column(
        "profile_skills", "skill_id", existing_type=sa.UUID(), nullable=True
    )
    op.create_index(
        "uix_profile_custom_skill",
        "profile_skills",
        ["profile_id", sa.literal_column("lower(custom_skill_name)")],
        unique=True,
        postgresql_where=sa.text("custom_skill_name IS NOT NULL"),
    )
    op.create_check_constraint(
        "chk_skill_or_custom",
        "profile_skills",
        "(skill_id IS NOT NULL AND custom_skill_name IS NULL) OR (skill_id IS NULL AND custom_skill_name IS NOT NULL)",
    )

    op.add_column(
        "skills", sa.Column("normalized_name", sa.String(length=100), nullable=True)
    )
    op.add_column("skills", sa.Column("category_id", sa.UUID(), nullable=True))
    op.add_column("skills", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("skills", sa.Column("is_active", sa.Boolean(), nullable=True))
    op.add_column(
        "skills", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True)
    )

    op.execute(
        "UPDATE skills SET normalized_name = lower(name), is_active = true, updated_at = created_at"
    )

    op.alter_column("skills", "normalized_name", nullable=False)
    op.alter_column("skills", "is_active", nullable=False)
    op.alter_column("skills", "updated_at", nullable=False)

    op.drop_index("ix_skill_name_lower", table_name="skills", if_exists=True)
    op.execute("ALTER TABLE skills DROP CONSTRAINT IF EXISTS skills_name_key")
    op.drop_index(op.f("ix_skills_name"), table_name="skills", if_exists=True)

    op.create_index(
        op.f("ix_skills_normalized_name"), "skills", ["normalized_name"], unique=True
    )
    op.create_foreign_key(
        "fk_skills_category_id",
        "skills",
        "skill_categories",
        ["category_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_skills_category_id", "skills", type_="foreignkey")
    op.drop_index(op.f("ix_skills_normalized_name"), table_name="skills")
    op.create_index("ix_skills_name", "skills", ["name"], unique=True)
    op.create_index(
        "ix_skill_name_lower",
        "skills",
        [sa.text("lower(name::text)")],
        unique=True,
    )
    op.execute("ALTER TABLE skills ADD CONSTRAINT skills_name_key UNIQUE (name)")

    op.drop_column("skills", "updated_at")
    op.drop_column("skills", "is_active")
    op.drop_column("skills", "description")
    op.drop_column("skills", "category_id")
    op.drop_column("skills", "normalized_name")

    op.drop_constraint("chk_skill_or_custom", "profile_skills", type_="check")
    op.drop_index(
        "uix_profile_custom_skill",
        table_name="profile_skills",
        postgresql_where=sa.text("custom_skill_name IS NOT NULL"),
    )
    # Reverting skill_id to nullable=False requires handling existing custom skills
    # Since we can't revert custom skills cleanly without a dummy skill, we just delete them or alter
    op.execute("DELETE FROM profile_skills WHERE skill_id IS NULL")
    op.alter_column(
        "profile_skills", "skill_id", existing_type=sa.UUID(), nullable=False
    )
    op.drop_column("profile_skills", "custom_skill_name")

    op.drop_index(op.f("ix_skill_aliases_normalized_alias"), table_name="skill_aliases")
    op.drop_table("skill_aliases")
    op.drop_index(op.f("ix_skill_categories_slug"), table_name="skill_categories")
    op.drop_table("skill_categories")
