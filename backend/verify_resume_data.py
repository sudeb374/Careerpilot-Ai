import asyncio
import json
from sqlalchemy import select
from app.core.database import async_session_factory
from app.models.profile import Resume

async def check_resume_data():
    async with async_session_factory() as db:
        stmt = select(Resume).where(Resume.id == '76b7c000-7140-437a-8b06-965be8fb489f')
        res = await db.execute(stmt)
        resume = res.scalar_one_or_none()
        
        if resume:
            print(f"Resume ID: {resume.id}")
            print(f"Has parsed text: {resume.parsed_text is not None}")
            print(f"Has structured data: {resume.structured_data is not None}")
            print(f"Has analysis data: {resume.analysis_data is not None}")
        else:
            print("Resume not found")

if __name__ == "__main__":
    asyncio.run(check_resume_data())
