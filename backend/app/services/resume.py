import uuid

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile, Resume
from app.services.storage import create_signed_url, delete_file, upload_file, download_file
from app.services.parser import extract_resume_text, ParserError, NoReadableTextError
from app.services.structured_extractor import extract_structured_data

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

async def list_resumes(db: AsyncSession, profile_id: uuid.UUID) -> list[Resume]:
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

async def parse_resume(db: AsyncSession, profile_id: uuid.UUID, resume_id: str) -> dict:
    resume = await get_resume_by_id(db, profile_id, resume_id)
    
    try:
        file_bytes = await download_file("resumes", resume.storage_path)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download resume securely."
        ) from e
        
    try:
        extracted_text = extract_resume_text(file_bytes, resume.file_type)
    except NoReadableTextError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except ParserError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during resume extraction."
        ) from e
        
    if not extracted_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No text could be extracted."
        )
        
    MAX_TEXT_LENGTH = 100000
    message = "Resume parsed successfully."
    
    if len(extracted_text) > MAX_TEXT_LENGTH:
        extracted_text = extracted_text[:MAX_TEXT_LENGTH]
        message = "Resume parsed successfully. Text was truncated to the maximum allowed length."
        
    try:
        resume.parsed_text = extracted_text
        await db.commit()
        await db.refresh(resume)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save parsed text."
        ) from e
        
    return {
        "id": resume.id,
        "status": "success",
        "character_count": len(extracted_text),
        "extracted_text": extracted_text,
    }

async def structure_resume(db: AsyncSession, profile_id: uuid.UUID, resume_id: str) -> dict:
    resume = await get_resume_by_id(db, profile_id, resume_id)
    
    if not resume.parsed_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume text has not been extracted yet. Please extract text first."
        )
        
    try:
        structured_data_obj = await extract_structured_data(db, resume.parsed_text)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract structured data from resume."
        ) from e
        
    try:
        resume.structured_data = structured_data_obj.model_dump(mode="json")
        resume.analysis_data = None
        await db.commit()
        await db.refresh(resume)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save structured data."
        ) from e
        
    return {
        "id": resume.id,
        "status": "success",
        "structured_data": structured_data_obj,
        "message": "Resume structured successfully."
    }
