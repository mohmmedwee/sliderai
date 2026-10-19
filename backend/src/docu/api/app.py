"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import create_async_engine

from docu.api.routers.health import router as health_router
from docu.core.config import get_settings
from docu.storage.blob_store import build_blob_store

__all__ = ["create_app"]


def _spa_index() -> Path | None:
    candidate = Path("web/dist/index.html")
    if candidate.is_file():
        return candidate
    return None


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    engine = create_async_engine(settings.database.url, pool_pre_ping=True)
    redis = Redis.from_url(settings.redis.url)
    blob = build_blob_store(settings, Path(settings.storage.upload_dir))
    app.state.engine = engine
    app.state.redis = redis
    app.state.blob_store = blob
    app.state.settings = settings
    try:
        yield
    finally:
        await redis.close()
        await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(lifespan=_lifespan)
    app.include_router(health_router)
    if settings.storage.file_storage == "local":
        app.add_api_route("/v1/_local-upload/{key:path}", _local_upload, methods=["PUT"])
    index = _spa_index()
    if index is not None:
        app.mount("/", StaticFiles(directory=index.parent, html=True), name="spa")
    return app


async def _local_upload(key: str, request: Request, sig: str) -> dict[str, bool]:
    settings = get_settings()
    serializer = URLSafeTimedSerializer(settings.auth.secret_key, salt="docu-local-upload")
    try:
        payload = serializer.loads(sig, max_age=900)
    except (BadSignature, SignatureExpired) as exc:
        raise HTTPException(status_code=403, detail="bad signature") from exc
    if not isinstance(payload, dict) or payload.get("key") != key or payload.get("op") != "put":
        raise HTTPException(status_code=403, detail="bad signature")
    body = await request.body()
    max_bytes = int(payload.get("max_bytes", 0))
    if len(body) > max_bytes:
        raise HTTPException(status_code=413, detail="too large")
    request.app.state.blob_store.put(key, body, content_type=payload.get("content_type"))
    return {"ok": True}
