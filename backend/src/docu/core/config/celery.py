"""Celery broker settings face."""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = ["CELERY_FLAT", "CelerySettings"]


class CelerySettings(BaseModel):
    """Broker URL. Empty means use REDIS_URL (filled in on Settings)."""

    broker_url: str = Field(default="")


CELERY_FLAT: dict[str, str] = {
    "celery_broker_url": "broker_url",
}
