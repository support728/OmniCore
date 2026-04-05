from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fastapi_rag_backend.app.config import settings


def get_database_url() -> str:
    if settings.database_url:
        return settings.database_url
    if settings.environment.lower() == "dev" and settings.use_sqlite_fallback:
        return settings.sqlite_fallback_dsn
    return settings.postgres_dsn


DATABASE_URL = get_database_url()
engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


def is_postgres_backend() -> bool:
    return DATABASE_URL.startswith("postgresql+")


def is_sqlite_backend() -> bool:
    return DATABASE_URL.startswith("sqlite+")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    async with engine.begin() as conn:
        if is_postgres_backend():
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        from fastapi_rag_backend.app.models import Base

        await conn.run_sync(Base.metadata.create_all)
