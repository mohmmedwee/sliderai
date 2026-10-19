# Phase 3: US1, create a deck from one prompt (task cards) 🎯 MVP

Before any card, read [IMPLEMENTER.md](../IMPLEMENTER.md), **especially §6 (the LangGraph primer)**. Every agent card assumes it.

**Story test**: quickstart.md › US1, plus "Agent behavior" steps 1, 2, and 5.

**Exit check**:
- With `AGENT_FAKE_MODEL=1`: register, send a prompt on Create, and watch slides stream into the editor in en and ar.
- With a real `UPSTREAM`: the same works. `uv run pytest -m "db or redis or not slow"` and `pnpm test:e2e -- create` pass.

---

## Tests first (T053–T059)

<a id="t053"></a>
### T053 · Reducer tests (write first)

**Depends on**: T014 · **Parallel**: yes · **Size**: M

**Read first**: contracts/agent-tools.md › Document tools (the error codes); data-model.md › Layout rules

**Files**: create `BT/unit/test_reducers.py` and `BT/fixtures/docs.py` (sample `DocumentState` builders)

**Tests**. They import `docu.agent.reducers.apply` (which doesn't exist yet). Signature per T061.

1. `set_title`: sets the title. An empty title gives `invalid_slide` (title). 141 characters is an error.
2. `set_theme`: a known id sets it. An unknown id is rejected by the arguments model. Test this in T060's test instead, and here assume valid args.
3. `add_slide`:
   - `afterSlideId=None` puts the slide first. Omitting it puts the slide last. A given id inserts after that slide.
   - An unknown id gives `unknown_slide`. The 61st slide gives `too_many_slides`.
   - A new id is generated, and the returned `changed_slide_ids == [new_id]`.
4. `update_slide`:
   - A patch merges fields. A `None` value clears the field.
   - The merged slide is validated again: switching the layout to `points` with no points gives `invalid_slide:points_required`.
   - An unknown id gives `unknown_slide`.
5. `delete_slide`: deleting the only slide gives `last_slide`.
6. `move_slide`: `after=None` moves to the front, and moving after itself is a no-op returning `changed=[]`.
7. `replace_slides`: every id is new and unique. 0 slides fails validation. 61 slides gives `too_many_slides`.
8. **Ops**: each successful call returns `ops` matching contracts/sse-events.md `DocOp` (e.g. `update_slide` returns `{op:'update_slide', slideId, slide:<full merged>}`).
9. **Hypothesis**: for random sequences of valid calls on a valid doc, the result always validates as `DocumentState` and the ids are unique.
10. **Purity**: the input `DocumentState` is not mutated (compare its `model_dump()` before and after).

**Acceptance**:
- [ ] The tests fail with `ModuleNotFoundError` before T061

---

<a id="t054"></a>
### T054 · Port the MA loop-policy tests (write first)

**Depends on**: T003 · **Parallel**: yes · **Size**: M

**Read first**: `MA/tests/{test_agent_budget,test_agent_clipping,test_agent_repeat_guard,test_context_compact,test_context_overflow}.py`

**Files**: create `BT/unit/test_budget.py`, `BT/unit/test_guards.py`, and `BT/unit/test_compact.py`

**Steps**:

1. Copy the MA tests. Change the imports to `docu.agent.budget`, `docu.agent.guards`, and `docu.agent.compact`.
2. Rewrite tests that call private names (`_tool_keep_priority`, `_looks_like_tool_history_echo`, …) to test the public functions listed in T065, T066, and T067. Keep the **same scenarios and expected numbers**.
3. Drop the cases about `run_python`, `edit_docx`, Cleverso, and Work (`schema_only` nudges stay, but under a generic "deferred MCP" profile flag).
4. Add a runaway test: `is_runaway_repetition("ha"*200)` is True, and `trim_runaway_tail` keeps 8 repeats.

**Acceptance**:
- [ ] The tests fail with `ModuleNotFoundError` before T065–T067
- [ ] Every remaining MA scenario is represented

---

<a id="t055"></a>
### T055 · Graph tests with a fake model (write first)

**Depends on**: T014 · **Parallel**: yes · **Size**: L

**Read first**: IMPLEMENTER §6 (all of it); plan.md › Agent Design (node table)

**Files**: create `BT/unit/test_graph.py` and `BT/fixtures/fake_scripts/*.json`

**Setup**: a fixture builds the graph with `build_graph(profile=DECK, checkpointer=InMemorySaver(), store=InMemoryStore())` (T073) and a `FakeToolModel` script (T062). It runs the turn with the helper `run_turn_for_test(graph, text, doc) -> (events, final_state)`, which collects the `astream` output through the emitter mapping (T074) into a list.

**Cases** (each one is a script plus assertions):

| # | Script | Expect |
|---|---|---|
| 1 | `replace_slides(5 valid)`, then the text "Done" | `final_state.draft` has 5 slides. Events in order: `tool_call`, `doc_patch`, `tool_result(ok)`, `text_delta`. `final=="text"`. |
| 2 | 9× `add_slide` with `effort="low"` (step budget 4 + 1 auto-continue) | `step_limit` emitted, then `wrap_up` runs (one call with no tools), then `final=="cap"` |
| 3 | `update_slide(slideId="nope")`, then a correct `update_slide` | The first `tool_result` has `ok=false` and contains `unknown_slide`. The second succeeds. The turn does not fail. |
| 4 | An AIMessage with `invalid_tool_calls=[{name:'replace_slides', args:'{"slides":[{"lay', id:'c1'}]` | The ToolMessage contains "not valid JSON" plus the replace_slides hint ("Write fewer slides per call…") |
| 5 | The same failing `update_slide(bad)` 3 times | The third gets "Refused: this exact call already failed twice…" without running |
| 6 | An empty AIMessage (`content=""`, no tools), then "Hello" | One retry with `effort` lowered (`downgrade_effort`), and the final text is "Hello" |
| 7 | The model raises a context-overflow error the first time | `clip_old_tool_payloads` is called, `max_tokens_cap` is set, the retry succeeds, `loop.overflow_retries==1` |
| 8 | The text "I made you a deck" with no tool calls | The draft is unchanged and `final=="text"` (commit writes no revision; asserted in T057) |
| 9 | `ask_user` alongside a sibling `add_slide` in one AIMessage | `add_slide` gets "Skipped: waiting for the user's reply…" (the MA rule), and `ask_user` interrupts |

**Acceptance**:
- [ ] The tests fail before T072/T073
- [ ] The scripts live as JSON files that the e2e tests can reuse

---

<a id="t056"></a>
### T056 · Interrupt and resume tests (write first)

**Depends on**: T024 · **Parallel**: yes · **Size**: M

**Read first**: research.md R25; IMPLEMENTER §6.6; data-model.md › pending_inputs, the Turn state machine

**Files**: create `BT/integration/test_interrupts.py` (markers `db`, `redis`)

**Cases**. They use the real Postgres checkpointer and run the Celery task functions **directly** (`turn._main(...)`, `resume._main(...)`), not through a broker.

1. **ask_user**:
   - Script: `ask_user(question, options=[A,B])`, then after the resume, `replace_slides`, then text.
   - After `turn`: the status is `waiting_input`, a `pending_inputs` row exists, the stream holds `ask_user` then `waiting_input`, and the lease is still held.
   - Call `resume(answers={"choice":"B"})`: the stream continues with the same id prefix, and the turn becomes `committed`. The model saw the answer, so the ToolMessage content includes "B".
2. **Approval deny**: the doc has `manual_edits_since_agent=2`, and the script is `replace_slides`. Expect `tool_approval` with `approvalCard.kind=="replace_slides"` and `manualEditsLost==2`. Resume with `deny`: the ToolMessage is "Denied by user.", and the draft is unchanged.
3. **allow_thread**: approve with `allow_thread`. A second `replace_slides` in the next turn of the same thread does **not** interrupt.
4. **Restart**: after the interrupt, dispose of all engines and Redis clients (simulating a worker restart), create fresh ones, resume, and the turn commits (SC-011).
5. **Expiry**: set `pending_inputs.expires_at` in the past and run `interrupt_expiry._main()`. The turn becomes `cancelled` with `reason=expired`, the credits are refunded, the lease is released, and the stream has `turn_cancelled`.
6. **Double resume**: a second resume with the same `toolCallId` gives `409 invalid_request` (single use).

**Acceptance**:
- [ ] The tests fail before T075–T077

---

<a id="t057"></a>
### T057 · Turn lifecycle tests (write first)

**Depends on**: T024, T039 · **Parallel**: yes · **Size**: M

**Files**: create `BT/integration/test_turn_lifecycle.py`

**Cases**:

1. **Commit is atomic**:
   - After a successful turn there is 1 new `document_revisions` row (`source='agent_turn'`, `version = base+1`), `documents.version` is incremented, the `messages` rows are user plus assistant (the assistant row has `blocks`), and `turns` has its usage and `credits_charged`.
   - The ledger has `reserve`, then `settle` or `refund`.
   - Make the final write in commit raise (monkeypatch). Then **none** of the above exist, and the turn is `failed(internal)` with the credits refunded.
2. **Text only**: no revision is written and the version is unchanged, but the messages are stored.
3. **Cancel**: set the cancel flag mid-stream (the script has a `sleep` step in the fake model). The status becomes `cancelled(user)`, no revision is written, credits are refunded, and the lease is released.
4. **doc_busy**: while a lease is held, `POST /v1/threads/{id}/turns` → 409 `doc_busy`.
5. **Reaper**: a `running` turn with a heartbeat older than 90 s. After `turn_reaper._main()`, it is `failed(worker_lost)`, refunded, and released.
6. **Insufficient credits**: balance 0 → 402 and no turn row (or `rejected`).


**Acceptance**:
- [ ] Every case listed above is its own test function (`test_<short_name>`)
- [ ] The tests run and **fail for the expected reason** (missing module or not implemented) until the implementation task lands
- [ ] No production code is added in this task

---

<a id="t058"></a>
### T058 · SSE relay tests (write first)

**Depends on**: T008 · **Parallel**: yes · **Size**: S

**Read first**: contracts/sse-events.md › Transport; `MA/tests/test_sse_heartbeat.py`

**Files**: create `BT/integration/test_sse.py`

**Cases**:

1. XADD 3 events, then a terminal event. GET `/v1/turns/{id}/events` gets 4 frames with `id:` lines, and the stream closes.
2. Reconnect with `Last-Event-ID` = the 2nd id. You get the 3rd and the terminal event only.
3. With no events for 15 s (patch the interval to 0.1 s), a `: ping` comment arrives.
4. After `waiting_input`, the stream closes. A later XADD on the same key, followed by a reconnect with the last id, gets the new events (resume continues the same stream).
5. A missing stream key and a turn that finished over 1 h ago → 410.
6. A user without view access → 404.


**Acceptance**:
- [ ] Every case listed above is its own test function (`test_<short_name>`)
- [ ] The tests run and **fail for the expected reason** (missing module or not implemented) until the implementation task lands
- [ ] No production code is added in this task

---

<a id="t059"></a>
### T059 · e2e test: create from a prompt (write first)

**Depends on**: T049 · **Parallel**: yes · **Size**: M

**Read first**: ux.md §5.2, §5.4, §6; quickstart.md › US1

**Files**: create `frontend/apps/web/tests/e2e/create.spec.ts`, plus fake scripts `backend/tests/fixtures/fake_scripts/{deck_water_en,deck_solar_ar,clarify_then_draft}.json`

**Cases** (projects `en-desktop` and `ar-desktop`; the backend runs with `AGENT_FAKE_MODEL=1`):

1. Log in. On Create, type `#script:deck_water_en\nA 6-slide deck on the water cycle` and send. The URL becomes `/doc/:id`, the `filmstrip-item-1`…`6` appear, `slide-1-title` is not empty, and the agent column shows the final text.
2. Arabic: `#script:deck_solar_ar …`. `html[dir=rtl]`, and the slide titles contain Arabic characters.
3. Clarify: `#script:clarify_then_draft`. A ChoicePrompt with options appears, click an option, then the slides appear (the same turn: no new user bubble).
4. Stop: use a script with a slow step, click Stop. The status shows "Stopped", and the filmstrip count matches the count before the turn.

---

## Agent core (T060–T074)

**Acceptance**:
- [ ] Every case listed above is its own test function (`test_<short_name>`)
- [ ] The tests run and **fail for the expected reason** (missing module or not implemented) until the implementation task lands
- [ ] No production code is added in this task
<a id="t060"></a>
### T060 · Tool argument models

**Depends on**: T014 · **Parallel**: yes · **Size**: S

**Read first**: contracts/agent-tools.md (every table)

**Files**: create `BE/domain/tools.py` and `BT/unit/test_tool_args.py`

**Steps**:

1. Write one `ApiModel` per tool in contracts/agent-tools.md, with exactly the fields, limits, and optionality given there:
   - `SetTitleArgs`, `SetThemeArgs`, `AddSlideArgs`, `UpdateSlideArgs` (`patch: SlidePatch`, where every field is optional and `None` means clear; use a sentinel to tell "absent" from `None`: `model_fields_set`), `DeleteSlideArgs`, `MoveSlideArgs`, `ReplaceSlidesArgs`
   - `AskUserArgs` (+ `AskUserField`), `ReadSkillArgs`, `RememberArgs`, `ForgetArgs`, `ReadAttachmentArgs`, `SearchAttachmentsArgs`, `WebSearchArgs`, `FetchUrlArgs`, `GenerateImageArgs`, `ListMcpToolsArgs`, `UseMcpToolsArgs`
2. `SetThemeArgs.theme_id` is validated at **runtime** against the allowed theme ids passed in a validation context (`model_validate(x, context={"theme_ids": {...}})`), because themes include workspace themes.
3. Each model has a docstring. LangChain uses it as the tool description, so write it for the **model**: one or two sentences saying when to use the tool.
4. Tests: limits are enforced, `SlidePatch` tells absent from `None`, and an unknown theme with context is rejected.

**Acceptance**:
- [ ] The field names and limits match the contract exactly

---

<a id="t061"></a>
### T061 · Pure document reducers

**Depends on**: T053, T060 · **Parallel**: no · **Size**: M

**Files**: create `BE/agent/reducers.py`

**Interface**:

```python
@dataclass(frozen=True)
class ToolOutcome:
    ok: bool
    state: DocumentState                 # unchanged when ok=False
    changed_slide_ids: list[str]
    ops: list[dict]                      # DocOp dicts (camelCase, by_alias) — empty when ok=False
    message: str                         # model-facing result text

def apply(state: DocumentState, name: str, args: BaseModel) -> ToolOutcome: ...
```

**Steps**:

1. Dispatch on `name` to one private function per tool. Each works on `state.model_copy(deep=True)`.
2. Success messages are short and model-facing, e.g. `"ok: updated slide 3 (id ab12cd34ef)"`, `"ok: wrote 6 slides"`.
3. Error messages use the form `"Error: <code>: <hint>"`, e.g. `"Error: unknown_slide: no slide with id 'x'. Valid ids: a1,b2,c3"`. List up to 12 ids. That helps the model correct itself.
4. Validation errors from rebuilding a `Slide` become `"Error: invalid_slide: <field>: <msg>"`. Take the first error only.

**Acceptance**:
- [ ] T053 passes
- [ ] No I/O and no globals

**Verify**: `uv run pytest tests/unit/test_reducers.py -q`

---

<a id="t062"></a>
### T062 · Model registry

**Depends on**: T003 · **Parallel**: yes · **Size**: L

**Read first**: research.md R8; IMPLEMENTER §6.5 (reasoning) and §6.9 (fake model); `MAS/clients/upstream.py` (the `_upstream_effort` mapping, how `enable_thinking` and reasoning are sent, `sanitize_model_id`)

**Files**: create `BE/agent/models.py`, `BE/agent/fake.py`, and `BT/unit/test_models.py`

**Interface**:

```python
EFFORT_UI_TO_MA = {"fast": "low", "standard": "medium", "deep": "xhigh"}

@dataclass(frozen=True)
class ModelChoice:
    provider: str; model: str; base_url: str | None; api_key: str
    context_window: int; max_completion_tokens: int; thinking: bool

class ModelRegistry:
    def __init__(self, settings: Settings, overrides: PlatformModelSettings | None = None): ...
    def chat(self, *, effort: str, thinking: bool | None = None, max_tokens: int | None = None) -> BaseChatModel
    def small(self) -> BaseChatModel                   # titles, summaries
    def choice(self) -> ModelChoice                    # for logging + turns.model
```

**Steps**:

1. `chat()`: `init_chat_model(f"{provider}:{model}", base_url=…, api_key=…, max_tokens=…, streaming=True, timeout=120)`.
   - For `openai`: pass `reasoning_effort=_upstream_effort(effort, top=settings.llm.top_effort)` (ported from MA) **only when** `thinking` is on, and `extra_body={"enable_thinking": thinking}` (MA behavior for self-hosted Qwen-style servers).
   - For `anthropic`: map effort to `thinking={"type":"enabled","budget_tokens":…}` (low 1024, medium 4096, xhigh 16000), or no thinking.
   - Wrap: `.with_retry(retry_if_exception_type=(httpx.TransportError, APITimeoutError, InternalServerError-like), stop_after_attempt=settings.agent.upstream_retries + 1)`. Never retry on context overflow (T072 handles that).
   - Then `.with_fallbacks([fallback])` when `FALLBACK_MODEL` is set.
   - Return the **unbound** model. Nodes call `bind_tools`.
2. **Reasoning capture**. Many OpenAI-compatible servers (vLLM, SGLang) send `delta.reasoning_content`, which `ChatOpenAI` may drop.
   - Add `class ReasoningChatOpenAI(ChatOpenAI)` that overrides `_convert_chunk_to_generation_chunk` (check the method name in the pinned version). It copies `choice.delta.reasoning_content` (or `reasoning`) into `AIMessageChunk.additional_kwargs["reasoning_content"]`.
   - Use it for provider `openai` when `base_url` isn't api.openai.com.
   - **Test it** with a respx-mocked SSE stream that contains `reasoning_content` deltas.
3. `fake.py`:
   - `FakeToolModel(GenericFakeChatModel)` with `bind_tools(self, tools, **kw) -> self`.
   - `load_script(name) -> list[AIMessage]` reads `backend/tests/fixtures/fake_scripts/<name>.json`. The format is a list of `{content, tool_calls?, invalid_tool_calls?, reasoning?, raise?: "context_overflow"|"timeout", sleep_s?}`.
   - `FakeToolModel` honors `raise` (it raises the matching exception) and `sleep_s` (`asyncio.sleep`, which makes cancel testable).
   - The registry returns `FakeToolModel` when `settings.fake.agent_fake_model`. The script is picked by the `#script:<name>` first line of the **latest human message**. Expose `select_script(messages)` so the model node can pass it in. The default is `default.json` (one `replace_slides` with 4 slides, then "Done.").
4. `is_context_overflow(exc) -> bool`: port MA `stream.is_context_overflow` (its message markers) and also match `BadRequestError` with `context_length_exceeded`.

**Acceptance**:
- [ ] The respx test shows that `reasoning_content` arrives in `additional_kwargs`
- [ ] Effort mapping tests pass for both providers
- [ ] The fake model works with `bind_tools`

**Verify**: `uv run pytest tests/unit/test_models.py -q`

---

<a id="t063"></a>
### T063 · Agent profiles

**Depends on**: T003 · **Parallel**: yes · **Size**: S

**Read first**: research.md R20 (the table); `MAS/services/agent_profiles.py`; `MA/tests/test_agent_profiles.py`

**Files**: create `BE/agent/profiles.py` and `BT/unit/test_profiles.py`

**Steps**:

1. Port the `AgentProfile` dataclass with the same field names. Drop `preload_mcp_groups` and the Work and Cleverso blocks. Add:
   - `prompt_name: str`
   - `default_skills: frozenset[str]`
   - `document_tools: bool = True`
   - `allowed_formats: frozenset[Format]`
2. Define `DECK`, `DOCUMENT`, `WEBPAGE`, `SOCIAL`, `ASSISTANT`, and `IMPORT` exactly per the R20 table. `PROFILES: dict[str, AgentProfile]` and `profile_for_format(format) -> AgentProfile` (presentation → DECK, and so on).
3. Keep `cap_effort`, `thinking_enabled`, `allows_tool`, and `allows_skill` (with MA's semantics).
4. Port the relevant MA profile tests, and add: `profile_for_format("social").max_effort == "medium"`, and `IMPORT` allows only its 4 tools.

**Acceptance**:
- [ ] Matches the R20 table cell for cell

---

<a id="t064"></a>
### T064 · Prompts v0

**Depends on**: T004 · **Parallel**: yes · **Size**: M (writing)

**Read first**: contracts/agent-tools.md › Profile prompt contract (the 8 rules); `MA/prompts/{system.md,date_context.md,context_compact.md,auto_title.md,skills_index.md,session_web_search_on.md,session_web_search_off.md}`; ux.md §6.6 (what users see)

**Files**: create `backend/prompts/{deck,document,webpage,social,assistant,date_context,context_compact,auto_title,skills_index,session_web_search_on,session_web_search_off,wrap_up,nudge_continue,nudge_empty}.md`

**Steps**:

1. Copy these MA files **verbatim**, then remove any Cleverso or Work lines: `date_context`, `context_compact`, `auto_title`, `skills_index`, `session_web_search_on`, `session_web_search_off`.
2. Write `deck.md` (about 60–100 lines) in this structure:
   - **Who you are**: an agent that builds presentation decks with tools.
   - **The 8 contract rules**, rephrased as instructions.
   - **The slide schema in brief**: the 7 layouts, their fields, and when to use each.
   - **Writing style**: concrete, short, and in the user's language.
   - **Variables**: `{format}`, `{locale_name}`, `{today}`.
   - **Two short examples**: one first-draft turn (a `replace_slides` call shown as JSON), and one edit turn (`update_slide`).
3. `document.md`, `webpage.md`, and `social.md` follow the same structure, with format-specific guidance:
   - documents: more `points`, `title` sections, fewer `hero`
   - webpage: hero first, then sections with buttons
   - social: 1–3 slides, short text
4. `assistant.md`: help with an existing document. Prefer targeted edits.
5. `wrap_up.md` (MA's wrap-up text: summarize what you did and what's left, without tools), `nudge_continue.md` (MA auto-continue text), and `nudge_empty.md` (MA empty-reply text).
6. Every prompt is **English**. The model replies in the user's language because of rule 1. Arabic example lines inside the prompts are fine.

**Acceptance**:
- [ ] Every contract rule appears in each profile prompt (check with a test that greps for the key phrases, `BT/unit/test_prompt_rules.py`)
- [ ] No "Cleverso", "Work", or `run_python` mentions

---

<a id="t065"></a>
### T065 · Port budget logic and message conversion

**Depends on**: T054, T062 · **Parallel**: no · **Size**: M

**Read first**: `MAS/services/agent/budget.py` (all of it); `MAS/services/context_compact.py` › `estimate_tokens`, `estimate_message_tokens`; IMPLEMENTER §6.3

**Files**: create `BE/agent/budget.py` and `BE/agent/msgconv.py`

**Steps**:

1. Port `budget.py` **unchanged in logic**, with the same public names:
   - `prompt_tokens`, `completion_budget`, `clip_old_tool_payloads`, `fit_prompt_to_context`
   - `tool_keep_priority` (rename to public), `trim_tools_for_context`, `schema_tokens_for`, `downgrade_effort`, `step_budget`
   - `estimate_tokens` and `estimate_message_tokens`, which move here from context_compact
2. `tool_keep_priority`: replace MA's tool names with ours. Highest priority (never trimmed): the document tools and `ask_user`. Then `read_attachment`, `search_attachments`, `read_skill`, `remember`. The lowest are `mcp_*`, `web_*`, and `fetch_url`.
3. `msgconv.py`: `to_dicts(msgs)` and `from_dicts(dicts)` (IMPLEMENTER §6.3). **Preserve `id`** on round-trip, because compaction needs ids to remove messages. Put the id in `dict["id"]` and restore it.
4. `step_budget(settings, effort)`: map MA effort to steps using MA's settings (`settings.agent.*`). Make sure `fast→low` yields at least 4 and `deep→xhigh` at most 16.

**Acceptance**:
- [ ] The T054 budget and clipping tests pass
- [ ] A round trip through `to_dicts` and `from_dicts` keeps ids, tool_calls, and tool_call_id

**Verify**: `uv run pytest tests/unit/test_budget.py -q`

---

<a id="t066"></a>
### T066 · Port context compaction

**Depends on**: T065 · **Parallel**: no · **Size**: M

**Read first**: `MAS/services/context_compact.py` (`prepare_model_messages`, `_summarize`, `_format_turns`, `CompactResult`); `MA/prompts/context_compact.md`

**Files**: create `BE/agent/compact.py`

**Interface**:

```python
@dataclass(frozen=True)
class CompactPlan:
    remove_ids: list[str]        # message ids folded into the summary
    summary: str                 # new rolling summary (old summary + folded turns)

async def maybe_compact(messages: list[BaseMessage], summary: str, *, settings: Settings,
                        small_model: BaseChatModel, notify: Callable[[str], None] | None) -> CompactPlan | None
```

**Steps**:

1. Port the policy: when `estimate_message_tokens(to_dicts(messages)) + overhead > settings.agent.compact_threshold × context_window`, fold every turn except the last `settings.agent.keep_recent_turns` into the summary, using `context_compact.md` and the small model. Below the threshold, return `None`.
2. **Never** split an AIMessage with tool_calls from its ToolMessages. Fold whole turns, where a turn is a HumanMessage up to the next HumanMessage.
3. Call `notify("status.compacting")` **before** the model call. The node maps it to a `status` event.
4. If summarization fails, log a WARNING and return `None`. The fit and clip step in `prepare` still protects the context (MA's fallback behavior).

**Acceptance**:
- [ ] The T054 compact tests pass
- [ ] Turns are never split

**Verify**: `uv run pytest tests/unit/test_compact.py -q`

---

<a id="t067"></a>
### T067 · Port the guards

**Depends on**: T065 · **Parallel**: no · **Size**: M

**Read first**: `MAS/services/runaway.py`; `MAS/services/agent/repeats.py`; `MAS/services/agent/replies.py` (`handle_text_only_reply`, `_looks_like_tool_history_echo`, `_looks_like_prose_user_question`, `TextOnlyOutcome`); `MAS/services/agent/tool_round.py` (`_FAILED_CALL_LIMIT`, `_exact_call_key`, `_unparseable`, `_cut_off_result`); `MAS/services/tools/registry.py` (`broken_json_hint`, `argument_error`)

**Files**: create `BE/agent/guards.py`

**Interface** (all pure functions on dicts or strings):

```python
def is_runaway_repetition(text: str) -> bool                      # port
def trim_runaway_tail(text: str, *, keep_repeats: int = 8) -> str # port
def tool_fingerprint(name: str, raw_args: str) -> str             # port (repeats.py)
def repeat_count(history: list[str], fp: str) -> int              # port
FAILED_CALL_LIMIT = 2                                             # port
def refuse_repeat_message(name: str) -> str                       # "Refused: this exact call already failed twice. Change the arguments or try another approach."
def broken_json_message(name: str, raw: str, *, cut_off: bool) -> str   # port argument_error + broken_json_hint + _cut_off_result; replace_slides hint text from contracts/agent-tools.md
def missing_args_message(name: str, missing: list[str]) -> str    # port wording

@dataclass(frozen=True)
class TextOnlyDecision:                                           # port of TextOnlyOutcome, generic
    kind: Literal["done", "retry_empty", "nudge_echo", "nudge_prose_ask", "nudge_schema_only"]
    nudge_text: str | None
    lower_effort: bool
def decide_text_only(content: str, *, loop: LoopFlags, settings: Settings, deferred_mcp: bool,
                     saw_reasoning: bool, last_finish: str | None) -> TextOnlyDecision
```

**Steps**:

1. Port each function, keeping the MA thresholds and wording. Remove the Cleverso-specific nudge text. The schema-only nudge says "Continue now: call the connector tool you just loaded, or ask_user."
2. `decide_text_only` must **not** mutate anything. The `guards` node (T072) applies its result.

**Acceptance**:
- [ ] The T054 guard tests pass

**Verify**: `uv run pytest tests/unit/test_guards.py -q`

---

<a id="t068"></a>
### T068 · Context message builder

**Depends on**: T014, T063 · **Parallel**: yes · **Size**: S

**Read first**: contracts/agent-tools.md › Context message (the JSON shape)

**Files**: create `BE/agent/context.py` and `BT/unit/test_context.py`

**Interface**:

```python
def build_context_message(*, profile: AgentProfile, locale: str, draft: DocumentState,
                          template: TemplateOut | None, attachments: list[AttachmentBrief],
                          steps_remaining: int) -> SystemMessage
```

**Steps**:

1. Render the exact JSON from the contract (camelCase), wrapped as:

```
<document_context>
{json}
</document_context>
```

   It goes in a **SystemMessage placed right before the latest HumanMessage** in `llm_input`. Don't put it in the main system prompt; that keeps prompt caching stable.
2. Slides include their `id` and every non-empty field. `notes` are included, cut to 500 characters each.
3. `template` is None until US3 (T114 fills it), and `attachments` is empty until US6.
4. Test: the JSON parses, the slide ids are present, and the size of a 60-slide doc is under 40k characters (cut slide bodies to 600 characters if not).


**Acceptance**:
- [ ] `build_context_message` output parses as JSON inside `<document_context>` and contains every slide id
- [ ] A 60-slide document's context is under 40k characters

**Verify**: `uv run pytest tests/unit/test_context.py -q`

---

<a id="t069"></a>
### T069 · Document tools

**Depends on**: T060, T061, T071 · **Parallel**: no · **Size**: M

**Read first**: IMPLEMENTER §6.6 and §6.8; contracts/agent-tools.md › Shared rules

**Files**: create `BE/agent/tools/document.py` and `BE/agent/tools/__init__.py` (the `build_tools` skeleton)

**Design**: the document tools are **not executed by LangChain's tool runner**. The `tools` node (T072) calls `reducers.apply` itself, because it owns `state.draft`. This module provides only:

```python
DOCUMENT_TOOL_NAMES = frozenset({"set_title","set_theme","add_slide","update_slide","delete_slide","move_slide","replace_slides"})
def document_tool_specs(theme_ids: list[str]) -> list[BaseTool]   # StructuredTool with args_schema, func raises NotImplementedError (schema only)
```

and in `tools/__init__.py`:

```python
@dataclass
class ToolSet:
    specs: list[BaseTool]                              # what bind_tools sees
    runners: dict[str, Callable[..., Awaitable[str]]]  # non-document tools: name → async fn(args_model) -> str
def build_tools(profile, ctx: TurnContext, settings, *, theme_ids, web_search: bool, plan: str) -> ToolSet
```

**Steps**:

1. `document_tool_specs` builds a `StructuredTool.from_function(name=…, description=<args model docstring>, args_schema=<model>, func=_schema_only)` for each tool. For `set_theme`, put the theme id list in the description ("One of: paper, ink, …") so the model sees the valid values.
2. `build_tools` returns the document specs plus (for now) `ask_user` (T070). Later cards add their tools here behind the profile checks (`profile.allows_tool(name)`).

**Acceptance**:
- [ ] `build_tools(DECK, …).specs` names equal the document tools plus `ask_user`
- [ ] The JSON schema the model sees has camelCase field names (check `tool.tool_call_schema.model_json_schema()`)

---

<a id="t070"></a>
### T070 · `ask_user` (interrupt)

**Depends on**: T060 · **Parallel**: no · **Size**: M

**Read first**: `MAS/services/tools/ask_user.py` (all of it: limits, `_is_process_step_option`, `_looks_like_action_menu`, `_clean_options`, `_clean_fields`, `_ACTION_MENU_ERROR`); `MA/tests/test_ask_user_choosers.py`; contracts/sse-events.md › ask_user; IMPLEMENTER §6.6

**Files**: create `BE/agent/tools/ask_user.py` and `BT/unit/test_ask_user.py`

**Interface**:

```python
def validate_ask(args: AskUserArgs) -> str | None          # None if ok, else model-facing error (port MA rules)
def ask_payload(call_id: str, args: AskUserArgs) -> dict    # {"kind":"ask_user","toolCallId":..., "question":..., "options":..., "fields":..., "allowFreeText":...}
def answer_to_tool_text(args: AskUserArgs, answer: dict) -> str   # e.g. 'User answered: grade="5", length="8 slides"'
```

**Steps**:

1. Port MA's cleaning and validation: the option and field limits, and the rejection of action-menu and process-step options with MA's error text.
2. These functions are pure. The `tools` node does `answer = interrupt(ask_payload(...))`, then `answer_to_tool_text(...)`.
3. Port the MA chooser tests.

**Acceptance**:
- [ ] The MA chooser scenarios pass
- [ ] 65 options are rejected with a model-facing error (not an exception)

---

<a id="t071"></a>
### T071 · Approval policy and cards

**Depends on**: T060, T061 · **Parallel**: no · **Size**: M

**Read first**: research.md R22 (the table); contracts/sse-events.md › approvalCard; `MAS/services/agent/helpers.py` (`needs_approval`, `always_needs_approval`)

**Files**: create `BE/agent/approvals.py` and `BT/unit/test_approvals.py`

**Interface**:

```python
Policy = Literal["always", "ask", "never"]
def policy_for(name: str, args: BaseModel, *, state: TurnState, overrides: dict[str, Policy]) -> Policy
def approval_card(name: str, args: BaseModel, *, state: TurnState, credits_for_image: int) -> dict   # ApprovalCard dict (camelCase)
def is_preapproved(name: str, state: TurnState) -> bool   # name in state["approved_tools"]
```

**Steps**:

1. The R22 defaults:
   - `replace_slides` → `ask` if `state["manual_edits_since_agent"] > 0`, otherwise `always`
   - `delete_slide` → `ask` once 3 or more `delete_slide` calls are already **in this turn** (count the ToolMessages since the last HumanMessage)
   - `generate_image` → `ask`
   - names starting with `mcp_` that are flagged as write tools (T210 provides `is_write_tool(name)`; until then treat every `mcp_` name as write) → `ask`
   - everything else → `always`
2. `overrides` comes from the platform admin later (T219). For now pass `{}`.
3. Cards:
   - `replace_slides`: `before` = the current draft's `SlideSummary` list (`{id,index,layout,title}`), `after` = the summaries of the new slides, plus `manualEditsLost`
   - `delete_slides`: the slides that will be removed
   - `generate_image`: the prompt, slide id, and credits
   - `mcp_write`: the server, tool, and arguments preview (the first 6 lines of pretty JSON)
4. Tests: each policy branch, and each card shape against contracts/sse-events.md.


**Acceptance**:
- [ ] Each R22 default policy branch has a passing test
- [ ] Each of the 4 card shapes validates against `ApprovalCard` (T016)

**Verify**: `uv run pytest tests/unit/test_approvals.py -q`

---

<a id="t072"></a>
### T072 · Graph nodes

**Depends on**: T062–T071 · **Parallel**: no · **Size**: L (split into 2 PRs if needed: (a) prepare/model/guards, (b) tools/wrap_up/commit/title)

**Read first**: plan.md › Agent Design (node table and diagram); IMPLEMENTER §6 (all of it); `MAS/services/agent/service.py` (the main loop: how the step budget, auto-continue, overflow retry, and wrap-up interact)

**Files**: create `BE/agent/nodes/{__init__,prepare,model,guards,tools,wrap_up,commit,title}.py` and `BE/agent/system_prompt.py`

**Steps** (node specs; each node returns only the keys it changes):

**`system_prompt.py`**: `build_system_prompt(profile, ctx, *, memory_block, skills_index, connector_instructions, web_search) -> str`. Port MA `agent/prompt.py`, `build_system_prompt`, in this order:
1. the profile prompt (`load_prompt(profile.prompt_name, …)`)
2. `date_context`
3. the memory block (T190; empty for now)
4. the session lines (web on/off)
5. connector instructions (T210)
6. inlined skills
7. the skills index (T197)

Missing pieces are passed as `""`.

**`prepare`**:
1. If `state["steps_used"] == 0` and this is the first round of the turn, compute the step budget (already in the input). Nothing else.
2. Compaction: `plan = await maybe_compact(messages, summary, …, notify=writer)`. If there's a plan, return `{"messages": [RemoveMessage(id=i) for i in plan.remove_ids], "summary": plan.summary}`, and continue building `llm_input` from the remaining messages.
3. Build `llm_input`:
   - `[SystemMessage(system_prompt)]`
   - `+ ([SystemMessage("<summary>…</summary>")] if summary)`
   - `+ messages` (with the context message from T068 inserted right before the last HumanMessage)
4. Fit: convert to dicts, run `fit_prompt_to_context` and `clip_old_tool_payloads` on **this copy only**, then convert back. `messages` stays untouched.
5. Trim tool specs (`trim_tools_for_context`) and store the kept names in `state["tool_names"]` (add this key to `TurnState` in T073).
6. Return `{"llm_input": …, "tool_names": …}` (and the compaction keys if any).

**`model`**:
1. `chat = registry.chat(effort=state["effort"], thinking=…, max_tokens=min(completion_budget(...), loop.max_tokens_cap or inf)).bind_tools([specs filtered by tool_names])`
2. `msg = await chat.ainvoke(state["llm_input"])`. Streaming to the client happens through `stream_mode="messages"` automatically. Don't stream by hand.
3. On context overflow (`is_context_overflow`), if `loop.overflow_retries < 2`:
   - clip harder (`keep=1, chars=600` on the second retry)
   - set `max_tokens_cap = max(2048, max_tokens // 2)`
   - increment `overflow_retries`
   - return `{"loop": …, "llm_input": <clipped>, "final": None}`
   - route back to `model` (the conditional edge in T073 checks `loop["retry_model"]`)
   - if retries are exhausted → raise `TurnFailed("context_overflow")`
4. Other exceptions (after LangChain's retries) → `TurnFailed("upstream_unreachable" | "provider_auth" | "provider_rate_limited")`, mapped from the status code.
5. Return `{"messages": [msg], "usage": add(state.usage, msg.usage_metadata)}`.

**`guards`**:
1. The last AIMessage `m`:
   - if `is_runaway_repetition(m.content)` → replace it with the trimmed content (`AIMessage(id=m.id, content=trim…)`), set `final="cut"`, route to `commit`
   - if `m.tool_calls` or `m.invalid_tool_calls` → route to `tools`
2. Otherwise run `decide_text_only(...)`:
   - `done` → `final="text"` → `commit`
   - `retry_*` or `nudge_*` → remove `m` (`RemoveMessage`), append a HumanMessage with the nudge text (mark it `additional_kwargs={"nudge": True}`; T085 hides nudges in the UI), set `lower_effort → effort=downgrade_effort(effort)`, update the loop flags, route to `prepare`
3. **Step cap**: if `steps_used >= max_steps`:
   - `auto_continued` is False → set it True, `max_steps += settings.agent.auto_continue_steps`, append the `nudge_continue` HumanMessage, route to `prepare`
   - otherwise → write `step_limit`, route to `wrap_up`

**`tools`** (**read IMPLEMENTER §6.6 first. No side effects before `interrupt()`**):
1. `m` = the last AIMessage. `calls = m.tool_calls`, `bad = m.invalid_tool_calls`. `asking = any(c.name == "ask_user")`.
2. For each `bad` → `ToolMessage(broken_json_message(...), tool_call_id=id, status="error")`.
3. For each call **in order**:
   - **a.** If `asking` and `name != "ask_user"` → ToolMessage "Skipped: waiting for the user's reply after ask_user. Do not call more tools until they answer." (MA wording)
   - **b.** Repeat guard: if the fingerprint failed `FAILED_CALL_LIMIT` times before in this turn (`loop.recent_tool_fps`) → the refuse message.
   - **c.** Parse args with the Pydantic model (a validation error becomes a ToolMessage with the error text). `set_theme` gets the theme-ids context.
   - **d.** Approval: `policy_for(...)`. `never` → "Denied by policy.". `ask` and not preapproved → `decision = interrupt({"kind":"approval","toolCallId":id,"name":name,"arguments":raw,"approvalCard":card})`. On `deny` → "Denied by user."; on `allow_thread` → add to `approved_tools`.
   - **e.** `ask_user` → `validate_ask`, then `answer = interrupt(ask_payload(...))`, then `answer_to_tool_text`.
   - **f.** Document tool → `out = reducers.apply(draft, name, args)`. If `out.ok`, set `draft = out.state`, add `changed_slide_ids`, and `writer({"type":"doc_patch","toolCallId":id,"ops":out.ops,"changedSlideIds":out.changed_slide_ids,"draftVersion":n})`. Emit `doc_patch` **after** all interrupts in this node have returned, by collecting patches in a local list and writing them at the end of the node. Then the ToolMessage gets `out.message`.
   - **g.** Other tool → `await toolset.runners[name](args)`. Exceptions become `"Error: <Type>: <msg>"`.
   - **h.** Track the fingerprint, and on failure append it to `recent_tool_fps`.
4. Increment `steps_used` by 1 if any call was "charged" (MA rule: setup tools such as `read_skill` and `list_mcp_tools` are not charged; use `settings.agent.uncharged_tools`).
5. Return `{"messages": tool_messages, "draft": …, "changed_slide_ids": …, "steps_used": …, "loop": …, "approved_tools": …}`.

**`wrap_up`**: `registry.chat(effort="low").ainvoke(llm_input + [HumanMessage(load_prompt("wrap_up"))])` with **no tools**. Append the result, set `final="cap"`.

**`commit`**: **does not write the database**. The worker writes it (T075). That keeps the graph testable with in-memory savers. It only sets `state["final"]` if it's missing. *(The node exists so the graph has a single clear end point.)*

**`title`**: if `ctx` says this is the thread's first turn (`runtime.context.first_turn`, which you add to `TurnContext`), call the small model with `auto_title.md` (port MA `auto_title._clean_title`, max 60 characters), and `writer({"type":"thread_title","title":…})`. The worker saves it.

**Acceptance**:
- [ ] The T055 cases pass (with T073 and T074)
- [ ] No database or Redis access inside nodes (grep the files for `session` and `redis`; there should be none)

**Verify**: `uv run pytest tests/unit/test_graph.py -q`

---

<a id="t073"></a>
### T073 · Build the graph

**Depends on**: T072 · **Parallel**: no · **Size**: M

**Read first**: IMPLEMENTER §6.2; plan.md › Graph diagram

**Files**: create `BE/agent/state.py` and `BE/agent/graph.py`

**Steps**:

1. `state.py`: `TurnState`, `LoopFlags`, and `TurnContext` exactly as in IMPLEMENTER §6.2, plus `tool_names: list[str]` and `first_turn: bool` (in context).
2. `graph.py`:

```python
def build_graph(profile: AgentProfile, *, checkpointer, store, registry: ModelRegistry,
                settings: Settings, toolset_factory: Callable[[TurnContext], ToolSet]):
    g = StateGraph(TurnState, context_schema=TurnContext)
    g.add_node("prepare", prepare); g.add_node("model", model); g.add_node("guards", guards)
    g.add_node("tools", tools); g.add_node("wrap_up", wrap_up); g.add_node("commit", commit); g.add_node("title", title)
    g.add_edge(START, "prepare"); g.add_edge("prepare", "model")
    g.add_conditional_edges("model", route_after_model, {"retry": "model", "guards": "guards"})
    g.add_conditional_edges("guards", route_after_guards, {"tools": "tools", "prepare": "prepare", "commit": "commit", "wrap_up": "wrap_up"})
    g.add_edge("tools", "prepare"); g.add_edge("wrap_up", "commit"); g.add_edge("commit", "title"); g.add_edge("title", END)
    return g.compile(checkpointer=checkpointer, store=store)
```

3. Pass the dependencies to the nodes with `functools.partial` or a small `Deps` object bound by closure. **Not** through state.
4. `GraphCache`: one compiled graph per `profile.id` per process.

**Acceptance**:
- [ ] T055 passes end to end with `InMemorySaver`

---

<a id="t074"></a>
### T074 · Event emitter

**Depends on**: T016, T073 · **Parallel**: no · **Size**: M

**Read first**: IMPLEMENTER §6.5; contracts/sse-events.md (every event); `MAS/services/chat_turn.py` (`_collect`, `_seal_open_reasoning`, `_close_open_tools`)

**Files**: create `BE/agent/emit.py` and `BT/unit/test_emit.py`

**Interface**:

```python
class EventSink(Protocol):
    async def emit(self, event: dict) -> str: ...     # returns stream id

class RedisSink:  # XADD turn:{id} * data <json>; MAXLEN ~ 5000; EXPIRE set on terminal (T075)
class ListSink:   # tests

class TurnEmitter:
    def __init__(self, sink: EventSink): self.blocks: list[dict] = []; self.text_parts: list[str] = []
    async def handle(self, mode: str, chunk: Any) -> None         # maps one astream item → 0..n events, also folds into blocks via collect()
    async def emit(self, event: dict) -> None                      # validate with turn_event_adapter, then sink.emit + collect
    def close_open(self) -> None                                   # port _close_open_tools
```

**Mapping rules**:

| Stream input | Event(s) |
|---|---|
| `messages`, `AIMessageChunk` from node `model` with `content` | `text_delta` |
| the same chunk with `additional_kwargs.reasoning_content` | `reasoning_delta` |
| `tool_call_chunks` | `tool_call_delta` with the accumulated `argumentsChars` per index (send at most one per 250 ms per index) |
| `messages` from nodes other than `model` (e.g. `wrap_up`, `title`) | text from `wrap_up` streams as `text_delta`. **Ignore `title`.** |
| `updates`: `{"model": {"messages":[AIMessage]}}` | `tool_call` for each `tool_calls` entry (with `arguments` as a JSON string) |
| `updates`: `{"tools": {"messages":[ToolMessage…]}}` | `tool_result` (`ok = status != "error"` and content doesn't start with "Error:", "Refused:", or "Denied") |
| `updates`: `{"__interrupt__": (Interrupt,)}` | the `ask_user` event, or `tool_approval`, from `value["kind"]`. Then `waiting_input` (with `expiresAt` from the worker). |
| `custom` | passed through after validation (`doc_patch`, `status`, `memory_saved`, `skill_loaded`, `step_limit`, `thread_title` (worker-only: not sent to the client), …) |

**Blocks**: port `_collect` into `collect(event, blocks, text_parts)`, extended for `ask_user`, `tool_approval`, `memory_saved`, `skill_loaded`, `step_limit`, and `doc_patch` (it adds `changedSlideIds` to the turn's slide set). This is the `messages.blocks` format in data-model.md.

**Hidden messages**: HumanMessages with `additional_kwargs.nudge` never produce events.

**Acceptance**:
- [ ] Unit tests feed a recorded `astream` list and assert the exact event list and blocks
- [ ] Every emitted event validates against `TurnEvent`

---

## Worker, service, API (T075–T080)

<a id="t075"></a>
### T075 · Celery `turn` task

**Depends on**: T073, T074, T039 · **Parallel**: no · **Size**: L

**Read first**: plan.md › Interrupt and resume; data-model.md › turns, pending_inputs, the Turn state machine; IMPLEMENTER §5.6 and §6.4

**Files**: create `BE/worker/tasks/turn.py`, `BE/worker/turn_runtime.py` (shared with resume), and `BE/services/leases.py`

**Steps**:

**`leases.py`**:
- `acquire(redis, doc_id, turn_id, ttl_ms=120_000) -> bool` (`SET NX PX`)
- `renew(redis, doc_id, turn_id, ttl_ms)` (Lua: renew only if the value equals `turn_id`)
- `release(redis, doc_id, turn_id)` (Lua compare-and-delete)
- `holder(redis, doc_id) -> str | None`

**`turn_runtime.run_graph(turn_id, input_or_command)`** does the shared work:
1. Load the turn, document, and thread with `system_session` (the worker doesn't know the workspace yet). Then open `scoped_session(workspace_id)` for every later read and write.
2. Set the turn to `running` and `started_at` if it isn't set yet. Emit `turn_started` (first run only).
3. Build the `TurnContext` and the graph (from the cache), and open `langgraph_persistence`.
4. Start a **heartbeat** task: every 20 s, `renew` the lease, set `turns.heartbeat_at=now()` (the column is in data-model.md; add it to the T022 model and migration if it's missing), and check `redis.get(f"turn:{id}:cancel")`. If it is set, cancel the main task.
5. `async for mode, chunk in graph.astream(...): await emitter.handle(mode, chunk)`.
6. **Outcomes**:
   - **Interrupt seen** → insert a `pending_inputs` row (`expires_at=now+30min`), set the turn to `waiting_input`, emit `waiting_input`, renew the lease with a TTL of 31 min, stop the heartbeat, and return. **Don't release the lease or refund.**
   - **Normal end** → `commit_turn(...)` (below), then emit `done` and `turn_committed`, then `EXPIRE turn:{id} 3600`, then release the lease.
   - **CancelledError** → refund, set the turn to `cancelled(user)`, emit `turn_cancelled`, release.
   - **TurnFailed(code)** or any other exception → refund, set the turn to `failed(code|internal)`, emit `turn_failed` with `retryable` from `RETRYABLE`, release. Log the traceback.

**`commit_turn`** runs in **one** `scoped_session` transaction:
1. Reload the doc `FOR UPDATE`. If `version != base_version` → `TurnFailed("version_conflict")`.
2. If `draft` differs from the stored content: update the document (title, theme_id, content, `version+1`, `manual_edits_since_agent=0`), and insert `document_revisions` (`source='agent_turn'`, `turn_id`).
3. Insert the assistant `messages` row with `text`, `blocks`, and `slide_ids`. The user message row is inserted by the service at enqueue time (T078).
4. Compute the credits with `credits_for_usage(...)`, call `ledger.settle(...)`, and update the `turns` row: status `committed`, usage, cost, latency, `committed_version`.
5. If there's a `thread_title` from the emitter → update `threads.title`.

**Celery wrapper**: `@app.task(name="docu.turn", queue="turns", acks_late=True)` with `def turn(turn_id: str) -> None: asyncio.run(run_graph(UUID(turn_id), None))`. The initial input is built inside `run_graph` from the turn row: user text, effort, skill, web_search, and the doc.

**Acceptance**:
- [ ] T057 passes (cases 1, 2, 3, 5 together with T077)
- [ ] T056 cases 1, 2, 4 pass together with T076

---

<a id="t076"></a>
### T076 · Celery `resume` task

**Depends on**: T075 · **Parallel**: no · **Size**: S

**Files**: create `BE/worker/tasks/resume.py`

**Steps**:

1. `@app.task(name="docu.turn_resume", queue="turns")` with `def resume(turn_id: str, tool_call_id: str) -> None`.
2. Load the `pending_inputs` row (it must have `answered_at` set and `answer` filled by the API, T079). Build `Command(resume={interrupt_id: answer})`, where the interrupt id is stored in `pending_inputs.payload["interruptId"]`. **The emitter must include that id when it records the pending row (T075).**
3. Call `run_graph(turn_id, Command(...))`. Emit to the same stream key (it continues).
4. Before running, set the turn to `running` and emit `status` "Resuming…".

**Acceptance**:
- [ ] T056 cases 1–4 pass

---

<a id="t077"></a>
### T077 · Turn reaper and interrupt expiry

**Depends on**: T075 · **Parallel**: no · **Size**: S

**Files**: create `BE/worker/tasks/turn_reaper.py` and `BE/worker/tasks/interrupt_expiry.py`, and register them in the beat schedule (every 30 s and every 60 s)

**Steps**:

1. **Reaper** (`system_session`): `running` turns with `heartbeat_at < now - 90s` become `failed(worker_lost)`. Refund, release the lease (force delete if the holder matches), and emit `turn_failed`.
2. **Expiry**: `waiting_input` turns whose pending input has `expires_at < now` become `cancelled(expired)`. Refund, release, and emit `turn_cancelled` with reason `expired`.
3. Both are idempotent (a status check inside the UPDATE … WHERE).

**Acceptance**:
- [ ] T056 case 5 and T057 case 5 pass

---

<a id="t078"></a>
### T078 · Turn service

**Depends on**: T075, T034 · **Parallel**: no · **Size**: M

**Files**: create `BE/services/turns.py` and `BE/services/threads.py`

**Interface**:

```python
async def start_turn(ctx: WorkspaceCtx, *, thread_id, text, attachment_ids, effort_ui, skill, web_search) -> UUID
async def create_thread_and_turn(ctx, *, prompt, format, template_id, attachment_ids, effort_ui, skill, web_search) -> tuple[thread_id, document_id, turn_id]
async def cancel(ctx, turn_id) -> None
async def submit_input(ctx, turn_id, *, tool_call_id, decision, answers) -> None
```

**Steps for `start_turn`**:
1. Check permission `can(ctx,"doc.edit",doc)` (403) and `require_verified`.
2. Effort: map the UI value with `EFFORT_UI_TO_MA`, then `profile.cap_effort`, then the plan cap (T178 later; until then no cap).
3. Lease: `leases.holder(doc)` held → 409 `doc_busy`.
4. Reserve: `ledger.reserve(estimate_reservation(...))`. If short → 402 `insufficient_credits`.
5. Insert the `turns` row (`queued`, profile, effort, `prompt_version_id` = the active version or the file-default sentinel, `base_version`) and the user `messages` row (`text`, `attachment_ids`).
6. `leases.acquire(doc, turn)`. If acquiring fails (a race) → refund and 409.
7. `turn.delay(str(turn_id))` **after** the transaction commits: use `session.info["after_commit"]` hooks or call it after the `async with`.

**`create_thread_and_turn`**:
- creates a document with one placeholder `title` slide (title = the first 60 characters of the prompt, cleaned)
- theme = the template's theme, or `paper`
- `format`, and a thread linked to the template
- then calls `start_turn`

**`cancel`**: `SET turn:{id}:cancel 1 EX 300`. If the turn is still `queued` (no worker yet), mark it `cancelled` directly and refund.

**`submit_input`**:
1. The turn is `waiting_input`, and the user started the turn (`turn.answer` permission).
2. Lock the `pending_inputs` row `FOR UPDATE`. It must have no `answered_at` and not be expired (409 otherwise).
3. Validate the answer against the payload: options must be one of the listed ones unless `allowFreeText`, and fields must match their keys.
4. Store it, then `resume.delay(...)`.

**Acceptance**:
- [ ] The service-level paths in T057 and T056 pass

---

<a id="t079"></a>
### T079 · Turn and thread routes (US1 subset)

**Depends on**: T078 · **Parallel**: no · **Size**: M

**Read first**: contracts/rest-api.md › Threads, turns, messages; Models

**Files**: create `BE/api/routers/{threads,turns,models}.py`, `BE/domain/api/{threads,turns}.py`, and `BT/integration/test_turn_routes.py`

**Steps**: implement **only these rows**, exactly as in the contract:
- `POST /v1/threads` (201 `{threadId, documentId, turnId}`)
- `POST /v1/threads/{id}/turns` (202 `{turnId}`)
- `GET /v1/turns/{id}`
- `POST /v1/turns/{id}/cancel` (202)
- `POST /v1/turns/{id}/resume` (202)
- `GET /v1/threads/{id}/active-turn`
- `GET /v1/models`

**Notes**:
- Rate limit turns at 20/min per user and 200/hour per workspace (T036).
- `GET /v1/models` returns `{efforts:["fast","standard","deep"] filtered by profile/plan caps, default:"standard", thinking}`.

**Acceptance**:
- [ ] Every status code in the contract rows is covered by a test

---

<a id="t080"></a>
### T080 · SSE relay

**Depends on**: T058, T079 · **Parallel**: no · **Size**: M

**Read first**: contracts/sse-events.md › Transport; `MAS/api/routes/chat.py` (`_sse_from_job`, `iter_job_sse_frames`, `SSE_HEARTBEAT_SEC`)

**Files**: create `BE/api/sse.py`

**Steps**:

1. `GET /v1/turns/{id}/events` checks `doc.view` permission (404 otherwise). It returns `EventSourceResponse(gen(), ping=None)`. Write the heartbeat yourself, as MA does.
2. `gen()`:
   - `last = request.headers.get("last-event-id") or "0-0"`
   - loop: `XREAD BLOCK 15000 COUNT 100 STREAMS turn:{id} last`
   - for each entry, yield `{"id": entry_id, "data": entry["data"]}` and set `last = entry_id`
   - if the event type is terminal or `waiting_input` → return
   - when XREAD times out, yield the comment `": ping\n\n"` (MA heartbeat)
   - stop when the client disconnects (`await request.is_disconnected()`)
3. Key missing, or the turn is terminal with `finished_at` over 1 h ago → `410`.
4. **Nginx note**: `X-Accel-Buffering: no` header (MA README › proxy notes).

**Acceptance**:
- [ ] T058 passes

---

## Frontend (T081–T087)

<a id="t081"></a>
### T081 · Create screen

**Depends on**: T047, T079, T043, T044 · **Parallel**: yes · **Size**: L

**Read first**: ux.md §5.2 (wireframe and every bullet), §6.2, §4.23, §4.27; `MAF/components/chat/{Composer,ComposerPlusMenu,ModelEffortPicker}.tsx`

**Files**: create `FE/pages/Create.tsx` and `FE/components/chat/{Composer,ComposerPlusMenu,ModelEffortPicker}.tsx` (ported and extended)

**Steps**:

1. Port the MA `Composer` and restyle it to ux.md §5.2: max width 720, auto-grow from 2 to 10 lines, Enter to send, Shift+Enter for a newline, rotating placeholder (3 i18n keys per format), and the send/stop states (§6.2).
2. Port `ComposerPlusMenu`. Its items are Upload file (disabled until T159, with a tooltip "Coming soon"), Choose template (navigates to `/templates?pick=1`), and Import PPTX/DOCX (disabled until T158).
3. Port `ModelEffortPicker` and reduce it to Fast, Standard, and Deep, loaded from `GET /v1/models`. Show no model ids.
4. The `⚙` popover holds the web toggle (hidden until T216) and the skill picker (hidden until T203). Render the button, but hide those items behind the feature flags `web_search` and `skills` (`FE/lib/flags.ts` returns false for now).
5. Format chips (Pill): Presentation, Document, Webpage, Social, plus Import and Polish existing (both disabled until their stories land). Exactly one format is selected.
6. Send: `POST /v1/threads {prompt, format, effort, …}`, then navigate to `/doc/:documentId?turn=:turnId`. The editor attaches to the stream.
7. The suggested templates row and the bottom tabs exist as **slots**: Suggested is filled in T118, and the Recent tabs list documents and threads with T095 and T106. Until then, show skeletons, and empty states once the APIs exist.
8. States: unverified banner (`me.user.emailVerified === false`) and out-of-credits banner (`creditBalance <= 0`), per §5.2.
9. Use every test id listed in §5.2.

**Acceptance**:
- [ ] Matches the ux.md §5.2 wireframe in en and ar at 1440 and 390 widths
- [ ] Keyboard: Tab order goes input → + → ⚙ → effort → send → chips
- [ ] T059 case 1 reaches the editor

---

<a id="t082"></a>
### T082 · SSE client and run manager (port)

**Depends on**: T080, T017 · **Parallel**: no · **Size**: M

**Read first**: `MAF/lib/sse.ts` (`streamChat`, `watchChat`); `MAF/lib/chatRunner.ts` (`startChatRun`, `resumeChatRunIfActive`, `stopChatRun`, `subscribeChatRun`, `getChatRun`, `ChatRunSnapshot`)

**Files**: create `FE/lib/sse.ts` and `FE/lib/turnRunner.ts`

**Steps**:

1. `sse.ts`: `async function* streamTurnEvents(turnId, {lastEventId, signal}): AsyncGenerator<{id: string, event: TurnEvent}>`.
   - Use `fetch` with `Accept: text/event-stream` and `Last-Event-ID`, parse `id:` and `data:` lines, and ignore comment lines (MA behavior).
   - Reconnect with backoff (0.5 s, 1 s, 2 s, max 5 s) until a terminal event or `waiting_input`. A 410 stops the stream and refetches the turn through `GET /v1/turns/{id}`.
2. `turnRunner.ts` is ported from `chatRunner.ts`, simplified for one active turn per document:
   - `startTurn(docId, turnId)` attaches the stream and stores the last id in `sessionStorage` (`turn:<id>:last`)
   - `attachIfActive(threadId)` calls `GET /v1/threads/{id}/active-turn`, then attaches
   - `stopTurn(turnId)` calls `POST cancel`
   - `subscribe(docId, fn)` for snapshot updates
   - Each event is passed to the turn store (T083).
3. Keep MA's notification hook (`setChatNotifyCopy` becomes `setTurnNotifyCopy`) for T087.

**Acceptance**:
- [ ] Unit test with a mocked fetch stream: events parse, a reconnect resumes from the last id, and comments are ignored

---

<a id="t083"></a>
### T083 · Turn and document store

**Depends on**: T017 · **Parallel**: no · **Size**: M

**Read first**: contracts/sse-events.md › DocOp and the client rule; ux.md §6.3

**Files**: create `FE/features/agent/turnStore.ts`, `FE/features/agent/applyOps.ts`, and their tests

**Interface** (Zustand):

```ts
interface DocTurnState {
  docId: string;
  committed: DocumentState; committedVersion: number;
  draft: DocumentState | null;              // non-null while a turn is active
  turn: { id: string; status: 'running'|'waiting_input'|'done'; baseVersion: number } | null;
  blocks: Block[];                          // live blocks for the current assistant message (same shape as messages.blocks)
  changedRecently: Record<string, number>;  // slideId → timestamp (for glow)
  apply(event: TurnEvent): void;
  view(): DocumentState;                    // draft ?? committed
}
```

**Steps**:

1. `applyOps(state, ops)` is a pure function, one case per DocOp. Unit test each op.
2. `apply(event)`:
   - `turn_started` → `draft = committed` clone, `turn = {...}`
   - `doc_patch` → `draft = applyOps(draft, ops)`, and mark changed slides
   - `text_delta`, `reasoning_delta`, `tool_*` → fold into `blocks`, mirroring backend `collect` (T074). Write it as a TS port of the same function.
   - `turn_committed` → `committed = draft`, `committedVersion = version`, `draft = null`
   - `turn_failed` or `turn_cancelled` → `draft = null` (rollback)
   - `waiting_input` → set the status
3. Changed-slide glow: an entry in `changedRecently` expires after 1200 ms.

**Acceptance**:
- [ ] Unit tests for every op and every terminal path (rollback restores the committed state exactly)

---

<a id="t084"></a>
### T084 · Editor layout

**Depends on**: T018, T083, T047 · **Parallel**: no · **Size**: L

**Read first**: ux.md §5.4 (the wireframe, §5.4.1, §5.4.2, §5.4.3, §5.4.4), §10 (canvas and filmstrip a11y)

**Files**: create `FE/pages/Editor.tsx`, `FE/features/editor/{EditorTopBar,Canvas,Filmstrip,AgentColumn,StatusLine}.tsx`, and `BE/api/routers/documents.py` (**only** `GET /v1/documents/{id}` now; T095 adds the rest)

**Steps**:

1. Backend: `GET /v1/documents/{id}` returns `{document, thread, activeTurnId, permissions}` per the contract (`permissions` from T034 `doc_permissions`).
2. `Editor.tsx`: a full-height grid. Filmstrip 148px, canvas 1fr, agent column 400px (360 between lg and xl). No app shell. On load, fetch the doc and `turnRunner.attachIfActive(threadId)`. If `?turn=` is in the URL, `startTurn`.
3. `EditorTopBar`:
   - Back, Title (read-only text here; inline edit comes in T099), save status (`Saved ✓`, static for now)
   - Buttons History, Patterns, Present, Share, Export: render them **disabled** with a tooltip "Coming soon" until their tasks land
   - Viewer badge when `!permissions.edit`
4. `Canvas`:
   - Render `turnStore.view().slides` stacked with 32px gaps, each `<Slide width={min(1100, canvasWidth-48)}>`.
   - An IntersectionObserver picks the active slide (the one whose center is nearest the viewport center) and updates `activeIndex`.
   - The changed-slide glow class reads `changedRecently`.
   - Region a11y labels per ux §10.
   - The hint "Select a card or element to edit" with `Kbd Esc` sits under the active slide (selection itself comes in T099).
5. `Filmstrip`: number plus a thumbnail (`<Slide width={128}>`), an active border, click to scroll the canvas smoothly to that slide. `listbox`/`option` roles with ↑/↓ keys. Pulse the badge of slides in the current `doc_patch`. ⚠ when the slide has `data-overflow` (from T018).
6. `AgentColumn`: a header (thread title), the thread (T085 fills it), `StatusLine` (ux §5.4.4), and the composer (the small variant of T081's Composer: no chips). Sending calls `POST /v1/threads/{id}/turns`, then `startTurn`.
7. Test ids: every editor id in ux.md §5.4.

**Acceptance**:
- [ ] Slides stream in live during a fake turn, in both languages
- [ ] Scrolling updates the filmstrip, and clicking the filmstrip scrolls the canvas
- [ ] It matches the ux.md §5.4 wireframe at 1440 width

---

<a id="t085"></a>
### T085 · Thread view (blocks, ask_user, approvals)

**Depends on**: T083, T084 · **Parallel**: no · **Size**: L

**Read first**: ux.md §6 (all of it); `MAF/components/chat/{Blocks,ChoicePrompt,ChoiceForm,ApprovalDiffCard,Markdown}.tsx`; contracts/sse-events.md › approvalCard, ask_user

**Files**: create `FE/features/agent/{Thread,UserMessage,AssistantMessage,SlidePreviewRow,AskUserCard,ApprovalCardView}.tsx`, port `FE/components/chat/{Blocks,ChoicePrompt,ChoiceForm,ApprovalDiffCard,Markdown}.tsx`, and add `GET /v1/threads/{id}/messages` (backend, contract row) in `BE/api/routers/threads.py`

**Steps**:

1. Backend: `GET /v1/threads/{id}/messages` is paginated oldest first and returns `{role, text, blocks, slideIds, attachmentIds, createdAt}`.
2. `Thread`: the history (the query) plus the live blocks from `turnStore`. It auto-scrolls to the bottom unless the user has scrolled up (then show a "Jump to latest" pill).
3. `UserMessage`: a bubble per ux §6.1. Edit and rewind come in T103.
4. `AssistantMessage`: render `blocks` in order with the ported `BlockView`, adapted to the §6.3 table.
   - **Thinking**: collapsed, "Thought for {s}s".
   - **Tool blocks**: the human label from §6.6 (i18n `tool.<name>.running|done` with params from the args: `count`, `index` (the slide index found by id in the current doc), `file`, `host`), a spinner or ✓ or ⚠, and expand shows the result text. A finished turn collapses its tools into "N steps ▸".
   - **Chips**: memory and skill.
   - **Errors**: T086.
3. `SlidePreviewRow`: mini thumbnails (`<Slide width={96}>`) of `slideIds` from the committed doc. Clicking one scrolls the canvas.
4. `AskUserCard`: wraps the ported `ChoicePrompt` and `ChoiceForm` (≤ 6 options as pills, otherwise a searchable dropdown, free text, fields form). Submitting calls `POST /v1/turns/{id}/resume {toolCallId, answers}`. Then collapse it to "You chose: …".
5. `ApprovalCardView`: extend `ApprovalDiffCard` with the 4 kinds from ux §6.5. `replace_slides` shows two columns, before and after (numbered titles), with the warning line. Buttons are Allow and Deny, plus a checkbox "Always allow in this thread". They post resume with `decision`.
6. Messages with `additional_kwargs.nudge` are never stored. Nudges never reach the client, so there is nothing to hide.

**Acceptance**:
- [ ] T059 cases 1–3 pass
- [ ] Reloading the page mid-turn shows the history and re-attaches live
- [ ] A finished thread re-renders identically from the stored `blocks`

---

<a id="t086"></a>
### T086 · Turn error UI

**Depends on**: T085 · **Parallel**: no · **Size**: S

**Read first**: contracts/sse-events.md › TurnErrorCode; ux.md §6.3 (the `turn_failed` and `turn_cancelled` rows)

**Files**: create `FE/features/agent/TurnError.tsx` and add the i18n keys `errors.turn.<code>` (en and ar, with real Arabic: write it, or mark it `__TODO_AR__` for T227)

**Steps**:

1. An error block with an icon, the localized message, and `Retry` when `retryable`. Retry re-sends the same user text as a new turn.
2. A cancelled row: "Stopped", or "Expired: no answer in 30 min".
3. `insufficient_credits` shows an `Upgrade` link (to `/settings/billing`).

**Acceptance**:
- [ ] Each of the 9 codes renders (unit test with a fixture per code)

---

<a id="t087"></a>
### T087 · Turn-finished notification (port)

**Depends on**: T082 · **Parallel**: yes · **Size**: S

**Read first**: `MAF/lib/notify.ts` (`ensureNotifyPermission`, `notifyChatDone`)

**Files**: create `FE/lib/notify.ts`

**Steps**:

1. Port the file. Call `ensureNotifyPermission()` the first time the user sends a turn (not on page load).
2. On `turn_committed` while `document.hidden`: notify with the title "Your document is ready" and the body = the doc title. Clicking it focuses the tab. Also prefix the tab title with `✓ ` until the tab is visible again (ux §8).

**Acceptance**:
- [ ] Works in Chrome when the tab is in the background (manual check)

---

## Evals (T088–T089)

<a id="t088"></a>
### T088 · Eval dataset v1 and runner

**Depends on**: T075 · **Parallel**: yes · **Size**: L (half is writing cases)

**Read first**: spec.md SC-002, SC-003; research.md R8 (follow-up); contracts/agent-tools.md › Profile prompt contract

**Files**: create `evals/run.py`, `evals/harness.py`, `evals/datasets/drafts.jsonl`, `evals/datasets/clarify.jsonl`, and `evals/scorers/{tool_validity,language,limits,asks_when_vague,no_template_copy}.py`. Add `evals/pyproject.toml`, or reuse the backend env with `uv run --project backend`.

**Steps**:

1. `harness.py`: run **one turn in-process** with the real graph and `InMemorySaver` against the configured upstream. Return `{final_state, events, usage, latency}`. No database.
2. **drafts.jsonl** has 40 lines: `{id, locale, format, prompt, expect: {min_slides, max_slides, lang}}`. Use 20 en and 20 ar, covering the 4 formats and different domains (school, business, events, personal).
3. **clarify.jsonl** has 10 vague prompts, with `expect: {asks: true}`, plus 5 clear ones with `expect: {asks: false}`.
4. Scorers (each returns 0..1):
   - **tool_validity**: the share of tool calls with no `Error:` result
   - **language**: the share of slide text in the expected script (Arabic-letter ratio over 0.6 for ar)
   - **limits**: title ≤ 10 words and points ≤ 5
   - **asks_when_vague**: an `ask_user` interrupt happened exactly when expected
   - **no_template_copy**: placeholder (always 1; used in US3)
5. `run.py --suite drafts|clarify|all --upload` runs with concurrency 4 and prints a table. With `--upload`, it pushes to LangSmith as a dataset and experiment (`langsmith.evaluate`). It writes `evals/results/<suite>-<date>.json` and compares it with `evals/baseline/<suite>.json`. It exits 1 on a drop of more than 3 points on any scorer.

**Acceptance**:
- [ ] `uv run python evals/run.py --suite drafts` works against a real upstream and produces scores
- [ ] A baseline file is committed

---

<a id="t089"></a>
### T089 · Evals workflow

**Depends on**: T088 · **Parallel**: yes · **Size**: S

**Files**: create `.github/workflows/evals.yml`

**Steps**:

1. Trigger on PRs that change `backend/src/docu/agent/**`, `backend/prompts/**`, `backend/skills/**`, or `evals/**`.
2. Secrets: `UPSTREAM`, `UPSTREAM_API_KEY`, `MODEL`, `LANGSMITH_API_KEY` (environment `evals`).
3. Run `uv run python evals/run.py --suite all --upload`, and post the score table as a PR comment (`marocchino/sticky-pull-request-comment`). Fail the job on a regression.

**Acceptance**:
- [ ] A PR that edits `deck.md` shows the eval table comment
