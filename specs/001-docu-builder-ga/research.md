# Research: Docu Builder GA

**Feature**: `001-docu-builder-ga` | **Date**: 2026-10-19 (rev. 3: built on the `my_agent` / agent_console concepts)

Each entry follows Spec Kit's format: Decision, Rationale, Alternatives considered.

**Reference implementation**: `~/Documents/myproject/my_agent` (agent_console). It is a working FastAPI agent console with a hand-written tool loop, typed SSE events, agent profiles, skills, memory, MCP connectors, approval gates (HITL), context compaction, and an EN/AR React frontend. Docu Builder keeps its **concepts and proven seams** but runs the loop on **LangChain + LangGraph** and removes its single-process limits.

---

## Part A: Concepts carried over from `my_agent`

| # | `my_agent` concept (module) | In Docu Builder (LangChain / LangGraph) | Change and why |
|---|---|---|---|
| A1 | Hand-written agent loop (`services/agent/service.py`, `stream.py`, `tool_round.py`, `replies.py`) | LangGraph `StateGraph`: `prepare → model → guards → tools → …` (R2) | Checkpoints, interrupts, and streaming come from the framework instead of ~1,500 lines of custom loop |
| A2 | Typed events (`models/events.py`: `text_delta`, `reasoning_delta`, `tool_call_delta`, `tool_call`, `tool_approval`, `tool_result`, `status`, `error`, `done`) | **Same names**, produced from `astream(stream_mode=["messages","updates","custom"])`, plus `doc_patch` and the turn lifecycle events (contracts/sse-events.md) | Keeps the my_agent frontend components (Blocks, ChoiceForm, ApprovalDiffCard) usable with no rename |
| A3 | `ToolRegistry`: errors returned to the model as text, hints for broken JSON, missing-argument checks | LangChain `@tool(args_schema=…)` + a custom `ToolNode` error handler that returns the same style of message (and the `broken_json_hint` logic) | Same behavior: the model retries instead of the turn failing |
| A4 | Agent profiles (`agent_profiles.py`: prompt, tool and skill allowlists, memory on/off, effort cap, thinking, deferred MCP) | `AgentProfile` dataclass → `build_graph(profile)`. Profiles: `deck`, `document`, `webpage`, `social`, plus `assistant` (a general helper inside the editor) | One profile per format replaces Chat/Work. The concept and fields are unchanged. |
| A5 | Skills (`skills/*/SKILL.md`, an index of name + description in the prompt, `read_skill` tool, inlined playbooks, user skills, skill generation) | Same file format and index. `read_skill` is a LangChain tool. User skills live in the DB. A `/` skill picker in the composer. | Writing playbooks (deck, report, pitch) and brand rules live as skills, not code. Licenses are checked (R21). |
| A6 | User memory (`repositories/memory.py`, capped list, prompt block, memory tool, Memory page) | LangGraph `AsyncPostgresStore`, namespace `("memories", user_id)`, the `remember` and `forget` tools, a prompt block, and a Memory page | The Store is read from inside graph nodes and tools through `get_store()`. It holds tone, audience, brand colors, and preferred language. |
| A7 | MCP connectors (`services/mcp/*`: registry, OAuth, sealed secrets, progressive `list_mcp_tools` / `use_mcp_tools`, shrinking results, guards) | `langchain-mcp-adapters` (`MultiServerMCPClient`) for the tools. my_agent's **OAuth flow, header sealing, result shrinking, and progressive loading** are ported as services. | The connection state moves from process memory to Redis and Postgres (R24) |
| A8 | HITL (`approvals.py` in-memory futures, `ask_user` choice and form tool, `ApprovalDiffCard`) | LangGraph **`interrupt()`** with `Command(resume=…)`, durable in the checkpointer. Same `tool_approval` and `ask_user` events. | Works across processes and restarts. The turn sits in `waiting_input` (R25). |
| A9 | Background chat jobs that survive disconnect (`chat_jobs.py`, `/chat/watch`, SSE heartbeats) | Celery `turns` queue, Redis Stream per turn, `Last-Event-ID` resume, 15 s heartbeat comments (R4, R5) | Removes the "one API process" limit in the my_agent README |
| A10 | Context budget (`budget.py`: fit the prompt, trim tools, clip old tool payloads, completion budget, overflow retries) | A `prepare` node (pre-model hook) using `trim_messages` / `count_tokens_approximately`, a payload clipper, and an overflow retry inside the model node | Same policies, now in one node |
| A11 | Context compaction (`context_compact.py`: rolling summary, `status` event "Compacting context…") | A `compact` step inside `prepare` that writes `state.summary` and emits `status` | Kept, with the same prompt (`prompts/context_compact.md`) |
| A12 | Runaway repetition cutoff and repeated failing calls (`runaway.py`, `agent/repeats.py`) | A `guards` node after `model`: cuts runaway text and refuses an identical failing tool call the third time | Ported as-is |
| A13 | Step budget by effort, auto-continue nudge, empty-reply recovery, `wrap_up` | `recursion_limit` from the effort level, one auto-continue extension, empty-reply retry at lower effort, and a final wrap-up node when the cap is hit | Same user-visible behavior |
| A14 | Upstream client (`clients/upstream.py`: OpenAI-compatible, effort mapping, `enable_thinking`, retries, SSE salvage) | `init_chat_model("openai:<MODEL>", base_url=UPSTREAM, api_key=…)` with `reasoning_effort` and `extra_body={"enable_thinking": …}`, plus `.with_retry()` and `.with_fallbacks()` (R8) | Any OpenAI-compatible endpoint (the self-hosted Cleverso model, OpenRouter, OpenAI) or Anthropic works through config |
| A15 | Model and effort picker (`ModelEffortPicker`, `/api/models`) | `GET /v1/models` plus an effort picker (fast, standard, deep) capped per plan and per profile | Kept |
| A16 | Auto-title (`auto_title.py`, `prompts/auto_title.md`) | `title` node run by the small model after the first commit | Same prompt |
| A17 | Rewind (`/conversations/{id}/rewind`) | `POST /v1/threads/{id}/rewind` edits an earlier user message and re-runs from there. **The document is restored to the revision from before that turn.** | Revisions make rewind safe for the document as well as the chat |
| A18 | Files (`BlobStore` local/S3, upload limits, previews, `convert_upload` through markitdown, `read_uploaded_file`, `search_files`) | `BlobStore` is ported **as is**. Attachments go through scan → parse (markitdown + PyMuPDF) → embed. Tools: `read_attachment`, `search_attachments`. | Adds vector retrieval (an item already on my_agent's TODO) |
| A19 | Web search and fetch (`web_search` via ddgs, `fetch_url`, session toggle prompts) | `web_search` (provider adapter: ddgs, Tavily, or Brave) and `fetch_url` tools, behind a per-session toggle with the same prompts | Sources are cited in slide speaker notes |
| A20 | Auth (argon2 password hashing, signed cookie sessions, `FIRST_USER_IS_ADMIN`, admin role) | Ported (R10), plus email verification, password reset, and Google sign-in (Authlib), plus workspaces and roles | Self-hosted, so it works in any data region (FR-037) |
| A21 | Admin (`/api/admin/users`, settings) | Platform admin: users, roles, model settings, versioned prompts, feature flags, usage and cost | Prompts can be edited by admins with versions, following the my_agent `002-workflows` spec |
| A22 | Prompts as Markdown files (`prompts/*.md`, `load_prompt` with variables, cached per process) | Same files and loader. DB-stored admin overrides win over the files (A21). | Kept |
| A23 | Frontend: React 19, Vite, Tailwind 4, react-router 7, TanStack Query, i18next EN/AR, `sse.ts`, `chatRunner`, Composer, Blocks, ChoiceForm, ApprovalDiffCard, Markdown, LanguageToggle, AppShell/NavRail | Reused as the base of `frontend/apps/web`. The editor (canvas, filmstrip, Patterns) is new. | Days of UI work saved, and the look stays consistent |
| A24 | Docker image with the SPA baked into the API image, `ENV.md`, health route, `alembic upgrade` entrypoint | Kept for single-host deploys. AWS ECS is the scaled path (R16). | Kept |

### Not carried over (on purpose)

| `my_agent` piece | Why not | Replacement |
|---|---|---|
| `run_python` sandbox | Running arbitrary code in a multi-tenant SaaS is a large security surface | Structured `table` and `chart` slide layouts, rendered by the frontend and exported natively (R26) |
| `write_file` for arbitrary files (pptx/docx/xlsx from Markdown) | The document **is** the structured deck now | Export (PDF, PPTX, PNG) from the structured document |
| `edit_docx` with an XML diff approval | Slides are structured, so there is no XML to diff | `update_slide` / `replace_slides` with a before/after approval card on large changes |
| Work / Cleverso profile and playbook | Not part of this product | Cleverso (or any TMS) can still connect as an MCP connector (A7) |
| The proprietary `docx` / `pptx` / `xlsx` / `pdf` skills | "© Anthropic, All rights reserved" (R21) | New in-house skills written for this product |
| In-memory `ChatJobBroker`, `ApprovalBroker`, MCP loaded-tool cache | Single process only | Celery + Redis Streams, LangGraph interrupts, Redis cache |

---

## Part B: Decisions

## R1. Backend language

- **Decision**: Python 3.12 for the backend: API, workers, agent, parsing, and export. TypeScript and React for the frontend.
- **Rationale**:
  - LangChain and LangGraph are Python-first.
  - Python has stronger parsing (PyMuPDF, markitdown, `python-pptx`).
  - The `my_agent` backend is already Python, so its code and seams port directly.
- **Alternatives considered**: TypeScript end to end (rejected in review on 2026-10-19).

## R2. Agent loop on LangGraph

- **Decision**: One `StateGraph(TurnState)` per profile:

```
START → prepare ─→ model ─→ guards ─┬─(tool calls)→ tools ─→ prepare …
                                   ├─(text only, needs nudge)→ prepare
                                   └─(done | cap)→ wrap_up? → commit → title? → END
```

  - **prepare**: fits the context (A10), compacts (A11), and injects the selected skill, memory block, and document context.
  - **model**: makes the model call, retries on overflow (A10), and streams.
  - **guards**: runaway cutoff, repeated failing calls, empty-reply recovery, and the auto-continue nudge (A12, A13).
  - **tools**: a custom `ToolNode` that validates arguments, gates approvals with `interrupt()`, runs the tool, and emits `doc_patch`.
  - **commit**: one transaction that writes the revision, the messages, and the credit settlement.
- **Rationale**: Keeps the behavior my_agent proved, and adds durable state, interrupts, and tracing.
- **Alternatives considered**:
  - Porting `AgentService` as is: no durable interrupts or checkpoints.
  - `create_react_agent`: can't host the draft document, the guards, or domain events.
  - Deep Agents: more framework than this product needs.

## R3. Thread durability

- **Decision**: `AsyncPostgresSaver`, with `thread_id = threads.id`. Messages the UI shows are also stored in `messages`, using the same block format as my_agent so its `Blocks` component renders them.
- **Alternatives considered**: Checkpoints only (hard to query).

## R4. Task queue

- **Decision**: Celery 5 with a Redis broker. Queues are `turns`, `files`, `exports`, and `default`, plus beat. Async code runs inside tasks with `asyncio.run`.
- **Rationale**: Replaces my_agent's in-process `ChatJobBroker`, so the API can scale out.
- **Alternatives considered**: arq (maintenance mode), Taskiq (young), keeping the in-process broker (single process).

## R5. Turn events to the browser

- **Decision**:
  - The worker appends events to the Redis Stream `turn:{id}`, kept for 1 h after the turn ends.
  - The API relays the stream with `sse-starlette`, supports `Last-Event-ID`, and sends `: ping` comments every 15 s. That is the same heartbeat as my_agent's `iter_job_sse_frames`.
- **Alternatives considered**: WebSockets, Postgres NOTIFY.

## R6. Applying edits: draft and commit

- **Decision**: Tools call pure reducers on `state.draft`. `commit` writes the revision while checking `base_version`.
- **Rationale**: Atomic turns, undo, and **safe rewind** (A17).

## R7. Concurrency between agent and user

- **Decision**: One turn lease per document in Redis, plus optimistic `version` checks on manual saves.

## R8. Models (OpenAI-compatible first)

- **Decision**: A model registry keyed by profile and plan:

```python
init_chat_model(
    f"{provider}:{model}",           # "openai:cleverso-model", "anthropic:claude-sonnet-5-5", …
    base_url=settings.llm.upstream,  # e.g. self-hosted OpenAI-compatible /v1 (as in my_agent)
    api_key=settings.llm.api_key,
    reasoning_effort=effort,         # mapped like my_agent's effort levels
    extra_body={"enable_thinking": thinking_on},
).with_retry(stop_after_attempt=3).with_fallbacks([fallback])
```

  - **Configurable per environment**:
    - `UPSTREAM`, `MODEL`, `VISION_MODEL`, `CONTEXT_WINDOW`, `MAX_COMPLETION_TOKENS`, `ENABLE_THINKING`. These are my_agent's names, kept so `ENV.md` carries over.
    - A small model for titles, summaries, and compaction.
    - A fallback model.
  - `scripts/check_endpoint.py` (from my_agent) checks that the endpoint emits real `tool_calls`, both streamed and not streamed, before an environment goes live.
- **Rationale**: my_agent runs on a self-hosted OpenAI-compatible Arabic model. The same deployment must work here. Anthropic, OpenAI, and OpenRouter work by changing config.
- **Follow-up**: Run the Arabic and English eval suites on each candidate model (T-eval tasks) before choosing the production default.

## R9. Embeddings and retrieval

- **Decision**:
  - The embedding provider is configurable. It can be an OpenAI-compatible `/embeddings` on the same upstream.
  - Choose it with a 50-query Arabic + English recall@5 benchmark, targeting at least 0.85.
  - Store vectors in pgvector (HNSW) and run a hybrid search that merges vector and `tsvector` results with reciprocal rank fusion.

## R10. Auth (ported from my_agent)

- **Decision**: Self-hosted auth, ported from `services/security.py` and `api/routes/auth.py`:
  - argon2id password hashes (`argon2-cffi`, rehashed when parameters change);
  - opaque session ids in an `HttpOnly` cookie, with session rows in Postgres (revocable and listable);
  - CSRF double-submit;
  - **added**: email verification, password reset, Google sign-in (Authlib OIDC), optional TOTP (`pyotp`), login rate limits;
  - `FIRST_USER_IS_ADMIN` bootstraps the platform admin.
- **Rationale**: Keeps identity data in our database and region (FR-037), reuses code that is already tested, and needs no outside identity vendor.
- **Alternatives considered**: WorkOS, Clerk, or Auth0 (outside processor, residency questions), Keycloak (more operations work).

## R11. Data access and migrations

- **Decision**: SQLAlchemy 2.0 async with asyncpg and Alembic (as in my_agent), plus RLS and a `scoped_session(workspace_id)` dependency. Repositories take `user_id` and `workspace_id` on every call, which is my_agent's ownership-in-the-interface rule.

## R12. Frontend and shared types

- **Decision**:
  - **Base:** my_agent's frontend stack: React 19, Vite, Tailwind 4, react-router 7, TanStack Query, i18next EN/AR.
  - **Reused components:** AppShell, NavRail, Composer, Blocks, ChoiceForm and ChoicePrompt, ApprovalDiffCard, Markdown, ModelEffortPicker, LanguageToggle, `sse.ts`, `chatRunner.ts`, `useAuth`.
  - **Types:** generated with `openapi-typescript` from FastAPI's OpenAPI, and CI fails on any drift.
  - **New:** a Zustand turn and document store for the editor.
- **Alternatives considered**: A fresh frontend on TanStack Router (more work, and its UI wouldn't match).

## R13. Document parsing and import

- **Decision**:
  - **Text extraction**: markitdown (as in my_agent's `convert_upload`) for DOCX, PPTX, and XLSX. PyMuPDF for PDF, with page numbers for citations. `CSVLoader` and `TextLoader` for the rest. All are wrapped as LangChain `BaseLoader`s.
  - **Import** of an existing PPTX or DOCX into an editable deck: parse the file into an outline (slide titles, bullets, notes) and run an `import` turn that calls `replace_slides` with layouts mapped to the outline.
  - **Splitting**: Arabic-aware separators, about 800-token chunks with 100 tokens of overlap.
- **Alternatives considered**: Unstructured (heavy, needed later for OCR).

## R14. Export

- **Decision**: Playwright Python renders the frontend `/_export/{id}` route to PDF and PNG. `python-pptx` writes PPTX with native shapes, native **tables**, and native **charts** (`chart_data` → `add_chart`). Arabic gets RTL through lxml `a:pPr rtl="1"`.

## R15. Billing

- **Decision**: Stripe plus an append-only credit ledger (reserve, settle, refund). Usage is taken from LangChain `usage_metadata`, which also delivers my_agent's TODO item "usage logging".

## R16. Hosting

- **Decision**:
  - **Two deploy paths:**
    - **Single host**: my_agent's Docker pattern (SPA baked into the API image), plus a worker container and a beat container.
    - **Scaled**: AWS ECS Fargate (api, worker-turns, worker-files, worker-exports, beat), RDS, ElastiCache, S3 + CloudFront, Terraform.
  - **Region:** FR-037.

## R17. Observability

- **Decision**: structlog, OpenTelemetry (FastAPI, SQLAlchemy, Celery, Redis, httpx), Sentry, and LangSmith with personal data hidden. Usage per turn (tokens, latency, model, steps) goes into `turns`.

## R18. Python tooling

- **Decision**: `uv`, `ruff` (my_agent's rule set plus `mypy --strict`), `pytest` with my_agent's marker scheme (`db`, `slow`, `e2e_*`), `pre-commit`.

## R19. Real-time collaboration

- **Decision**: Deferred to after GA.

## R20. Agent profiles for this product

| Profile | Prompt | Tools | Skills (default) | Memory | Effort cap | Thinking |
|---|---|---|---|---|---|---|
| `deck` | `prompts/deck.md` | document tools, attachments, web (if toggled), memory, ask_user, read_skill, images (if plan), MCP (deferred) | deck-writing, replying-bilingually, theme-factory, brand-guidelines | on | per plan | per config |
| `document` | `prompts/document.md` | same | report-writing, writing-deliverables, replying-bilingually | on | per plan | per config |
| `webpage` | `prompts/webpage.md` | same | landing-page-writing | on | per plan | per config |
| `social` | `prompts/social.md` | same, without MCP | social-post-writing | on | `medium` | off |
| `import` | `prompts/import.md` | `read_attachment`, `replace_slides`, `set_title`, `set_theme` | — | off | `medium` | off |

The format chosen in the composer picks the profile. Admins can switch skills on or off for each profile (A21).

## R21. Skills licensing and catalog

- **Decision**:
  - **Can be reused:**
    - my_agent's in-house skills: `replying-bilingually`, `answering-well`, `planning-with-intention`, `writing-deliverables`, `doc-coauthoring`, `research`, `working-with-documents`, `memory`.
    - The Apache-2.0 skills, with attribution: `theme-factory` (its themes feed the theme catalog), `brand-guidelines`, `internal-comms`, `canvas-design`.
  - **Can't be reused:** `docx`, `pptx`, `xlsx`, `pdf` ("© Anthropic, All rights reserved").
  - **New skills to write:** `deck-writing`, `report-writing`, `pitch-deck`, `lesson-deck`, `landing-page-writing`, `social-post-writing`, all in Arabic and English.
  - User skills (my_agent `user_skills`) and skill generation (`skill_generate_contract.md`) are kept for the Team plan.

## R22. Tool approval policy

- **Decision**: A policy per tool: `always`, `ask`, or `never` (my_agent TODO item). Defaults:

| Tool | Default | Notes |
|---|---|---|
| `replace_slides` on a document with manual edits since the last agent turn | `ask` | Shows a before/after card |
| `delete_slide` when the turn has already deleted 3 or more slides | `ask` | |
| `generate_image` | `ask` | Shows the credit cost |
| MCP write tools | `ask` | |
| Everything else | `always` | |

  Users can choose "always allow for this thread" (my_agent `auto_approve_tools`).

## R23. Memory scope

- **Decision**: Memory is per user, with up to 50 items (my_agent's cap), stored in the LangGraph Store at `("memories", user_id)`. A workspace-level "brand memory" lives at `("brand", workspace_id)` and only admins can edit it. Both are injected as one prompt block. Users see and edit theirs on the Memory page.

## R24. MCP connectors

- **Decision**:
  - **Tools:** `langchain-mcp-adapters` (`MultiServerMCPClient`, streamable HTTP) loads them, filtered by the profile allowlist.
  - **Ported from my_agent:**
    - the OAuth start and callback,
    - `seal_headers` (secrets encrypted at rest with `cryptography`),
    - result shrinking (`mcp/shrink.py`),
    - repeated-failure guards,
    - progressive loading through `list_mcp_tools` / `use_mcp_tools`.
  - **State:** the connection registry lives in Postgres and the loaded-tools cache in Redis, keyed by thread.
- **Scope**: Connectors are added per workspace by admins, or per user when the workspace allows it.

## R25. Human-in-the-loop with `interrupt()`

- **Decision**:
  - When a tool needs approval, or `ask_user` runs, the tools node calls `interrupt({...})`.
  - The worker emits `tool_approval` or `ask_user`, sets the turn to `waiting_input`, keeps the lease, and ends the task.
  - `POST /v1/turns/{id}/resume {decision|answers}` enqueues a resume task that runs `graph.ainvoke(Command(resume=…), config)`.
  - Unanswered interrupts expire after 30 min, which ends the turn as `cancelled` and refunds the credits.
- **Rationale**: Durable across processes, which is the multi-worker gap my_agent's README describes.

## R26. Tables and charts instead of a code sandbox

- **Decision**: Two new layouts:
  - `table`: up to 8 columns × 12 rows.
  - `chart`: bar, line, pie, or donut; up to 6 series × 24 points.
  - The renderer draws charts as SVG (no chart library at runtime in the share viewer).
  - PPTX export uses native charts.
  - The agent fills the data from the prompt, attachments, or web results.
- **Rationale**: Covers most "data in slides" needs without running code.
