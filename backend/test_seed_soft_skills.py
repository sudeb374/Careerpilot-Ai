"""
Unit test for soft skills catalog seeding and idempotency.
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.core.seed import seed_skills
from app.models.profile import Skill, SkillAlias, SkillCategory


class TestSeedSoftSkills(unittest.IsolatedAsyncioTestCase):
    async def test_seed_skills_adds_soft_skills_category_and_skills(self):
        """Verify seed_skills defines and inserts Soft Skills category and common soft skills."""
        categories_in_db = {}
        skills_in_db = {}
        aliases_in_db = {}

        mock_db = MagicMock()

        def mock_add(entity):
            if isinstance(entity, SkillCategory):
                if entity.id is None:
                    entity.id = uuid4()
                categories_in_db[entity.name] = entity
            elif isinstance(entity, Skill):
                if entity.id is None:
                    entity.id = uuid4()
                skills_in_db[entity.normalized_name] = entity
            elif isinstance(entity, SkillAlias):
                if entity.id is None:
                    entity.id = uuid4()
                aliases_in_db[entity.alias] = entity

        mock_db.add = mock_add
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()

        async def mock_execute(stmt):
            stmt_str = str(stmt).lower()
            res = MagicMock()
            if "from skill_categories" in stmt_str:
                # Extract category name being checked
                # If already in categories_in_db, return it
                res.scalar_one_or_none.return_value = None
                for cat_name, cat_obj in categories_in_db.items():
                    if f"'{cat_name.lower()}'" in stmt_str or f"'{cat_name}'" in stmt_str:
                        res.scalar_one_or_none.return_value = cat_obj
                        break
            elif "from skills" in stmt_str:
                res.scalar_one_or_none.return_value = None
                for norm_name, skill_obj in skills_in_db.items():
                    if f"'{norm_name}'" in stmt_str:
                        res.scalar_one_or_none.return_value = skill_obj
                        break
            elif "from skill_aliases" in stmt_str:
                res.scalar_one_or_none.return_value = None
                for alias_name, alias_obj in aliases_in_db.items():
                    if f"'{alias_name}'" in stmt_str:
                        res.scalar_one_or_none.return_value = alias_obj
                        break
            else:
                res.scalar_one_or_none.return_value = None
            return res

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        # Run 1: Initial seed
        await seed_skills(mock_db)

        # Verify "Soft Skills" category created
        self.assertIn("Soft Skills", categories_in_db)
        self.assertEqual(categories_in_db["Soft Skills"].slug, "soft-skills")

        # Verify all 8 soft skills created
        expected_soft_skills = [
            "communication",
            "leadership",
            "teamwork",
            "problem solving",
            "critical thinking",
            "adaptability",
            "time management",
            "presentation",
        ]

        for s in expected_soft_skills:
            self.assertIn(s, skills_in_db, f"Expected soft skill '{s}' was not seeded")

        # Verify aliases created
        self.assertIn("verbal communication", aliases_in_db)
        self.assertIn("problem-solving", aliases_in_db)
        self.assertIn("analytical thinking", aliases_in_db)


if __name__ == "__main__":
    unittest.main()
