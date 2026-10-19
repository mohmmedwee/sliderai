"""Celery application: queues turns, files, exports, and default."""

from __future__ import annotations

from celery import Celery

from docu.core.config import get_settings

__all__ = ["app"]

settings = get_settings()
app = Celery("docu", broker=settings.celery.broker_url)
app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    task_default_queue="default",
    task_routes={
        "docu.turn*": {"queue": "turns"},
        "docu.parse*": {"queue": "files"},
        "docu.scan*": {"queue": "files"},
        "docu.embed*": {"queue": "files"},
        "docu.import*": {"queue": "files"},
        "docu.export*": {"queue": "exports"},
        "docu.thumbnail*": {"queue": "exports"},
    },
    beat_schedule={},
)
