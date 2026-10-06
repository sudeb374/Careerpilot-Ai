import httpx
from fastapi import HTTPException, status
from app.core.config import settings

STORAGE_URL = f"{settings.supabase_url.rstrip('/')}/storage/v1"
BUCKET_NAME = "resumes"

def get_storage_headers() -> dict:
    if not settings.supabase_secret_key:
        raise ValueError("Supabase secret key is missing.")
    return {
        "Authorization": f"Bearer {settings.supabase_secret_key}",
        "apikey": settings.supabase_secret_key,
    }

async def upload_file(bucket_name: str, path: str, file_bytes: bytes, content_type: str) -> None:
    """Upload a file to a bucket."""
    headers = get_storage_headers()
    headers["Content-Type"] = content_type
    
    url = f"{STORAGE_URL}/object/{bucket_name}/{path}"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, content=file_bytes, headers=headers)
        if response.status_code not in (200, 201):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file to storage: {response.text}"
            )

async def delete_file(bucket_name: str, path: str) -> None:
    """Delete a file from a bucket."""
    headers = get_storage_headers()
    url = f"{STORAGE_URL}/object/{bucket_name}/{path}"
    
    async with httpx.AsyncClient() as client:
        response = await client.delete(url, headers=headers)
        if response.status_code not in (200, 204):
            # 400 or 404 is also okay if it doesn't exist, but let's log or raise
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete file from storage: {response.text}"
            )

async def create_signed_url(bucket_name: str, path: str, expires_in: int = 300) -> str:
    """Create a signed download URL for a file in a bucket."""
    headers = get_storage_headers()
    url = f"{STORAGE_URL}/object/sign/{bucket_name}/{path}"
    
    payload = {"expiresIn": expires_in}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return f"{settings.supabase_url.rstrip('/')}/storage/v1{data['signedURL']}"
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate signed URL: {response.text}"
            )
