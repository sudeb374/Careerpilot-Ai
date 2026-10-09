import io
import uuid

import docx
import fitz
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import async_session_factory
from app.core.dependencies import get_current_profile, get_current_user
from app.main import app
from app.models.profile import Profile, Resume

# --- Mock Documents ---

def create_valid_pdf() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(fitz.Point(50, 50), "Hello Resume PDF")
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes

def create_empty_pdf() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.draw_rect(fitz.Rect(50, 50, 100, 100), color=(1,0,0), fill=(1,0,0))
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes

def create_valid_docx() -> bytes:
    doc = docx.Document()
    doc.add_paragraph("Hello Resume DOCX")
    table = doc.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "Skill"
    table.rows[0].cells[1].text = "Python"
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()

# --- Mock Storage ---

from app.services import resume as resume_service

# We will patch storage.download_file dynamically in tests

# --- Test Setup ---

TEST_USER_ID = str(uuid.uuid4())
OTHER_USER_ID = str(uuid.uuid4())

@pytest.fixture
async def test_profile():
    async with async_session_factory() as db:
        profile = Profile(user_id=TEST_USER_ID, full_name="Test Student", role="student")
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        yield profile
        await db.delete(profile)
        await db.commit()

@pytest.fixture
async def other_profile():
    async with async_session_factory() as db:
        profile = Profile(user_id=OTHER_USER_ID, full_name="Other Student", role="student")
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        yield profile
        await db.delete(profile)
        await db.commit()

@pytest.fixture
async def test_client(test_profile):
    async def override_get_current_profile():
        return test_profile
    async def override_get_current_user():
        return TEST_USER_ID

    app.dependency_overrides[get_current_profile] = override_get_current_profile
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
        
    app.dependency_overrides.clear()

@pytest.fixture
async def unauth_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

# --- Tests ---

@pytest.mark.anyio
async def test_parse_valid_pdf(test_client, test_profile, monkeypatch):
    pdf_bytes = create_valid_pdf()
    
    async def mock_download_file(bucket, path):
        return pdf_bytes
    monkeypatch.setattr(resume_service, "download_file", mock_download_file)
    
    # Create resume in DB
    resume = Resume(
        profile_id=test_profile.id,
        original_filename="test.pdf",
        storage_path="test_path.pdf",
        file_type="application/pdf",
        file_size=len(pdf_bytes)
    )
    async with async_session_factory() as db:
        db.add(resume)
        await db.commit()
        await db.refresh(resume)
        resume_id = str(resume.id)
        
    res = await test_client.post(f"/api/v1/profile/resumes/{resume_id}/parse")
    print(res.json())
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "Hello Resume PDF" in data["extracted_text"]
    
    # Verify persistence
    async with async_session_factory() as db:
        r = await db.get(Resume, resume_id)
        assert r.parsed_text == data["extracted_text"]

@pytest.mark.anyio
async def test_parse_valid_docx(test_client, test_profile, monkeypatch):
    docx_bytes = create_valid_docx()
    
    async def mock_download_file(bucket, path):
        return docx_bytes
    monkeypatch.setattr(resume_service, "download_file", mock_download_file)
    
    resume = Resume(
        profile_id=test_profile.id,
        original_filename="test.docx",
        storage_path="test_path.docx",
        file_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        file_size=len(docx_bytes)
    )
    async with async_session_factory() as db:
        db.add(resume)
        await db.commit()
        await db.refresh(resume)
        resume_id = str(resume.id)
        
    res = await test_client.post(f"/api/v1/profile/resumes/{resume_id}/parse")
    print(res.json())
    assert res.status_code == 200
    data = res.json()
    assert "Hello Resume DOCX" in data["extracted_text"]
    assert "Skill | Python" in data["extracted_text"] # Testing table extraction

@pytest.mark.anyio
async def test_parse_empty_pdf(test_client, test_profile, monkeypatch):
    pdf_bytes = create_empty_pdf()
    
    async def mock_download_file(bucket, path):
        return pdf_bytes
    monkeypatch.setattr(resume_service, "download_file", mock_download_file)
    
    resume = Resume(
        profile_id=test_profile.id,
        original_filename="test.pdf",
        storage_path="test_path.pdf",
        file_type="application/pdf",
        file_size=len(pdf_bytes)
    )
    async with async_session_factory() as db:
        db.add(resume)
        await db.commit()
        await db.refresh(resume)
        resume_id = str(resume.id)
        
    res = await test_client.post(f"/api/v1/profile/resumes/{resume_id}/parse")
    assert res.status_code == 422
    assert "No readable text" in res.json()["detail"]

@pytest.mark.anyio
async def test_parse_corrupt_files(test_client, test_profile, monkeypatch):
    corrupt_bytes = b"Not a real file"
    
    async def mock_download_file(bucket, path):
        return corrupt_bytes
    monkeypatch.setattr(resume_service, "download_file", mock_download_file)
    
    # PDF
    resume_pdf = Resume(
        profile_id=test_profile.id,
        original_filename="test.pdf",
        storage_path="test_path_corrupt.pdf",
        file_type="application/pdf",
        file_size=len(corrupt_bytes)
    )
    # DOCX
    resume_docx = Resume(
        profile_id=test_profile.id,
        original_filename="test.docx",
        storage_path="test_path_corrupt.docx",
        file_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        file_size=len(corrupt_bytes)
    )
    async with async_session_factory() as db:
        db.add(resume_pdf)
        db.add(resume_docx)
        await db.commit()
        await db.refresh(resume_pdf)
        await db.refresh(resume_docx)
        
    res_pdf = await test_client.post(f"/api/v1/profile/resumes/{resume_pdf.id}/parse")
    assert res_pdf.status_code == 422
    assert "Failed to open PDF" in res_pdf.json()["detail"]
    
    res_docx = await test_client.post(f"/api/v1/profile/resumes/{resume_docx.id}/parse")
    assert res_docx.status_code == 422
    assert "Failed to open DOCX" in res_docx.json()["detail"]

