from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.base import Base


def _to_async_url(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    raise ValueError("Only PostgreSQL database URLs are supported.")


engine = create_async_engine(_to_async_url(settings.DATABASE_URL), echo=False, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def configure_database_url(database_url: str) -> None:
    """Switch the runtime database connection after verifying PostgreSQL + pgvector."""
    global engine, AsyncSessionLocal

    next_engine = create_async_engine(_to_async_url(database_url), echo=False, pool_pre_ping=True)
    try:
        async with next_engine.begin() as connection:
            if connection.dialect.name != "postgresql":
                raise ValueError("Configured database is not PostgreSQL.")
            await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            result = await connection.execute(
                text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
            )
            if result.scalar_one_or_none() != "vector":
                raise ValueError("pgvector extension is not enabled in the configured database.")
            await connection.run_sync(Base.metadata.create_all)
    except Exception:
        await next_engine.dispose()
        raise

    previous_engine = engine
    engine = next_engine
    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    await previous_engine.dispose()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
