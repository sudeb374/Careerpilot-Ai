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
from app.models.opportunity import Opportunity, SavedOpportunity
from app.models.profile import Profile

TEST_USER_A_ID = str(uuid4())
TEST_USER_B_ID = str(uuid4())

async def setup_test_db():
    async with async_session_factory() as db:
        # Create profiles
        for uid in [TEST_USER_A_ID, TEST_USER_B_ID]:
            result = await db.execute(select(Profile).where(Profile.user_id == uid))
            if not result.scalar_one_or_none():
                db.add(Profile(user_id=uid, full_name=f"Test User {uid}"))
        
        await db.commit()
        
        # Get profile IDs
        result = await db.execute(select(Profile).where(Profile.user_id.in_([TEST_USER_A_ID, TEST_USER_B_ID])))
        profiles = result.scalars().all()
        p_id_a = next(p.id for p in profiles if str(p.user_id) == TEST_USER_A_ID)
        p_id_b = next(p.id for p in profiles if str(p.user_id) == TEST_USER_B_ID)

        # Create opportunities
        opps = [
            Opportunity(title="Pub Opp", company_name="Pub", opportunity_type="Internship", work_model="Remote", status="Published"),
            Opportunity(title="Draft Opp", company_name="Draft", opportunity_type="Internship", work_model="Remote", status="Draft"),
            Opportunity(title="Closed Opp", company_name="Closed", opportunity_type="Internship", work_model="Remote", status="Closed"),
            Opportunity(title="Expired Opp", company_name="Exp", opportunity_type="Internship", work_model="Remote", status="Expired"),
        ]
        db.add_all(opps)
        await db.commit()
        
        for opp in opps:
            await db.refresh(opp)

        return {
            "p_id_a": p_id_a,
            "p_id_b": p_id_b,
            "pub_id": opps[0].id,
            "draft_id": opps[1].id,
            "closed_id": opps[2].id,
            "exp_id": opps[3].id,
        }

async def cleanup_test_db(data):
    async with async_session_factory() as db:
        await db.execute(SavedOpportunity.__table__.delete())
        await db.execute(Opportunity.__table__.delete().where(Opportunity.id.in_([
            data["pub_id"], data["draft_id"], data["closed_id"], data["exp_id"]
        ])))
        await db.execute(Profile.__table__.delete().where(Profile.user_id.in_([TEST_USER_A_ID, TEST_USER_B_ID])))
        await db.commit()

@pytest.mark.anyio
async def test_saved_opportunities():
    data = await setup_test_db()
    
    transport = ASGITransport(app=app)
    
    # 1. unauthenticated save -> 401
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(f"/api/v1/opportunities/{data['pub_id']}/save")
        assert res.status_code == 401

    # Override auth for Student A
    app.dependency_overrides[get_current_user] = lambda: TEST_USER_A_ID

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 2. authenticated save published -> 201
        res = await client.post(f"/api/v1/opportunities/{data['pub_id']}/save")
        assert res.status_code == 201

        # 3. duplicate save -> 409
        res = await client.post(f"/api/v1/opportunities/{data['pub_id']}/save")
        assert res.status_code == 409

        # 4. saved state -> true
        res = await client.get(f"/api/v1/opportunities/{data['pub_id']}/saved")
        assert res.status_code == 200
        assert res.json()["saved"] is True

        # 8, 9, 10. save Draft/Closed/Expired -> 404
        for opp_id in [data['draft_id'], data['closed_id'], data['exp_id']]:
            res = await client.post(f"/api/v1/opportunities/{opp_id}/save")
            assert res.status_code == 404

        # 11, 12, 13. saved list -> correct format
        res = await client.get("/api/v1/profile/saved-opportunities?page=1&page_size=10")
        assert res.status_code == 200
        list_data = res.json()
        assert list_data["total"] == 1
        assert list_data["items"][0]["id"] == str(data["pub_id"])

    # Switch to Student B
    app.dependency_overrides[get_current_user] = lambda: TEST_USER_B_ID

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 14. Student A cannot access Student B's saved state (check state for Student B is false)
        res = await client.get(f"/api/v1/opportunities/{data['pub_id']}/saved")
        assert res.status_code == 200
        assert res.json()["saved"] is False

        # 15. Student B's saved list is empty
        res = await client.get("/api/v1/profile/saved-opportunities")
        assert res.json()["total"] == 0

        # 16. Student B independently saves
        res = await client.post(f"/api/v1/opportunities/{data['pub_id']}/save")
        assert res.status_code == 201
        
    # Switch back to Student A to unsave
    app.dependency_overrides[get_current_user] = lambda: TEST_USER_A_ID
    
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 5. unsave -> 204
        res = await client.delete(f"/api/v1/opportunities/{data['pub_id']}/save")
        assert res.status_code == 204

        # 6. saved state after unsave -> false
        res = await client.get(f"/api/v1/opportunities/{data['pub_id']}/saved")
        assert res.json()["saved"] is False
        
        # 7. unsave unsaved -> 404
        res = await client.delete(f"/api/v1/opportunities/{data['pub_id']}/save")
        assert res.status_code == 404

    # Switch to Student B, B's relationship remains
    app.dependency_overrides[get_current_user] = lambda: TEST_USER_B_ID
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(f"/api/v1/opportunities/{data['pub_id']}/saved")
        assert res.json()["saved"] is True
        
        # 18. deleting saved relationship never deletes Opportunity
        res = await client.delete(f"/api/v1/opportunities/{data['pub_id']}/save")
        assert res.status_code == 204
        
        # check if opp still exists (by using an unauth request or DB check)
        
    # 17. deleting opportunity cleans up saved relationship
    async with async_session_factory() as db:
        # Re-save for student B
        db.add(SavedOpportunity(profile_id=data["p_id_b"], opportunity_id=data["pub_id"]))
        await db.commit()
        
        # Delete opportunity
        await db.execute(Opportunity.__table__.delete().where(Opportunity.id == data["pub_id"]))
        await db.commit()
        
        # Check if saved relationship is gone
        result = await db.execute(select(SavedOpportunity).where(SavedOpportunity.opportunity_id == data["pub_id"]))
        assert result.scalar_one_or_none() is None
        
    app.dependency_overrides.clear()
    await cleanup_test_db(data)
