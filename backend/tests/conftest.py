"""Test bootstrap. Sets fake-model env before any docu import."""

from __future__ import annotations

import os

os.environ["AGENT_FAKE_MODEL"] = "1"
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-bytes-minimum!!")
