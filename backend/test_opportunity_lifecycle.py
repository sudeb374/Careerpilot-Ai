import os
import sys
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.database import async_session_factory
from app.core.dependencies import get_current_user, require_admin
from app.main import app
from app.models.opportunity import Opportunity, SavedOpportunity
from app.models.profile import Profile

TEST_USER_ID = str(uuid4())
TEST_ADMIN_ID = str(uuid4())

def get_admin():
    return None  # We will override this to return the created admin profile

async def setup_test_db():
    async with async_session_factory() as db:
        # Create profile for student
        result = await db.execute(select(Profile).where(Profile.user_id == TEST_USER_ID))
        if not result.scalar_one_or_none():
            db.add(Profile(user_id=TEST_USER_ID, full_name="Test Student"))
            
        # Create profile for admin
        result = await db.execute(select(Profile).where(Profile.user_id == TEST_ADMIN_ID))
        if not result.scalar_one_or_none():
            db.add(Profile(user_id=TEST_ADMIN_ID, full_name="Test Admin", role="admin"))
            
        await db.commit()

        result = await db.execute(select(Profile).where(Profile.user_id == TEST_USER_ID))
        student_profile = result.scalar_one()
        
        result = await db.execute(select(Profile).where(Profile.user_id == TEST_ADMIN_ID))
        admin_profile = result.scalar_one()

        now = datetime.now(timezone.utc)
        future = now + timedelta(days=1)
        past = now - timedelta(days=1)

        opps = [
            # 1. Published with future deadline
            Opportunity(title="Pub Future", company_name="C1", opportunity_type="Internship", work_model="Remote", status="Published", deadline=future),
            # 2. Published with past deadline
            Opportunity(title="Pub Past", company_name="C2", opportunity_type="Internship", work_model="Remote", status="Published", deadline=past),
            # 3. Published with no deadline
            Opportunity(title="Pub No Deadline", company_name="C3", opportunity_type="Internship", work_model="Remote", status="Published", deadline=None),
            # 4. Draft with past deadline
            Opportunity(title="Draft Past", company_name="C4", opportunity_type="Internship", work_model="Remote", status="Draft", deadline=past),
            # 5. Closed with past deadline
            Opportunity(title="Closed Past", company_name="C5", opportunity_type="Internship", work_model="Remote", status="Closed", deadline=past),
            # 6. Expired
            Opportunity(title="Already Expired", company_name="C6", opportunity_type="Internship", work_model="Remote", status="Expired", deadline=past),
        ]
        db.add_all(opps)
        await db.commit()

        for opp in opps:
            await db.refresh(opp)

        # Create a saved relationship for the one that will expire
        saved = SavedOpportunity(profile_id=student_profile.id, opportunity_id=opps[1].id)
        db.add(saved)
        await db.commit()

        return {
            "student_profile_id": student_profile.id,
            "pub_future_id": opps[0].id,
            "pub_past_id": opps[1].id,
            "pub_none_id": opps[2].id,
            "draft_past_id": opps[3].id,
            "closed_past_id": opps[4].id,
            "expired_id": opps[5].id,
            "admin_profile": admin_profile,
        }

async def cleanup_test_db(data):
    async with async_session_factory() as db:
        opp_ids = [
            data["pub_future_id"], data["pub_past_id"], data["pub_none_id"],
            data["draft_past_id"], data["closed_past_id"], data["expired_id"]
        ]
        await db.execute(SavedOpportunity.__table__.delete().where(SavedOpportunity.opportunity_id.in_(opp_ids)))
        await db.execute(Opportunity.__table__.delete().where(Opportunity.id.in_(opp_ids)))
        await db.execute(Profile.__table__.delete().where(Profile.user_id.in_([TEST_USER_ID, TEST_ADMIN_ID])))
        await db.commit()

