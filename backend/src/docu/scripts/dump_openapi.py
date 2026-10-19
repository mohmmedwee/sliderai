"""Print the OpenAPI document. This does not open the database."""

from __future__ import annotations

import json
import os

os.environ.setdefault("AGENT_FAKE_MODEL", "1")
os.environ.setdefault("SECRET_KEY", "openapi-dump-secret-key-32-bytes!!")

from docu.api.app import create_app  # noqa: E402


def main() -> None:
    print(json.dumps(create_app().openapi(), indent=1, sort_keys=True))


if __name__ == "__main__":
    main()


__all__ = ["main"]
