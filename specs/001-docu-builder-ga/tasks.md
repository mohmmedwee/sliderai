# Tasks: Docu Builder GA

**Input**: Design documents from `/specs/001-docu-builder-ga/`
**Prerequisites**: plan.md, spec.md, **ux.md** (every UI task), research.md (Part A covers what is carried over from agent_console), data-model.md, contracts/, quickstart.md
**How to work a task**: this file is only the index. **The implementation details for every task are in its card in the [tasks/](./tasks/) folder**, one file per phase (`tasks/phase-NN-*.md`). Click a task ID to open its card. Read [IMPLEMENTER.md](./IMPLEMENTER.md) once, then for each task follow its card: Depends on, Read first, Files, Steps, Acceptance, and Verify. Don't implement from the one-line summary here.
**Stack**: A Python 3.12 backend (FastAPI, LangChain + LangGraph, SQLAlchemy, Celery) and a React 19 / TypeScript frontend, built on agent_console (`~/Documents/myproject/my_agent`, shortened to `MA`)

**Tests**: Required by the constitution (Principle V) for reducers, loop guards, interrupt/resume, the permissions matrix, the credit ledger, Stripe webhooks, and the turn lifecycle. Write those tests first and confirm they fail. Every story has Playwright e2e tests in both `ar` and `en`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on unfinished tasks)
- **[Story]**: The user story the task belongs to (US1–US14)
- `BE` = `backend/src/docu`, `BT` = `backend/tests`, `FE` = `frontend/apps/web/src`, `FP` = `frontend/packages`, `MA` = agent_console repo
- **Port** means copy from `MA`, rename the package to `docu`, adapt it to workspaces, and keep its tests passing. Never copy the `MA/skills/{docx,pptx,xlsx,pdf}` folders (proprietary license).

---

## Phase 1: Setup (Shared Infrastructure)

**Implementation cards for this phase**: [tasks/phase-01-setup.md](./tasks/phase-01-setup.md)

**Purpose**: Repository layout, plus the scaffolding ported from agent_console

