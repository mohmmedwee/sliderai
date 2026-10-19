"""Error codes stay in lockstep with the REST and SSE contracts."""

from __future__ import annotations

from typing import get_args

from docu.domain.errors import RETRYABLE, DomainError, ErrorCode, ErrorEnvelope, TurnErrorCode

REST_CODES = [
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

TURN_CODES = [
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

RETRYABLE_CODES = [
    "doc_busy",
    "upstream_unreachable",
    "provider_rate_limited",
    "version_conflict",
    "worker_lost",
    "internal",
]


def test_rest_codes_match_the_contract() -> None:
    assert list(get_args(ErrorCode)) == REST_CODES


def test_turn_codes_and_retryable_match_the_contract() -> None:
    assert list(get_args(TurnErrorCode)) == TURN_CODES
    assert frozenset(RETRYABLE_CODES) == RETRYABLE


def test_domain_error_and_envelope() -> None:
    err = DomainError("version_conflict", 409, "changed", {"version": 3})
    body = ErrorEnvelope(error={"code": err.code, "message": err.message, "details": err.details})
    dumped = body.model_dump(by_alias=True)
    assert dumped == {
        "error": {"code": "version_conflict", "message": "changed", "details": {"version": 3}}
    }
