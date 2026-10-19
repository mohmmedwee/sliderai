# Implementer Guide: Docu Builder GA

**Read this file once before picking up any task.** Every task card in `tasks/` assumes you know what is here. The cards are written so a developer or a smaller model can finish one task without guessing. When a card and this guide disagree, the card wins. When a card and a **contract** (`contracts/*.md`) or the **data model** (`data-model.md`) disagree, the contract wins. Stop and report it (see §9).

---

## 1. How to work one task

1. Open the task's card: `tasks.md` links each ID to `tasks/phase-NN-*.md#tNNN`.
2. Check **Depends on**. Every listed task must already be merged. If one isn't, stop and pick another task.
3. Read everything under **Read first**. They are short, specific sections, not whole documents.
4. If the card has **Tests**, write them first, run them, and confirm they **fail** for the right reason.
5. Do the **Steps** in order. Create only the files listed under **Files**. If you truly need another file, add it and say why in the PR.
6. Run the **Verify** command(s). All must pass.
7. Tick every **Acceptance** box. If you can't tick one, the task isn't done.
8. Commit with the message `T055: implement pure document reducers` (task id, colon, lowercase summary). Use one task per PR unless the card says it can be grouped.

**Size** on each card: **S** is about 1–2 h, **M** is half a day, **L** is 1–2 days. If an S task takes more than a day, stop and ask.

---

## 2. Hard rules (never break)

1. **Never change** `spec.md`, `contracts/*.md`, `data-model.md`, or the constitution inside a task PR. If they are wrong, report it (§9).
2. **Never copy** anything from `~/Documents/myproject/my_agent/skills/{docx,pptx,xlsx,pdf}/`. They are proprietary.
3. **Every user-visible string** goes in both `frontend/apps/web/src/i18n/en.json` and `ar.json`. No hard-coded UI text. The Arabic can be a placeholder copied from English, marked `"__TODO_AR__ …"`. CI fails if any `__TODO_AR__` is left at release.
4. **No secrets** in code, tests, fixtures, or logs. Use settings and `.env`. Never log message text, prompts, or attachment content above DEBUG.
5. **Never add a dependency** that the card doesn't name. If you need one, say so in the PR description.
6. **The agent never touches the database for documents directly.** It goes through reducers and `commit` only (Constitution I and IV).
7. **Every query on tenant data** goes through `scoped_session(workspace_id)` and a repository that takes `workspace_id` (§5.4).
8. **Type checks and lint stay green**: `ruff`, `mypy --strict`, `tsc --noEmit`, `eslint`.

---

## 3. Repository map and abbreviations

| Abbrev. | Path |
|---|---|
| `BE` | `backend/src/docu` |
| `BT` | `backend/tests` (`unit/`, `integration/`, `contract/`) |
| `FE` | `frontend/apps/web/src` |
| `FP` | `frontend/packages` (`slides/`, `api-types/`) |
| `MA` | `~/Documents/myproject/my_agent` (agent_console, the reference implementation) |
| `MAS` | `~/Documents/myproject/my_agent/src/agent_console` |
| `MAF` | `~/Documents/myproject/my_agent/frontend/src` |

The full tree is in `plan.md` › Project Structure.

---

## 4. Commands

```bash
# one-time
docker compose -f infra/compose.yaml up -d
cd backend && uv sync && uv run alembic upgrade head && uv run python -m docu.scripts.setup_langgraph && uv run python -m docu.scripts.seed && cd ..
cd frontend && pnpm install && cd ..

# run
cd backend && uv run uvicorn docu.api.app:create_app --factory --reload --port 8000
cd backend && uv run celery -A docu.worker.celery_app worker -Q turns,files,exports,default -l info
cd backend && uv run celery -A docu.worker.celery_app beat -l info
cd frontend && pnpm gen:api && pnpm dev

# check (run before every PR)
cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy src && uv run pytest -m "not slow"
cd frontend && pnpm lint && pnpm typecheck && pnpm test
cd frontend && pnpm test:e2e --project=en-desktop --project=ar-desktop   # when the card touches UI

# single test
cd backend && uv run pytest tests/unit/test_reducers.py -q
cd backend && uv run pytest tests/integration/test_rls.py -q -m db
```

`AGENT_FAKE_MODEL=1` makes every model call use scripted replies (§6.9). Use it in all tests and e2e tests.

---

## 5. Backend conventions

### 5.1 Python style

- Python 3.12. Start every module with `from __future__ import annotations`.
- Type everything. `Any` is allowed only at JSON boundaries.
- Async everywhere in the API and agent. Celery tasks are sync functions that call `asyncio.run(_main(...))`.
- Every module has an `__all__` listing its public names (an MA convention).
- Module docstring: one line saying what the module is for (the MA style).
- Comments explain **why**, not what. Match the density of the MA code: sparse, and only where the behavior is not obvious.
- No print statements. Use `log = structlog.get_logger(__name__)`.

