import asyncio
import os
import sys
from uuid import uuid4

from httpx import ASGITransport, AsyncClient

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app.core.database import async_session_factory
from app.core.dependencies import get_current_user
from app.main import app
from app.models.profile import Profile

TEST_USER_ID = str(uuid4())

async def setup_test_db():
    async with async_session_factory() as db:
        from sqlalchemy import select
        result = await db.execute(select(Profile).where(Profile.user_id == TEST_USER_ID))
        profile = result.scalars().first()
        if not profile:
            profile = Profile(
                user_id=TEST_USER_ID,
                full_name="Test User Pic",
                headline="Test Headline",
                location="Test City",
                role="student"
            )
            db.add(profile)
            await db.commit()
        return profile.id

async def create_fake_image(size_mb, valid_magic=True):
    size_bytes = size_mb * 1024 * 1024
    if valid_magic:
        # valid PNG magic bytes + padding
        content = b'\x89PNG\r\n\x1a\n' + b'\0' * (size_bytes - 8)
    else:
        # invalid magic bytes
        content = b'FAKEIMG' + b'\0' * (size_bytes - 7)
    return content

async def run_tests():
    print("Setting up test database...")
    await setup_test_db()
    
    app.dependency_overrides[get_current_user] = lambda: TEST_USER_ID
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. upload valid PNG
        print("1. Testing valid PNG upload...")
        png_content = await create_fake_image(1, True)
        files = {"file": ("test.png", png_content, "image/png")}
        resp = await client.post("/api/v1/profile/picture", files=files)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["profile_picture_path"] is not None
        assert data["profile_picture_path"].endswith(".png")
        assert "profile_picture_url" in data
        assert "http" in data["profile_picture_url"]
        
        # 2. fake content rejected
        print("2. Testing invalid image content rejected...")
        fake_content = await create_fake_image(1, False)
        files = {"file": ("fake.png", fake_content, "image/png")}
        resp = await client.post("/api/v1/profile/picture", files=files)
        assert resp.status_code == 400
        assert "match" in resp.json()["detail"] or "Invalid" in resp.json()["detail"]
        
        # 3. oversized rejected
        print("3. Testing oversized file rejected...")
        big_content = await create_fake_image(6, True)
        files = {"file": ("big.png", big_content, "image/png")}
        resp = await client.post("/api/v1/profile/picture", files=files)
        assert resp.status_code == 400
        assert "size" in resp.json()["detail"].lower()
        
        # 4. get signed url
        print("4. Testing get signed URL...")
        resp = await client.get("/api/v1/profile/picture")
        assert resp.status_code == 200
        assert "signed_url" in resp.json()
        assert "http" in resp.json()["signed_url"]
        
        # 5. replace existing
        print("5. Testing replace picture...")
        files = {"file": ("test2.png", png_content, "image/png")}
        resp = await client.post("/api/v1/profile/picture", files=files)
        assert resp.status_code == 200
        
        # 6. delete picture
        print("6. Testing delete picture...")
        resp = await client.delete("/api/v1/profile/picture")
        assert resp.status_code == 204
        
        # 7. verify DB path cleared
        print("7. Testing DB path cleared...")
        resp = await client.get("/api/v1/profile")
        assert resp.json()["profile_picture_path"] is None

    print("\nAll backend tests passed!")

if __name__ == "__main__":
    asyncio.run(run_tests())
