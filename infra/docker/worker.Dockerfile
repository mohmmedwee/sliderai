# syntax=docker/dockerfile:1

FROM python:3.12-slim
RUN useradd --create-home --uid 10001 app \
    && apt-get update \
    && apt-get install -y --no-install-recommends fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.11.14 /uv /usr/local/bin/uv
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev \
    && uv run playwright install --with-deps chromium
COPY backend/src src
COPY backend/prompts prompts
COPY backend/skills skills
COPY frontend/apps/web/src/assets/fonts /usr/share/fonts/docu
RUN fc-cache -f || true
USER app
ENV QUEUES=turns,files,exports,default
CMD ["sh", "-c", "uv run celery -A docu.worker.celery_app worker -Q ${QUEUES:-turns,files,exports,default}"]