### 5.2 Pydantic base models (from T014; use them everywhere)

```python
# BE/domain/base.py
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class ApiModel(BaseModel):
    """Wire model: camelCase JSON, snake_case Python, unknown fields rejected."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid", frozen=False)
```

All request, response, event, and tool-argument models inherit `ApiModel`. Serialize with `model.model_dump(by_alias=True, mode="json")`.

### 5.3 Errors (from T015)

```python
# BE/domain/errors.py
class DomainError(Exception):
    def __init__(self, code: str, status: int = 400, message: str = "", details: dict | None = None): ...
# raise DomainError("version_conflict", 409)
```

The exception handler (T035) turns it into `{"error": {"code", "message", "details"}}`. `message` is English and only for logs. The UI translates `code`.

### 5.4 Database access

```python
# In a route:
async def get_document(doc_id: UUID, ctx: WorkspaceCtx = Depends(workspace_scope)) -> DocumentOut:
    doc = await documents_repo.get(ctx.session, workspace_id=ctx.workspace_id, doc_id=doc_id)
    if doc is None:
        raise DomainError("not_found", 404)
```

- `WorkspaceCtx` (T033) holds `session` (already scoped), `user_id`, `workspace_id`, and `role`.
- Repositories are module-level async functions in `BE/db/repositories/<aggregate>.py`. They **always** take keyword-only `workspace_id`, and `user_id` when ownership matters (MA rule: ownership is part of the signature).
- Never call `session.commit()` inside a repository. The route or service owns the transaction (`async with session.begin():`).
- Primary keys are UUIDv7 (`uuid6.uuid7()` → `uuid.UUID`). Timestamps are `timestamptz` with `server_default=func.now()`.

### 5.5 Routers

- One file per resource in `BE/api/routers/`. `router = APIRouter(prefix="/v1/<resource>", tags=["<resource>"])`.
- Every route declares `response_model` and its error codes, both taken from `contracts/rest-api.md`.
- Register the router in `BE/api/app.py` in alphabetical order.

### 5.6 Celery task template

```python
# BE/worker/tasks/example.py
"""One line purpose."""
from __future__ import annotations
import asyncio
from docu.worker.celery_app import app

__all__ = ["example"]

@app.task(name="docu.example", queue="default", acks_late=True, max_retries=3)
def example(arg: str) -> None:
    asyncio.run(_main(arg))

async def _main(arg: str) -> None:
    async with task_resources() as res:   # T009: db engine, redis, settings
        ...
```

### 5.7 Test fixtures (from T002 and T022; reuse them, don't write your own)

| Fixture | Gives |
|---|---|
| `settings` | test `Settings` with `AGENT_FAKE_MODEL=1` |
| `db` | async session on a Testcontainers Postgres, rolled back after each test (marker `db`) |
| `redis` | a Testcontainers Redis client, flushed after each test |
| `client` | `httpx.AsyncClient` on the app, with no session |
| `make_user(**kw)` | creates a verified user and returns `(user, session_cookie)` |
| `make_workspace(owner, kind="team")` | workspace and owner membership |
| `login(client, user)` | sets the cookie and CSRF header on the client |
| `fake_model(script)` | patches the model registry with `GenericFakeChatModel(messages=iter(script))` |
| `make_document(ws, slides=n)` | document with `n` valid slides |

---

## 6. LangGraph primer for this project (read before any agent task)

### 6.1 Versions and imports

```python
from langchain.chat_models import init_chat_model
from langchain_core.messages import (AIMessage, AIMessageChunk, BaseMessage, HumanMessage,
                                     RemoveMessage, SystemMessage, ToolMessage)
from langchain_core.messages.utils import convert_to_openai_messages, count_tokens_approximately
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages, REMOVE_ALL_MESSAGES
from langgraph.types import interrupt, Command
from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres.aio import AsyncPostgresStore
```

Pin the versions in `backend/pyproject.toml` (T001). If an import path differs in the pinned version, fix the import, keep the behavior, and note it in the PR.

### 6.2 State and context (defined in T067; shown here so every agent task uses the same names)

