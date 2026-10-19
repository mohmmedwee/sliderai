# syntax=docker/dockerfile:1

FROM node:22-bookworm AS web
WORKDIR /src/frontend
COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./
COPY frontend/apps/web/package.json apps/web/package.json
COPY frontend/packages packages
RUN corepack enable && pnpm install --frozen-lockfile
COPY frontend/apps/web apps/web
RUN pnpm --filter web build

FROM python:3.12-slim AS api
RUN useradd --create-home --uid 10001 app
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.11.14 /uv /usr/local/bin/uv
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev
COPY backend/src src
COPY backend/prompts prompts
COPY backend/skills skills
COPY --from=web /src/frontend/apps/web/dist /app/web/dist
COPY infra/docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && chown -R app:app /app
USER app
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/v1/health')"
ENTRYPOINT ["/entrypoint.sh"]
