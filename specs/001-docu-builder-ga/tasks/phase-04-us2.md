# Phase 4: US2, refine by conversation and by hand (task cards)

Before any card, read [IMPLEMENTER.md](../IMPLEMENTER.md). **Story test**: quickstart.md › US2, plus "Agent behavior" steps 3 and 4.

**Exit check**: the locality eval is at least 95%. Undo and rewind restore the document byte for byte. `pnpm test:e2e -- refine` passes in en and ar.

---

## Tests first (T090–T094)

<a id="t090"></a>
### T090 · Document PATCH tests (write first)

**Depends on**: T079 · **Parallel**: yes · **Size**: S

**Read first**: contracts/rest-api.md › Documents and revisions (the PATCH row)

**Files**: create `BT/integration/test_documents.py`

**Cases**:

1. `PATCH {baseVersion: v, ops:[update_slide…]}` → 200 `{version: v+1}`. `manual_edits_since_agent` goes up by 1.
2. A stale `baseVersion` → 409 `version_conflict`.
3. While a lease is held by a turn → 409 `doc_busy`.
4. A viewer → 403. Another workspace → 404.
5. Invalid ops (unknown slide, a `points` layout with no points) → 400 `invalid_request` with `details.op_index`.
6. `title` only, or `themeId` only, are allowed without ops.
7. Duplicate → 201, the new doc has the same content and `title + " (copy)"`, and its own thread.
8. List: `q` matches the title (ILIKE), `format` filters, and the cursor paginates stably.
9. Soft delete removes it from the list, and restore brings it back.


**Acceptance**:
- [ ] Every case listed above is its own test function (`test_<short_name>`)
- [ ] The tests run and **fail for the expected reason** (missing module or not implemented) until the implementation task lands
- [ ] No production code is added in this task

---

<a id="t091"></a>
### T091 · Undo, restore, and rewind tests (write first)

**Depends on**: T075 · **Parallel**: yes · **Size**: M

**Files**: create `BT/integration/test_revisions.py`

**Cases**:

1. After a committed turn (v1 → v2), `POST /v1/turns/{id}/undo` → the doc content equals v1 exactly, the version is 3, the revision source is `restore`, and the response is 200 `{version:3}`.
2. Undo when a newer revision exists (a manual edit after the turn) → 409 `version_conflict`.
3. `GET /v1/documents/{id}/revisions` lists newest first, with `source` and `authorName`.
4. Restore revision r → content equals r, and a new revision is written.
5. **Rewind**. Thread messages are [u1, a1, u2, a2] and the doc versions are v0 → v1 (turn 1) → v2 (turn 2). Then `POST /v1/threads/{id}/rewind {messageId: u2, text: "new"}` →
   - the messages after u2 are deleted, and u2's text becomes "new"
   - the doc is restored to v1's content as a new revision
   - a new turn starts from `base_version` = that new version
   - the **LangGraph checkpoint is forked**: the model's history for the new turn has no a2 (assert with the fake script by inspecting the `llm_input` passed in, through a test hook)
6. Rewind while a turn is running → 409 `doc_busy`.


**Acceptance**:
- [ ] Every case listed above is its own test function (`test_<short_name>`)
- [ ] The tests run and **fail for the expected reason** (missing module or not implemented) until the implementation task lands
- [ ] No production code is added in this task

---

<a id="t092"></a>
### T092 · Approval-after-manual-edits test (write first)

**Depends on**: T075 · **Parallel**: yes · **Size**: S

**Files**: create `BT/integration/test_approval_policy.py`

**Cases**:

1. Manually PATCH 2 slides, then run a turn whose script is `replace_slides`. A `tool_approval` event arrives with `manualEditsLost == 2`, and `before` lists the current slides.
2. After a committed agent turn, `manual_edits_since_agent == 0`. The next `replace_slides` doesn't ask.


**Acceptance**:
- [ ] Every case listed above is its own test function (`test_<short_name>`)
- [ ] The tests run and **fail for the expected reason** (missing module or not implemented) until the implementation task lands
- [ ] No production code is added in this task

