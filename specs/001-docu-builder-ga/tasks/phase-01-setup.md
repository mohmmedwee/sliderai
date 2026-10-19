# Phase 1: Setup (task cards)

Before any card, read [IMPLEMENTER.md](../IMPLEMENTER.md). It defines the abbreviations `BE`, `BT`, `FE`, `FP`, `MA`, `MAS`, and `MAF`.

**Exit check for the phase**: `docker compose -f infra/compose.yaml up -d`, then `cd backend && uv run pytest -q`, then `cd frontend && pnpm build`. All pass. CI is green on an empty PR.

---

<a id="t001"></a>
### T001 · Create the repository layout

**Depends on**: none · **Parallel**: no (everything else needs it) · **Size**: S

**Read first**: `plan.md` › Project Structure

**Files**: create
- `backend/pyproject.toml`
- `backend/src/docu/__init__.py`
- the empty packages `backend/src/docu/{core,domain,db,db/models,db/repositories,storage,auth,services,billing,mcp,agent,agent/nodes,agent/tools,agent/loaders,api,api/routers,worker,worker/tasks,scripts}/__init__.py`
- `backend/prompts/.gitkeep`, `backend/skills/.gitkeep`, `backend/tests/{unit,integration,contract,fixtures}/.gitkeep`
- `frontend/package.json`, `frontend/pnpm-workspace.yaml`
- `evals/.gitkeep`, `infra/.gitkeep`, `.gitignore`, `README.md`

**Steps**:

1. Run `git init` at the repo root if there is no repo yet. Then create the folders listed above.
2. `backend/pyproject.toml`: project name `docu`, `requires-python = ">=3.12"`, build backend `hatchling` with `packages = ["src/docu"]`. Add these runtime dependencies, each with a `>=` floor at today's latest minor version (look each one up with `uv add <pkg>` and keep what uv resolves):
   - fastapi, uvicorn[standard], pydantic, pydantic-settings, sqlalchemy[asyncio], asyncpg, alembic, pgvector
   - redis, celery[redis], sse-starlette, httpx, structlog
   - langchain, langchain-core, langgraph, langgraph-checkpoint-postgres, langchain-openai, langchain-anthropic, langchain-mcp-adapters, langchain-community, langchain-text-splitters, langsmith
   - argon2-cffi, itsdangerous, cryptography, authlib, pyotp
   - markitdown[docx,pptx,xlsx], pymupdf, python-pptx, defusedxml, lxml, pillow
   - ddgs, boto3, stripe, jinja2, uuid6, python-multipart, email-validator, clamd
   - opentelemetry-sdk, opentelemetry-instrumentation-fastapi, opentelemetry-instrumentation-sqlalchemy, opentelemetry-instrumentation-celery, opentelemetry-instrumentation-redis, opentelemetry-instrumentation-httpx, opentelemetry-exporter-otlp
   - sentry-sdk[fastapi,celery]
   - playwright
