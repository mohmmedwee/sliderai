#!/bin/sh
set -eu
cd /app
if [ -f alembic.ini ]; then
  uv run alembic upgrade head
fi
if [ -f src/docu/scripts/setup_langgraph.py ]; then
  uv run python -m docu.scripts.setup_langgraph
fi
exec uv run uvicorn docu.api.app:create_app --factory --host 0.0.0.0 --port 8000 --proxy-headers
