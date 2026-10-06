import uuid
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile
from app.services.storage import upload_file, delete_file, create_signed_url

BUCKET_NAME = "profile-pictures"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_MIME_TYPES = {
    "image/jpeg": b"\xff\xd8\xff",
    "image/png": b"\x89PNG\r\n\x1a\n"
}

async def upload_profile_picture(db: AsyncSession, profile_id: str, user_id: str, file: UploadFile) -> str:
    """
    Validates, uploads to Supabase, updates DB, and handles replacement.
    Returns the new storage path.
    """
    file_bytes = await file.read()
    file_size = len(file_bytes)

    # 1. Size Validation
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds maximum limit of 5MB."
        )

    # 2. Magic Bytes Validation
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or unsupported image type. Only JPEG and PNG are allowed."
        )

    magic = ALLOWED_MIME_TYPES[file.content_type]
    if not file_bytes.startswith(magic):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content does not match its declared type."
        )

    # Ensure extension is consistent with content
    ext = "jpg" if file.content_type == "image/jpeg" else "png"
    
    # Check if existing profile picture
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalars().first()
    
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

    old_path = profile.profile_picture_path

    # Generate new path
    file_uuid = str(uuid.uuid4())
    new_path = f"{user_id}/{file_uuid}.{ext}"

    # Upload to storage
    await upload_file(BUCKET_NAME, new_path, file_bytes, file.content_type)

    # Database metadata update
    try:
        profile.profile_picture_path = new_path
        await db.commit()
    except Exception as e:
        await db.rollback()
        try:
            await delete_file(BUCKET_NAME, new_path)
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database transaction failed."
        ) from e

    # Clean up old file if it existed
    if old_path:
        try:
            await delete_file(BUCKET_NAME, old_path)
        except Exception:
            pass # ignore errors deleting old picture

    return new_path

async def get_profile_picture_url(db: AsyncSession, profile_id: str) -> str:
    """Returns a signed URL for the profile picture."""
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalars().first()

    if not profile or not profile.profile_picture_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile picture not found."
        )

    signed_url = await create_signed_url(BUCKET_NAME, profile.profile_picture_path, expires_in=3600)
    return signed_url

async def inject_profile_picture_url(profile: Profile) -> Profile:
    """Injects a signed URL into the profile object if a picture path exists."""
    if profile and profile.profile_picture_path:
        try:
            profile.profile_picture_url = await create_signed_url(BUCKET_NAME, profile.profile_picture_path, expires_in=3600)
        except Exception:
            profile.profile_picture_url = None
    else:
        profile.profile_picture_url = None
    return profile

async def delete_profile_picture(db: AsyncSession, profile_id: str) -> None:
    """Deletes profile picture from storage and clears the DB path."""
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalars().first()

    if not profile or not profile.profile_picture_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile picture not found."
        )

    old_path = profile.profile_picture_path

    # DB update first to avoid data inconsistency if Storage fails
    try:
        profile.profile_picture_path = None
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update database."
        ) from e
        
    # Delete from storage
    try:
        await delete_file(BUCKET_NAME, old_path)
    except Exception:
        pass # ignore
