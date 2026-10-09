import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import async_session_factory
from app.core.dependencies import get_current_profile, get_current_user
from app.main import app
from app.models.profile import Profile, Resume

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
def test_client(test_profile):
    async def mock_get_current_user():
        return {"sub": TEST_USER_ID, "email": "test@example.com"}

    async def mock_get_current_profile():
        return test_profile

    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[get_current_profile] = mock_get_current_profile
    transport = ASGITransport(app=app)
    yield AsyncClient(transport=transport, base_url="http://test")
    app.dependency_overrides.clear()

@pytest.fixture
def other_client(other_profile):
    async def mock_get_current_user():
        return {"sub": OTHER_USER_ID, "email": "other@example.com"}

    async def mock_get_current_profile():
        return other_profile

    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[get_current_profile] = mock_get_current_profile
    transport = ASGITransport(app=app)
    yield AsyncClient(transport=transport, base_url="http://test")
    app.dependency_overrides.clear()


@pytest.fixture
async def full_resume(test_profile):
    async with async_session_factory() as db:
        resume = Resume(
            profile_id=test_profile.id,
            original_filename="full.pdf",
            storage_path="full.pdf",
            file_type="application/pdf",
            file_size=1000,
            parsed_text="Full resume text",
            structured_data={
                "contact": {
                    "emails": ["test@example.com"],
                    "phones": ["123-456-7890"],
                    "linkedin_urls": ["linkedin.com/in/test"],
                    "github_urls": ["github.com/test"],
                    "portfolio_urls": []
                },
                "sections": {
                    "summary": "Experienced engineer.",
                    "education": "BS Computer Science.",
                    "experience": "Worked at Tech Co.",
                    "projects": "Built an app.",
                    "skills": "Python, Java."
                },
                "skills": [
                    {"skill_id": str(uuid.uuid4()), "name": "Python", "evidence": "Used Python"},
                    {"skill_id": str(uuid.uuid4()), "name": "Java", "evidence": "Used Java"},
                    {"skill_id": str(uuid.uuid4()), "name": "C++", "evidence": "Used C++"},
                    {"skill_id": str(uuid.uuid4()), "name": "SQL", "evidence": "Used SQL"},
                    {"skill_id": str(uuid.uuid4()), "name": "React", "evidence": "Used React"}
                ]
            }
        )
        db.add(resume)
        await db.commit()
        await db.refresh(resume)
        yield resume
        try:
            await db.delete(resume)
            await db.commit()
        except Exception:
            await db.rollback()


@pytest.fixture
async def poor_resume(test_profile):
    async with async_session_factory() as db:
        resume = Resume(
            profile_id=test_profile.id,
            original_filename="poor.pdf",
            storage_path="poor.pdf",
            file_type="application/pdf",
            file_size=1000,
            parsed_text="Poor resume text",
            structured_data={
                "contact": {
                    "emails": [],
                    "phones": [],
                    "linkedin_urls": [],
                    "github_urls": [],
                    "portfolio_urls": []
                },
                "sections": {},
                "skills": []
            }
        )
        db.add(resume)
        await db.commit()
        await db.refresh(resume)
        yield resume
        try:
            await db.delete(resume)
            await db.commit()
        except Exception:
            await db.rollback()


@pytest.fixture
async def projects_only_resume(test_profile):
    async with async_session_factory() as db:
        resume = Resume(
            profile_id=test_profile.id,
            original_filename="proj.pdf",
            storage_path="proj.pdf",
            file_type="application/pdf",
            file_size=1000,
            parsed_text="Proj resume text",
            structured_data={
                "contact": {
                    "emails": ["test@example.com"],
                    "phones": [],
                    "linkedin_urls": [],
                    "github_urls": [],
                    "portfolio_urls": []
                },
                "sections": {
                    "projects": "Built an app."
                },
                "skills": [
                    {"skill_id": str(uuid.uuid4()), "name": "Python", "evidence": "Used Python"}
                ]
            }
        )
        db.add(resume)
        await db.commit()
        await db.refresh(resume)
        yield resume
        try:
            await db.delete(resume)
            await db.commit()
        except Exception:
            await db.rollback()

@pytest.fixture
async def unparsed_resume(test_profile):
    async with async_session_factory() as db:
        resume = Resume(
            profile_id=test_profile.id,
            original_filename="unparsed.pdf",
            storage_path="unparsed.pdf",
            file_type="application/pdf",
            file_size=1000,
            parsed_text=None,
            structured_data=None
        )
        db.add(resume)
        await db.commit()
        await db.refresh(resume)
        yield resume
        try:
            await db.delete(resume)
            await db.commit()
        except Exception:
            await db.rollback()

