"""Every turn event round-trips, and the ask_user limits hold."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from docu.domain.document import Slide
from docu.domain.events import (
    AskUserEvent,
    DocPatchEvent,
    DoneEvent,
    ErrorEvent,
    MemorySavedEvent,
    ReasoningDeltaEvent,
    SkillLoadedEvent,
    StatusEvent,
    StepLimitEvent,
    TextDeltaEvent,
    TokenUsage,
    ToolApprovalEvent,
    ToolCallDeltaEvent,
    ToolCallEvent,
    ToolResultEvent,
    TurnCancelledEvent,
    TurnCommittedEvent,
    TurnFailedEvent,
    TurnStartedEvent,
    WaitingInputEvent,
    turn_event_adapter,
)

SLIDE = Slide.model_validate({"id": "slide00001", "layout": "hero", "title": "Hello"})
SUMMARY = {"id": "slide00001", "index": 0, "layout": "hero", "title": "Hello"}


def test_every_event_round_trips_as_json() -> None:
    events = [
        TextDeltaEvent(text="hi"),
        ReasoningDeltaEvent(text="hmm"),
        ToolCallDeltaEvent(index=0, id="c1", name="add_slide", arguments_chars=12),
        ToolCallEvent(id="c1", name="add_slide", arguments="{}"),
        ToolApprovalEvent(
            id="c1",
            name="replace_slides",
            arguments="{}",
            approval_card={"kind": "delete_slides", "slides": [SUMMARY]},
        ),
        AskUserEvent(id="q1", question="Which?", options=["A"], allow_free_text=True),
        ToolResultEvent(id="c1", name="add_slide", result="ok", ok=True),
        ErrorEvent(message="nope", code="internal"),
        StatusEvent(message="status.compacting"),
        DoneEvent(steps=3),
        TurnStartedEvent(
            turn_id="t1",
            base_version=1,
            model="m",
            effort="low",
            profile="deck",
        ),
        DocPatchEvent(
            tool_call_id="c1",
            ops=[{"op": "set_title", "title": "Deck"}],
            changed_slide_ids=["slide00001"],
            draft_version=2,
        ),
        MemorySavedEvent(memory_id="m1", text="prefers Arabic"),
        SkillLoadedEvent(name="deck-outline"),
        StepLimitEvent(steps=8),
        WaitingInputEvent(turn_id="t1", expires_at=datetime(2026, 10, 19, tzinfo=UTC)),
        TurnCommittedEvent(
            turn_id="t1",
            version=2,
            revision_id=UUID("018f3b2a-7c4e-7000-8000-000000000001"),
            credits_charged=4,
            changed_slide_ids=["slide00001"],
            usage=TokenUsage(input_tokens=10, output_tokens=20),
        ),
        TurnFailedEvent(turn_id="t1", code="worker_lost", message="lost", retryable=True),
        TurnCancelledEvent(turn_id="t1", reason="user"),
    ]
    for event in events:
        payload = event.model_dump(mode="json", by_alias=True)
        assert turn_event_adapter.validate_python(payload) == event


def test_unknown_event_type_fails() -> None:
    with pytest.raises(ValidationError):
        turn_event_adapter.validate_python({"type": "nope"})


def test_ask_user_rejects_65_options() -> None:
    with pytest.raises(ValidationError):
        AskUserEvent(id="q1", question="Which?", options=[str(i) for i in range(65)])


def test_doc_patch_carries_a_slide_op() -> None:
    event = DocPatchEvent(
        tool_call_id="c1",
        ops=[{"op": "insert_slide", "slide": SLIDE, "afterSlideId": None}],
        changed_slide_ids=[SLIDE.id],
        draft_version=2,
    )
    assert event.ops[0].op == "insert_slide"
