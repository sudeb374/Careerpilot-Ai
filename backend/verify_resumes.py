import asyncio
from sqlalchemy import select, func
from app.core.database import async_session_factory
from app.models.profile import Profile, Resume

async def investigate_resumes():
    async with async_session_factory() as db:
        # Count total profiles
        profile_count = await db.scalar(select(func.count(Profile.id)))
        print(f"Total Profiles: {profile_count}")
        
        # Count total resumes
        resume_count = await db.scalar(select(func.count(Resume.id)))
        print(f"Total Resumes: {resume_count}")
        
        # Fetch all resumes with their profile_id, is_active, and storage_path (hashed/masked for safety)
        stmt = select(Resume.id, Resume.profile_id, Resume.is_active, Resume.created_at, Resume.storage_path)
        res = await db.execute(stmt)
        resumes = res.all()
        
        profile_resume_counts = {}
        active_counts = {}
        for r in resumes:
            pid = str(r.profile_id)
            profile_resume_counts[pid] = profile_resume_counts.get(pid, 0) + 1
            if r.is_active:
                active_counts[pid] = active_counts.get(pid, 0) + 1
                
        print("\nResume counts per profile:")
        for pid, count in profile_resume_counts.items():
            print(f"Profile: {pid}, Total Resumes: {count}, Active: {active_counts.get(pid, 0)}")
            
        print("\nAll Resumes Details (safe):")
        for r in resumes:
            print(f"ID: {r.id}, Profile: {r.profile_id}, Active: {r.is_active}, Created: {r.created_at}")

if __name__ == "__main__":
    asyncio.run(investigate_resumes())
