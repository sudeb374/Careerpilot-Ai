import uuid
from typing import List

from fastapi import HTTPException, status, UploadFile
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Resume, Profile
from app.services.storage import upload_file, delete_file, create_signed_url

ALLOWED_MIME_TYPES = {
    "application/pdf": b"%PDF",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": b"PK\x03\x04"
}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

async def validate_resume_file(file: UploadFile) -> bytes:
    """Validate file type, size, and magic bytes."""
    file_bytes = await file.read()
    
    # Check size
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds maximum limit of 5MB."
        )
    
    # Check MIME type and magic bytes
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Only PDF and DOCX are allowed."
        )
    
    magic = ALLOWED_MIME_TYPES[file.content_type]
    if not file_bytes.startswith(magic):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content does not match its declared type."
        )
    
    return file_bytes

async def get_resume_by_id(db: AsyncSession, profile_id: uuid.UUID, resume_id: str) -> Resume:
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.profile_id == profile_id)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return resume

async def list_resumes(db: AsyncSession, profile_id: uuid.UUID) -> List[Resume]:
    result = await db.execute(
        select(Resume).where(Resume.profile_id == profile_id).order_by(Resume.created_at.desc())
    )
    return result.scalars().all()

async def upload_resume(db: AsyncSession, user_id: str, profile: Profile, file: UploadFile) -> Resume:
    file_bytes = await validate_resume_file(file)
    
    # Generate secure storage path
    file_uuid = str(uuid.uuid4())
    ext = "pdf" if file.content_type == "application/pdf" else "docx"
    storage_path = f"{user_id}/{file_uuid}.{ext}"
    
    # Upload to storage
    await upload_file("resumes", storage_path, file_bytes, file.content_type)
    
    # Database metadata
    try:
        resume = Resume(
            profile_id=profile.id,
            original_filename=file.filename or "resume",
            storage_path=storage_path,
            file_type=file.content_type,
            file_size=len(file_bytes),
            is_active=False
        )
        db.add(resume)
        await db.commit()
        await db.refresh(resume)
        return resume
    except Exception as e:
        # Compensating action if DB fails
        await db.rollback()
        try:
            await delete_file("resumes", storage_path)
        except Exception:
            pass  # We did our best to clean up the orphaned file
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save resume metadata."
        ) from e

async def activate_resume(db: AsyncSession, profile_id: uuid.UUID, resume_id: str) -> Resume:
    # Verify ownership
    resume = await get_resume_by_id(db, profile_id, resume_id)
    
    # Transaction: Deactivate all, activate this one
    await db.execute(
        update(Resume)
        .where(Resume.profile_id == profile_id)
        .values(is_active=False)
    )
    
    resume.is_active = True
    await db.commit()
    await db.refresh(resume)
    return resume

async def create_download_url(db: AsyncSession, profile_id: uuid.UUID, resume_id: str) -> dict:
    resume = await get_resume_by_id(db, profile_id, resume_id)
    
    # 5 minutes expiration
    signed_url = await create_signed_url("resumes", resume.storage_path, expires_in=300)
    return {
        "signed_url": signed_url,
        "original_filename": resume.original_filename,
        "file_type": resume.file_type
    }

async def delete_resume(db: AsyncSession, profile_id: uuid.UUID, resume_id: str) -> None:
    resume = await get_resume_by_id(db, profile_id, resume_id)
    
    # Delete from storage first
    await delete_file("resumes", resume.storage_path)
    
    # Delete from DB
    try:
        await db.delete(resume)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete resume metadata."
        ) from e