---

<a id="t093"></a>
### T093 · Edit-locality eval (write first)

**Depends on**: T088 · **Parallel**: yes · **Size**: M

**Files**: create `evals/datasets/edits.jsonl` and `evals/scorers/locality.py`

**Steps**:

1. 40 cases (20 en, 20 ar). Each is `{doc: <DocumentState JSON, 5–8 slides>, prompt: "make slide 3 shorter", expect_changed: [<slide ids>], allow_added: 0|1}`. Mix these intents:
   - shorten, translate one slide, change a layout, add after X, delete X, retitle the doc, change the theme
   - and 4 "change everything" prompts, where every slide is expected to change
2. `locality.py` scores 1 if the set of changed slide ids (compare the draft before and after, by id and content) equals `expect_changed`, allowing up to `allow_added` new slides. Otherwise 0.
3. Add `edits` to `run.py` suites.

**Acceptance**:
- [ ] The baseline with prompt v0 is recorded. The target for T098 is at least 0.95.

---

<a id="t094"></a>
### T094 · e2e test: refine (write first)

**Depends on**: T059 · **Parallel**: yes · **Size**: M

**Files**: create `frontend/apps/web/tests/e2e/refine.spec.ts` and the fake scripts `{edit_slide3,replace_all,two_turns}.json`

**Cases** (en-desktop and ar-desktop):

1. On a created deck, send `#script:edit_slide3 make slide 3 shorter`. Only `slide-3` gets the glow class, and the assistant message shows one preview.
2. "Undo this turn" → slide 3's title is back to the previous text.
3. Inline edit: click `slide-1-title`, type, press Esc. The save status shows `Saved`. The version history shows a manual entry.
4. Conflict: open the same doc in a second page and edit in both. The second page shows `banner-conflict`.
5. Approval: after the manual edit, `#script:replace_all` → the approval card appears. Deny → the slides are unchanged.
6. Rewind: edit the first user message → the doc reverts, and a new turn runs.
7. Conversations: the thread is listed. Archive it, and it moves to the Archived tab.
8. Present: press `btn-present`, then ArrowRight twice, then Esc → back in the editor.

---

## Backend (T095–T098)

**Acceptance**:
- [ ] Every case listed above is its own test function (`test_<short_name>`)
- [ ] The tests run and **fail for the expected reason** (missing module or not implemented) until the implementation task lands
- [ ] No production code is added in this task
<a id="t095"></a>
### T095 · Document routes (full)

**Depends on**: T090, T084 · **Parallel**: no · **Size**: M

**Read first**: contracts/rest-api.md › Documents and revisions (every row, including duplicate)

**Files**: modify `BE/api/routers/documents.py`. Create `BE/services/documents.py`, `BE/domain/api/documents.py`, and `BE/db/repositories/documents.py` (extend).

**Steps**:

1. `GET /v1/documents?q&format&cursor&limit` uses repository `list_recent`, with title ILIKE `%q%` when `q` is set. Each item is `{id,title,format,themeId,updatedAt,thumbnailUrl|null,slideCount}`.
2. `POST /v1/documents {title?, format, themeId?}` creates a document with one empty `title` slide (title "Untitled" / "بدون عنوان" by `me.locale`) and a thread. Returns 201 `{documentId, threadId}`. This powers **New blank**. Enable the `topbar-new-blank` button from T047 now.
3. `POST /v1/documents/{id}/duplicate` follows the contract row.
4. `PATCH /v1/documents/{id}`:
   1. lock the doc `FOR UPDATE`
   2. check the lease (busy → 409)
   3. check `baseVersion` (409)
   4. apply the ops with `reducers.apply` (the same reducers as the agent; map each DocOp to its tool name)
   5. on an invalid op → 400 with `details.op_index`
   6. bump the version and `manual_edits_since_agent += 1`
   7. call `revisions.touch_manual(...)` (T096)
5. `DELETE` soft deletes and `POST …/restore` undeletes. Only the document owner or an admin may do either (`can(...,"doc.delete")`).

