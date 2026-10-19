"""Slide ids and UUIDv7s."""

from __future__ import annotations

import secrets
import string
from uuid import UUID

import uuid6

_ALPHABET = string.ascii_letters + string.digits


def new_slide_id() -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(10))


def new_uuid() -> UUID:
    return uuid6.uuid7()


__all__ = ["new_slide_id", "new_uuid"]