@pytest.mark.anyio
async def test_parse_unsupported_file_type(test_client, test_profile, monkeypatch):
    async def mock_download_file(bucket, path):
        return b"content"
    monkeypatch.setattr(resume_service, "download_file", mock_download_file)
    
    resume = Resume(
        profile_id=test_profile.id,
        original_filename="test.txt",
        storage_path="test_path.txt",
        file_type="text/plain",
        file_size=7
    )
    async with async_session_factory() as db:
        db.add(resume)
        await db.commit()
        await db.refresh(resume)
        resume_id = str(resume.id)
        
    res = await test_client.post(f"/api/v1/profile/resumes/{resume_id}/parse")
    assert res.status_code == 422
    assert "Unsupported file type" in res.json()["detail"]

@pytest.mark.anyio
async def test_unauthenticated_request(unauth_client, test_profile):
    res = await unauth_client.post(f"/api/v1/profile/resumes/{uuid.uuid4()}/parse")
    assert res.status_code == 401

@pytest.mark.anyio
async def test_another_user_resume(test_client, other_profile):
    # Resume belongs to other_profile, test_client is logged in as test_profile
    resume = Resume(
        profile_id=other_profile.id,
        original_filename="test.pdf",
        storage_path="test_path.pdf",
        file_type="application/pdf",
        file_size=100
    )
    async with async_session_factory() as db:
        db.add(resume)
        await db.commit()
        await db.refresh(resume)
        resume_id = str(resume.id)
        
    res = await test_client.post(f"/api/v1/profile/resumes/{resume_id}/parse")
    assert res.status_code == 404
    assert "Resume not found" in res.json()["detail"]

@pytest.mark.anyio
async def test_missing_resume(test_client):
    res = await test_client.post(f"/api/v1/profile/resumes/{uuid.uuid4()}/parse")
    assert res.status_code == 404

@pytest.mark.anyio
async def test_storage_download_failure(test_client, test_profile, monkeypatch):
    from fastapi import HTTPException
    async def mock_download_file(bucket, path):
        raise HTTPException(status_code=404, detail="File not found in storage")
    monkeypatch.setattr(resume_service, "download_file", mock_download_file)
    
    resume = Resume(
        profile_id=test_profile.id,
        original_filename="test.pdf",
        storage_path="test_path.pdf",
        file_type="application/pdf",
        file_size=100
    )
    async with async_session_factory() as db:
        db.add(resume)
        await db.commit()
        await db.refresh(resume)
        resume_id = str(resume.id)
        
    res = await test_client.post(f"/api/v1/profile/resumes/{resume_id}/parse")
    assert res.status_code == 404
    assert "File not found in storage" in res.json()["detail"]

@pytest.mark.anyio
async def test_failed_extraction_does_not_overwrite(test_client, test_profile, monkeypatch):
    pdf_bytes = create_empty_pdf()
    
    async def mock_download_file(bucket, path):
        return pdf_bytes
    monkeypatch.setattr(resume_service, "download_file", mock_download_file)
    
    resume = Resume(
        profile_id=test_profile.id,
        original_filename="test.pdf",
        storage_path="test_path.pdf",
        file_type="application/pdf",
        file_size=len(pdf_bytes),
        parsed_text="Valid previous text"
    )
    async with async_session_factory() as db:
        db.add(resume)
        await db.commit()
        await db.refresh(resume)
        resume_id = str(resume.id)
        
    res = await test_client.post(f"/api/v1/profile/resumes/{resume_id}/parse")
    assert res.status_code == 422
    
    # Verify text was NOT overwritten
    async with async_session_factory() as db:
        r = await db.get(Resume, resume_id)
        assert r.parsed_text == "Valid previous text"

@pytest.mark.anyio
async def test_duplicate_parsing_does_not_create_records(test_client, test_profile, monkeypatch):
    pdf_bytes = create_valid_pdf()
    
    async def mock_download_file(bucket, path):
        return pdf_bytes
    monkeypatch.setattr(resume_service, "download_file", mock_download_file)
    
    resume = Resume(
        profile_id=test_profile.id,
        original_filename="test.pdf",
        storage_path="test_path.pdf",
        file_type="application/pdf",
        file_size=len(pdf_bytes)
    )
    async with async_session_factory() as db:
        db.add(resume)
        await db.commit()
        await db.refresh(resume)
        resume_id = str(resume.id)
        
        # Count initial resumes
        from sqlalchemy import func, select
        result = await db.execute(select(func.count()).select_from(Resume).where(Resume.profile_id == test_profile.id))
        initial_count = result.scalar()
        
    res1 = await test_client.post(f"/api/v1/profile/resumes/{resume_id}/parse")
    assert res1.status_code == 200
    
    res2 = await test_client.post(f"/api/v1/profile/resumes/{resume_id}/parse")
    assert res2.status_code == 200
    
    async with async_session_factory() as db:
        result = await db.execute(select(func.count()).select_from(Resume).where(Resume.profile_id == test_profile.id))
        final_count = result.scalar()
        
    assert initial_count == final_count
