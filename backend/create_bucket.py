import asyncio
import httpx
from app.core.config import settings
from app.services.storage import get_storage_headers

async def create_bucket():
    headers = get_storage_headers()
    url = f"{settings.supabase_url.rstrip('/')}/storage/v1/bucket"
    payload = {
        "id": "profile-pictures",
        "name": "profile-pictures",
        "public": False,
        "file_size_limit": 5 * 1024 * 1024,
        "allowed_mime_types": ["image/jpeg", "image/png"]
    }
    
    async with httpx.AsyncClient() as client:
        # Check if bucket exists
        resp = await client.get(url, headers=headers)
        if resp.status_code == 200:
            buckets = resp.json()
            if any(b["id"] == "profile-pictures" for b in buckets):
                print("Bucket profile-pictures already exists.")
                return

        resp = await client.post(url, json=payload, headers=headers)
        if resp.status_code in (200, 201):
            print("Created bucket profile-pictures.")
        else:
            print(f"Failed to create bucket: {resp.text}")

if __name__ == "__main__":
    asyncio.run(create_bucket())