@pytest.fixture
async def unstructured_resume(test_profile):
    async with async_session_factory() as db:
        resume = Resume(
            profile_id=test_profile.id,
            original_filename="unstructured.pdf",
            storage_path="unstructured.pdf",
            file_type="application/pdf",
            file_size=1000,
            parsed_text="I have text but no structure.",
            structured_data=None
        )
        db.add(resume)
        await db.commit()
        await db.refresh(resume)
        yield resume
        try:
            await db.delete(resume)
            await db.commit()
        except Exception:
            await db.rollback()

@pytest.mark.anyio
async def test_analyze_full_resume(test_client, full_resume):
    # Test POST
    resp = await test_client.post(f"/api/v1/profile/resumes/{full_resume.id}/analyze")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    analysis = data["analysis"]
    
    assert analysis["schema_version"] == 1
    assert "analysis_generated_at" in analysis
    
    # 15 (contact) + 10 (summary) + 15 (education) + 20 (skills) + 25 (exp/proj) + 15 (org) = 100
    assert analysis["completeness_score"] == 100
    assert analysis["score_label"] == "Strong completeness"
    
    # Categories
    assert analysis["category_scores"]["contact"] == 15
    assert analysis["category_scores"]["summary"] == 10
    assert analysis["category_scores"]["education"] == 15
    assert analysis["category_scores"]["skills"] == 20
    assert analysis["category_scores"]["experience_projects"] == 25
    assert analysis["category_scores"]["organization"] == 15
    
    # Test GET
    resp2 = await test_client.get(f"/api/v1/profile/resumes/{full_resume.id}/analysis")
    assert resp2.status_code == 200
    assert resp2.json()["analysis"]["completeness_score"] == 100


@pytest.mark.anyio
async def test_analyze_poor_resume(test_client, poor_resume):
    resp = await test_client.post(f"/api/v1/profile/resumes/{poor_resume.id}/analyze")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    analysis = data["analysis"]
    
    # 0 for everything, except 5 for organization (sections_found < 2)
    assert analysis["completeness_score"] == 5
    assert analysis["score_label"] == "Needs improvement"
    assert len(analysis["findings"]) >= 6 # Missing contact, summary, edu, skills, exp/proj, poor org


@pytest.mark.anyio
async def test_analyze_projects_only(test_client, projects_only_resume):
    resp = await test_client.post(f"/api/v1/profile/resumes/{projects_only_resume.id}/analyze")
    assert resp.status_code == 200
    analysis = resp.json()["analysis"]
    
    # Check that projects_experience scored 20, and missing formal experience is just a low severity finding
    assert analysis["category_scores"]["experience_projects"] == 20
    
    # Ensure there's a finding about missing formal experience but it doesn't fail them completely
    findings = [f for f in analysis["findings"] if f["identifier"] == "no_formal_exp"]
    assert len(findings) == 1
    assert findings[0]["severity"] == "low"
    
    strengths = [s for s in analysis["strengths"] if s["identifier"] == "proj_only"]
    assert len(strengths) == 1


@pytest.mark.anyio
async def test_analyze_unparsed(test_client, unparsed_resume):
    resp = await test_client.post(f"/api/v1/profile/resumes/{unparsed_resume.id}/analyze")
    assert resp.status_code == 200
    assert resp.json()["status"] == "error"
    assert "not been extracted yet" in resp.json()["message"]


@pytest.mark.anyio
async def test_analyze_unstructured(test_client, unstructured_resume):
    resp = await test_client.post(f"/api/v1/profile/resumes/{unstructured_resume.id}/analyze")
    assert resp.status_code == 200
    assert resp.json()["status"] == "error"
    assert "Structured data has not been generated" in resp.json()["message"]


@pytest.mark.anyio
async def test_get_unanalyzed(test_client, poor_resume):
    # GET before POST
    resp = await test_client.get(f"/api/v1/profile/resumes/{poor_resume.id}/analysis")
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"
    assert "No analysis exists" in resp.json()["message"]


@pytest.mark.anyio
async def test_analyze_unauthenticated(full_resume):
    # No overrides
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    resp = await client.post(f"/api/v1/profile/resumes/{full_resume.id}/analyze")
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_analyze_other_user(other_client, full_resume):
    resp = await other_client.post(f"/api/v1/profile/resumes/{full_resume.id}/analyze")
    assert resp.status_code == 400
    assert "unauthorized" in resp.json()["detail"].lower()

    resp = await other_client.get(f"/api/v1/profile/resumes/{full_resume.id}/analysis")
    assert resp.status_code == 404
    assert "unauthorized" in resp.json()["detail"].lower()