@pytest.mark.anyio
async def test_opportunity_lifecycle():
    data = await setup_test_db()
    
    transport = ASGITransport(app=app)
    
    # STUDENT REQUESTS (triggers expiration logic)
    app.dependency_overrides[get_current_user] = lambda: TEST_USER_ID

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Check student listing
        res = await client.get("/api/v1/opportunities")
        assert res.status_code == 200
        items = res.json()["items"]
        item_ids = [item["id"] for item in items]
        
        # 1. Published with future deadline stays Published
        assert str(data["pub_future_id"]) in item_ids
        
        # 2. Published with past deadline becomes Expired, absent from listing
        assert str(data["pub_past_id"]) not in item_ids
        
        # 3. Published with no deadline remains Published
        assert str(data["pub_none_id"]) in item_ids
        
        # 4, 5, 6. Draft/Closed/Expired not in listing
        assert str(data["draft_past_id"]) not in item_ids
        assert str(data["closed_past_id"]) not in item_ids
        assert str(data["expired_id"]) not in item_ids
        
        # 8. Students cannot open details for expired opportunities
        res = await client.get(f"/api/v1/opportunities/{data['pub_past_id']}")
        assert res.status_code == 404
        
        # 15. Existing saved relationships are not deleted during expiration
        res = await client.get("/api/v1/profile/saved-opportunities")
        assert res.status_code == 200
        saved_items = res.json()["items"]
        assert len(saved_items) == 1
        assert saved_items[0]["id"] == str(data["pub_past_id"])
        assert saved_items[0]["status"] == "Expired"  # Saved list should show Expired status
    
    # ADMIN REQUESTS
    app.dependency_overrides.clear()
    app.dependency_overrides[require_admin] = lambda: data["admin_profile"]

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Check admin listing
        res = await client.get("/api/v1/admin/opportunities")
        assert res.status_code == 200
        admin_items = {item["id"]: item for item in res.json()["items"]}
        
        # Verify statuses
        assert admin_items[str(data["pub_future_id"])]["status"] == "Published"
        assert admin_items[str(data["pub_past_id"])]["status"] == "Expired"
        assert admin_items[str(data["pub_none_id"])]["status"] == "Published"
        assert admin_items[str(data["draft_past_id"])]["status"] == "Draft" # 4. Draft with past deadline remains Draft
        assert admin_items[str(data["closed_past_id"])]["status"] == "Closed" # 5. Closed with past deadline remains Closed
        assert admin_items[str(data["expired_id"])]["status"] == "Expired" # 6. Expired remains Expired
        
        # 9. Admins can still inspect and manage expired records
        res = await client.get(f"/api/v1/admin/opportunities/{data['pub_past_id']}")
        assert res.status_code == 200
        assert res.json()["status"] == "Expired"
        
        now = datetime.now(timezone.utc)
        past_str = (now - timedelta(days=1)).isoformat()
        future_str = (now + timedelta(days=1)).isoformat()
        
        # 10. Creating a Published opportunity with a past deadline is rejected
        create_payload = {
            "title": "New Pub Past",
            "company_name": "C",
            "opportunity_type": "Internship",
            "work_model": "Remote",
            "status": "Published",
            "deadline": past_str
        }
        res = await client.post("/api/v1/admin/opportunities", json=create_payload)
        assert res.status_code == 422
        
        # 11. Changing an opportunity to Published with a past deadline is rejected
        res = await client.patch(f"/api/v1/admin/opportunities/{data['draft_past_id']}", json={"status": "Published"})
        assert res.status_code == 422
        
        # 14. Missing deadlines remain valid for Published
        create_payload["deadline"] = None
        res = await client.post("/api/v1/admin/opportunities", json=create_payload)
        assert res.status_code == 201
        new_opp_id = res.json()["id"]
        
        # 12. Explicitly republishing expired opportunity with future deadline
        res = await client.patch(f"/api/v1/admin/opportunities/{data['pub_past_id']}", json={
            "status": "Published",
            "deadline": future_str
        })
        assert res.status_code == 200
        assert res.json()["status"] == "Published"
        
        # 13. Partial updates preserve fields
        res = await client.patch(f"/api/v1/admin/opportunities/{data['pub_past_id']}", json={
            "title": "Updated Title"
        })
        assert res.status_code == 200
        assert res.json()["status"] == "Published"
        assert res.json()["deadline"] == future_str.replace('+00:00', 'Z') # Check it's retained
        
        # Cleanup the newly created opp
        await client.delete(f"/api/v1/admin/opportunities/{new_opp_id}")

    app.dependency_overrides.clear()
    await cleanup_test_db(data)
