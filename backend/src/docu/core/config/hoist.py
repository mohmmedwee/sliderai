"""Hoist flat env/kwargs into nested settings groups."""

from __future__ import annotations

import os
from typing import Any

from pydantic import BaseModel

__all__ = ["hoist_group"]


def hoist_group(data: dict[str, Any], group: str, mapping: dict[str, str]) -> dict[str, Any]:
    nested: dict[str, Any] = {}
    existing = data.get(group)
    if isinstance(existing, dict):
        nested.update(existing)
    elif isinstance(existing, BaseModel):
        nested.update(existing.model_dump())

    lower_keys = {str(k).lower(): k for k in data}

    for flat, nested_key in mapping.items():
        if nested_key in nested:
            continue
        # Process env wins over .env extras (same priority as BaseSettings fields).
        env_val = os.environ.get(flat.upper())
        if env_val is not None and env_val != "":
            nested[nested_key] = env_val
            src_key = lower_keys.get(flat.lower())
            if src_key is not None and src_key != group:
                data.pop(src_key, None)
            continue
        src_key = lower_keys.get(flat.lower())
        if src_key is not None and src_key != group:
            nested[nested_key] = data.pop(src_key)

    for flat in mapping:
        src_key = lower_keys.get(flat.lower())
        if src_key is not None and src_key != group and src_key in data:
            data.pop(src_key, None)

    if nested:
        data[group] = nested
    return data
