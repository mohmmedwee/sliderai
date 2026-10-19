"""FastAPI dependencies for process resources stored on app.state."""

from __future__ import annotations

from typing import Any, cast

from fastapi import Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine

from docu.storage.blob_store import BlobStore

__all__ = ["get_blob_store", "get_engine", "get_redis"]


def get_engine(request: Request) -> AsyncEngine:
    engine: AsyncEngine = request.app.state.engine
    return engine


def get_redis(request: Request) -> Redis[bytes]:
    client: Redis[bytes] = request.app.state.redis
    return client


def get_blob_store(request: Request) -> BlobStore:
    store: Any = request.app.state.blob_store
    return cast(BlobStore, store)
