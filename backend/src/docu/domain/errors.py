"""API and turn error codes."""

from __future__ import annotations

from typing import Literal

from docu.domain.base import ApiModel


class DomainError(Exception):
    def __init__(
        self,
        code: str,
        status: int = 400,
        message: str = "",
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message or code)
        self.code = code
        self.status = status
        self.message = message
        self.details = details or {}


class ErrorBody(ApiModel):
    code: str
    message: str
    details: dict[str, object]


class ErrorEnvelope(ApiModel):
    error: ErrorBody


ErrorCode = Literal[
    "invalid_request",
    "unauthenticated",
    "forbidden",
    "email_unverified",
    "plan_required",
    "not_found",
    "version_conflict",
    "doc_busy",
    "insufficient_credits",
    "too_large",
    "unsupported_type",
    "rate_limited",
    "internal",
    "invalid_credentials",
    "totp_required",
]

TurnErrorCode = Literal[
    "insufficient_credits",
    "doc_busy",
    "upstream_unreachable",
    "provider_auth",
    "provider_rate_limited",
    "context_overflow",
    "version_conflict",
    "worker_lost",
    "content_blocked",
    "internal",
]

RETRYABLE: frozenset[str] = frozenset(
    {
        "doc_busy",
        "upstream_unreachable",
        "provider_rate_limited",
        "version_conflict",
        "worker_lost",
        "internal",
    }
)

__all__ = [
    "RETRYABLE",
    "DomainError",
    "ErrorBody",
    "ErrorCode",
    "ErrorEnvelope",
    "TurnErrorCode",
]
