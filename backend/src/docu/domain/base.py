"""Wire models: camelCase JSON, snake_case Python."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    """Wire model: camelCase JSON, snake_case Python, unknown fields rejected."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
        frozen=False,
    )


__all__ = ["ApiModel"]