**Acceptance**:
- [ ] T090 passes
- [ ] The ops path reuses `reducers.apply` (no second copy of the editing logic)

---

<a id="t096"></a>
### T096 · Revisions service and routes

**Depends on**: T095 · **Parallel**: no · **Size**: M

**Read first**: data-model.md › document_revisions

**Files**: create `BE/services/revisions.py` and `BE/api/routers/revisions.py`

**Steps**:

1. `touch_manual(s, doc, user)` uses debounced snapshots. If the latest revision is `manual` by the same user and is under 30 s old, **update** that revision's content in place. That is the one allowed update: a manual session isn't final until 30 s of quiet. Otherwise insert a new `manual` revision.
2. `GET /v1/documents/{id}/revisions` lists `{id, version, source, authorName, createdAt, slideCount}`, newest first, paginated.
3. `GET /v1/documents/{id}/revisions/{revId}` returns the full content (used by the history preview).
4. `POST …/revisions/{revId}/restore` checks the lease and inserts a new revision with `source='restore'` and that content. Increments the version.
5. Theme changes from Patterns (T120) write `source='theme'` through the PATCH path. The PATCH body's optional `revisionSource: 'theme'` field is in the contract.

**Acceptance**:
- [ ] T091 cases 3–4 pass

---

<a id="t097"></a>
### T097 · Undo and rewind

**Depends on**: T096, T078 · **Parallel**: no · **Size**: L

**Read first**: contracts/rest-api.md (the undo and rewind rows); `MAS/api/routes/conversations.py` (`rewind`); LangGraph docs on `graph.aget_state_history` and `update_state` (forking a checkpoint)

**Files**: modify `BE/api/routers/{turns,threads}.py` and `BE/services/turns.py`. Create `BE/agent/checkpoints.py`.

**Steps**:

1. **Undo** `POST /v1/turns/{id}/undo`:
   - the turn is `committed` and the doc's version == `turn.committed_version` (else 409)
   - restore the revision whose version == `turn.base_version`, with source `restore`
   - **don't** touch the messages or the checkpoint. The agent sees the restored doc through the context message next turn.
