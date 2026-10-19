"""Theme catalog: unique ids, the Theme model, and WCAG contrast."""

from __future__ import annotations

import json
from pathlib import Path

from docu.domain.document import Theme

THEMES_PATH = Path(__file__).resolve().parents[2] / "src" / "docu" / "data" / "themes.json"


def _channel(value: float) -> float:
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def contrast(left: str, right: str) -> float:
    def luminance(color: str) -> float:
        red = int(color[1:3], 16) / 255
        green = int(color[3:5], 16) / 255
        blue = int(color[5:7], 16) / 255
        return 0.2126 * _channel(red) + 0.7152 * _channel(green) + 0.0722 * _channel(blue)

    lighter, darker = sorted((luminance(left), luminance(right)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def test_themes_validate_and_pass_contrast() -> None:
    raw = json.loads(THEMES_PATH.read_text())
    themes = [Theme.model_validate(item) for item in raw]
    assert len(themes) == 26
    assert len({theme.id for theme in themes}) == 26
    assert sum(theme.id.startswith("tf-") for theme in themes) == 10
    for theme in themes:
        tokens = theme.tokens
        assert contrast(tokens.ink, tokens.paper) >= 4.5
        assert contrast(tokens.paper, tokens.accent) >= 3.0
