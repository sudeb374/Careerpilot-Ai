import asyncio
from sqlalchemy import select
from app.core.database import async_session_factory
from app.models.profile import Profile

async def check_profile():
    async with async_session_factory() as db:
        user_id = '92acf8f8-3242-4c02-ad6b-2b6592066f88'
        stmt = select(Profile.id, Profile.user_id, Profile.full_name).where(Profile.user_id == user_id)
        res = await db.execute(stmt)
        profiles = res.all()
        print(f"Profiles for user {user_id}:")
        for p in profiles:
            print(f"ID: {p.id}, UserID: {p.user_id}")

        stmt2 = select(Profile.id, Profile.user_id, Profile.full_name).where(Profile.id == 'e3ebb6b1-a483-430b-a218-6dcf9377d9cb')
        res2 = await db.execute(stmt2)
        profiles_2 = res2.all()
        print(f"\nProfiles with ID e3ebb6b1-a483-430b-a218-6dcf9377d9cb:")
        for p in profiles_2:
            print(f"ID: {p.id}, UserID: {p.user_id}")

if __name__ == "__main__":
    asyncio.run(check_profile())
