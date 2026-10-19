"""Health and readiness over the ASGI app."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from docu.api.app import create_app


class _DeadRedis:
    async def ping(self) -> bool:
        raise ConnectionError("redis stopped")

    async def aclose(self) -> None:
        return None


@pytest.mark.redis
async def test_health_ok() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["revision"] == "dev"
    assert "model" in body


@pytest.mark.redis
async def test_ready_503_when_redis_stopped() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        app.state.redis = _DeadRedis()
        response = await client.get("/v1/ready")
    assert response.status_code == 503
