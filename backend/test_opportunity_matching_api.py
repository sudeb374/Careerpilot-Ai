import os
import sys
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.database import async_session_factory
from app.core.dependencies import get_current_user
from app.main import app
from app.models.opportunity import Opportunity, OpportunitySkill
from app.models.profile import CareerPreference, Profile, ProfileSkill, Skill

TEST_USER_ID = str(uuid4())

async def setup_test_db():
    async with async_session_factory() as db:
        # Create profile
        result = await db.execute(select(Profile).where(Profile.user_id == TEST_USER_ID))
        if not result.scalar_one_or_none():
            db.add(Profile(user_id=TEST_USER_ID, full_name="Test API User"))
        
        await db.commit()
        
        result = await db.execute(select(Profile).where(Profile.user_id == TEST_USER_ID))
        profile = result.scalar_one()

        # Create skills
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

        skill1 = await get_or_create_skill("Python")
        skill2 = await get_or_create_skill("React")
        skill3 = await get_or_create_skill("Java")
        
        # Add Candidate Evidence
        ps1 = ProfileSkill(profile_id=profile.id, skill_id=skill1.id, proficiency="expert")
        db.add(ps1)
        prefs = CareerPreference(
            profile_id=profile.id,
            desired_roles=["Software Engineer"],
            locations=["Remote"],
            work_model=["Remote"],
            preferred_domains=["Technology"]
        )
        db.add(prefs)
        await db.commit()

        # Create opportunities with varying match scores
        
        # 1. High match: matches role, work model, location, domain, and skills
        opp_high = Opportunity(
            title="Software Engineer", 
            company_name="Tech Co", 
            opportunity_type="Full-Time", 
            work_model="Remote", 
            domain="Technology",
            locations=["Remote"],
            status="Published", 
            created_by_profile_id=profile.id
        )
        
        # 2. Medium match: matches work model and some skills, but different role and domain
        opp_medium = Opportunity(
            title="Data Analyst", 
            company_name="Finance Co", 
            opportunity_type="Full-Time", 
            work_model="Remote", 
            domain="Finance",
            locations=["New York"],
            status="Published", 
            created_by_profile_id=profile.id
        )
        
        # 3. Low match: matches nothing
        opp_low = Opportunity(
            title="HR Manager", 
            company_name="HR Co", 
            opportunity_type="Full-Time", 
            work_model="On-site", 
            domain="Human Resources",
            locations=["London"],
            status="Published", 
            created_by_profile_id=profile.id
        )

        opps = [
            opp_high, opp_medium, opp_low,
            Opportunity(title="Draft Opp", company_name="Draft", opportunity_type="Internship", work_model="Remote", status="Draft", created_by_profile_id=profile.id),
            Opportunity(title="Closed Opp", company_name="Closed", opportunity_type="Internship", work_model="Remote", status="Closed", created_by_profile_id=profile.id),
            Opportunity(title="Expired Opp", company_name="Exp", opportunity_type="Internship", work_model="Remote", status="Expired", created_by_profile_id=profile.id),
        ]
        db.add_all(opps)
        await db.commit()
        
        # Add skills to opportunities
        db.add(OpportunitySkill(opportunity_id=opp_high.id, skill_id=skill1.id)) # Python -> high score
        db.add(OpportunitySkill(opportunity_id=opp_medium.id, skill_id=skill1.id)) # Python -> medium score
        db.add(OpportunitySkill(opportunity_id=opp_medium.id, skill_id=skill2.id)) # React -> medium score penalty
        db.add(OpportunitySkill(opportunity_id=opp_low.id, skill_id=skill3.id)) # Java -> low score
        await db.commit()
        
        for opp in opps:
            await db.refresh(opp)

        return {
            "high_id": opp_high.id,
            "medium_id": opp_medium.id,
            "low_id": opp_low.id,
            "draft_id": opps[3].id,
            "closed_id": opps[4].id,
            "exp_id": opps[5].id,
        }

@pytest.mark.anyio
async def test_matching_api():
    app.dependency_overrides.clear()
    data = await setup_test_db()
    transport = ASGITransport(app=app)
    
    # 1. unauthenticated requests -> 401
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(f"/api/v1/opportunities/{data['high_id']}/match")
        assert res.status_code == 401
        
        res = await client.get("/api/v1/profile/opportunity-matches")
        assert res.status_code == 401

    # Override auth
    app.dependency_overrides[get_current_user] = lambda: TEST_USER_ID

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 2. authenticated request single match -> 200
        res = await client.get(f"/api/v1/opportunities/{data['high_id']}/match")
        assert res.status_code == 200
        json_data = res.json()
        assert "score" in json_data
        assert "data_coverage" in json_data
        
        # Privacy check
        assert "email" not in str(json_data).lower()
        assert "phone" not in str(json_data).lower()

        # 3. Draft/Closed/Expired -> 404
        for opp_id in [data['draft_id'], data['closed_id'], data['exp_id']]:
            res = await client.get(f"/api/v1/opportunities/{opp_id}/match")
            assert res.status_code == 404
            
        # Non-existent -> 404
        res = await client.get(f"/api/v1/opportunities/{uuid4()}/match")
        assert res.status_code == 404

        # 4. Ranked list match with distinct scores
        res = await client.get("/api/v1/profile/opportunity-matches?page=1&page_size=10")
        assert res.status_code == 200
        list_data = res.json()
        
        assert "items" in list_data
        items = list_data["items"]
        assert len(items) >= 3
        
        # Ensure draft/closed/expired are not in the results
        returned_ids = [item["opportunity"]["id"] for item in items]
        assert str(data['draft_id']) not in returned_ids
        assert str(data['closed_id']) not in returned_ids
        assert str(data['exp_id']) not in returned_ids
        
        # Verify Descending Order
        scores = [item["match"]["score"] for item in items]
        assert scores == sorted(scores, reverse=True), "Scores are not sorted in descending order"
        
        # Assert at least three distinct scores
        distinct_scores = set(scores)
        assert len(distinct_scores) >= 3, "Did not get at least 3 distinct scores for ranking validation"
        
        # Test pagination
        res_pag = await client.get("/api/v1/profile/opportunity-matches?page=1&page_size=2")
        assert res_pag.status_code == 200
        pag_data = res_pag.json()
        assert len(pag_data["items"]) == 2
        assert pag_data["page_size"] == 2
        assert pag_data["total"] >= 3
