"""Liveness and readiness."""

from __future__ import annotations

import os

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from docu.core.config import get_settings

__all__ = ["router"]

router = APIRouter(prefix="/v1", tags=["health"])


@router.get("/health")
async def health() -> dict[str, object]:
    settings = get_settings()
    return {
        "ok": True,
        "revision": os.environ.get("GIT_SHA", "dev"),
        "model": settings.llm.model,
    }


@router.get("/ready", response_model=None)
async def ready(request: Request) -> JSONResponse:
    try:
        engine = request.app.state.engine
        async with engine.connect() as conn:
            await conn.execute(text("select 1"))
        await request.app.state.redis.ping()
    except Exception:
        return JSONResponse({"ok": False}, status_code=503)
    return JSONResponse({"ok": True})
