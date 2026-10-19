"""Per-task resources. Each Celery task builds its own; nothing is shared across loops."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from docu.core.config import Settings, get_settings
from docu.storage.blob_store import BlobStore, build_blob_store

__all__ = ["Res", "task_resources"]


@dataclass
class Res:
    engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]
    redis: Redis[bytes]
    blob: BlobStore
    settings: Settings


@asynccontextmanager
async def task_resources() -> AsyncIterator[Res]:
    settings = get_settings()
    engine = create_async_engine(settings.database.url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    redis = Redis.from_url(settings.redis.url)
    blob = build_blob_store(settings, Path(settings.storage.upload_dir))
    try:
        yield Res(engine, session_factory, redis, blob, settings)
    finally:
        await redis.close()
        await engine.dispose()
