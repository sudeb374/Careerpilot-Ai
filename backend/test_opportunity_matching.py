import os
import sys
from datetime import date
from uuid import uuid4

import pytest

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.database import async_session_factory
from app.models.opportunity import Opportunity, OpportunitySkill
from app.models.profile import (
    CareerPreference,
    Education,
    Experience,
    Profile,
    ProfileSkill,
    Resume,
    Skill,
)
from app.services.matching import calculate_opportunity_match


async def setup_test_data(db):
    user_id = uuid4()
    profile = Profile(user_id=user_id, full_name="Match Test Student")
    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    # Add Skills
    async def get_or_create_skill(name: str):
        norm = name.lower()
        from sqlalchemy import select
        res = await db.execute(select(Skill).where(Skill.normalized_name == norm))
        skill = res.scalar_one_or_none()
        if not skill:
            skill = Skill(id=uuid4(), name=name, normalized_name=norm)
            db.add(skill)
            await db.commit()
            await db.refresh(skill)
        return skill

    skill_python = await get_or_create_skill("Python")
    skill_react = await get_or_create_skill("React")
    skill_java = await get_or_create_skill("Java")

    return {
        "profile": profile,
        "skill_python": skill_python,
        "skill_react": skill_react,
        "skill_java": skill_java
    }

async def cleanup_test_data(db, data):
    # Delete the test profile (which cascades to Resume, Education, Experience, ProfileSkill, CareerPreference)
    await db.execute(Profile.__table__.delete().where(Profile.id == data["profile"].id))
    
    # The OpportunitySkill table has CASCADE from Opportunity, but we didn't create an Opportunity in setup_test_data!
    # Wait, test_opportunity_matching doesn't create any Opportunities in setup_test_data. It only tests matching logic on dummy Opportunity instances.
    # So we don't need to delete from Opportunity.__table__ or OpportunitySkill.__table__ here!
    await db.commit()

from unittest.mock import patch

@pytest.mark.anyio
async def test_matching_logic():
    with patch('app.services.matching.is_model_available', return_value=False):
        async with async_session_factory() as db:
            data = await setup_test_data(db)
            profile = data["profile"]
        
        # Candidate Evidence
        # Profile Skill: Python
        ps1 = ProfileSkill(profile_id=profile.id, skill_id=data["skill_python"].id, proficiency="intermediate")
        db.add(ps1)
        
        # Resume Skill: React
        resume = Resume(
            profile_id=profile.id,
            original_filename="test.pdf",
            storage_path=f"test/{uuid4().hex}.pdf",
            file_type="application/pdf",
            file_size=1024,
            is_active=True,
            structured_data={
                "skills": [
                    {"skill_id": str(data["skill_react"].id), "name": "React", "evidence": "Built app"}
                ]
            }
        )
        db.add(resume)
        
        # Career Preferences
        prefs = CareerPreference(
            profile_id=profile.id,
            desired_roles=["Software Engineer"],
            locations=["New York", "Remote"],
            work_model=["Remote", "Hybrid"],
            preferred_domains=["Technology", "Finance"]
        )
        db.add(prefs)
        
        # Experience
        exp = Experience(
            profile_id=profile.id,
            title="Intern",
            company="Tech Corp",
            start_date=date(2021, 1, 1),
            end_date=date(2023, 1, 1) # 2 years
        )
        db.add(exp)
        
        # Opportunity 1: Full match (Published)
        opp1 = Opportunity(
            title="Software Engineer Intern",
            company_name="Acme",
            opportunity_type="Internship",
            work_model="Remote",
            locations=["Remote"],
            domain="Technology",
            required_experience_min=1,
            required_experience_max=3,
            status="Published"
        )
        db.add(opp1)
        await db.commit()
        await db.refresh(opp1)
        
        os1 = OpportunitySkill(opportunity_id=opp1.id, skill_id=data["skill_python"].id)
        os2 = OpportunitySkill(opportunity_id=opp1.id, skill_id=data["skill_react"].id)
        db.add_all([os1, os2])
        await db.commit()
        
        # Test Full Match
        res1 = await calculate_opportunity_match(db, profile.id, opp1.id)
        assert res1.score == 100.0
        assert res1.data_coverage == "High"
        assert res1.score_label == "Strong Match"
        
        # Opportunity 2: Partial match (Published)
        # Missing required skill (Java)
        # Title doesn't match role exactly (Data Scientist)
        # Location doesn't match (San Francisco) and model is On-site
        # Domain doesn't match (Healthcare)
        opp2 = Opportunity(
            title="Data Scientist",
            company_name="BioTech",
            opportunity_type="Full-Time",
            work_model="On-site",
            locations=["San Francisco"],
            domain="Healthcare",
            required_experience_min=5, # Doesn't match experience (Candidate has 2)
            education_requirements="PhD required",
            status="Published"
        )
        db.add(opp2)
        await db.commit()
        await db.refresh(opp2)
        
        os3 = OpportunitySkill(opportunity_id=opp2.id, skill_id=data["skill_java"].id)
        os4 = OpportunitySkill(opportunity_id=opp2.id, skill_id=data["skill_python"].id)
        db.add_all([os3, os4])
        await db.commit()
        
        res2 = await calculate_opportunity_match(db, profile.id, opp2.id)
        # Points calculation:
        # Skills: Python matched, Java missing (1/2) * 40 = 20
        # Role: No match = 0
        # Work Model/Location: No match = 0
        # Experience: Cand has 2y, req 5y. exp_assessed = True, No match = 0
        # Education: has text = not_assessed
        # Domain: Healthcare != Technology/Finance = 0
        
        assert res2.score == round((20 / 92.5) * 100, 1) # 21.6
        assert "Education Text" in res2.components_not_assessed
        
        # Opportunity 3: Draft
        opp3 = Opportunity(
            title="Software Engineer Intern",
            company_name="Acme",
            opportunity_type="Internship",
            work_model="Remote",
            locations=["Remote"],
            domain="Technology",
            status="Draft"
        )
        db.add(opp3)
        await db.commit()
        await db.refresh(opp3)
        
        res3 = await calculate_opportunity_match(db, profile.id, opp3.id)
        assert res3.score is None
        assert res3.data_coverage == "Unavailable"
        assert "Opportunity is not Published" in res3.mismatched_preferences[0]

        # Cleanup
        await cleanup_test_data(db, data)