- [x] [T001](tasks/phase-01-setup.md#t001) Create the repo layout from plan.md: `backend/` (uv project `docu`, `src/` layout, `prompts/`, `skills/`), `frontend/` (pnpm workspace: `apps/web`, `packages/{slides,api-types}`), `evals/`, and `infra/`
- [x] [T002](tasks/phase-01-setup.md#t002) [P] Set up backend tooling: ruff (MA rule set), mypy strict, pytest with MA's markers (`db`, `slow`, `e2e_*`), pre-commit, in `backend/pyproject.toml`
- [x] [T003](tasks/phase-01-setup.md#t003) [P] Port settings with MA's env names (`UPSTREAM`, `UPSTREAM_API_KEY`, `MODEL`, `VISION_MODEL`, `CONTEXT_WINDOW`, `MAX_COMPLETION_TOKENS`, `ENABLE_THINKING`, `SECRET_KEY`, `FIRST_USER_IS_ADMIN`, …) and its nested settings and hoist pattern from `MA/src/agent_console/config/`, into `BE/core/config.py`. Also port `ENV.md` and `.env.example`.
- [x] [T004](tasks/phase-01-setup.md#t004) [P] Port the prompts loader (`load_prompt` with variables, cached per process) from `MA/src/agent_console/prompts.py` to `BE/core/prompts.py`
- [x] [T005](tasks/phase-01-setup.md#t005) [P] Port `BlobStore` (Protocol, Local, S3) from `MA/src/agent_console/storage/blob_store.py` to `BE/storage/blob_store.py`, with its tests
- [ ] [T006](tasks/phase-01-setup.md#t006) [P] Create the local stack (Postgres 16 + pgvector, Redis 7, MinIO, Mailpit, ClamAV) in `infra/compose.yaml`
- [x] [T007](tasks/phase-01-setup.md#t007) [P] Port the frontend base from `MA/frontend` into `frontend/apps/web`:
  - Vite, Tailwind 4, react-router 7, TanStack Query, i18next with `en.json` and `ar.json`
  - AppShell, NavRail, LanguageToggle, ConfirmDialog, `useTheme`, `useLocalSetting`
  - a dev proxy from `/v1` and `/s` to `:8000`
- [x] [T008](tasks/phase-01-setup.md#t008) [P] Scaffold the FastAPI app factory: health, readiness, lifespan, and serving `web/dist` in single-host mode (as in `MA/src/agent_console/main.py`), in `BE/api/app.py`
- [x] [T009](tasks/phase-01-setup.md#t009) [P] Scaffold Celery with queues `turns`, `files`, `exports`, and `default`, routing, and beat, in `BE/worker/celery_app.py`
- [ ] [T010](tasks/phase-01-setup.md#t010) [P] Port `scripts/check_endpoint.py`, which checks a plain reply, `tool_calls`, and `tool_calls` while streaming, to `BE/scripts/check_endpoint.py`
- [x] [T011](tasks/phase-01-setup.md#t011) [P] Set up Playwright projects `en-desktop`, `ar-desktop`, `en-mobile`, `ar-mobile`, plus Vitest, in `frontend/apps/web/`
- [ ] [T012](tasks/phase-01-setup.md#t012) [P] Add the CI workflow with two jobs:
  - backend: ruff, mypy, unit tests, integration tests
  - frontend: lint, typecheck, Vitest, e2e, build, api-types drift check

  in `.github/workflows/ci.yml`
- [ ] [T013](tasks/phase-01-setup.md#t013) [P] Port MA's multi-stage Dockerfile (SPA baked into the API image) and add `worker` (with Playwright Chromium and fonts) and `beat` images, in `infra/docker/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Implementation cards for this phase**: [tasks/phase-02-foundational.md](./tasks/phase-02-foundational.md)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Domain models and shared types

- [x] [T014](tasks/phase-02-foundational.md#t014) Define the Pydantic `Slide` (7 layouts, `table`, `chart`, `notes`), `DocumentContent`, `Theme`, and the `CssField` validator, with camelCase aliases, in `BE/domain/document.py`
- [ ] [T015](tasks/phase-02-foundational.md#t015) [P] Define the error envelope, codes, and `TurnErrorCode` in `BE/domain/errors.py`
- [ ] [T016](tasks/phase-02-foundational.md#t016) [P] Define the event union in `BE/domain/events.py`: MA's events (`text_delta`, `reasoning_delta`, `tool_call_delta`, `tool_call`, `tool_approval`, `tool_result`, `status`, `error`, `done`, plus `ask_user`) and the new `doc_patch`, `memory_saved`, `skill_loaded`, `step_limit`, `waiting_input`, and `turn_*` events. Register them in the OpenAPI components.
- [ ] [T017](tasks/phase-02-foundational.md#t017) Add OpenAPI → TypeScript generation (`pnpm gen:api`) and an `openapi-fetch` client in `FP/api-types/` and `FE/lib/api.ts`

### Slide renderer

- [ ] [T018](tasks/phase-02-foundational.md#t018) Build the slide renderer: 7 layouts, theme CSS variables, `dir="auto"` per text block, and a scale prop for thumbnails, in `FP/slides/src/{Slide.tsx,layouts/*.tsx,theme.ts}`
- [ ] [T019](tasks/phase-02-foundational.md#t019) [P] Add the SVG chart renderer (bar, line, pie, donut; RTL-aware axes; no runtime chart library) and the table renderer in `FP/slides/src/{charts,table}/`
- [ ] [T020](tasks/phase-02-foundational.md#t020) [P] Add 16 system themes, including MA `skills/theme-factory/themes` (Apache-2.0, with attribution in `NOTICE`), and a contrast test (≥ 4.5:1) in `FP/slides/src/themes.ts` and `FP/slides/tests/contrast.test.ts`
- [ ] [T021](tasks/phase-02-foundational.md#t021) [P] Bundle the fonts (IBM Plex Sans Arabic, Inter, Noto Naskh Arabic, Fraunces) in `FP/slides/src/fonts.css`

### Database

- [ ] [T022](tasks/phase-02-foundational.md#t022) Write SQLAlchemy models for `users` (self-hosted auth columns), `sessions`, `identities`, `auth_tokens`, `workspaces`, `memberships`, `documents`, `document_revisions`, `threads`, `messages`, `turns`, `pending_inputs`, `themes`, `templates`, `prompt_versions`, and `platform_settings`, in `BE/db/models/*.py`
- [ ] [T023](tasks/phase-02-foundational.md#t023) Write SQLAlchemy models for `credit_ledger` and `audit_log` in `BE/db/models/{ledger,audit}.py`
- [ ] [T024](tasks/phase-02-foundational.md#t024) Write the initial Alembic migration: extensions, tables, the append-only ledger trigger, and RLS policies on tenant tables, in `backend/alembic/versions/0001_initial.py`
- [ ] [T025](tasks/phase-02-foundational.md#t025) Add the `scoped_session(workspace_id)` dependency (`SET LOCAL app.workspace_id`). Repositories take `user_id` and `workspace_id` in every signature (MA rule). In `BE/db/session.py` and `BE/db/repositories/`.
- [ ] [T026](tasks/phase-02-foundational.md#t026) [P] Write the RLS isolation integration test in `BT/integration/test_rls.py`
- [ ] [T027](tasks/phase-02-foundational.md#t027) [P] Add a seed script for themes, 24 bilingual templates, and the built-in skills sync in `BE/scripts/seed.py`
- [ ] [T028](tasks/phase-02-foundational.md#t028) Add the LangGraph setup script (`AsyncPostgresSaver.setup()` and `AsyncPostgresStore.setup()`) in `BE/scripts/setup_langgraph.py`

### Auth (ported) and workspace scope

- [ ] [T029](tasks/phase-02-foundational.md#t029) [P] Port the password hasher (argon2id with rehash) from `MA/src/agent_console/services/security.py` to `BE/auth/passwords.py`, with its tests
- [ ] [T030](tasks/phase-02-foundational.md#t030) Implement DB-backed opaque sessions (hashed id, revocable, `last_seen_at`) and CSRF double-submit in `BE/auth/{sessions,csrf}.py`
- [ ] [T031](tasks/phase-02-foundational.md#t031) Port and extend the auth routes in `BE/api/routers/auth.py`:
  - register and login (rate limited), plus logout
  - the first user becomes platform admin when `FIRST_USER_IS_ADMIN` is set
  - email verification, forgot and reset password
  - the personal workspace is created on registration
- [ ] [T032](tasks/phase-02-foundational.md#t032) [P] Add the mail client: SMTP to Mailpit in dev and SES in production, with Jinja2 ar/en (RTL) layouts, in `BE/core/mail.py` and `BE/emails/`
- [ ] [T033](tasks/phase-02-foundational.md#t033) Add the `current_user` and `workspace_scope` dependencies (404 for non-members) and block creation for unverified emails (`403 email_unverified`), in `BE/api/deps.py`
- [ ] [T034](tasks/phase-02-foundational.md#t034) Implement `can(ctx, action, doc=None)` from the data-model.md matrix in `BE/services/permissions.py`
- [ ] [T035](tasks/phase-02-foundational.md#t035) [P] Add security headers, CSP, and the error envelope handlers in `BE/core/{security,errors}.py`
- [ ] [T036](tasks/phase-02-foundational.md#t036) [P] Add Redis token-bucket rate limiting in `BE/core/ratelimit.py`

### Credit ledger core (test-first)

- [ ] [T037](tasks/phase-02-foundational.md#t037) [P] Write unit and Hypothesis tests for credit math in `BT/unit/test_credits.py`
- [ ] [T038](tasks/phase-02-foundational.md#t038) [P] Write ledger integration tests (concurrency, idempotency, the trigger) in `BT/integration/test_ledger.py`
- [ ] [T039](tasks/phase-02-foundational.md#t039) Implement the ledger service with row locks in `BE/billing/ledger.py`
- [ ] [T040](tasks/phase-02-foundational.md#t040) Add the price table and `credits_for_usage()` in `BE/billing/prices.py`
- [ ] [T041](tasks/phase-02-foundational.md#t041) Grant Free credits on signup and monthly from beat (temporary until US9) in `BE/worker/tasks/credits.py`

### UI foundation (ux.md §2–§4)

- [ ] [T042](tasks/phase-02-foundational.md#t042) Implement the design tokens from ux.md §2 (light and dark, Tailwind 4 `@theme`, keeping MA token names), self-hosted fonts (IBM Plex Sans Arabic, Inter, IBM Plex Mono), Lucide icons, and a token contrast test, in `FE/styles/tokens.css`, `FE/assets/fonts/`, and `FE/styles/tokens.test.ts`
- [ ] [T043](tasks/phase-02-foundational.md#t043) [P] Build UI primitives set A (ux.md §4.1–§4.8, §4.17, §4.18, §4.30): Button, IconButton, Pill, PillTabs, TextInput, SearchInput, Select, Checkbox, Radio, ColorSwatch, Tooltip, Badge, Kbd, in `FE/components/ui/`
- [ ] [T044](tasks/phase-02-foundational.md#t044) [P] Build UI primitives set B (ux.md §4.9, §4.12–§4.16, §4.19–§4.22): Card, Dialog, Menu/Popover, Sheet, Toast (with provider), CreditPill, EmptyState, Skeleton, Banner, in `FE/components/ui/`
- [ ] [T045](tasks/phase-02-foundational.md#t045) Add the dev-only UI gallery route `/__ui` that renders every primitive in every state, in en/ar × light/dark, with a Playwright screenshot test, in `FE/pages/dev/UiGallery.tsx` and `frontend/apps/web/tests/e2e/ui-gallery.spec.ts`
- [ ] [T046](tasks/phase-02-foundational.md#t046) [P] Add placeholder illustrations and a placeholder logo (ux.md §9 sizes) in `FE/assets/illustrations/` and `FE/assets/brand/`

### Web shell

- [ ] [T047](tasks/phase-02-foundational.md#t047) Adapt the shell (ux.md §3.1): sidebar (workspace label, Create, Documents, Conversations, Templates, Memory, Skills, Connectors, Settings, Admin when platform admin, Trash), top bar with the credit counter, and RTL logical CSS, in `FE/components/{AppShell,NavRail,TopBar}.tsx`
- [ ] [T048](tasks/phase-02-foundational.md#t048) [P] Build the mobile shell (ux.md §3.2: bottom tab bar, More drawer, compact top bar) in `FE/components/{MobileTabBar,MoreDrawer}.tsx`
- [ ] [T049](tasks/phase-02-foundational.md#t049) [P] Port `useAuth` and the Login and Register pages, and add Verify, Forgot, and Reset, in `FE/hooks/useAuth.tsx` and `FE/pages/auth/`
- [ ] [T050](tasks/phase-02-foundational.md#t050) [P] Add `GET /v1/me` and `PATCH /v1/me` (language, digits), and persist the language switch, in `BE/api/routers/me.py` and `FE/lib/direction.ts`

### Observability

- [ ] [T051](tasks/phase-02-foundational.md#t051) [P] Set up structlog, OpenTelemetry (FastAPI, SQLAlchemy, Celery, Redis, httpx), and Sentry in `BE/core/{logging,otel}.py`
- [ ] [T052](tasks/phase-02-foundational.md#t052) [P] Add Sentry to the web app and an error boundary in `FE/lib/sentry.ts`

**Checkpoint**: Register (first user is admin), verify, log in, and see the shell in both languages. The DB, RLS, ledger, and auth tests pass.

---

## Phase 3: User Story 1 - Create a deck from one prompt (Priority: P1) 🎯 MVP

**Implementation cards for this phase**: [tasks/phase-03-us1.md](./tasks/phase-03-us1.md)

**Goal**: The agent_console loop, rebuilt on LangGraph, drafts a themed deck that streams into the editor. It includes clarifying questions, approvals, thinking blocks, and loop guards.

**Independent Test**: quickstart.md › US1 and "Agent behavior" steps 1, 2, and 5

### Tests for User Story 1 (write first, confirm they fail) ⚠️

- [ ] [T053](tasks/phase-03-us1.md#t053) [P] [US1] Write unit and Hypothesis tests for the 7 document reducers (every error code, the 60-slide cap, unique ids, table and chart shape rules) in `BT/unit/test_reducers.py`
- [ ] [T054](tasks/phase-03-us1.md#t054) [P] [US1] Port MA's budget, clipping, runaway, and repeats tests to the new modules, testing at the module seam (not private helpers), in `BT/unit/test_{budget,guards}.py`
- [ ] [T055](tasks/phase-03-us1.md#t055) [P] [US1] Write graph tests with `GenericFakeChatModel` in `BT/unit/test_graph.py`. They cover:
  - the tool loop
  - step cap → `step_limit` → wrap_up
  - auto-continue happens once
  - broken JSON → hint returned to the model
  - the third identical failing call is refused
  - an empty reply is retried at lower effort
  - context overflow → clip and retry
  - text only → document unchanged
- [ ] [T056](tasks/phase-03-us1.md#t056) [P] [US1] Write interrupt integration tests in `BT/integration/test_interrupts.py`:
  - `ask_user` pauses and the resume continues
  - an approval deny returns "Denied by user."
  - `allow_thread` is remembered for the thread
  - a worker restart between the pause and the resume still works (SC-011)
  - after 30 min the turn becomes `cancelled(expired)` and the credits are refunded
- [ ] [T057](tasks/phase-03-us1.md#t057) [P] [US1] Write turn lifecycle integration tests in `BT/integration/test_turn_lifecycle.py`:
  - a commit happens in one transaction
  - failure and cancel discard the draft and refund
  - `doc_busy`
  - `worker_lost` from the reaper
- [ ] [T058](tasks/phase-03-us1.md#t058) [P] [US1] Write the SSE relay integration test (`Last-Event-ID` resume, 15 s ping, 410 after the stream expires, resume continues the same stream) in `BT/integration/test_sse.py`
- [ ] [T059](tasks/phase-03-us1.md#t059) [P] [US1] Write the e2e test "create from prompt", including a clarifying question, in both languages with the fake model, in `frontend/apps/web/tests/e2e/create.spec.ts`

### Implementation for User Story 1

- [ ] [T060](tasks/phase-03-us1.md#t060) [P] [US1] Define the tool argument models from contracts/agent-tools.md in `BE/domain/tools.py`
- [ ] [T061](tasks/phase-03-us1.md#t061) [US1] Implement the pure document reducers in `BE/agent/reducers.py`
- [ ] [T062](tasks/phase-03-us1.md#t062) [P] [US1] Build the model registry: `init_chat_model` for any OpenAI-compatible `UPSTREAM` or Anthropic, mapping effort to `reasoning_effort`, `extra_body.enable_thinking`, `.with_retry()`, `.with_fallbacks()`, a small model, and `GenericFakeChatModel` when `AGENT_FAKE_MODEL=1`, in `BE/agent/models.py`
- [ ] [T063](tasks/phase-03-us1.md#t063) [P] [US1] Define `AgentProfile` and the `deck`, `document`, `webpage`, `social`, and `assistant` profiles (research.md R20). The model follows MA `agent_profiles.py`. In `BE/agent/profiles.py`.
- [ ] [T064](tasks/phase-03-us1.md#t064) [P] [US1] Write prompts v0: `deck.md`, `document.md`, `webpage.md`, `social.md`, `assistant.md`. Port `date_context.md`, `context_compact.md`, `auto_title.md`, `skills_index.md`, and `session_web_search_{on,off}.md` from `MA/prompts`. Put them in `backend/prompts/`, with DB overrides resolved by `BE/core/prompts.py` (active `prompt_versions`).
- [ ] [T065](tasks/phase-03-us1.md#t065) [US1] Port the budget logic (token estimates, `fit_prompt_to_context`, `clip_old_tool_payloads`, `trim_tools_for_context`, completion and step budgets) from `MA/.../agent/budget.py` to `BE/agent/budget.py`
- [ ] [T066](tasks/phase-03-us1.md#t066) [US1] Port compaction (rolling summary into `state.summary`, emitting `status`) from `MA/.../context_compact.py` to `BE/agent/compact.py`
- [ ] [T067](tasks/phase-03-us1.md#t067) [US1] Port the guards (runaway cutoff, repeated failing call fingerprints, empty-reply recovery, auto-continue nudge, schema-only and prose-ask nudges) from `MA/.../runaway.py`, `agent/repeats.py`, and `agent/replies.py` to `BE/agent/guards.py`
- [ ] [T068](tasks/phase-03-us1.md#t068) [P] [US1] Build the context message (format, locale, template, attachments, the document with slide ids, limits) in `BE/agent/context.py`
- [ ] [T069](tasks/phase-03-us1.md#t069) [US1] Implement the document tools as `@tool(args_schema=…)`, emitting `doc_patch` through `get_stream_writer()`, in `BE/agent/tools/document.py`
- [ ] [T070](tasks/phase-03-us1.md#t070) [US1] Implement `ask_user` with `interrupt()`, MA's option and field limits, and its rejection of action-menu options, in `BE/agent/tools/ask_user.py`
- [ ] [T071](tasks/phase-03-us1.md#t071) [US1] Implement the approval policy (`always`, `ask`, `never`; defaults from R22) and approval cards (`replace_slides` before/after, `delete_slides`, `generate_image`, `mcp_write`) in `BE/agent/approvals.py`
- [ ] [T072](tasks/phase-03-us1.md#t072) [US1] Implement the graph nodes `prepare`, `model`, `guards`, `tools`, `wrap_up`, `commit`, and `title`, with the custom ToolNode error handling (MA `ToolRegistry` messages and `broken_json_hint`), in `BE/agent/nodes/*.py`
- [ ] [T073](tasks/phase-03-us1.md#t073) [US1] Build the graph: `build_graph(profile)` compiled with the checkpointer and Store, `TurnState`, the `TurnContext` context schema, and a per-profile cache, in `BE/agent/{state,graph}.py`
- [ ] [T074](tasks/phase-03-us1.md#t074) [US1] Write the emitter that maps `astream(stream_mode=["messages","updates","custom"])` to contract events, including `reasoning_delta`, `tool_call_delta` with `argumentsChars`, and `__interrupt__`, and writes them to Redis with XADD, in `BE/agent/emit.py`
- [ ] [T075](tasks/phase-03-us1.md#t075) [US1] Implement the Celery `turn` task: lease, heartbeat, cancel polling, run the graph, handle an interrupt (`pending_inputs` row, `waiting_input`, keep the lease), commit, and settle. In `BE/worker/tasks/turn.py`.
- [ ] [T076](tasks/phase-03-us1.md#t076) [US1] Implement the Celery `resume` task (`Command(resume=answer)` on the same stream) in `BE/worker/tasks/resume.py`
- [ ] [T077](tasks/phase-03-us1.md#t077) [US1] Add the beat task `turn_reaper` (no heartbeat for 90 s → `worker_lost`, refund, release) and `interrupt_expiry` (expired after 30 min → cancelled, refund) in `BE/worker/tasks/{turn_reaper,interrupt_expiry}.py`
- [ ] [T078](tasks/phase-03-us1.md#t078) [US1] Implement the turn service (permission, reserve, lease, `turns` row with profile, effort, and `prompt_version_id`, enqueue) in `BE/services/turns.py`
- [ ] [T079](tasks/phase-03-us1.md#t079) [US1] Add the routes `POST /v1/threads`, `POST /v1/threads/{id}/turns`, `GET /v1/turns/{id}`, `POST /v1/turns/{id}/cancel`, `POST /v1/turns/{id}/resume`, `GET /v1/threads/{id}/active-turn`, and `GET /v1/models` in `BE/api/routers/{threads,turns,models}.py`
- [ ] [T080](tasks/phase-03-us1.md#t080) [US1] Implement the SSE relay (`sse-starlette`, XREAD BLOCK, `Last-Event-ID`, 15 s ping comments as in MA `iter_job_sse_frames`, 410) in `BE/api/sse.py`
- [ ] [T081](tasks/phase-03-us1.md#t081) [P] [US1] Build the Create screen (illustration, heading, format chips) using the ported MA `Composer`, `ComposerPlusMenu`, and `ModelEffortPicker` (efforts from `/v1/models`), in `FE/pages/Create.tsx` and `FE/components/chat/`
- [ ] [T082](tasks/phase-03-us1.md#t082) [US1] Port `sse.ts` and `chatRunner.ts` (fetch SSE, reconnect with `Last-Event-ID`, re-attach through `active-turn`) to `FE/lib/`
- [ ] [T083](tasks/phase-03-us1.md#t083) [US1] Add the turn and document store (Zustand: `committed`/`draft`, applying `DocOp`, rollback on failure or cancel) in `FE/features/agent/turnStore.ts`
- [ ] [T084](tasks/phase-03-us1.md#t084) [US1] Build the editor layout: top bar, canvas with the next slide peeking, numbered filmstrip, and agent column, in `FE/pages/Editor.tsx` and `FE/features/editor/{Canvas,Filmstrip}.tsx`
- [ ] [T085](tasks/phase-03-us1.md#t085) [US1] Build the thread view on the ported MA `Blocks` (collapsible thinking, tool blocks that collapse when done, `tool_call_delta` progress), `ChoicePrompt`/`ChoiceForm` (`ask_user`), and `ApprovalDiffCard` adapted to slide before/after cards, plus slide previews inside messages, in `FE/features/agent/`
- [ ] [T086](tasks/phase-03-us1.md#t086) [US1] Add turn error messages for each `TurnErrorCode` in ar/en, with Retry, in `FE/features/agent/TurnError.tsx` and `FE/i18n/`
- [ ] [T087](tasks/phase-03-us1.md#t087) [P] [US1] Port `notify.ts` to send a browser notification when a background turn finishes, in `FE/lib/notify.ts`
- [ ] [T088](tasks/phase-03-us1.md#t088) [P] [US1] Create eval dataset v1 in `evals/` with:
  - 40 ar/en draft cases across 4 formats
  - 10 vague prompts that should trigger `ask_user`
  - scorers for tool validity, language, limits, and asking when appropriate
  - a LangSmith runner
- [ ] [T089](tasks/phase-03-us1.md#t089) [P] [US1] Add the evals workflow (it blocks the merge on a drop of more than 3 points) in `.github/workflows/evals.yml`

**Checkpoint**: The MVP. Internal alpha can start on any OpenAI-compatible model.

---

## Phase 4: User Story 2 - Refine by conversation and by hand (Priority: P1)

**Implementation cards for this phase**: [tasks/phase-04-us2.md](./tasks/phase-04-us2.md)

**Goal**: Local edits, inline editing, undo, rewind, version history, approval before overwriting manual edits, Conversations, Documents, and Present

**Independent Test**: quickstart.md › US2 and "Agent behavior" steps 3 and 4

### Tests for User Story 2 ⚠️

- [ ] [T090](tasks/phase-04-us2.md#t090) [P] [US2] Write integration tests for document PATCH (`base_version`, `version_conflict`, `doc_busy`) in `BT/integration/test_documents.py`
- [ ] [T091](tasks/phase-04-us2.md#t091) [P] [US2] Write integration tests for undo, restore, and **rewind** (messages truncated, document restored to the turn's `base_version`, new turn started) in `BT/integration/test_revisions.py`
- [ ] [T092](tasks/phase-04-us2.md#t092) [P] [US2] Write a test that `replace_slides` after manual edits triggers the `ask` policy with a correct `manualEditsLost` count, in `BT/integration/test_approval_policy.py`
- [ ] [T093](tasks/phase-04-us2.md#t093) [P] [US2] Create the edit-locality eval (40 ar/en cases) in `evals/datasets/edits.jsonl` and `evals/scorers/locality.py`
- [ ] [T094](tasks/phase-04-us2.md#t094) [P] [US2] Write e2e tests for refine, undo, rewind, inline edit, conflict, approval card, conversations, and present in `frontend/apps/web/tests/e2e/refine.spec.ts`

### Implementation for User Story 2

- [ ] [T095](tasks/phase-04-us2.md#t095) [US2] Add the document routes (list with `q`, `format`, and cursor; create a blank document; duplicate; get; PATCH with ops; soft delete; restore) and the service in `BE/api/routers/documents.py` and `BE/services/documents.py`
- [ ] [T096](tasks/phase-04-us2.md#t096) [US2] Add the revisions service and routes, including a debounced manual-revision writer that tracks "manual edits since the last agent turn", in `BE/services/revisions.py`
- [ ] [T097](tasks/phase-04-us2.md#t097) [US2] Add `POST /v1/turns/{id}/undo` and `POST /v1/threads/{id}/rewind` (ported from MA's `/conversations/{id}/rewind` and extended with the document revision restore) in `BE/api/routers/{turns,threads}.py`
- [ ] [T098](tasks/phase-04-us2.md#t098) [US2] Write prompt v1 for targeted edits and check it against the locality eval, in `backend/prompts/deck.md` (as a new version)
- [ ] [T099](tasks/phase-04-us2.md#t099) [US2] Add inline editing on the canvas (select, edit, Esc, hint, save with `baseVersion`) in `FE/features/editor/{Selection,InlineText}.tsx`
- [ ] [T100](tasks/phase-04-us2.md#t100) [US2] Add banners for agent editing (with Stop), waiting for your answer, and conflict (with reload) in `FE/features/editor/Banners.tsx`
- [ ] [T101](tasks/phase-04-us2.md#t101) [P] [US2] Let users reorder slides by dragging in the filmstrip (`move_slide` op) in `FE/features/editor/Filmstrip.tsx`
- [ ] [T102](tasks/phase-04-us2.md#t102) [P] [US2] Add the filmstrip context menu (duplicate, delete with confirm, move up/down) and the `+ slide` layout picker (ux.md §5.4.2) in `FE/features/editor/{FilmstripMenu,LayoutPicker}.tsx`
- [ ] [T103](tasks/phase-04-us2.md#t103) [P] [US2] Add message actions: edit and re-send (rewind), "Undo this turn", and thumbs up/down sent to LangSmith feedback, in `FE/features/agent/MessageActions.tsx` and `BE/api/routers/messages.py`
- [ ] [T104](tasks/phase-04-us2.md#t104) [P] [US2] Add the version history drawer in `FE/features/editor/VersionHistory.tsx`
- [ ] [T105](tasks/phase-04-us2.md#t105) [P] [US2] Build Conversations by porting MA `ConversationList`, `useConversations`, and `groupConversations` (Active and Archived tabs, the balloon empty state as original artwork), in `FE/pages/Conversations.tsx`
- [ ] [T106](tasks/phase-04-us2.md#t106) [P] [US2] Add the thread list, update, and messages routes in `BE/api/routers/threads.py`
- [ ] [T107](tasks/phase-04-us2.md#t107) [P] [US2] Build the Documents screen (recent and all, thumbnails, search, format filter) and the New blank button in `FE/pages/Documents.tsx`
- [ ] [T108](tasks/phase-04-us2.md#t108) [P] [US2] Add Present mode in `FE/features/editor/Present.tsx`
- [ ] [T109](tasks/phase-04-us2.md#t109) [P] [US2] Add the Trash screen in `FE/pages/Trash.tsx`
- [ ] [T110](tasks/phase-04-us2.md#t110) [US2] Add the narrow-viewport layout (slide counter, agent as a sheet) in `FE/features/editor/Responsive.tsx`

**Checkpoint**: The locality eval is at least 95%. Rewind and undo restore the document exactly.

---

## Phase 5: User Story 3 - Templates and themes (Priority: P2)

**Implementation cards for this phase**: [tasks/phase-05-us3.md](./tasks/phase-05-us3.md)

- [ ] [T111](tasks/phase-05-us3.md#t111) [P] [US3] Write integration tests for template facets and filters in `BT/integration/test_templates.py`
- [ ] [T112](tasks/phase-05-us3.md#t112) [P] [US3] Create the template-following eval (20 cases) in `evals/datasets/templates.jsonl`
- [ ] [T113](tasks/phase-05-us3.md#t113) [US3] Add the template and theme routes (facets, save as a workspace template, delete) in `BE/api/routers/{templates,themes}.py`
- [ ] [T114](tasks/phase-05-us3.md#t114) [US3] Pass the attached template into the context message in `BE/agent/context.py`
- [ ] [T115](tasks/phase-05-us3.md#t115) [P] [US3] Build the template library (search, format, category, and color filters, grid, empty state) in `FE/pages/Templates.tsx` and `FE/features/library/`
- [ ] [T116](tasks/phase-05-us3.md#t116) [P] [US3] Add the template preview dialog (slide carousel, name, category, `Use template`) from ux.md §5.6 in `FE/features/library/TemplatePreview.tsx`
- [ ] [T117](tasks/phase-05-us3.md#t117) [P] [US3] Add the template card in the composer (removable) and the choose flow in `FE/components/chat/TemplateCard.tsx`
- [ ] [T118](tasks/phase-05-us3.md#t118) [P] [US3] Add suggested templates on Create in `FE/features/library/Suggested.tsx`
- [ ] [T119](tasks/phase-05-us3.md#t119) [P] [US3] Add "Save as template" for admins and a workspace templates section in `FE/features/library/SaveAsTemplate.tsx`
- [ ] [T120](tasks/phase-05-us3.md#t120) [US3] Add the Patterns overlay (instant, revision with `source='theme'`, no credits) in `FE/features/editor/Patterns.tsx`
- [ ] [T121](tasks/phase-05-us3.md#t121) [P] [US3] Write the e2e test for templates and themes in `frontend/apps/web/tests/e2e/templates.spec.ts`

---

## Phase 6: User Story 4 - Accounts, workspaces, and roles (Priority: P2)

**Implementation cards for this phase**: [tasks/phase-06-us4.md](./tasks/phase-06-us4.md)

### Tests ⚠️

- [ ] [T122](tasks/phase-06-us4.md#t122) [P] [US4] Write the permissions matrix integration test (every role × every route, cross-workspace 404, platform admin never sees workspace content) in `BT/integration/test_permissions_matrix.py`
- [ ] [T123](tasks/phase-06-us4.md#t123) [P] [US4] Write integration tests for invitations in `BT/integration/test_invitations.py`
- [ ] [T124](tasks/phase-06-us4.md#t124) [P] [US4] Write auth integration tests (Google link and create, TOTP enable and login, session revoke, reset revokes all sessions) in `BT/integration/test_auth.py`
- [ ] [T125](tasks/phase-06-us4.md#t125) [P] [US4] Write e2e tests for team invite → viewer is read-only in `frontend/apps/web/tests/e2e/workspaces.spec.ts`

### Implementation

- [ ] [T126](tasks/phase-06-us4.md#t126) [US4] Add Google sign-in (Authlib OIDC with PKCE, `identities` linking) in `BE/auth/google.py` and `BE/api/routers/auth.py`
- [ ] [T127](tasks/phase-06-us4.md#t127) [US4] Add TOTP (`pyotp`, sealed secret, recovery codes) and the session list and revoke routes in `BE/auth/totp.py`
- [ ] [T128](tasks/phase-06-us4.md#t128) [US4] Add the `invitations` and `document_access` models and migration in `BE/db/models/{invitations,access}.py`
- [ ] [T129](tasks/phase-06-us4.md#t129) [US4] Add the workspace and member routes in `BE/api/routers/workspaces.py`
- [ ] [T130](tasks/phase-06-us4.md#t130) [US4] Add the invitation service, routes, and ar/en email templates in `BE/services/invitations.py`
- [ ] [T131](tasks/phase-06-us4.md#t131) [US4] Write audit log entries for member, invite, role, and auth events in `BE/services/audit.py`
- [ ] [T132](tasks/phase-06-us4.md#t132) [P] [US4] Add the workspace switcher and plan badge in `FE/components/WorkspaceSwitcher.tsx`
- [ ] [T133](tasks/phase-06-us4.md#t133) [P] [US4] Build Settings › Members in `FE/pages/settings/Members.tsx`
- [ ] [T134](tasks/phase-06-us4.md#t134) [P] [US4] Port MA `SettingsPage` and `ProfileMenu` and extend them: profile, language, digits, security (password, 2FA, sessions), in `FE/pages/settings/`
- [ ] [T135](tasks/phase-06-us4.md#t135) [P] [US4] Add the invitation accept page in `FE/pages/InviteAccept.tsx`
- [ ] [T136](tasks/phase-06-us4.md#t136) [US4] Add `POST /v1/me/export` and the data export task in `BE/worker/tasks/account.py`
- [ ] [T137](tasks/phase-06-us4.md#t137) [US4] Add account deletion (re-authentication, soft delete, revoke sessions, audit, 30-day purge) in `BE/api/routers/me.py`
- [ ] [T138](tasks/phase-06-us4.md#t138) [P] [US4] Build Settings › Data in `FE/pages/settings/Data.tsx`
- [ ] [T139](tasks/phase-06-us4.md#t139) [US4] Hide or disable UI by role (from the `permissions` field) in `FE/lib/permissions.ts`

---

## Phase 7: User Story 5 - Share and present via link (Priority: P2)

**Implementation cards for this phase**: [tasks/phase-07-us5.md](./tasks/phase-07-us5.md)

- [ ] [T140](tasks/phase-07-us5.md#t140) [P] [US5] Write sharing integration tests in `BT/integration/test_sharing.py`
- [ ] [T141](tasks/phase-07-us5.md#t141) [US5] Add the `share_links` model and the sharing service in `BE/db/models/share.py` and `BE/services/sharing.py`
- [ ] [T142](tasks/phase-07-us5.md#t142) [US5] Add the sharing routes in `BE/api/routers/sharing.py`
- [ ] [T143](tasks/phase-07-us5.md#t143) [US5] Serve the `/s/{token}` OG shell and `GET /v1/public/{token}` in `BE/api/{share_page.py,routers/public.py}`
- [ ] [T144](tasks/phase-07-us5.md#t144) [US5] Add the thumbnail task (Playwright, debounced after commit) in `BE/worker/tasks/thumbnail.py`
- [ ] [T145](tasks/phase-07-us5.md#t145) [P] [US5] Build the Share dialog in `FE/features/sharing/ShareDialog.tsx`
- [ ] [T146](tasks/phase-07-us5.md#t146) [P] [US5] Build the share viewer entry (under 120 KB, Present, mobile, Free badge) in `FE/pages/Share.tsx`
- [ ] [T147](tasks/phase-07-us5.md#t147) [P] [US5] Write the e2e test for sharing in `frontend/apps/web/tests/e2e/share.spec.ts`

---

## Phase 8: User Story 6 - Attachments, import, and data slides (Priority: P3)

**Implementation cards for this phase**: [tasks/phase-08-us6.md](./tasks/phase-08-us6.md)

- [ ] [T148](tasks/phase-08-us6.md#t148) [P] [US6] Write unit tests for the Arabic-aware splitter in `BT/unit/test_splitter.py`
- [ ] [T149](tasks/phase-08-us6.md#t149) [P] [US6] Write integration tests for the attachment pipeline (states, EICAR test file, parse error, limits) in `BT/integration/test_attachments.py`
- [ ] [T150](tasks/phase-08-us6.md#t150) [P] [US6] Create the grounding, injection, and import eval (30 cases, including Arabic PDFs, a PPTX to import, and CSV → chart) in `evals/datasets/grounding.jsonl`
- [ ] [T151](tasks/phase-08-us6.md#t151) [P] [US6] Run the embedding benchmark (R9) in `evals/embeddings/benchmark.py`
- [ ] [T152](tasks/phase-08-us6.md#t152) [US6] Add the `attachments` and `attachment_chunks` models and migration in `BE/db/models/attachments.py`
- [ ] [T153](tasks/phase-08-us6.md#t153) [US6] Add the attachment routes (presign, complete, get, delete; type checked from the file's bytes; size limits as in MA `MAX_UPLOAD_BYTES` handling) in `BE/api/routers/attachments.py`
- [ ] [T154](tasks/phase-08-us6.md#t154) [US6] Add the scan task (clamd) in `BE/worker/tasks/scan.py`
- [ ] [T155](tasks/phase-08-us6.md#t155) [US6] Port the markitdown conversion from MA `services/tools/convert_upload.py` into LangChain loaders (DOCX, PPTX, XLSX through markitdown; PDF through PyMuPDF with page markers; CSV; TXT), in `BE/agent/loaders/`
- [ ] [T156](tasks/phase-08-us6.md#t156) [US6] Add the parse and embed tasks (splitter, `init_embeddings`, summary by the small model) in `BE/worker/tasks/{parse,embed}.py`
- [ ] [T157](tasks/phase-08-us6.md#t157) [US6] Implement `read_attachment` and `search_attachments` (hybrid search with reciprocal rank fusion, `<attachment_content>` wrapping) in `BE/agent/tools/attachments.py`
- [ ] [T158](tasks/phase-08-us6.md#t158) [US6] Add the `import` profile and prompt, an outline loader for PPTX and DOCX, and the `import` task (outline → `replace_slides`, keeping language and direction) in `BE/agent/profiles.py`, `backend/prompts/import.md`, and `BE/worker/tasks/import_doc.py`
- [ ] [T159](tasks/phase-08-us6.md#t159) [P] [US6] Add composer attachments by porting MA `ComposerPlusMenu` upload and `UploadErrorBanner`: chips with status, and the Import chip on Create, in `FE/components/chat/Attachments.tsx`
- [ ] [T160](tasks/phase-08-us6.md#t160) [P] [US6] Add input and output moderation in `BE/agent/moderation.py`
- [ ] [T161](tasks/phase-08-us6.md#t161) [US6] Add the retention task in `BE/worker/tasks/retention.py`

---

## Phase 9: User Story 7 - Export (Priority: P3)

**Implementation cards for this phase**: [tasks/phase-09-us7.md](./tasks/phase-09-us7.md)

- [ ] [T162](tasks/phase-09-us7.md#t162) [P] [US7] Add visual snapshot tests (7 layouts × 4 themes × ar/en) in `BT/integration/test_export_visual.py`
- [ ] [T163](tasks/phase-09-us7.md#t163) [P] [US7] Write PPTX tests (editable text, RTL, native tables, native charts) in `BT/unit/test_pptx.py`
- [ ] [T164](tasks/phase-09-us7.md#t164) [US7] Add the `exports` model and routes in `BE/db/models/exports.py` and `BE/api/routers/exports.py`
- [ ] [T165](tasks/phase-09-us7.md#t165) [US7] Add the internal export route (fixed size, print CSS, watermark, signed token) in `FE/pages/ExportRender.tsx`
- [ ] [T166](tasks/phase-09-us7.md#t166) [US7] Add the PDF and PNG task (Playwright) in `BE/worker/tasks/export_pdf.py`
- [ ] [T167](tasks/phase-09-us7.md#t167) [US7] Add the PPTX task (`python-pptx`: 7 layouts, native `add_table` and `add_chart`, images, RTL through lxml, speaker notes) in `BE/worker/tasks/export_pptx.py`
- [ ] [T168](tasks/phase-09-us7.md#t168) [P] [US7] Add the Export menu in `FE/features/export/ExportMenu.tsx`

---

## Phase 10: User Story 8 - Images on slides (Priority: P3)

**Implementation cards for this phase**: [tasks/phase-10-us8.md](./tasks/phase-10-us8.md)

- [ ] [T169](tasks/phase-10-us8.md#t169) [P] [US8] Write `generate_image` tests (approval card shows the cost, moderation, credits, provider error) in `BT/unit/test_image_tool.py`
- [ ] [T170](tasks/phase-10-us8.md#t170) [US8] Add the `assets` model and the image provider adapter in `BE/db/models/assets.py` and `BE/agent/images/provider.py`
- [ ] [T171](tasks/phase-10-us8.md#t171) [US8] Implement the `generate_image` tool (policy `ask`) in `BE/agent/tools/image.py`
- [ ] [T172](tasks/phase-10-us8.md#t172) [US8] Add image upload and the variants task in `BE/api/routers/assets.py` and `BE/worker/tasks/image.py`
- [ ] [T173](tasks/phase-10-us8.md#t173) [US8] Render `slide.image` with a focal point in `FP/slides/src/layouts/{Hero,Split}.tsx`
- [ ] [T174](tasks/phase-10-us8.md#t174) [P] [US8] Add the image picker in `FE/features/editor/ImageField.tsx`

---

## Phase 11: User Story 9 - Plans, credits, billing (Priority: P3)

**Implementation cards for this phase**: [tasks/phase-11-us9.md](./tasks/phase-11-us9.md)

- [ ] [T175](tasks/phase-11-us9.md#t175) [P] [US9] Write Stripe webhook tests in `BT/integration/test_stripe_webhooks.py`
- [ ] [T176](tasks/phase-11-us9.md#t176) [P] [US9] Write plan gating tests (watermark, images, attachments, workspace skills, effort caps) in `BT/integration/test_plans.py`
- [ ] [T177](tasks/phase-11-us9.md#t177) [US9] Add the `subscriptions` and `stripe_events` models in `BE/db/models/billing.py`
- [ ] [T178](tasks/phase-11-us9.md#t178) [US9] Add plan definitions (FR-034 prices, allowances, features, effort caps) in `BE/billing/plans.py`
- [ ] [T179](tasks/phase-11-us9.md#t179) [US9] Add the checkout, portal, billing, and ledger routes in `BE/api/routers/billing.py`
- [ ] [T180](tasks/phase-11-us9.md#t180) [US9] Add the Stripe webhook handler (idempotent, grants on `invoice.paid`, seats, audit) in `BE/billing/stripe_webhooks.py`
- [ ] [T181](tasks/phase-11-us9.md#t181) [US9] Sync seats in `BE/services/seats.py`
- [ ] [T182](tasks/phase-11-us9.md#t182) [US9] Replace the temporary Free grant (T041) with a plan-aware grant in `BE/worker/tasks/credits.py`
- [ ] [T183](tasks/phase-11-us9.md#t183) [US9] Add daily Stripe reconciliation in `BE/worker/tasks/reconcile.py`
- [ ] [T184](tasks/phase-11-us9.md#t184) [US9] Add usage alerts at 80% and 100% in `BE/worker/tasks/usage_alerts.py`
- [ ] [T185](tasks/phase-11-us9.md#t185) [P] [US9] Build Settings › Billing in `FE/pages/settings/Billing.tsx`
- [ ] [T186](tasks/phase-11-us9.md#t186) [P] [US9] Add the upgrade banner and out-of-credits state in `FE/features/billing/`
- [ ] [T187](tasks/phase-11-us9.md#t187) [P] [US9] Write the e2e test for billing in `frontend/apps/web/tests/e2e/billing.spec.ts`

---

## Phase 12: User Story 10 - Memory and brand (Priority: P2)

**Implementation cards for this phase**: [tasks/phase-12-us10.md](./tasks/phase-12-us10.md)

**Independent Test**: quickstart.md › US10

- [ ] [T188](tasks/phase-12-us10.md#t188) [P] [US10] Write memory tests in `BT/integration/test_memory.py`:
  - the 50 cap gives an error that leads to `ask_user`
  - namespaces are isolated (no access to another user's memories)
  - brand memory can only be edited by admins
  - the prompt block includes both kinds
- [ ] [T189](tasks/phase-12-us10.md#t189) [P] [US10] Create the memory eval (SC-012: edit turns with and without memory) in `evals/datasets/memory.jsonl`
- [ ] [T190](tasks/phase-12-us10.md#t190) [US10] Implement Store-backed memory (memories and brand namespaces, CRUD, prompt block) following MA `repositories/memory.py`, in `BE/agent/memory.py`
- [ ] [T191](tasks/phase-12-us10.md#t191) [US10] Implement the `remember` and `forget` tools (emitting `memory_saved`), and port MA `skills/memory/SKILL.md` guidance into the prompt, in `BE/agent/tools/memory.py`
- [ ] [T192](tasks/phase-12-us10.md#t192) [US10] Add the memory and brand-memory routes in `BE/api/routers/memory.py`
- [ ] [T193](tasks/phase-12-us10.md#t193) [P] [US10] Port MA `MemoryPage`, and add a Brand section for admins, in `FE/pages/Memory.tsx`
- [ ] [T194](tasks/phase-12-us10.md#t194) [P] [US10] Add the "Remembered" chip in the thread in `FE/features/agent/MemoryChip.tsx`
- [ ] [T195](tasks/phase-12-us10.md#t195) [P] [US10] Write the e2e test for memory in `frontend/apps/web/tests/e2e/memory.spec.ts`

---

## Phase 13: User Story 11 - Skills (Priority: P3)

**Implementation cards for this phase**: [tasks/phase-13-us11.md](./tasks/phase-13-us11.md)

**Independent Test**: quickstart.md › US11

- [ ] [T196](tasks/phase-13-us11.md#t196) [P] [US11] Write skills tests (index lines, profile and workspace filters, `/skill` forced load, size cap, user skill validation) in `BT/unit/test_skills.py`
- [ ] [T197](tasks/phase-13-us11.md#t197) [US11] Port the skill catalog (SKILL.md front matter, index line, read with cap) from MA `repositories/skill_catalog.py` and `skills.py`. Merge built-in files with workspace DB skills. In `BE/agent/skills.py`.
- [ ] [T198](tasks/phase-13-us11.md#t198) [US11] Implement the `read_skill` tool and the selected-skill injection (MA `inject_selected_skill`), emitting `skill_loaded`, in `BE/agent/tools/skills.py`
- [ ] [T199](tasks/phase-13-us11.md#t199) [P] [US11] Copy MA's in-house skills (`replying-bilingually`, `answering-well`, `planning-with-intention`, `writing-deliverables`, `doc-coauthoring`, `research`, `working-with-documents`) and the Apache-2.0 `theme-factory` and `brand-guidelines` (with NOTICE) into `backend/skills/`
- [ ] [T200](tasks/phase-13-us11.md#t200) [P] [US11] Write the new skills in ar and en: `deck-writing`, `report-writing`, `pitch-deck`, `lesson-deck`, `landing-page-writing`, `social-post-writing`, in `backend/skills/`
- [ ] [T201](tasks/phase-13-us11.md#t201) [US11] Add the `skills` model and routes (list, get, create, patch, delete, and generate using the ported `skill_generate_contract.md`) in `BE/api/routers/skills.py` and `BE/services/skill_generate.py`
- [ ] [T202](tasks/phase-13-us11.md#t202) [P] [US11] Port MA `SkillsPage` and add a workspace skill editor in `FE/pages/Skills.tsx`
- [ ] [T203](tasks/phase-13-us11.md#t203) [P] [US11] Add a `/` skill picker in the composer and a "Using skill" chip in `FE/components/chat/SkillPicker.tsx`
- [ ] [T204](tasks/phase-13-us11.md#t204) [P] [US11] Write the e2e test for skills in `frontend/apps/web/tests/e2e/skills.spec.ts`

---

## Phase 14: User Story 12 - Connectors (MCP) (Priority: P3)

**Implementation cards for this phase**: [tasks/phase-14-us12.md](./tasks/phase-14-us12.md)

**Independent Test**: quickstart.md › US12

- [ ] [T205](tasks/phase-14-us12.md#t205) [P] [US12] Write an MCP test fixture server (`get_report` read tool and `create_page` write tool) in `evals/fixtures/mcp_wiki/`
- [ ] [T206](tasks/phase-14-us12.md#t206) [P] [US12] Write connector tests in `BT/integration/test_connectors.py`:
  - OAuth start and callback, with secrets sealed at rest
  - progressive `list_mcp_tools` / `use_mcp_tools`
  - the loaded-tools cache in Redis survives across turns
  - write tools ask for approval
  - large results are shrunk
  - repeated failures are refused
- [ ] [T207](tasks/phase-14-us12.md#t207) [US12] Add the `connectors` model and migration in `BE/db/models/connectors.py`
- [ ] [T208](tasks/phase-14-us12.md#t208) [US12] Port MA `services/mcp/{oauth_flow,secrets,shrink,guards,groups,progressive,names}.py` into `BE/mcp/`, replacing in-process state with Postgres and Redis
- [ ] [T209](tasks/phase-14-us12.md#t209) [US12] Add the MCP client built on `langchain-mcp-adapters` (`MultiServerMCPClient`, streamable HTTP, per-workspace headers) with tool-group mapping, in `BE/mcp/client.py`
- [ ] [T210](tasks/phase-14-us12.md#t210) [US12] Implement `list_mcp_tools`, `use_mcp_tools`, and dynamic `mcp_<server>_<tool>` registration in `build_tools`, in `BE/agent/tools/mcp.py`
- [ ] [T211](tasks/phase-14-us12.md#t211) [US12] Add the connector routes (CRUD, OAuth, reconnect, status) in `BE/api/routers/connectors.py`
- [ ] [T212](tasks/phase-14-us12.md#t212) [P] [US12] Port MA `ConnectorsPage`, `McpServerDialog`, `McpConnectorDetails`, and `mcpOAuth.ts` to `FE/pages/Connectors.tsx`

---

## Phase 15: User Story 13 - Web research (Priority: P3)

**Implementation cards for this phase**: [tasks/phase-15-us13.md](./tasks/phase-15-us13.md)

**Independent Test**: quickstart.md › US13

- [ ] [T213](tasks/phase-15-us13.md#t213) [P] [US13] Write web tool tests (SSRF guard blocks private ranges, size cap, the toggle hides the tools, citations go into `notes`) in `BT/unit/test_web_tools.py`
- [ ] [T214](tasks/phase-15-us13.md#t214) [US13] Port MA `clients/search.py` (ddgs) behind a provider adapter (ddgs, Tavily, Brave) and implement `web_search` in `BE/agent/tools/web.py`
- [ ] [T215](tasks/phase-15-us13.md#t215) [US13] Port and harden `fetch_url` (HTTPS only, DNS-resolved IP check, 2 MB, readable text) in `BE/agent/tools/web.py`
- [ ] [T216](tasks/phase-15-us13.md#t216) [P] [US13] Add the web toggle to the composer, and port MA `WebSearchResults` and `FetchUrlResult` blocks, in `FE/components/chat/`

---

## Phase 16: User Story 14 - Platform administration (Priority: P2)

**Implementation cards for this phase**: [tasks/phase-16-us14.md](./tasks/phase-16-us14.md)

**Independent Test**: quickstart.md › US14

- [ ] [T217](tasks/phase-16-us14.md#t217) [P] [US14] Write admin tests in `BT/integration/test_admin.py`:
  - only platform admins can call the routes
  - the API key is write-only
  - activating a prompt version is recorded on the next turn
  - the usage aggregates are correct
- [ ] [T218](tasks/phase-16-us14.md#t218) [US14] Add the platform settings service (model settings with a 30 s cache, sealed API key, flags) and make the model registry read from it, in `BE/services/platform_settings.py`
- [ ] [T219](tasks/phase-16-us14.md#t219) [US14] Add the admin routes (users, model settings with the check probe, prompts and versions, profiles, flags, usage) in `BE/api/routers/admin.py`
- [ ] [T220](tasks/phase-16-us14.md#t220) [US14] Add the usage aggregation (daily rollup from `turns`) in `BE/services/usage.py` and `BE/worker/tasks/usage_rollup.py`
- [ ] [T221](tasks/phase-16-us14.md#t221) [P] [US14] Port MA `AdminPage` and extend it with tabs: Users, Model, Prompts (diff and versions), Profiles, Flags, Usage. In `FE/pages/admin/`.

---

## Phase 17: Polish, Hardening, and Launch

**Implementation cards for this phase**: [tasks/phase-17-polish.md](./tasks/phase-17-polish.md)

- [ ] [T222](tasks/phase-17-polish.md#t222) [P] Add ⌘K search (MA TODO "Keyboard-first") in `BE/api/routers/search.py` and `FE/components/CommandK.tsx`
- [ ] [T223](tasks/phase-17-polish.md#t223) [P] Add Schemathesis contract tests in `BT/contract/test_openapi.py`
- [ ] [T224](tasks/phase-17-polish.md#t224) [P] Add axe-core checks to every e2e spec in `frontend/apps/web/tests/e2e/a11y.ts`
- [ ] [T225](tasks/phase-17-polish.md#t225) [P] Do a manual screen reader pass and record it in `docs/a11y-audit.md`
- [ ] [T226](tasks/phase-17-polish.md#t226) [P] Add bundle budgets in `frontend/apps/web/vite.config.ts`
- [ ] [T227](tasks/phase-17-polish.md#t227) [P] Have a native reviewer audit the Arabic copy (UI, templates, skills, emails, prompts)
- [ ] [T228](tasks/phase-17-polish.md#t228) [P] Turn on LangSmith production sampling with personal data hidden and an annotation queue in `BE/agent/tracing.py`
- [ ] [T229](tasks/phase-17-polish.md#t229) [P] Build dashboards and alerts (SLOs, queue depth, waiting-input backlog, provider errors, cost) in `infra/observability/`
- [ ] [T230](tasks/phase-17-polish.md#t230) [P] Add product analytics events in `FE/lib/analytics.ts`
- [ ] [T231](tasks/phase-17-polish.md#t231) Run the model bake-off: the full eval suite on each candidate upstream (the self-hosted model, Anthropic, OpenAI-compatible options). Record the default in research.md R8.
- [ ] [T232](tasks/phase-17-polish.md#t232) Run a k6 load test (500 turns, 5,000 viewers, 200 paused turns resumed at once) in `infra/load/`
- [ ] [T233](tasks/phase-17-polish.md#t233) Have an outside party run a pen test (auth, SSRF in `fetch_url`, MCP, uploads, share links), and fix high and critical findings
- [ ] [T234](tasks/phase-17-polish.md#t234) [P] Add legal pages, including third-party NOTICE (Apache skills and themes), in `FE/pages/legal/`
- [ ] [T235](tasks/phase-17-polish.md#t235) [P] Add the status page and help menu in `FE/components/Help.tsx`
- [ ] [T236](tasks/phase-17-polish.md#t236) [P] Replace the placeholder logo and illustrations with the final original art (ux.md §9). Check sizes, dark variants, and that nothing resembles the reference product.
- [ ] [T237](tasks/phase-17-polish.md#t237) Write the single-host deploy guide (MA `DEPLOYMENT.md` style: Compose with api, worker, beat, db, redis) in `docs/DEPLOYMENT.md`
- [ ] [T238](tasks/phase-17-polish.md#t238) Write the Terraform for staging (ECS api, worker-turns, worker-files, worker-exports, beat, clamav; RDS; ElastiCache; S3 + CloudFront + WAF; SES; Secrets Manager) in `infra/terraform/`
- [ ] [T239](tasks/phase-17-polish.md#t239) Bring up production in the FR-037 region (point-in-time recovery, cross-region snapshots, S3 versioning) in `infra/terraform/envs/prod/`
- [ ] [T240](tasks/phase-17-polish.md#t240) Add the deploy workflow (staging on merge, manual promotion to production, migrations first, blue/green) in `.github/workflows/deploy.yml`
- [ ] [T241](tasks/phase-17-polish.md#t241) Run a restore drill and write runbooks (upstream outage, stuck queue, waiting-input backlog, webhook backlog) in `docs/runbooks/`
- [ ] [T242](tasks/phase-17-polish.md#t242) Run quickstart.md end to end on staging in both languages and sign off SC-001 to SC-012

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup → Foundational → US1 (MVP).** Foundational blocks every story.
- **US2** depends on US1.
- **US3** depends on the US1 Create screen and editor (T081, T084).
- **US4** depends on Foundational only. It can run in parallel with US1.
- **US5** depends on US4 and the US1 editor.
- **US6, US7, US8, US10, US11, and US13** depend on US1. US6 and US7 can run in parallel.
- **US9** depends on Foundational (the ledger) and US4. Plan gating elsewhere uses flags until T178 lands.
- **US12** depends on US1 and US4 (workspace admins).
- **US14** depends on US1. The model registry reads env until the platform settings service lands.
- **Polish** depends on every GA story.

### Within each story

- Tests marked ⚠️ come first and must fail.
- Backend order: domain → model and migration → service → router or task → `pnpm gen:api` → UI → e2e.
- Ported modules keep their MA tests, rewritten at the new seam.
- Prompt and skill changes ship only with a passing eval run.

### Parallel Opportunities

- Phase 1: every task marked [P] after the first.
- Phase 2 has five tracks: domain and types, renderer, database, auth, ledger.
- After Foundational:
  - **Track A** (agent): US1 → US2 → US10 → US11 → US13
  - **Track B** (platform): US4 → US5 → US9 → US12 → US14
  - **Track C** (content): US3 → US6 → US7 → US8, starting after T081 and T084

## Implementation Strategy

### MVP first

1. Setup, then Foundational, then US1.
2. Validate with quickstart.md › US1 on the **same OpenAI-compatible upstream as agent_console**, then on one more provider.
3. Internal alpha.

### Incremental delivery

| Milestone | Stories added | Release |
|---|---|---|
| Alpha | US1 + US2 | Internal |
| Closed beta | + US3, US4, US5, US10, US14 | Invited users |
| Open beta | + US6, US7, US8, US11, US13 | Public, free plan |
| GA | + US9, US12, Polish | Paid plans |

### Suggested team (4–5 developers)

- **Python/AI engineer**: graph, nodes, guards, interrupts, memory, skills, evals (US1, US2, US10, US11, US13)
- **Python platform engineer**: auth port, DB, ledger, workspaces, sharing, billing, MCP, admin, infra (US4, US5, US9, US12, US14)
- **Frontend engineer ×2**: port MA components, editor, library, sharing, settings, admin UI
- **Content and QA (part-time)**: Arabic copy, skills, templates, eval datasets

## Notes

- 242 tasks in total:

| Phase | Tasks |
|---|---|
| Setup | 13 |
| Foundational | 39 |
| US1 | 37 |
| US2 | 21 |
| US3 | 11 |
| US4 | 18 |
| US5 | 8 |
| US6 | 14 |
| US7 | 7 |
| US8 | 6 |
| US9 | 13 |
| US10 | 8 |
| US11 | 9 |
| US12 | 8 |
| US13 | 4 |
| US14 | 5 |
| Polish | 21 |
| **Total** | **242** |
- Resolve FR-034 (pricing) before T178, FR-037 (region) before T239, and FR-038 (retention) before the retention task in Phase 8.
- Never copy `MA/skills/{docx,pptx,xlsx,pdf}`, which are proprietary (research.md R21).
