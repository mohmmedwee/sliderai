"""LLM / upstream / vision settings face."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

__all__ = ["LLM_FLAT", "LlmSettings"]


class LlmSettings(BaseModel):
    """Where chat and vision models live, and how we talk to them."""

    upstream: str = Field(
        default="",
        description="Base URL of the OpenAI-compatible endpoint, including the /v1 path.",
    )
    upstream_api_key: str = Field(
        default="",
        description="Bearer token for upstream when the endpoint requires auth.",
    )
    upstream_top_effort: str = Field(
        default="xhigh",
        description=(
            "Value sent for UI Thorough/xhigh. Use `xhigh` for local models; "
            "`high` for hosted endpoints that only accept low/medium/high."
        ),
    )
    enable_thinking: bool = Field(
        default=True,
        description="When false, chat streams omit reasoning effort.",
    )
    model: str = Field(default="", description="Pinned chat model id.")
    models_free_only: bool = Field(
        default=False,
        description="When true, the picker only lists ids ending in :free.",
    )
    vision_model: str = Field(default="", description="Multimodal model id. Empty uses MODEL.")
    vision_timeout: float = Field(default=300.0, gt=0)
    max_image_bytes: int = Field(default=8 * 1024 * 1024, gt=0)
    request_timeout: float = Field(default=1_800.0, gt=0)
    stream_idle_timeout: float = Field(default=240.0, gt=0)
    connect_timeout: float = Field(default=10.0, gt=0)
    model_listing_timeout: float = Field(default=15.0, gt=0)
    context_window: int = Field(default=32_768, gt=0)
    max_completion_tokens: int = Field(default=8_192, gt=256)
    small_model: str = Field(default="", description="Empty means use MODEL.")
    fallback_provider: str = Field(default="")
    fallback_model: str = Field(default="")
    fallback_api_key: str = Field(default="")
    provider: Literal["openai", "anthropic"] = "openai"

    @field_validator("upstream")
    @classmethod
    def _strip_upstream_slash(cls, value: str) -> str:
        return value.strip().rstrip("/")


LLM_FLAT: dict[str, str] = {
    "upstream": "upstream",
    "upstream_api_key": "upstream_api_key",
    "upstream_top_effort": "upstream_top_effort",
    "enable_thinking": "enable_thinking",
    "model": "model",
    "models_free_only": "models_free_only",
    "vision_model": "vision_model",
    "vision_timeout": "vision_timeout",
    "max_image_bytes": "max_image_bytes",
    "request_timeout": "request_timeout",
    "stream_idle_timeout": "stream_idle_timeout",
    "connect_timeout": "connect_timeout",
    "model_listing_timeout": "model_listing_timeout",
    "context_window": "context_window",
    "max_completion_tokens": "max_completion_tokens",
    "small_model": "small_model",
    "fallback_provider": "fallback_provider",
    "fallback_model": "fallback_model",
    "fallback_api_key": "fallback_api_key",
    "provider": "provider",
}
