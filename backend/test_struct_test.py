import asyncio
from app.core.database import async_session_factory
from app.services.structured_extractor import extract_structured_data

text = """
John Doe
john.doe@example.com
(555) 123-4567
github.com/johndoe
https://www.linkedin.com/in/johndoe

SUMMARY
Experienced software engineer with 5 years in Python and React.

TECHNICAL SKILLS
Python, JavaScript, React, SQL, PostgreSQL, PyTorch

EXPERIENCE
Software Engineer
Google
2020 - Present
Built stuff.

EDUCATION
B.S. Computer Science
University of California
"""

async def run_test():
    async with async_session_factory() as db:
        res = await extract_structured_data(db, text)
        print(res.model_dump_json(indent=2))

if __name__ == "__main__":
    asyncio.run(run_test())