3. Add the dev dependency group: pytest, pytest-asyncio, hypothesis, testcontainers[postgres,redis], respx, schemathesis, mypy, ruff, pre-commit, types-redis.
4. Run `cd backend && uv lock && uv sync`, and commit `uv.lock`.
5. `frontend/pnpm-workspace.yaml` lists `apps/*` and `packages/*`. `frontend/package.json` is private with scripts `dev`, `build`, `lint`, `typecheck`, `test`, `test:e2e`, and `gen:api`, each forwarding to `apps/web` with `pnpm --filter web <script>`.
6. `.gitignore`: `.env`, `.venv/`, `node_modules/`, `dist/`, `web/dist/`, `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `uploads/`, `var/`, `playwright-report/`, `test-results/`.
7. `README.md`: one paragraph, plus links to `specs/001-docu-builder-ga/` and `IMPLEMENTER.md`.

**Acceptance**:
- [x] `cd backend && uv sync && uv run python -c "import docu, langgraph, langchain_openai"` exits 0
- [x] The tree matches plan.md, apart from folders later tasks will fill
- [x] `uv.lock` is committed, and `.env` is ignored

**Verify**: `cd backend && uv run python -c "import docu; print('ok')"`

---

<a id="t002"></a>
### T002 · Backend tooling (ruff, mypy, pytest, pre-commit)

**Depends on**: T001 · **Parallel**: yes · **Size**: S

**Read first**: `MA/pyproject.toml` (the `[tool.ruff]` and `[tool.pytest.ini_options]` sections)

**Files**: modify `backend/pyproject.toml`. Create `.pre-commit-config.yaml` and `backend/tests/conftest.py`.

**Steps**:

1. Copy MA's `[tool.ruff]` (`line-length = 100`) and `[tool.ruff.lint] select = ["E","F","I","UP","B","SIM"]`. Set `src = ["src", "tests"]`.
2. Add `[tool.mypy]`: `strict = true`, `plugins = ["pydantic.mypy"]`, `python_version = "3.12"`, `mypy_path = "src"`. Add an override `ignore_missing_imports = true` for `celery.*`, `clamd.*`, `pptx.*`, `fitz.*`, `ddgs.*`, `markitdown.*`.
3. Add `[tool.pytest.ini_options]`:
   - `testpaths = ["tests"]`, `asyncio_mode = "auto"`, `pythonpath = ["src"]`, `addopts = "-m 'not slow'"`
   - markers:
     - `db`: needs Postgres (testcontainers)
     - `redis`: needs Redis (testcontainers)
     - `slow`: long running
     - `e2e_llm`: needs a real model (`UPSTREAM` set)
4. `backend/tests/conftest.py`: set `os.environ["AGENT_FAKE_MODEL"] = "1"` and `os.environ.setdefault("SECRET_KEY", "test-secret-key-32-bytes-minimum!!")` **before** any `docu` import. Later tasks add the fixtures (IMPLEMENTER §5.7).
5. `.pre-commit-config.yaml`: ruff (lint and format) and the standard hooks trailing-whitespace, end-of-file-fixer, check-yaml, and check-added-large-files (`--maxkb=500`).

**Acceptance**:
- [x] `uv run ruff check . && uv run ruff format --check . && uv run mypy src` passes on the empty package
- [x] `uv run pytest` runs and reports "no tests ran" without errors

**Verify**: `cd backend && uv run ruff check . && uv run mypy src && uv run pytest -q`

---

<a id="t003"></a>
### T003 · Port settings (with MA env names)

**Depends on**: T001 · **Parallel**: yes · **Size**: M

**Read first**:
- `MAS/config/settings.py`, `MAS/config/hoist.py`, `MAS/config/cache.py`, and every `MAS/config/*.py` face file
- `MA/.env.example`, `MA/ENV.md`

**Files**: create `BE/core/config/__init__.py`, `BE/core/config/settings.py`, `BE/core/config/hoist.py`, `BE/core/config/cache.py`, plus one face file per group (below), `backend/.env.example`, `backend/ENV.md`, and `BT/unit/test_settings.py`.

**Steps**:

1. Port `hoist.py` and `cache.py` unchanged (`get_settings`, `clear_settings`, `override_settings`, `settings_override`).
2. Port the face files for the groups **kept**, with the same class and field names:

| Group | Faces |
|---|---|
| kept as-is | `llm` (LlmSettings), `agent` (AgentSettings), `skills`, `memory`, `prompts`, `files`, `web` |
| kept, Work fields removed | `mcp` (drop `work_servers` and anything Cleverso) |
| replaced | MA `auth` (rewrite per step 4), `database`, `redis` |

3. **Drop** the MA settings for Work, Cleverso, run_python, and docx editing (`tools.py` entries for `run_python`, `edit_docx`).
4. Add new groups, each a face file with a `*_FLAT` map (the MA pattern):
   - `auth`: `SECRET_KEY` (min 32 characters), `SESSION_TTL_DAYS=30`, `COOKIE_SECURE=true`, `FIRST_USER_IS_ADMIN=false`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `PUBLIC_BASE_URL`
   - `storage`: `FILE_STORAGE=local|s3`, `UPLOAD_DIR`, `S3_BUCKET`, `S3_ENDPOINT_URL`, `S3_REGION`, `MAX_UPLOAD_BYTES=26214400`
   - `mail`: `MAIL_BACKEND=smtp|ses`, `SMTP_HOST=localhost`, `SMTP_PORT=1025`, `MAIL_FROM`
   - `billing`: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `CREDIT_MARGIN=1.3`
   - `celery`: `CELERY_BROKER_URL` (defaults to `REDIS_URL`)
   - `observability`: `SENTRY_DSN`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`
   - `fake`: `AGENT_FAKE_MODEL=false`
5. `llm` must have these fields, with the same env names as MA:

| Env | Default |
|---|---|
| `UPSTREAM` | (required unless `AGENT_FAKE_MODEL`) |
| `UPSTREAM_API_KEY` | `""` |
| `MODEL` | (required unless `AGENT_FAKE_MODEL`) |
| `VISION_MODEL` | `""` |
| `CONTEXT_WINDOW` | `32768` |
| `MAX_COMPLETION_TOKENS` | `8192` |
| `ENABLE_THINKING` | `true` |
| `UPSTREAM_TOP_EFFORT` | `xhigh` |

   Add `SMALL_MODEL` (empty means use `MODEL`), `FALLBACK_PROVIDER`, `FALLBACK_MODEL`, `FALLBACK_API_KEY`, and `PROVIDER` (`openai` default, or `anthropic`). Use `PROVIDER=openai` for any OpenAI-compatible endpoint.
6. Write `backend/.env.example` listing **every** variable with a comment. Write `backend/ENV.md` in MA's `ENV.md` format: required vars, categories, a production skeleton.
7. Tests (`BT/unit/test_settings.py`):
   - env `UPSTREAM=http://x/v1` sets `get_settings().llm.upstream`
   - a missing `SECRET_KEY` raises at load time
   - `override_settings` works
   - `AGENT_FAKE_MODEL=1` makes `UPSTREAM` optional

**Drop**: every Work/Cleverso/run_python field.

**Acceptance**:
- [ ] `from docu.core.config import get_settings; get_settings().llm.context_window` works
- [ ] MA field names are kept (`settings.llm.*`, `settings.agent.*`, `settings.skills.max_chars`, `settings.prompts.dir`)
- [ ] `.env.example` contains every field, with no real secrets
- [ ] Tests pass

**Verify**: `cd backend && uv run pytest tests/unit/test_settings.py -q`

---

<a id="t004"></a>
### T004 · Port the prompts loader

**Depends on**: T003 · **Parallel**: yes · **Size**: S

**Read first**: `MAS/prompts.py`, `MA/prompts/README.md`, `MA/tests/test_prompts.py`

**Files**: create `BE/core/prompts.py` and `BT/unit/test_prompts.py`

**Steps**:

1. Port `load_prompt(name, *, prompt_dir=None, **vars)`, `_SafeMap` (missing `{var}` stays literal), the per-process cache, and `clear_prompt_cache()`. The default `prompt_dir` is `settings.prompts.dir`, which defaults to `backend/prompts`.
2. **Don't port** `system_prompt()`. Profiles replace it.
3. Add the hook `set_prompt_override_resolver(fn: Callable[[str], str | None])`. When it is set, `load_prompt` first asks `fn(name)` for a DB override. The real resolver comes in T218, so default to `None`.
4. Port `MA/tests/test_prompts.py` and adapt the imports.

**Acceptance**:
- [ ] `load_prompt("date_context", today="Monday")` substitutes the value (using a test fixture prompt dir)
- [ ] Missing variables stay as `{name}` and don't raise
- [ ] The override resolver wins over the file when set
- [ ] Tests pass

**Verify**: `uv run pytest tests/unit/test_prompts.py -q`

---

<a id="t005"></a>
### T005 · Port BlobStore

**Depends on**: T003 · **Parallel**: yes · **Size**: S

**Read first**: `MAS/storage/blob_store.py`, `MA/tests/test_blob_missing.py`

**Files**: create `BE/storage/blob_store.py` and `BT/unit/test_blob_store.py`

**Steps**:

1. Port `BlobMissingError`, `BlobStore` (Protocol), `LocalBlobStore`, `S3BlobStore`, and `build_blob_store(settings, upload_dir)` unchanged, apart from imports and settings paths (`settings.storage.*`).
2. Add `presigned_put(key, content_type, max_bytes, expires=900) -> dict` and `presigned_get(key, filename, expires=86400) -> str` to the Protocol.
   - **S3**: `generate_presigned_post` with a `content-length-range` condition, and `generate_presigned_url`.
   - **Local**: return a URL to `/v1/_local-upload/{key}?sig=…`, signed with `itsdangerous`. T008 adds that dev-only route.
3. Port the MA test, and add a local-store round-trip test.

**Acceptance**:
- [ ] Put, get, and delete round-trip on `LocalBlobStore` in tests
- [ ] `BlobMissingError` is raised for a missing key
- [ ] The S3 class is constructed with `moto`-free tests, by mocking `boto3.client`

**Verify**: `uv run pytest tests/unit/test_blob_store.py -q`

---

<a id="t006"></a>
### T006 · Local infrastructure (Docker Compose)

**Depends on**: T001 · **Parallel**: yes · **Size**: S

**Files**: create `infra/compose.yaml`

**Steps**:

1. Define these services:

| Service | Image | Notes |
|---|---|---|
| `db` | `pgvector/pgvector:pg16` | env `POSTGRES_USER=docu`, `POSTGRES_PASSWORD=docu`, `POSTGRES_DB=docu`; port 5432; volume `pgdata`; healthcheck `pg_isready` |
| `redis` | `redis:7-alpine` | port 6379; healthcheck `redis-cli ping` |
| `minio` | `minio/minio` | `server /data --console-address :9001`; ports 9000 and 9001; creds `minio` / `minio12345` |
| `minio-init` | `minio/mc` | creates the bucket `docu` and exits |
| `mailpit` | `axllent/mailpit` | ports 1025 (SMTP) and 8025 (UI) |
| `clamav` | `clamav/clamav:stable` | port 3310; healthcheck `clamdcheck.sh` |

2. Add a header comment with the `.env` values that match: `DATABASE_URL=postgresql+asyncpg://docu:docu@localhost:5432/docu`, `REDIS_URL=redis://localhost:6379/0`, and the S3 endpoint `http://localhost:9000`.

**Acceptance**:
- [ ] `docker compose -f infra/compose.yaml up -d` brings every service to healthy within 2 min (ClamAV may take longer on first run while it downloads signatures; this is noted in the comment)
- [ ] `psql postgresql://docu:docu@localhost:5432/docu -c "create extension if not exists vector"` succeeds

**Verify**: `docker compose -f infra/compose.yaml ps`

---

<a id="t007"></a>
### T007 · Port the frontend base from MA

**Depends on**: T001 · **Parallel**: yes · **Size**: M

**Read first**: `MA/frontend/package.json`, `MAF/main.tsx`, `MAF/App.tsx`, `MAF/i18n/index.ts`, `MAF/components/{AppShell,NavRail,LanguageToggle,ConfirmDialog}.tsx`, `MAF/hooks/{useTheme,useLocalSetting}.ts`, `MA/frontend/vite.config.ts`

**Files**: create `frontend/apps/web/` (package.json, vite.config.ts, tsconfig*.json, index.html, `src/main.tsx`, `src/App.tsx`, `src/router.tsx`, `src/i18n/{index.ts,en.json,ar.json}`, `src/components/…` as ported, `src/hooks/…` as ported), plus `frontend/packages/slides/package.json` and `frontend/packages/api-types/package.json` (stubs).

**Steps**:

1. Copy MA's `frontend/package.json` dependency versions for react, react-dom, react-router-dom, @tanstack/react-query, i18next, react-i18next, tailwindcss, @tailwindcss/vite, vite, and typescript. Add `zustand`, `lucide-react`, `openapi-fetch`, and (dev) `openapi-typescript`, `@playwright/test`, `vitest`, `@testing-library/react`, `@axe-core/playwright`, `eslint`, `typescript-eslint`, `eslint-plugin-react-hooks`.
2. Copy `vite.config.ts`. Set the dev proxy so `/v1` and `/s` go to `http://localhost:8000`, keeping `ws: false`.
3. Copy `i18n/index.ts`. Start `en.json` and `ar.json` with MA's **generic** keys only (`common.*`, `auth.*`, `nav.*`). Remove Cleverso and Work keys. Language detection: the stored setting, then `navigator.language`, then `en`. On change, set `<html lang dir>`.
4. Copy `AppShell`, `NavRail`, `LanguageToggle`, `ConfirmDialog`, `useTheme`, and `useLocalSetting`. **Remove** links to Work, Files, and Cleverso. T047 restyles them, so keep the code compiling now.
5. `router.tsx`: React Router 7 data router with lazy routes, holding placeholder pages that only render `<h1>{t('nav.x')}</h1>` for `/`, `/documents`, `/conversations`, `/templates`, `/memory`, `/skills`, `/connectors`, `/settings/*`, `/admin/*`, `/trash`, `/doc/:id`, `/s/:token`, `/login`, `/register`, and `*` (404).
6. `packages/slides` and `packages/api-types` are empty packages with `"main": "src/index.ts"`, exporting nothing yet.

**Drop**: Work pages, `agentSpace.ts`, `mcpCatalog` Cleverso entries, and `cleverso` assets (these return in later tasks only if a card asks).

**Acceptance**:
- [ ] `cd frontend && pnpm install && pnpm --filter web build` succeeds
- [ ] `pnpm dev` serves `/`, and switching the language flips `dir` on `<html>`
- [ ] No "Cleverso" string remains anywhere under `frontend/` (`grep -ri cleverso frontend/apps` is empty)

**Verify**: `cd frontend && pnpm build && ! grep -ri cleverso apps/web/src`

---

<a id="t008"></a>
### T008 · FastAPI app factory

**Depends on**: T003, T005 · **Parallel**: yes · **Size**: S

**Read first**: `MAS/main.py` (the lifespan and SPA mount), `MAS/api/routes/health.py`

**Files**: create `BE/api/app.py`, `BE/api/routers/health.py`, `BE/api/resources.py`, and `BT/integration/test_health.py`

**Steps**:

1. `create_app() -> FastAPI` with a lifespan that creates the SQLAlchemy async engine (`settings.database.url`, `pool_pre_ping=True`), a Redis pool, and the BlobStore, stores them on `app.state`, and disposes of them on shutdown.
2. `BE/api/resources.py`: `get_engine()`, `get_redis()`, `get_blob_store()` FastAPI dependencies that read `app.state`.
3. `GET /v1/health` → `{ok, revision, model}`, where `revision` comes from the env `GIT_SHA` or `"dev"`. `GET /v1/ready` checks the DB (`select 1`) and Redis (`ping`), returning 200 or 503.
4. **Single-host mode**: if `web/dist/index.html` exists, mount it at `/` with an SPA fallback (port MA's mount logic), after every `/v1` and `/s` route.
5. Add the dev-only `PUT /v1/_local-upload/{key}` that validates the signed URL from T005. Register it only when `FILE_STORAGE=local`.

**Acceptance**:
- [ ] `uv run uvicorn docu.api.app:create_app --factory` starts, and `curl localhost:8000/v1/health` returns `{"ok":true,...}`
- [ ] `/v1/ready` returns 503 when Redis is stopped
- [ ] The test with an httpx `AsyncClient` passes

**Verify**: `uv run pytest tests/integration/test_health.py -q -m "db or redis"`

---

<a id="t009"></a>
### T009 · Celery app

**Depends on**: T003 · **Parallel**: yes · **Size**: S

**Files**: create `BE/worker/celery_app.py`, `BE/worker/resources.py`, and `BT/unit/test_celery_config.py`

**Steps**:

1. `app = Celery("docu", broker=settings.celery.broker_url)`:
   - `task_acks_late=True`, `worker_prefetch_multiplier=1`, `task_reject_on_worker_lost=True`
   - `task_default_queue="default"`
   - `task_routes`: `docu.turn*` → `turns`, `docu.parse|scan|embed|import*` → `files`, `docu.export*|thumbnail` → `exports`
2. `app.conf.beat_schedule = {}`. Later tasks add entries in their own modules with `app.conf.beat_schedule.update(...)`, imported via `include=[...]`.
3. `BE/worker/resources.py`: `@asynccontextmanager async def task_resources()` yields `Res(engine, session_factory, redis, blob, settings)` and disposes of the engine on exit. Each Celery task creates its own resources (no globals shared across `asyncio.run`).
4. Test: the routing map sends `docu.turn` to `turns`.

**Acceptance**:
- [ ] `uv run celery -A docu.worker.celery_app inspect ping` gets a reply from a running worker
- [ ] The routing test passes

**Verify**: `uv run pytest tests/unit/test_celery_config.py -q`

---

<a id="t010"></a>
### T010 · Port `check_endpoint`

**Depends on**: T003 · **Parallel**: yes · **Size**: S

**Read first**: `MA/scripts/check_endpoint.py`

**Files**: create `BE/scripts/check_endpoint.py`

**Steps**:

1. Port the three checks: a plain reply, a non-streamed `tool_calls` reply, and a streamed `tool_calls` reply. **Replace** MA's `UpstreamClient` with `init_chat_model(f"{settings.llm.provider}:{settings.llm.model}", base_url=settings.llm.upstream, api_key=settings.llm.api_key)`. Use a one-tool schema `get_time(timezone: str)`.
2. Expose `async def run_checks(settings) -> dict[str, bool | str]` (T219 reuses it for the admin "Check connection" button). The CLI prints ✓/✗ per check and exits 1 on any failure.

**Acceptance**:
- [ ] `uv run python -m docu.scripts.check_endpoint` against a working upstream prints three ✓ and exits 0
- [ ] With a wrong key it prints ✗ with a short reason and exits 1

**Verify**: run it manually (it needs a real upstream, so it is not in CI)

---

<a id="t011"></a>
### T011 · Frontend test setup (Vitest and Playwright)

**Depends on**: T007 · **Parallel**: yes · **Size**: S

**Files**: create `frontend/apps/web/vitest.config.ts`, `frontend/apps/web/playwright.config.ts`, `frontend/apps/web/tests/e2e/smoke.spec.ts`, and `frontend/apps/web/tests/e2e/fixtures.ts`

**Steps**:

1. Vitest: `environment: 'jsdom'`, setup file that registers `@testing-library/jest-dom`.
2. Playwright projects:

| Project | Viewport | Locale | Extra |
|---|---|---|---|
| `en-desktop` | 1440×900 | `en-US` | |
| `ar-desktop` | 1440×900 | `ar-SA` | `storageState` sets the language to `ar` |
| `en-mobile` | iPhone 14 device | `en-US` | |
| `ar-mobile` | iPhone 14 device | `ar-SA` | language `ar` |

   `webServer` starts `pnpm dev`, and `baseURL` is `http://localhost:5173`.
3. `fixtures.ts` exports a `test` with a `login(page, {email, password})` helper (implemented in T049; stub it now) and a `locale` fixture.
4. `smoke.spec.ts`: open `/`, and expect `html[dir]` to be `rtl` for the `ar-*` projects and `ltr` otherwise.

**Acceptance**:
- [ ] `pnpm test` runs (0 tests is OK)
- [ ] `pnpm test:e2e` passes `smoke.spec.ts` in all 4 projects

**Verify**: `cd frontend && pnpm test:e2e`

---

<a id="t012"></a>
### T012 · CI workflow

**Depends on**: T002, T011 · **Parallel**: yes · **Size**: S

**Files**: create `.github/workflows/ci.yml`

**Steps**:

1. Trigger on `pull_request` and on `push` to `main`.
2. Job `backend` (ubuntu-latest):
   - `astral-sh/setup-uv`
   - `uv sync --frozen`
   - `ruff check`, `ruff format --check`
   - `mypy src`
   - `pytest -m "not slow and not e2e_llm"` (testcontainers needs Docker, which ubuntu runners have)
3. Job `frontend`:
   - `pnpm/action-setup` and Node 22
   - `pnpm install --frozen-lockfile`
   - `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build`
4. Job `api-types` (needs backend):
   - start the API with `AGENT_FAKE_MODEL=1` and service containers for Postgres and Redis
   - `pnpm gen:api`
   - `git diff --exit-code frontend/packages/api-types` (Principle III)
   - This job is a no-op until T017 exists. Guard it with `if: hashFiles('frontend/packages/api-types/src/schema.d.ts') != ''`.
5. Job `e2e` (needs frontend and backend): API, worker, and web against service containers, with `AGENT_FAKE_MODEL=1`. Run `pnpm test:e2e --project=en-desktop --project=ar-desktop`. Upload `playwright-report` on failure.
6. Add a check that fails on `__TODO_AR__` in `ar.json`, only on release branches (`if: startsWith(github.ref, 'refs/heads/release/')`).

**Acceptance**:
- [ ] A PR with the current skeleton shows all jobs green (e2e runs the smoke test)

**Verify**: open a draft PR and watch the checks

---

<a id="t013"></a>
### T013 · Docker images

**Depends on**: T008, T009 · **Parallel**: yes · **Size**: S

**Read first**: `MA/Dockerfile`, `MA/docker-compose.yml`, `MA/scripts/docker-entrypoint.sh`

**Files**: create `infra/docker/api.Dockerfile`, `infra/docker/worker.Dockerfile`, `infra/docker/entrypoint.sh`, and `infra/compose.prod.yaml`

**Steps**:

1. `api.Dockerfile`, ported from MA's two stages:
   - **Stage 1** (`node:22`): `pnpm install --frozen-lockfile && pnpm build`, producing `frontend/apps/web/dist`.
   - **Stage 2** (`python:3.12-slim`): `uv sync --frozen --no-dev`. Copy `backend/src`, `backend/prompts`, `backend/skills`, and `backend/alembic*`, and copy the SPA into `/app/web/dist`. Run as the non-root user `app`.
2. `worker.Dockerfile`: the same Python stage, plus `uv run playwright install --with-deps chromium`, plus the fonts (`fonts-noto-core`, plus the bundled `FE/assets/fonts` copied to `/usr/share/fonts/docu`, then `fc-cache -f`). Its entrypoint is `celery -A docu.worker.celery_app worker -Q ${QUEUES:-turns,files,exports,default}`. The `beat` service uses the same image with the command `celery … beat`.
3. `entrypoint.sh` (api): `alembic upgrade head`, then `python -m docu.scripts.setup_langgraph`, then `exec uvicorn docu.api.app:create_app --factory --host 0.0.0.0 --port 8000 --proxy-headers`.
4. `compose.prod.yaml`: `api`, `worker`, `beat`, `db`, `redis`, `clamav`, with `env_file: .env`. This is the single-host deploy (research.md R16).
5. Healthcheck: `curl -f http://127.0.0.1:8000/v1/health`.

**Acceptance**:
- [ ] `docker compose -f infra/compose.prod.yaml up --build` serves the SPA at `:8000` and `/v1/health` is ok
- [ ] The worker container can run `python -c "from playwright.sync_api import sync_playwright"`

**Verify**: `docker compose -f infra/compose.prod.yaml up --build -d && curl -f localhost:8000/v1/health`
