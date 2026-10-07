import asyncio

import httpx


async def run():
    async with httpx.AsyncClient() as client:
        res = await client.get("http://127.0.0.1:8000/api/v1/profile/resumes")
        print(res.status_code)
        print(res.text)

asyncio.run(run())
