# Environment variable guide (DevOps)

Copy `.env.example` → `.env`, fill values, **never commit `.env`**.

Settings load from environment variables or a `.env` file via Pydantic
Settings (names are case-insensitive; use `UPPER_SNAKE` as below).

```bash
cp .env.example .env
# edit .env
```

With **Docker Compose**, `DATABASE_URL` and `REDIS_URL` match `infra/compose.yaml`.

---

## Minimum production set

| Variable | Example | Notes |
| --- | --- | --- |
| `SECRET_KEY` | `openssl rand -base64 48` | **Required.** At least 32 characters |
| `COOKIE_SECURE` | `true` | Must be `true` behind HTTPS |
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@db:5432/docu` | Async driver `asyncpg` required |
| `REDIS_URL` | `redis://redis:6379/0` | Broker default, cache, leases |
| `UPSTREAM` | `https://llm.example/v1` | Required unless `AGENT_FAKE_MODEL=1`. Must end with `/v1` |
| `UPSTREAM_API_KEY` | | If the model host requires auth |
| `MODEL` | `your-tool-model` | Required unless `AGENT_FAKE_MODEL=1` |
| `VISION_MODEL` | | Empty uses `MODEL` |
| `CONTEXT_WINDOW` | `32768` | Must match the model server |
| `MAX_COMPLETION_TOKENS` | `8192` | Upper bound on one completion |
| `ENABLE_THINKING` | `true` | |
| `UPSTREAM_TOP_EFFORT` | `xhigh` | Use `high` if the host rejects `xhigh` |
| `PROVIDER` | `openai` | `openai` for any OpenAI-compatible endpoint, or `anthropic` |
| `PUBLIC_BASE_URL` | `https://docu.example.com` | Absolute API origin |
| `FRONTEND_ORIGIN` | `https://docu.example.com` | Browser origin of the SPA |
| `FIRST_USER_IS_ADMIN` | `true` → then `false` | `true` only for bootstrap |

`AGENT_FAKE_MODEL=1` makes `UPSTREAM` and `MODEL` optional. Leave it `false` in production.

### Copy-paste production skeleton

```bash
SECRET_KEY=
COOKIE_SECURE=true
SESSION_TTL_DAYS=30
FIRST_USER_IS_ADMIN=true

PUBLIC_BASE_URL=https://docu.example.com
FRONTEND_ORIGIN=https://docu.example.com

DATABASE_URL=postgresql+asyncpg://docu:CHANGE_ME@db:5432/docu
REDIS_URL=redis://redis:6379/0
REDIS_PREFIX=docu:

UPSTREAM=https://llm.example/v1
UPSTREAM_API_KEY=
MODEL=
PROVIDER=openai
CONTEXT_WINDOW=32768
MAX_COMPLETION_TOKENS=8192
ENABLE_THINKING=true
UPSTREAM_TOP_EFFORT=high
AGENT_FAKE_MODEL=false

FILE_STORAGE=s3
S3_BUCKET=docu
S3_REGION=us-east-1
DATA_REGION=local
RETENTION_DAYS=30

MAIL_BACKEND=ses
MAIL_FROM=noreply@docu.example.com

STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
CREDIT_MARGIN=1.3
```

Plan prices (`plan_price_cents`, `plan_monthly_credits`) and `DATA_REGION` / `RETENTION_DAYS` are placeholders. See `BLOCKED.md`.

## Categories

### LLM

`UPSTREAM`, `UPSTREAM_API_KEY`, `MODEL`, `VISION_MODEL`, `CONTEXT_WINDOW`, `MAX_COMPLETION_TOKENS`, `ENABLE_THINKING`, `UPSTREAM_TOP_EFFORT`, `PROVIDER`, `SMALL_MODEL`, `FALLBACK_PROVIDER`, `FALLBACK_MODEL`, `FALLBACK_API_KEY`, `MODELS_FREE_ONLY`, `VISION_TIMEOUT`, `MAX_IMAGE_BYTES`, `REQUEST_TIMEOUT`, `STREAM_IDLE_TIMEOUT`, `CONNECT_TIMEOUT`, `MODEL_LISTING_TIMEOUT`.

### Auth

`SECRET_KEY`, `SESSION_TTL_DAYS` (default 30), `COOKIE_SECURE` (default true), `FIRST_USER_IS_ADMIN` (default false), `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `PUBLIC_BASE_URL`, `FRONTEND_ORIGIN`.

### Data

`DATABASE_URL`, `DATABASE_ECHO`, `REDIS_URL`, `REDIS_PREFIX`, `CACHE_SEARCH_TTL`, `CACHE_FETCH_TTL`, `CELERY_BROKER_URL` (defaults to `REDIS_URL`).

### Storage and mail

`FILE_STORAGE` (`local` or `s3`), `UPLOAD_DIR`, `S3_BUCKET`, `S3_ENDPOINT_URL`, `S3_REGION`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `MAX_UPLOAD_BYTES` (default 26214400), `MAX_FILE_CHARS`, `MAIL_BACKEND` (`smtp` or `ses`), `SMTP_HOST`, `SMTP_PORT`, `MAIL_FROM`.

### Billing and product

`STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `CREDIT_MARGIN` (default 1.3), `DATA_REGION` (default `local`), `RETENTION_DAYS` (default 30).

### Agent, skills, memory, prompts, web, MCP

`MAX_STEPS`, `SETUP_ALLOWANCE`, `AUTO_CONTINUE_STEPS`, `EMPTY_REPLY_RETRIES`, `UPSTREAM_RETRIES`, `REPEAT_LIMIT`, `BUDGET_FLOOR`, `BUDGET_MARGIN`, `ESTIMATE_SAFETY`, `CLIP_KEEP`, `CLIP_CHARS`, `CONTEXT_SUMMARIZE_RATIO`, `CONTEXT_KEEP_RECENT`, `CONTEXT_SUMMARIZE_AFTER_MESSAGES`, `APPROVAL_TIMEOUT`, `MAX_SKILL_CHARS`, `SKILL_DIRS`, `SKILL_ALLOWLIST`, `MAX_USER_SKILLS`, `MAX_USER_SKILL_BODY_CHARS`, `MAX_MEMORY_ITEMS`, `MAX_MEMORY_CHARS`, `PROMPT_DIR`, `SYSTEM_PROMPT`, `SEARCH_RESULTS`, `FETCH_TIMEOUT`, `MAX_PAGE_CHARS`, `MCP_ENABLED`, `MCP_CONFIG_PATH`, `MCP_REQUIRE_APPROVAL`, `MAX_MCP_SERVERS_PER_USER`, `MCP_CONNECT_TIMEOUT_SEC`, `MCP_MAX_INSTRUCTIONS_CHARS`, `MCP_MAX_UPLOAD_BYTES`, `MCP_OAUTH_CLIENT_ID`, `MCP_OAUTH_CLIENT_SECRET`.

### Observability

`SENTRY_DSN`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`.

### Tests

`AGENT_FAKE_MODEL=1` scripts every model call. Tests set this before importing `docu`.
