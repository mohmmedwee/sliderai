# Phase 12: US10, memory and brand (task cards)

Before any card, read [IMPLEMENTER.md](../IMPLEMENTER.md) (§6.7 Store). **Story test**: quickstart.md › US10.

---

<a id="t188"></a>
### T188 · Memory tests (write first)

**Depends on**: T028 · **Parallel**: yes · **Size**: S

**Read first**: research.md R23; data-model.md › LangGraph Store (memories); `MAS/repositories/memory.py` (`MemoryLimitError`, the cap)

**Files**: create `BT/integration/test_memory.py`

**Cases** (real `AsyncPostgresStore`):

1. `remember` 50 times works. The 51st returns a tool error telling the model to `ask_user` which memory to replace.
2. User A's memories are never visible to user B, even in the same workspace.
3. Brand memory `PUT` as an editor → 403. As an admin → 200. Every member's prompt block includes it.
4. `memory_block(user, workspace)` renders "About you:" with the bullets, then "Brand rules for {workspace}:" with the bullets. It is empty when both are empty, and capped at 2,500 characters.
5. `forget` with another user's id → "Error: not_found".
6. REST CRUD: create, edit, delete, and list ordered by `createdAt` desc.


**Acceptance**:
- [ ] Every case listed above is its own test function (`test_<short_name>`)
- [ ] The tests run and **fail for the expected reason** (missing module or not implemented) until the implementation task lands
- [ ] No production code is added in this task

---

<a id="t189"></a>
### T189 · Memory eval (write first)

**Depends on**: T088 · **Parallel**: yes · **Size**: M

**Read first**: spec.md SC-012

**Files**: create `evals/datasets/memory.jsonl` and `evals/scorers/memory_gain.py`

**Steps**:

1. 20 scenarios. Each has `memories: [..]` (e.g. "formal Arabic", "brand color #0B5FFF", "audience: grade 5") and a prompt that doesn't restate them.
2. Run each scenario twice (with and without the memories). Use a **judge** (the small model with a rubric) to check whether the draft follows each memory.
3. `memory_gain` = the compliance rate with memories minus the rate without. SC-012 is proxied as "would have needed fewer follow-up edits". Report both.


**Acceptance**:
- [ ] Every case listed above is its own test function (`test_<short_name>`)
- [ ] The tests run and **fail for the expected reason** (missing module or not implemented) until the implementation task lands
- [ ] No production code is added in this task

---

<a id="t190"></a>
### T190 · Store-backed memory

**Depends on**: T188 · **Parallel**: no · **Size**: M

**Read first**: `MAS/repositories/memory.py` (cap, `prompt_block`); `MA/skills/memory/SKILL.md`

**Files**: create `BE/agent/memory.py` and modify `BE/agent/nodes/prepare.py` (through `system_prompt.py`)

**Interface**:

```python
MEM_NS = lambda user_id: ("memories", str(user_id))
BRAND_NS = lambda ws_id: ("brand", str(ws_id))
async def list_memories(store, user_id) -> list[Memory]
async def add_memory(store, user_id, text, *, kind, source) -> Memory      # raises MemoryLimitError at 50
async def update_memory(store, user_id, memory_id, text) -> Memory
async def delete_memory(store, user_id, memory_id) -> None
async def get_brand(store, ws_id) -> list[str]; async def set_brand(store, ws_id, items, updated_by) -> None
async def memory_block(store, user_id, ws_id) -> str
```

**Steps**:

1. Keys are UUIDv7 strings, and values follow data-model.md. List with `store.asearch(ns, limit=50)`.
2. The `prepare` node passes `memory_block` into the system prompt, when the profile has `use_memory` (every profile except `import`).
3. In the API (T192), the Store comes from a process-wide `AsyncPostgresStore` opened in the app lifespan.


**Acceptance**:
- [ ] T188 cases 2 and 4 pass
- [ ] The system prompt contains the memory block for every profile except `import`

**Verify**: `uv run pytest tests/integration/test_memory.py -q -m db`

---

<a id="t191"></a>
### T191 · `remember` and `forget` tools

**Depends on**: T190, T069 · **Parallel**: no · **Size**: S

**Read first**: contracts/agent-tools.md (`remember`, `forget`, and prompt rule 7); `MAS/services/tools/memory.py`

**Files**: create `BE/agent/tools/memory.py` and modify `backend/prompts/*.md` (add a "Memory" section ported from `MA/skills/memory/SKILL.md` guidance: what to remember and what never to store)

**Steps**:

1. The runners use `get_store()`. `remember` emits the custom event `memory_saved` (with `memoryId` and `text`) through `get_stream_writer()`.
2. At the cap, return MA's limit message adapted: "Error: memory_full: you have 50 memories. Use ask_user to ask which one to replace, then forget it."
3. Register both tools when `profile.use_memory`.

**Acceptance**:
- [ ] T188 cases 1 and 5 pass, and the chip event is emitted

---

<a id="t192"></a>
### T192 · Memory routes

**Depends on**: T190 · **Parallel**: no · **Size**: S

**Read first**: contracts/rest-api.md › Memory

**Files**: create `BE/api/routers/memory.py`

**Steps**: the rows exactly as in the contract. Personal memory needs only `current_user` (no workspace scope). Brand memory needs `workspace_scope`. GET is any member, PUT is admin or owner, and PUT writes an audit entry `brand.updated`.

**Acceptance**:
- [ ] T188 cases 3 and 6 pass

---

<a id="t193"></a>
### T193 · Memory page

**Depends on**: T192 · **Parallel**: yes · **Size**: M

**Read first**: ux.md §5.7; `MAF/pages/MemoryPage.tsx`

**Files**: create `FE/pages/Memory.tsx` (ported and extended)

**Steps**:

1. Port the MA page: the list with inline edit, delete, `+ Add`, and the counter "12 / 50".
2. Add a source chip per item (Saved by agent, Added by you).
3. Add a Brand section with the anchor `#brand`: read-only for non-admins, and an editable list (max 30) for admins.
4. Empty state per ux.md §5.7.


**Acceptance**:
- [ ] Add, edit, and delete persist
- [ ] The counter updates
- [ ] The Brand section is editable only for admins

**Verify**: `pnpm test:e2e -- memory`

---

<a id="t194"></a>
### T194 · "Remembered" chip

**Depends on**: T191, T085 · **Parallel**: yes · **Size**: S

**Read first**: ux.md §6.3 (the `memory_saved` row)

**Files**: create `FE/features/agent/MemoryChip.tsx` and register it in the BlockView chip renderer

**Steps**: a chip "🧠 Remembered: "{text}"" (truncated to 60 characters) that links to `/memory`. Rendered from live events and from the stored `blocks` (`kind: "chip", chip: "memory"`).


**Acceptance**:
- [ ] The chip renders from a live event and after a reload (stored blocks)

**Verify**: `pnpm test:e2e -- memory`

---

<a id="t195"></a>
### T195 · e2e test: memory

**Depends on**: T193, T194 · **Parallel**: yes · **Size**: S

**Files**: create `frontend/apps/web/tests/e2e/memory.spec.ts`

**Cases**:

1. `#script:remember_formal` → the chip appears, and the Memory page lists the item.
2. A new document with `#script:uses_memory`. The fake script asserts that the memory block is in its input, through a test hook that echoes "MEMORY_SEEN" when the block is present. The reply shows "MEMORY_SEEN".
3. Delete the memory on the page; the next turn doesn't echo it.

**Acceptance**:
- [ ] All 3 cases pass in en and ar

**Verify**: `pnpm test:e2e -- memory`
