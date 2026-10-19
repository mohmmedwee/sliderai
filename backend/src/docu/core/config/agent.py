"""Agent-loop settings face — budget, clipping, approvals, setup tools."""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = ["AGENT_FLAT", "AgentSettings"]


class AgentSettings(BaseModel):
    """Agent-loop knobs: budget, clipping, approvals, setup tools."""

    max_steps: int = Field(default=24, gt=0, description="Tool-call rounds before wrap-up.")
    setup_tools: set[str] = Field(
        default_factory=lambda: {
            "read_skill",
            "list_uploaded_files",
            "ask_user",
            "list_mcp_tools",
            "use_mcp_tools",
        },
        description="Tool names whose rounds do not spend the step budget.",
    )
    schema_only_tools: set[str] = Field(
        default_factory=lambda: {"list_mcp_tools", "use_mcp_tools", "read_skill"},
    )
    setup_allowance: int = Field(default=12, gt=0)
    auto_continue_steps: int = Field(default=8, gt=0)
    empty_reply_retries: int = Field(default=4, gt=0)
    upstream_retries: int = Field(default=2, ge=0)
    repeat_guarded_tools: set[str] = Field(
        default_factory=lambda: {
            "read_uploaded_file",
            "read_file",
            "search_uploaded_files",
            "web_search",
            "fetch_url",
        },
    )
    repeat_limit: int = Field(default=2, gt=0)
    budget_ceiling: dict[str, int] = Field(
        default_factory=lambda: {
            "minimal": 4_096,
            "low": 8_192,
            "medium": 12_288,
            "xhigh": 16_384,
            "high": 16_384,
        },
    )
    budget_floor: int = Field(default=4_096, gt=0)
    budget_margin: int = Field(default=1_024, gt=0)
    estimate_safety: float = Field(default=1.15, ge=1.0)
    clip_keep: int = Field(default=2, gt=0)
    clip_chars: int = Field(default=600, gt=0)
    clip_mark: str = Field(default="… [clipped]")
    # Mirrors llm.*; the card's env defaults live on LlmSettings and are copied across.
    context_window: int = Field(default=32_768, gt=0)
    context_summarize_ratio: float = Field(default=0.55, gt=0.1, le=0.95)
    context_keep_recent: int = Field(default=6, gt=0)
    context_summarize_after_messages: int = Field(default=24, gt=0)
    max_completion_tokens: int = Field(default=8_192, gt=256)
    approval_required_tools: set[str] = Field(default_factory=lambda: {"write_file"})
    approval_required_mcp_tools: set[str] = Field(default_factory=set)
    approval_timeout: float = Field(default=600.0, gt=0)


AGENT_FLAT: dict[str, str] = {
    "max_steps": "max_steps",
    "setup_tools": "setup_tools",
    "schema_only_tools": "schema_only_tools",
    "setup_allowance": "setup_allowance",
    "auto_continue_steps": "auto_continue_steps",
    "empty_reply_retries": "empty_reply_retries",
    "upstream_retries": "upstream_retries",
    "repeat_guarded_tools": "repeat_guarded_tools",
    "repeat_limit": "repeat_limit",
    "budget_ceiling": "budget_ceiling",
    "budget_floor": "budget_floor",
    "budget_margin": "budget_margin",
    "estimate_safety": "estimate_safety",
    "clip_keep": "clip_keep",
    "clip_chars": "clip_chars",
    "clip_mark": "clip_mark",
    "context_summarize_ratio": "context_summarize_ratio",
    "context_keep_recent": "context_keep_recent",
    "context_summarize_after_messages": "context_summarize_after_messages",
    "approval_required_tools": "approval_required_tools",
    "approval_required_mcp_tools": "approval_required_mcp_tools",
    "approval_timeout": "approval_timeout",
}
