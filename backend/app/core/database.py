"""
CareerPilot AI — Database Configuration

Sets up SQLAlchemy engine and session factory.
Actual database connections will be established when Phase 2 begins.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings


def _get_async_url(raw_url: str) -> URL | str:
    # Safely split by the LAST '@' to separate credentials from host
    if "@" in raw_url:
        prefix_and_creds, host_and_db = raw_url.rsplit("@", 1)
        if "://" in prefix_and_creds:
            scheme, creds = prefix_and_creds.split("://", 1)
            # Force async psycopg driver
            scheme = "postgresql+psycopg"

            if ":" in creds:
                user, pwd = creds.split(":", 1)

                if "/" in host_and_db:
                    host_port, dbname = host_and_db.split("/", 1)
                else:
                    host_port, dbname = host_and_db, ""

                if ":" in host_port:
                    host, port_str = host_port.split(":", 1)
                    port = int(port_str)
                else:
                    host, port = host_port, 5432

                return URL.create(
                    drivername=scheme,
                    username=user,
                    password=pwd,  # URL.create correctly handles unencoded passwords
                    host=host,
                    port=port,
                    database=dbname,
                )

    # Fallback to simple replace if parsing fails
    return raw_url.replace(
        "postgresql://",
        "postgresql+psycopg://",
    ).replace("postgresql+psycopg+psycopg://", "postgresql+psycopg://")


_async_database_url = _get_async_url(settings.database_url)
engine = create_async_engine(
    _async_database_url,
    echo=settings.app_debug,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields a database session and ensures cleanup."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