2. **Rewind** `POST /v1/threads/{id}/rewind {messageId, text}`:
   1. no active turn (409)
   2. find the turn that started with `messageId` (`turns` where the user message id equals it)
   3. delete `messages` created after that user message, update its text, and restore the doc to that turn's `base_version` as a new revision
   4. **Checkpoint fork** (`checkpoints.fork_before(thread_id, human_message_id)`): walk `aget_state_history(config)` to the checkpoint whose `messages` doesn't yet contain that HumanMessage id, and take its `checkpoint_id`. The new turn runs with `config["configurable"]["checkpoint_id"] = that_id`, which makes LangGraph branch from there.
   5. start a new turn through `start_turn(...)`, reusing the edited message id (don't insert a new user row)
3. Handle the case where a summary was compacted past that point: if no such checkpoint exists, fall back to a fresh thread state. Clear it by giving the thread a new `checkpoint_ns`: add `threads.checkpoint_ns`, default `""`, and include it in the configurable. Log it at INFO.

**Acceptance**:
- [ ] T091 passes, including the fork assertion

---

<a id="t098"></a>
### T098 · Prompt v1: targeted edits

**Depends on**: T093, T064 · **Parallel**: no · **Size**: M

**Files**: modify `backend/prompts/{deck,document,webpage,social,assistant}.md`

**Steps**:

1. Add an **"Editing rules"** section:
   - identify the slides the user means (by number, as the user sees it 1-based, or by content), and map them to ids from `<document_context>`
   - change only those
   - prefer `update_slide` with the smallest patch
   - for "add a slide about X", use `add_slide` after the most relevant slide
   - never call `replace_slides` unless the user asks to redo, restructure, or rewrite everything
2. Add one Arabic edit example and one English edit example.
3. Run the `edits` eval and iterate until it's at least 0.95 (or document the best score and the failures in the PR). Run `drafts` to make sure it didn't regress.

**Acceptance**:
- [ ] The eval comment on the PR shows edits ≥ 0.95, and drafts doesn't drop more than 3 points

---

## Frontend (T099–T110)

<a id="t099"></a>
### T099 · Inline editing, title editing, save status

**Depends on**: T095, T084 · **Parallel**: no · **Size**: L

**Read first**: ux.md §5.4 (the Top bar bullets), §5.4.1 (Selection), §10 (Canvas keyboard)

**Files**: create `FE/features/editor/{Selection,InlineText,useDocSave}.ts(x)` and modify `FE/features/editor/{Canvas,EditorTopBar}.tsx`

**Steps**:

1. `useDocSave()` keeps a queue of ops with a 600 ms debounce.
   - It sends `PATCH {baseVersion, ops}`. On 200 it updates `committed` and `committedVersion` in the store.
   - On 409 `version_conflict` → status `conflict` (T100 banner). On 409 `doc_busy` → keep the ops queued and retry after the turn ends.
   - Offline (fetch failure) → status `offline`, retrying with backoff.
   - It exposes the status `saving | saved | offline | conflict`.
2. **Selection** state in the store: `{slideId, field}`. Clicking a `data-field` block in the active slide selects it, and `Slide mode="edit"` (T018) makes it contenteditable.
   - Esc or an outside click deselects and commits the text through `onChange`, which becomes an `update_slide` op with a patch for that field.
   - Points: Enter adds a point after the current one, and Backspace on an empty point deletes it. Both are ops.
   - Paste strips formatting (`plaintext-only`).
3. Keyboard (ux §10): Tab and Shift+Tab move between the active slide's blocks, Enter edits, Esc exits, and Alt+↑/↓ goes to the previous or next slide.
4. **Disabled while a turn runs** (`turn != null`) or when `!permissions.edit`.
5. Title inline edit in the top bar: click to edit, Enter or blur saves (a `set_title` op), Esc cancels, max 140 characters.
6. Save status in the top bar: `Saving…` / `Saved ✓` (fades after 2 s) / `Offline – retrying` / `Conflict` (red, with Reload).

**Acceptance**:
- [ ] T094 case 3 passes
- [ ] Edits made during a turn are impossible (the UI is disabled)
- [ ] The whole flow works from the keyboard alone

---

<a id="t100"></a>
### T100 · Editor banners

**Depends on**: T099 · **Parallel**: no · **Size**: S

**Read first**: ux.md §5.4.5 (the table)

**Files**: create `FE/features/editor/Banners.tsx`

**Steps**: build the 5 banners from the table, using the T044 `Banner`, in priority order: conflict > waiting > running > offline > viewer. **Stop** calls `turnRunner.stopTurn`. **Go to question** scrolls the thread to the open card and focuses its first control. **Reload** refetches the doc and drops the queued ops (after a confirm if any are queued). Test ids: `banner-<kind>`.

**Acceptance**:
- [ ] T094 case 4 passes

---

<a id="t101"></a>
### T101 · Filmstrip drag to reorder

**Depends on**: T099 · **Parallel**: yes · **Size**: M

**Read first**: ux.md §5.4.2; §10 (filmstrip keyboard reorder)

**Files**: modify `FE/features/editor/Filmstrip.tsx`

**Steps**:

1. Native HTML5 drag and drop (no library). The drop indicator is a 2px violet line between items. Drop sends a `move_slide` op with `afterSlideId`.
2. Keyboard: Space on a focused item picks it up (announce through the aria-live region "Picked up slide 3"), ↑/↓ moves it, Space drops, and Esc cancels.
3. Disabled during turns and for viewers.

**Acceptance**:
- [ ] Reorder works by mouse and by keyboard in en and ar, and persists after a reload

---

<a id="t102"></a>
### T102 · Filmstrip context menu and layout picker

**Depends on**: T101 · **Parallel**: yes · **Size**: M

**Read first**: ux.md §5.4.2 (the context menu and `+ slide` bullets)

**Files**: create `FE/features/editor/{FilmstripMenu,LayoutPicker}.tsx`

**Steps**:

1. The ⋯ button on hover, and right-click, open a Menu: Duplicate (an `add_slide` op with a copy of the slide after itself), Delete (Dialog confirm if the slide's title or body differ from the layout defaults), Move up, Move down.
2. `+ slide` opens a Popover with 7 layout tiles (a mini `<Slide>` with sample content and the layout name). Picking one sends an `add_slide` op after the active slide, with a localized placeholder title ("New slide" / "شريحة جديدة"), and `points: ["…"]` for `points`, a 2×2 `table`, and a 3-point bar `chart`.

**Acceptance**:
- [ ] Every menu action works and persists, in both languages

---

<a id="t103"></a>
### T103 · Message actions: edit and rewind, undo, feedback

**Depends on**: T097, T085 · **Parallel**: yes · **Size**: M

**Read first**: ux.md §6.1; contracts/rest-api.md (the rewind, undo, and feedback rows)

**Files**: create `FE/features/agent/MessageActions.tsx` and `BE/api/routers/messages.py` (feedback)

**Steps**:

1. User bubble hover → `Edit` turns the bubble into a textarea with Cancel and Send. Send calls `POST /v1/threads/{id}/rewind`, then `startTurn` with the returned `turnId`. The thread list refetches.
2. Assistant hover → 👍 👎 calls `POST /v1/messages/{id}/feedback {rating, comment?}`. 👎 opens a small popover with an optional comment. The backend sends it with `langsmith.Client().create_feedback(run_id, key="user_rating", score=1|0, comment=…)`. The run id is stored on the turn (`turns.langsmith_run_id`, in data-model.md), and the backend only calls LangSmith when tracing is enabled.
3. `Undo this turn` shows only on the latest committed assistant message, and only when the doc version equals that turn's `committed_version`. It calls the undo endpoint and refetches.

**Acceptance**:
- [ ] T094 cases 2 and 6 pass

---

<a id="t104"></a>
### T104 · Version history drawer

**Depends on**: T096 · **Parallel**: yes · **Size**: M

**Read first**: ux.md §5.4.7

**Files**: create `FE/features/editor/VersionHistory.tsx`

**Steps**:

1. The History button opens a `Sheet` (end side, 400px) listing revisions grouped by day, each with a time, source icon, author, and slide count.
2. Clicking a row loads `GET …/revisions/{revId}`. The canvas renders that content **read-only**, with the banner "Viewing version from {time}" and the buttons `Restore` and `Back to current`.
3. Restore opens a confirm Dialog, then calls `POST …/restore`, then refetches the doc, closes the drawer, and shows a toast.

**Acceptance**:
- [ ] Preview never changes the document until Restore

---

<a id="t105"></a>
### T105 · Conversations page

**Depends on**: T106 · **Parallel**: yes · **Size**: M

**Read first**: ux.md §5.5; `MAF/components/ConversationList.tsx`, `MAF/hooks/useConversations.ts`, `MAF/lib/groupConversations.ts`

**Files**: create `FE/pages/Conversations.tsx`. Port `FE/components/ConversationList.tsx`, `FE/hooks/useThreads.ts`, and `FE/lib/groupThreads.ts`.

**Steps**: port and rename (conversation → thread). Build the header with PillTabs (Active/Archived) and the rows per §5.5. Archive and Restore use PATCH `{archived}`. Delete opens a confirm Dialog, then `DELETE`. The empty state uses the placeholder illustration. Clicking a row navigates to `/doc/:documentId`.

**Acceptance**:
- [ ] T094 case 7 passes, and groups by day work across locales

---

<a id="t106"></a>
### T106 · Thread routes (list and update)

**Depends on**: T079 · **Parallel**: yes · **Size**: S

**Read first**: contracts/rest-api.md › Threads (the GET list, PATCH, and DELETE rows; the messages GET is already done in T085)

**Files**: modify `BE/api/routers/threads.py`

**Steps**:

1. `GET /v1/threads?archived=false&cursor` returns `{id,title,documentId,documentTitle,format,updatedAt,archived}`, newest first.
2. `PATCH {archived?, title?}`.
3. `DELETE` soft deletes the thread and **also** deletes its attachments (call a hook that is a no-op until T161).

**Acceptance**:
- [ ] Contract status codes are covered by tests in `BT/integration/test_threads.py`

---

<a id="t107"></a>
### T107 · Documents page, card menu, Create tabs

**Depends on**: T095, T044 · **Parallel**: yes · **Size**: M

**Read first**: ux.md §5.3, §4.11; §5.2 (the bottom tabs)

**Files**: create `FE/pages/Documents.tsx` and `FE/components/DocumentCard.tsx`. Modify `FE/pages/Create.tsx` (the Recent tabs).

**Steps**:

1. `DocumentCard`: the thumbnail is `thumbnailUrl`, or a fallback `<Slide width=…>` of the first slide (fetch `GET /v1/documents/{id}` lazily when visible), plus the title, "Edited {relative}", and the format icon. The ⋯ menu has Open, Duplicate, Rename (inline dialog → PATCH title), and Move to trash.
2. The Documents page per §5.3: search (debounced 300 ms, written to the URL), format Select, sort Select, a responsive grid, infinite scroll, and an empty state.
3. Create's bottom tabs: Recent documents (8 cards) and Recent conversations (8 rows).

**Acceptance**:
- [ ] Every menu action works, and the grid columns match the §5.3 breakpoints

---

<a id="t108"></a>
### T108 · Present mode

**Depends on**: T084 · **Parallel**: yes · **Size**: S

**Read first**: ux.md §5.4.8

**Files**: create `FE/features/editor/Present.tsx` and the route `/doc/:id/present`

**Steps**:

1. Fullscreen API on enter, a black backdrop, and a centered `<Slide width=fit>` that fits both width and height.
2. Keys: ←/→ mirrored in RTL (in RTL, ← goes **next**), Space and PageDown go next, PageUp goes back, Home and End jump, F toggles fullscreen, and Esc exits to the editor.
3. Idle for 2 s hides the cursor. Mouse movement shows the bottom bar `‹ 3 / 12 ›` and ✕.
4. Reuse this component in the share viewer (T146).

**Acceptance**:
- [ ] T094 case 8 passes, and the keys are correct in ar

---

<a id="t109"></a>
### T109 · Trash page

**Depends on**: T095 · **Parallel**: yes · **Size**: S

**Read first**: ux.md §5.14

**Files**: create `FE/pages/Trash.tsx` and add `GET /v1/documents?deleted=true` to T095's list route (a filter, owner or admin only)

**Steps**: a grid of deleted docs with `Restore` and `Delete forever` (a destructive confirm Dialog). The info banner says "Items are deleted forever after 30 days". The hard-delete job comes from T137's purge pattern. Add `docu.trash_purge` daily in `BE/worker/tasks/retention.py`, creating the file if T161 hasn't yet.

**Acceptance**:
- [ ] Restore works. A forever-delete removes the doc, its revisions, and its thread (cascade).

---

<a id="t110"></a>
### T110 · Editor on narrow screens

**Depends on**: T084, T044 · **Parallel**: no · **Size**: M

**Read first**: ux.md §5.4 › Editor on mobile; §4.15 (Sheet bottom variant)

**Files**: create `FE/features/editor/Responsive.tsx` and modify `FE/pages/Editor.tsx`

**Steps**:

1. Below `lg`: the filmstrip is replaced by a counter `3 / 12` with prev and next buttons above the canvas.
2. Below `md`: the agent column becomes a bottom `Sheet` with 3 heights (closed shows the composer bar only, half, full) and a drag handle. The top-bar actions collapse into a ⋯ menu.
3. During a turn, the sheet auto-opens to half if it was closed, so users see progress.

**Acceptance**:
- [ ] At 390px: create a deck, answer a question, approve, present. All work in `en-mobile` and `ar-mobile` (extend `refine.spec.ts` with a mobile project run).
