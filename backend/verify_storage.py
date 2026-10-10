import asyncio
import os
from app.core.config import settings
from supabase import create_client, Client

async def check_storage():
    url: str = settings.supabase_url
    key: str = settings.supabase_secret_key
    supabase: Client = create_client(url, key)

    try:
        # List all files in 'resumes' bucket
        res = supabase.storage.from_("resumes").list()
        print("Folders in 'resumes' bucket:")
        for item in res:
            if item['name'] != '.emptyFolderPlaceholder':
                print(f"Folder: {item['name']}")
                sub_res = supabase.storage.from_("resumes").list(item['name'])
                for sub_item in sub_res:
                    if sub_item['name'] != '.emptyFolderPlaceholder':
                        print(f"  File: {sub_item['name']}, Created: {sub_item['created_at']}")
    except Exception as e:
        print(f"Error accessing storage: {e}")

if __name__ == "__main__":
    asyncio.run(check_storage())
