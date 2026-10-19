"""Turn stream events. Discriminated on type for the SSE contract."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, TypeAdapter

from docu.domain.base import ApiModel
from docu.domain.document import Slide
from docu.domain.errors import TurnErrorCode


class TextDeltaEvent(ApiModel):
    type: Literal["text_delta"] = "text_delta"
    text: str


class ReasoningDeltaEvent(ApiModel):
    type: Literal["reasoning_delta"] = "reasoning_delta"
    text: str


class ToolCallDeltaEvent(ApiModel):
    type: Literal["tool_call_delta"] = "tool_call_delta"
    index: int
    id: str = ""
    name: str = ""
    arguments_chars: int = 0


class ToolCallEvent(ApiModel):
    type: Literal["tool_call"] = "tool_call"
    id: str
    name: str
    arguments: str


class SlideSummary(ApiModel):
    id: str
    index: int
    layout: str
    title: str


class ReplaceSlidesCard(ApiModel):
    kind: Literal["replace_slides"] = "replace_slides"
    before: list[SlideSummary]
    after: list[SlideSummary]
    manual_edits_lost: int


class DeleteSlidesCard(ApiModel):
    kind: Literal["delete_slides"] = "delete_slides"
    slides: list[SlideSummary]


class GenerateImageCard(ApiModel):
    kind: Literal["generate_image"] = "generate_image"
    slide_id: str
    prompt: str
    credits: int


class McpWriteCard(ApiModel):
    kind: Literal["mcp_write"] = "mcp_write"
    server: str
    tool: str
    arguments_preview: str


ApprovalCard = Annotated[
    ReplaceSlidesCard | DeleteSlidesCard | GenerateImageCard | McpWriteCard,
    Field(discriminator="kind"),
]


class ToolApprovalEvent(ApiModel):
    type: Literal["tool_approval"] = "tool_approval"
    id: str
    name: str
    arguments: str
    approval_card: ApprovalCard


class AskUserField(ApiModel):
    key: str
    label: str
    type: Literal["choice", "text", "number"]
    options: list[str] | None = None


class AskUserEvent(ApiModel):
    type: Literal["ask_user"] = "ask_user"
    id: str
    question: str
    options: list[Annotated[str, Field(max_length=120)]] | None = Field(None, max_length=64)
    fields: list[AskUserField] | None = Field(None, max_length=6)
    allow_free_text: bool = False


class ToolResultEvent(ApiModel):
    type: Literal["tool_result"] = "tool_result"
    id: str
    name: str
    result: str
    ok: bool


class ErrorEvent(ApiModel):
    type: Literal["error"] = "error"
    message: str
    code: str


class StatusEvent(ApiModel):
    type: Literal["status"] = "status"
    message: str


class DoneEvent(ApiModel):
    type: Literal["done"] = "done"
    steps: int


class TurnStartedEvent(ApiModel):
    type: Literal["turn_started"] = "turn_started"
    turn_id: str
    base_version: int
    model: str
    effort: str
    profile: str


class SetTitleOp(ApiModel):
    op: Literal["set_title"] = "set_title"
    title: str


class SetThemeOp(ApiModel):
    op: Literal["set_theme"] = "set_theme"
    theme_id: str


class InsertSlideOp(ApiModel):
    op: Literal["insert_slide"] = "insert_slide"
    slide: Slide
    after_slide_id: str | None


class UpdateSlideOp(ApiModel):
    op: Literal["update_slide"] = "update_slide"
    slide_id: str
    slide: Slide


class DeleteSlideOp(ApiModel):
    op: Literal["delete_slide"] = "delete_slide"
    slide_id: str


class MoveSlideOp(ApiModel):
    op: Literal["move_slide"] = "move_slide"
    slide_id: str
    after_slide_id: str | None


class ReplaceSlidesOp(ApiModel):
    op: Literal["replace_slides"] = "replace_slides"
    slides: list[Slide]


DocOp = Annotated[
    SetTitleOp
    | SetThemeOp
    | InsertSlideOp
    | UpdateSlideOp
    | DeleteSlideOp
    | MoveSlideOp
    | ReplaceSlidesOp,
    Field(discriminator="op"),
]


class DocPatchEvent(ApiModel):
    type: Literal["doc_patch"] = "doc_patch"
    tool_call_id: str
    ops: list[DocOp]
    changed_slide_ids: list[str]
    draft_version: int


class MemorySavedEvent(ApiModel):
    type: Literal["memory_saved"] = "memory_saved"
    memory_id: str
    text: str


class SkillLoadedEvent(ApiModel):
    type: Literal["skill_loaded"] = "skill_loaded"
    name: str


class StepLimitEvent(ApiModel):
    type: Literal["step_limit"] = "step_limit"
    steps: int


class WaitingInputEvent(ApiModel):
    type: Literal["waiting_input"] = "waiting_input"
    turn_id: str
    expires_at: datetime


class TokenUsage(ApiModel):
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    reasoning_tokens: int = 0


class TurnCommittedEvent(ApiModel):
    type: Literal["turn_committed"] = "turn_committed"
    turn_id: str
    version: int
    revision_id: UUID
    credits_charged: int
    changed_slide_ids: list[str]
    usage: TokenUsage


class TurnFailedEvent(ApiModel):
    type: Literal["turn_failed"] = "turn_failed"
    turn_id: str
    code: TurnErrorCode
    message: str
    retryable: bool


class TurnCancelledEvent(ApiModel):
    type: Literal["turn_cancelled"] = "turn_cancelled"
    turn_id: str
    reason: Literal["user", "expired"]


TurnEvent = Annotated[
    TextDeltaEvent
    | ReasoningDeltaEvent
    | ToolCallDeltaEvent
    | ToolCallEvent
    | ToolApprovalEvent
    | AskUserEvent
    | ToolResultEvent
    | ErrorEvent
    | StatusEvent
    | DoneEvent
    | TurnStartedEvent
    | DocPatchEvent
    | MemorySavedEvent
    | SkillLoadedEvent
    | StepLimitEvent
    | WaitingInputEvent
    | TurnCommittedEvent
    | TurnFailedEvent
    | TurnCancelledEvent,
    Field(discriminator="type"),
]

turn_event_adapter: TypeAdapter[TurnEvent] = TypeAdapter(TurnEvent)

__all__ = [
    "ApprovalCard",
    "AskUserEvent",
    "AskUserField",
    "DocOp",
    "DocPatchEvent",
    "DoneEvent",
    "ErrorEvent",
    "MemorySavedEvent",
    "ReasoningDeltaEvent",
    "SkillLoadedEvent",
    "StatusEvent",
    "StepLimitEvent",
    "TextDeltaEvent",
    "TokenUsage",
    "ToolApprovalEvent",
    "ToolCallDeltaEvent",
    "ToolCallEvent",
    "ToolResultEvent",
    "TurnCancelledEvent",
    "TurnCommittedEvent",
    "TurnEvent",
    "TurnFailedEvent",
    "TurnStartedEvent",
    "WaitingInputEvent",
    "turn_event_adapter",
]
