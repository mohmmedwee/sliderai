"""Celery routes document work onto the right queues."""

from __future__ import annotations

from docu.worker.celery_app import app


def test_turn_route_uses_turns_queue() -> None:
    assert app.amqp.router.route({}, "docu.turn")["queue"].name == "turns"


def test_file_and_export_routes() -> None:
    assert app.amqp.router.route({}, "docu.parse")["queue"].name == "files"
    assert app.amqp.router.route({}, "docu.export_pdf")["queue"].name == "exports"
