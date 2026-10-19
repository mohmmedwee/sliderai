"""Placeholders for open product decisions. See BLOCKED.md."""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = ["PRODUCT_FLAT", "ProductSettings"]


class ProductSettings(BaseModel):
    """FR-037 region and FR-038 retention. Defaults are for local/dev."""

    data_region: str = Field(default="local")
    retention_days: int = Field(default=30, gt=0)


PRODUCT_FLAT: dict[str, str] = {
    "data_region": "data_region",
    "retention_days": "retention_days",
}