```python
class LoopFlags(TypedDict, total=False):          # MA _LoopState
    empty_retries: int; auto_continued: bool; overflow_retries: int
    max_tokens_cap: int | None; recent_tool_fps: list[str]
    schema_only_nudge: bool; prose_ask_nudge: bool; pending_schema_only: bool

class TurnState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]   # full log, checkpointed across turns
    summary: str                                          # rolling compaction summary
    llm_input: list[BaseMessage]                          # per-round view built by `prepare`; NOT add_messages
    draft: dict                                           # DocumentContent + title/theme as plain dict
    base_version: int
    changed_slide_ids: list[str]
    manual_edits_since_agent: int
    usage: dict                                           # summed usage_metadata
    steps_used: int; max_steps: int
    effort: str                                           # MA scale: minimal|low|medium|xhigh
    loop: LoopFlags
    approved_tools: list[str]                             # "allow for this thread"
    skill: str | None; web_search: bool
    final: Literal["text", "cap", "cut"] | None

@dataclass(frozen=True)
class TurnContext:                                        # runtime context — never seen by the model
    user_id: UUID; workspace_id: UUID; document_id: UUID; thread_id: UUID; turn_id: UUID
    profile_id: str; locale: Literal["en", "ar"]; plan: str; prompt_version_id: UUID
```

Node signature: `async def prepare(state: TurnState, runtime: Runtime[TurnContext]) -> dict:`. Return **only the keys you change**.

### 6.3 Two message lists. Don't mix them up.

- `messages` is the permanent conversation, saved by the checkpointer across turns. Only append to it, through the `add_messages` reducer. The only removals are compaction (`RemoveMessage`) and rewind.
- `llm_input` is rebuilt by `prepare` **every round**. It holds the system prompt, the summary, the context message, and a clipped copy of `messages`. `model` sends `llm_input`, never `messages`.
- **MA functions work on OpenAI dicts.** Port them unchanged, then convert at the edge with the helpers from T059:

```python
# BE/agent/msgconv.py
def to_dicts(msgs: list[BaseMessage]) -> list[dict]: return convert_to_openai_messages(msgs)
def from_dicts(dicts: list[dict]) -> list[BaseMessage]: ...   # uses langchain_core.messages.convert_to_messages
```

### 6.4 Per-turn reset

At the start of each turn, the worker calls the graph with:

```python
inp = {"messages": [HumanMessage(content=text, id=str(message_id))],
       "draft": doc_as_dict, "base_version": doc.version, "changed_slide_ids": [],
       "steps_used": 0, "max_steps": step_budget(settings, effort), "effort": effort,
       "loop": {}, "usage": {}, "skill": skill, "web_search": web_search, "final": None,
       "manual_edits_since_agent": n}
```

Keys that aren't `add_messages` are overwritten, which resets them. `messages` gets the new human message appended.

### 6.5 Streaming

```python
async for mode, chunk in graph.astream(inp_or_command, config=cfg, context=ctx,
                                       stream_mode=["messages", "updates", "custom"]):
    if mode == "messages":   msg, meta = chunk            # AIMessageChunk from the `model` node
    elif mode == "updates":  # {node_name: returned_dict} or {"__interrupt__": (Interrupt(value=..., id=...),)}
    elif mode == "custom":   # whatever a node/tool passed to get_stream_writer()(...)
```

`cfg = {"configurable": {"thread_id": str(thread_id)}, "recursion_limit": 4 * max_steps + 10}`.
- Text deltas come from `msg.content`, and only in chunks whose `meta["langgraph_node"] == "model"`.
- Tool argument progress comes from `msg.tool_call_chunks`.
- Reasoning comes from `msg.additional_kwargs.get("reasoning_content")`. T056 makes sure it is filled for OpenAI-compatible upstreams.

### 6.6 Interrupts. The one rule people get wrong.

**When a node calls `interrupt()`, the whole node runs again from the top on resume.** So, inside the `tools` node:
- Do **nothing with side effects before** the `interrupt()` call. That means no reducer application, no DB writes, no `get_stream_writer()` events for that call.
- Process tool calls **in order**. Those that ran before an interrupt in the same node run will run again on resume, so document tools must be pure (they are: reducers on `state.draft`). I/O tools (`generate_image`, MCP writes) always need approval and run only after `interrupt()` returns.
- Read the resume value as the return value of `interrupt(payload)`.

Resume:

```python
await graph.astream(Command(resume={interrupt_id: answer}), config=cfg, context=ctx, stream_mode=[...])
```

### 6.7 Store (memory)

`store = runtime.store` inside nodes. Inside tools, use `get_store()` from `langgraph.config`. Namespaces are `("memories", str(user_id))` and `("brand", str(workspace_id))`.

### 6.8 Tools

- Build tools per turn with a closure over `TurnContext`, so the model never supplies ids:

```python
def build_tools(profile: AgentProfile, ctx: TurnContext, settings: Settings) -> list[BaseTool]: ...
```

