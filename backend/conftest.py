import os
import pytest
from unittest.mock import patch

# Load settings first
from app.core.config import settings

# 1. Fail fast if TEST_DATABASE_URL is missing or unsafe
if not settings.test_database_url:
    pytest.exit("FATAL: TEST_DATABASE_URL is not configured. Please set it in .env to an isolated local PostgreSQL database (e.g., postgresql+psycopg://user:password@localhost:5432/careerpilot_test).")

if "supabase" in settings.test_database_url.lower() or "pooler" in settings.test_database_url.lower():
    pytest.exit("FATAL: TEST_DATABASE_URL points to a shared Supabase database. Please set it to a local isolated test database to prevent data corruption.")

# 2. Patch settings so any late imports see the test URL
settings.database_url = settings.test_database_url

# 3. Recreate the engine and session factory with the test URL
from app.core.database import _get_async_url, get_db_session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import app.core.database as db_module

test_engine = create_async_engine(
    _get_async_url(settings.test_database_url),
    echo=False,
    pool_pre_ping=True,
)
test_async_session_factory = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Monkeypatch the global factory so manual imports use the test DB
db_module.engine = test_engine
db_module.async_session_factory = test_async_session_factory

# Also override the FastAPI dependency
from app.main import app

async def override_get_db_session():
    async with test_async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

app.dependency_overrides[get_db_session] = override_get_db_session

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"
