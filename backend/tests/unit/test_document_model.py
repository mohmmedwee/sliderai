"""Layout rules, the CSS field grammar, and camelCase wire names."""

from __future__ import annotations

from uuid import UUID

import pytest
from pydantic import ValidationError

from docu.domain.document import (
    ChartData,
    CssField,
    DocumentState,
    Slide,
    SlideImage,
    SlideInput,
    TableData,
    Theme,
    ThemeTokens,
)
from docu.domain.ids import new_slide_id, new_uuid


def _slide(**overrides: object) -> Slide:
    data: dict[str, object] = {"id": "slide00001", "layout": "hero", "title": "Hello"}
    data.update(overrides)
    return Slide.model_validate(data)


def test_each_layout_accepts_a_valid_sample() -> None:
    _slide(layout="hero")
    _slide(layout="title")
    _slide(layout="points", points=["One"])
    _slide(layout="quote", body="Ada")
    _slide(layout="split", field="#abc")
    _slide(
        layout="table",
        table=TableData(columns=["A", "B"], rows=[["x", 1], ["y", None]]),
    )
    _slide(
        layout="chart",
        chart=ChartData(
            kind="bar",
            labels=["Q1", "Q2"],
            series=[{"name": "Rev", "values": [1.0, 2.0]}],
        ),
    )


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"layout": "points"}, "points_required"),
        ({"layout": "points", "points": []}, "points_required"),
        ({"layout": "table"}, "table_required"),
        (
            {"layout": "table", "table": {"columns": ["A"], "rows": [["x", "y"]]}},
            "table_shape",
        ),
        ({"layout": "chart"}, "chart_required"),
        (
            {
                "layout": "chart",
                "chart": {
                    "kind": "line",
                    "labels": ["A", "B"],
                    "series": [{"name": "S", "values": [1]}],
                },
            },
            "chart_shape",
        ),
        (
            {
                "layout": "chart",
                "chart": {
                    "kind": "pie",
                    "labels": ["A"],
                    "series": [{"name": "S", "values": [1]}, {"name": "T", "values": [2]}],
                },
            },
            "chart_shape",
        ),
        (
            {"layout": "hero", "table": {"columns": ["A"], "rows": [["x"]]}},
            "field_not_allowed",
        ),
        (
            {
                "layout": "title",
                "chart": {
                    "kind": "donut",
                    "labels": ["A"],
                    "series": [{"name": "S", "values": [1]}],
                },
            },
            "field_not_allowed",
        ),
    ],
)
def test_layout_rules_raise_the_contract_codes(overrides: dict[str, object], code: str) -> None:
    with pytest.raises(ValidationError, match=code):
        _slide(**overrides)


@pytest.mark.parametrize(
    "value",
    [
        "#abc",
        "#aabbcc",
        "rgb(1, 2, 3)",
        "hsl(180,50%,50%)",
        "linear-gradient(135deg, #abc 0%, #aabbcc 100%)",
        "linear-gradient(0deg, rgb(0,0,0) 0%, hsl(0,0%,100%) 50%, #fff 100%)",
    ],
)
def test_css_field_accepts_the_grammar(value: str) -> None:
    _slide(field=value)


@pytest.mark.parametrize("value", ["url(x)", "red; background:url()", "var(--a)"])
def test_css_field_rejects_anything_outside_the_grammar(value: str) -> None:
    with pytest.raises(ValidationError, match="invalid_field"):
        _slide(field=value)


def test_wire_names_are_camel_case() -> None:
    state = DocumentState(
        title="Deck",
        theme_id="clean",
        slides=[
            _slide(
                image=SlideImage(
                    asset_id=UUID("018f3b2a-7c4e-7000-8000-000000000001"),
                    alt="Cover",
                ),
            )
        ],
    )
    dumped = state.model_dump(by_alias=True)
    assert dumped["themeId"] == "clean"
    assert "theme_id" not in dumped
    image = dumped["slides"][0]["image"]
    assert "assetId" in image
    assert "asset_id" not in image


def test_slide_input_has_no_id_and_theme_round_trips() -> None:
    slide = SlideInput.model_validate({"layout": "hero", "title": "Hello"})
    assert "id" not in slide.model_dump()
    theme = Theme(
        id="clean",
        name="Clean",
        tokens=ThemeTokens(bg="#fff", paper="#fff", ink="#111", accent="#abc", tone="light"),
        tags=["default"],
    )
    assert theme.model_dump(by_alias=True)["tokens"]["tone"] == "light"


def test_ids() -> None:
    slide_id = new_slide_id()
    assert len(slide_id) == 10
    assert slide_id.isalnum()
    assert isinstance(new_uuid(), UUID)


def test_css_annotation_is_the_field_type() -> None:
    assert CssField is not None