- **The `tools` node does not use the prebuilt ToolNode.** It loops over `AIMessage.tool_calls` itself, so it can apply MA's error messages, repeat guards, approvals, and draft updates (T066).
- Bad JSON: LangChain puts unparseable calls in `AIMessage.invalid_tool_calls`. Answer each one with a `ToolMessage` that carries MA's `broken_json_hint` text.

### 6.9 Fake model for tests

```python
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
script = [AIMessage(content="", tool_calls=[{"name": "replace_slides", "args": {...}, "id": "c1"}]),
          AIMessage(content="Done — 5 slides.")]
fake = GenericFakeChatModel(messages=iter(script))
```

When `AGENT_FAKE_MODEL=1`, the registry (T056) loads scripts from `backend/tests/fixtures/fake_scripts/<name>.json`. The script name comes from the first line of the user prompt when it starts with `#script:<name>`. Otherwise it uses `default.json`. That lets e2e tests choose a script.

`GenericFakeChatModel` does not support `bind_tools` by default. T056 adds `FakeToolModel(GenericFakeChatModel)` whose `bind_tools()` returns `self`.

---

## 7. Frontend conventions

- React 19 function components, TypeScript strict, Tailwind 4. Follow MA's existing component style; open the ported file next to yours.
- **API**: only through `FE/lib/api.ts` (generated types plus `openapi-fetch`). No raw `fetch` except the SSE client.
- **Server state** lives in TanStack Query (`useQuery` keys: `['documents', id]`, `['threads', id, 'messages']`, …). **Editor and turn state** live in Zustand (`FE/features/agent/turnStore.ts`).
- **i18n**: `const { t } = useTranslation()`. Keys are `area.component.thing`, e.g. `editor.banner.agentEditing`.
- **RTL**: only logical classes (`ms-*`, `me-*`, `ps-*`, `pe-*`, `start-*`, `end-*`, `text-start`). Never `ml-`, `mr-`, `left-`, or `right-`. Directional icons get `rtl:-scale-x-100`.
- **Test ids**: `data-testid="area-thing"` (e.g. `composer-send`, `filmstrip-item-3`). e2e tests use only test ids and roles, never translated text.
- Every page component is lazy loaded in the router.

---

## 8. Porting from agent_console (MA)

When a card says **Port**:
1. Copy the named file(s) from `MAS` (or `MAF`) to the target path.
2. Rename imports `agent_console.` → `docu.`. Keep the function names and signatures unless the card says otherwise.
3. Keep the module docstring and comments. They explain hard-won behavior.
4. Copy the matching MA test file(s) from `MA/tests/` (the card names them) and make them pass. Rewrite tests that import private names (`_foo`) so they test the public function instead.
5. Remove what the card lists under **Drop**: Cleverso, Work, run_python, docx editing.
6. Settings: T003 keeps MA's settings groups and field names (`settings.llm.*`, `settings.agent.*`, `settings.skills.*`, …), so ported code reads settings unchanged.

---

## 9. When you are blocked or something is wrong

Don't guess. Add a short note at the top of the PR description:

```
BLOCKED: <task id> — <one sentence what is unclear or contradictory> — <files/sections involved> — <the two options you see>
```

Then stop that task and pick another one with no unfinished dependencies.

---

## 10. Definition of Done (every task)

- [ ] Every **Acceptance** item on the card is ticked.
- [ ] **Verify** commands pass locally, and CI is green.
- [ ] New code has tests. Tests the card asked for were written first.
- [ ] `ruff`, `mypy --strict`, `tsc`, and `eslint` are clean.
- [ ] UI changes: works in `ar` (RTL) and `en`, at desktop and 390 px width, and has no axe violations.
- [ ] No new `TODO` without a task id (`# TODO(T123): …`).
- [ ] The PR title starts with the task id, and the description lists any deviation from the card.

---

## 11. Glossary

| Term | Meaning |
|---|---|
| **Turn** | One user message and everything the agent does until it commits, fails, is cancelled, or waits for input |
| **Draft** | The in-memory copy of the document that a turn edits (`state.draft`) |
| **Revision** | An immutable snapshot of a document, written on every commit, manual save session, restore, or theme change |
| **Profile** | The settings for one document format: prompt, tools, skills, memory, and effort cap (`BE/agent/profiles.py`) |
| **Interrupt** | A LangGraph pause waiting for the user (`ask_user` or an approval). The turn is in `waiting_input`. |
| **Lease** | A Redis key `doc:{id}:lease` that ensures only one turn runs per document |
| **Effort** | UI `fast`/`standard`/`deep` maps to MA `low`/`medium`/`xhigh`. Effort sets the step budget and the model's reasoning effort. |
| **MA** | agent_console, the reference repo in `~/Documents/myproject/my_agent` |
