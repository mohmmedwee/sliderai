"""Document content: slides, themes, and the CSS field grammar."""

from __future__ import annotations

import re
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AfterValidator, Field, model_validator

from docu.domain.base import ApiModel

_BYTE = r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
_HUE = r"(?:360|3[0-5]\d|[12]\d\d|[1-9]?\d)"
_PCT = r"(?:100|[1-9]?\d)"
_HEX = r"#[0-9A-Fa-f]{6}|#[0-9A-Fa-f]{3}"
_RGB = rf"rgb\(\s*{_BYTE}\s*,\s*{_BYTE}\s*,\s*{_BYTE}\s*\)"
_HSL = rf"hsl\(\s*{_HUE}\s*,\s*{_PCT}%\s*,\s*{_PCT}%\s*\)"
_COLOR = rf"(?:{_HEX}|{_RGB}|{_HSL})"
_STOP = rf"{_COLOR}\s+{_PCT}%"
_GRADIENT = rf"linear-gradient\(\s*{_HUE}deg\s*,\s*{_STOP}(?:\s*,\s*{_STOP}){{1,3}}\s*\)"
_CSS = re.compile(rf"(?:{_COLOR}|{_GRADIENT})")

Format = Literal["presentation", "document", "webpage", "social"]
Layout = Literal["hero", "title", "points", "quote", "split", "table", "chart"]


def validate_css_field(value: str) -> str:
    if _CSS.fullmatch(value) is None:
        raise ValueError("invalid_field")
    return value


CssField = Annotated[str, AfterValidator(validate_css_field)]


class TableData(ApiModel):
    columns: list[Annotated[str, Field(max_length=40)]] = Field(min_length=1, max_length=8)
    rows: list[list[str | float | None]] = Field(min_length=1, max_length=12)


class ChartSeries(ApiModel):
    name: str = Field(max_length=40)
    values: list[float | None] = Field(min_length=1, max_length=24)


class ChartData(ApiModel):
    kind: Literal["bar", "line", "pie", "donut"]
    labels: list[Annotated[str, Field(max_length=40)]] = Field(min_length=1, max_length=24)
    series: list[ChartSeries] = Field(min_length=1, max_length=6)
    unit: str | None = Field(None, max_length=12)


class SlideImage(ApiModel):
    asset_id: UUID
    alt: str = Field(min_length=1, max_length=200)
    focal: tuple[float, float] | None = None


class SlideInput(ApiModel):
    layout: Layout
    kicker: str | None = Field(None, max_length=60)
    title: str = Field(min_length=1, max_length=140)
    body: str | None = Field(None, max_length=600)
    points: list[Annotated[str, Field(max_length=160)]] | None = Field(None, max_length=6)
    button: str | None = Field(None, max_length=40)
    field: CssField | None = None
    image: SlideImage | None = None
    table: TableData | None = None
    chart: ChartData | None = None
    notes: str | None = Field(None, max_length=2000)

    @model_validator(mode="after")
    def _layout_rules(self) -> SlideInput:
        if self.layout != "table" and self.table is not None:
            raise ValueError("field_not_allowed")
        if self.layout != "chart" and self.chart is not None:
            raise ValueError("field_not_allowed")
        if self.layout == "points" and not self.points:
            raise ValueError("points_required")
        if self.layout == "table":
            if self.table is None:
                raise ValueError("table_required")
            width = len(self.table.columns)
            if any(len(row) != width for row in self.table.rows):
                raise ValueError("table_shape")
        if self.layout == "chart":
            if self.chart is None:
                raise ValueError("chart_required")
            if self.chart.kind in {"pie", "donut"} and len(self.chart.series) != 1:
                raise ValueError("chart_shape")
            width = len(self.chart.labels)
            if any(len(series.values) != width for series in self.chart.series):
                raise ValueError("chart_shape")
        return self


class Slide(SlideInput):
    """A slide with its stored id. SlideInput is the same shape without one."""

    id: str


class DocumentContent(ApiModel):
    slides: list[Slide] = Field(min_length=1, max_length=60)


class ThemeTokens(ApiModel):
    bg: str
    paper: str
    ink: str
    accent: str
    tone: Literal["light", "dark"]
    font: Literal["sans", "serif"] = "sans"


class Theme(ApiModel):
    id: str
    name: str
    tokens: ThemeTokens
    tags: list[str]


class DocumentState(ApiModel):
    """What a turn edits: the agent's draft and the editor's working copy."""

    title: str = Field(min_length=1, max_length=140)
    theme_id: str
    slides: list[Slide] = Field(min_length=1, max_length=60)


__all__ = [
    "ChartData",
    "ChartSeries",
    "CssField",
    "DocumentContent",
    "DocumentState",
    "Format",
    "Layout",
    "Slide",
    "SlideImage",
    "SlideInput",
    "TableData",
    "Theme",
    "ThemeTokens",
    "validate_css_field",
]
