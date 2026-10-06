import asyncio
import sys
from uuid import uuid4

# Add backend dir to sys.path if not there
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.dependencies import get_current_user
from app.models.profile import Profile
from app.core.database import async_session_factory

# We'll need a real test user ID
TEST_USER_ID = str(uuid4())


async def setup_test_db():
    async with async_session_factory() as db:
        # Check if test profile exists
        from sqlalchemy import select

        result = await db.execute(
            select(Profile).where(Profile.user_id == TEST_USER_ID)
        )
        profile = result.scalars().first()
        if not profile:
            profile = Profile(
                user_id=TEST_USER_ID,
                full_name="Test User",
                headline="Test Headline",
                location="Test City",
                role="student",
            )
            db.add(profile)
            await db.commit()
        return profile.id


async def run_tests():
    print("Setting up test database...")
    await setup_test_db()

    # Override get_current_user dependency
    app.dependency_overrides[get_current_user] = lambda: TEST_USER_ID

    print("Starting tests...")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. GET profile returns the new fields
        print("1. Testing GET profile...")
        response = await client.get("/api/v1/profile")
        assert response.status_code == 200, response.text
        data = response.json()
        assert "about" in data
        assert "phone" in data
        assert "linkedin_url" in data
        assert "github_url" in data
        assert "portfolio_url" in data

        # 2. PATCH about successfully
        print("2. Testing PATCH about...")
        response = await client.patch(
            "/api/v1/profile", json={"about": "I am a software engineer."}
        )
        assert response.status_code == 200, response.text
        assert response.json()["about"] == "I am a software engineer."

        # 3. PATCH phone successfully
        print("3. Testing PATCH phone...")
        response = await client.patch("/api/v1/profile", json={"phone": "+1234567890"})
        assert response.status_code == 200, response.text
        assert response.json()["phone"] == "+1234567890"

        # 4. PATCH LinkedIn/GitHub/Portfolio URLs successfully
        print("4. Testing PATCH URLs...")
        response = await client.patch(
            "/api/v1/profile",
            json={
                "linkedin_url": "https://linkedin.com/in/test",
                "github_url": "https://github.com/test",
                "portfolio_url": "https://myportfolio.com/",
            },
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["linkedin_url"] == "https://linkedin.com/in/test"
        assert data["github_url"] == "https://github.com/test"
        assert data["portfolio_url"] == "https://myportfolio.com/"

        # 5. Empty optional values work correctly
        print("5. Testing empty optional values...")
        response = await client.patch(
            "/api/v1/profile",
            json={"about": "", "phone": "   ", "linkedin_url": "", "github_url": None},
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["about"] is None
        assert data["phone"] is None
        assert data["linkedin_url"] is None
        assert data["github_url"] is None
        assert data["portfolio_url"] == "https://myportfolio.com/"  # untouched

        # 6. Invalid URL scheme is rejected
        print("6. Testing invalid URL scheme...")
        response = await client.patch(
            "/api/v1/profile", json={"linkedin_url": "javascript:alert(1)"}
        )
        assert response.status_code == 422, "Should reject invalid URL scheme"

        response = await client.patch(
            "/api/v1/profile", json={"linkedin_url": "not-a-url"}
        )
        assert response.status_code == 422, "Should reject invalid URL"

        # 7. About exceeding the maximum length is rejected
        print("7. Testing about exceeding max length...")
        response = await client.patch("/api/v1/profile", json={"about": "A" * 2001})
        assert response.status_code == 422, "Should reject length > 2000"

        # 8. Existing role protection still works
        print("8. Testing role protection...")
        # ProfileUpdate schema doesn't have role field, so it will be ignored by Pydantic
        # but let's make sure it doesn't get updated if sent
        response = await client.patch("/api/v1/profile", json={"role": "admin"})
        # Fastapi returns 200 but ignores unknown fields depending on config
        assert response.status_code == 200
        assert response.json()["role"] == "student"  # Unchanged

        # 9. Existing profile functionality remains unaffected
        print("9. Testing existing functionality...")
        response = await client.patch(
            "/api/v1/profile", json={"full_name": "Updated Name"}
        )
        assert response.status_code == 200
        assert response.json()["full_name"] == "Updated Name"

    print("\nAll tests passed successfully!")


if __name__ == "__main__":
    asyncio.run(run_tests())
