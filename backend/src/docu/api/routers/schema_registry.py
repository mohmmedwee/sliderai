"""A route that exists only to publish the turn-event union in OpenAPI."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from docu.domain.events import TurnEvent

__all__ = ["router"]

router = APIRouter(prefix="/v1", tags=["schema"])


@router.get("/_schema/turn-event", response_model=TurnEvent)
def turn_event_schema() -> TurnEvent:
    raise HTTPException(status_code=404)
