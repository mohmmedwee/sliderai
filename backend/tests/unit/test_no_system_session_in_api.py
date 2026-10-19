"""The API must not bypass row-level security."""

from __future__ import annotations

from pathlib import Path


def test_api_does_not_import_system_session() -> None:
    root = Path(__file__).resolve().parents[2] / "src" / "docu" / "api"
    offenders = [
        str(path.relative_to(root))
        for path in root.rglob("*.py")
        if "system_session" in path.read_text()
    ]
    assert offenders == []
