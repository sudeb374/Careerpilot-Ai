"""
CareerPilot AI — Idempotent Interview Question Bank Seeder.

Seeds or updates curated interview questions safely and idempotently.
Can be executed as a CLI command or imported directly in tests/migrations.

Usage:
    python -m app.seeds.seed_interview_questions [--dry-run]
"""

import argparse
import asyncio
import logging
import sys
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.database import async_session_factory
from app.models.interview_question import InterviewQuestion
from app.seeds.interview_questions_data import CURATED_INTERVIEW_QUESTIONS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


async def seed_interview_questions(
    db: AsyncSession,
    questions: list[dict[str, Any]] | None = None,
    dry_run: bool = False,
) -> dict[str, int]:
    """
    Idempotently seed interview questions into the database.
    Updates existing questions matched by stable identifier, or inserts new ones.
    Does not duplicate existing questions on repeated runs.
    """
    target_questions = questions if questions is not None else CURATED_INTERVIEW_QUESTIONS
    stats = {"created": 0, "updated": 0, "unchanged": 0, "total_processed": len(target_questions)}

    for q_data in target_questions:
        identifier = q_data["identifier"]
        stmt = select(InterviewQuestion).where(InterviewQuestion.identifier == identifier)
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()

        if existing:
            # Check if fields need updating
            has_changes = False
            for field in [
                "question_text",
                "category",
                "difficulty",
                "role_tags",
                "is_general",
                "skill_tags",
                "expected_points",
                "rubric",
                "reference_answer",
                "is_active",
            ]:
                new_val = q_data.get(field)
                old_val = getattr(existing, field)
                if old_val != new_val:
                    setattr(existing, field, new_val)
                    has_changes = True

            if has_changes:
                stats["updated"] += 1
            else:
                stats["unchanged"] += 1
        else:
            new_question = InterviewQuestion(
                identifier=q_data["identifier"],
                question_text=q_data["question_text"],
                category=q_data["category"],
                difficulty=q_data["difficulty"],
                role_tags=q_data.get("role_tags", []),
                is_general=q_data.get("is_general", False),
                skill_tags=q_data.get("skill_tags", []),
                expected_points=q_data.get("expected_points", []),
                rubric=q_data.get("rubric"),
                reference_answer=q_data.get("reference_answer"),
                is_active=q_data.get("is_active", True),
            )
            db.add(new_question)
            stats["created"] += 1

    if dry_run:
        await db.rollback()
        logger.info("[DRY RUN] Rolled back all changes: %s", stats)
    else:
        await db.commit()
        logger.info("Successfully applied seed data: %s", stats)

    return stats


async def main() -> None:
    parser = argparse.ArgumentParser(description="Seed interview question bank idempotently.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the seed run without committing to the database.",
    )
    args = parser.parse_args()

    # Safety confirmation if running against an external or Supabase database
    db_url = settings.database_url or ""
    if "supabase" in db_url.lower() or "pooler" in db_url.lower():
        logger.warning(
            "Target database appears to be a remote Supabase instance. "
            "Production safety: verify this is intentional."
        )

    async with async_session_factory() as session:
        try:
            results = await seed_interview_questions(session, dry_run=args.dry_run)
            logger.info("Finished interview question seeding summary: %s", results)
        except Exception as exc:
            logger.exception("Failed to seed interview questions: %s", exc)
            await session.rollback()
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
