# Phase 16: US14, platform administration (task cards)

Before any card, read [IMPLEMENTER.md](../IMPLEMENTER.md). **Story test**: quickstart.md › US14.

---

<a id="t217"></a>
### T217 · Admin tests (write first)

**Depends on**: T033 · **Parallel**: yes · **Size**: S

**Files**: create `BT/integration/test_admin.py`

**Cases**:

1. A non-admin on any `/v1/admin/*` route → 403. A platform admin → 200.
2. `PUT /model-settings {apiKey}` stores it sealed. `GET` returns `apiKeySet: true` and never the key.
3. A new prompt version, then activating it → the next turn's `turns.prompt_version_id` equals it. Roll back → the older version.
4. `PUT /profiles/deck {skills:[…]}` → the skills index for `deck` changes on the next turn.
5. Usage: seed 10 turns across 2 days, 2 models, and 2 workspaces, run the rollup, and check the totals per grouping.
6. Deactivating a user → their sessions stop working (401).
7. The platform admin can't read workspace documents (a 404 on `GET /v1/documents/{id}` with an `x-workspace-id` they aren't a member of).


**Acceptance**:
- [ ] Every case listed above is its own test function (`test_<short_name>`)
- [ ] The tests run and **fail for the expected reason** (missing module or not implemented) until the implementation task lands
- [ ] No production code is added in this task

---

<a id="t218"></a>
### T218 · Platform settings service

**Depends on**: T217, T127 (seal) · **Parallel**: no · **Size**: M

**Read first**: data-model.md › platform_settings, prompt_versions

**Files**: create `BE/services/platform_settings.py` and modify `BE/agent/models.py`, `BE/core/prompts.py`, and `BE/core/flags.py` (create it)

**Steps**:

1. `get_platform_settings()` reads the single row, cached for 30 s per process. It merges over env defaults: DB values win, and empty values fall back to env.
2. `ModelRegistry` takes `overrides` from it (T062 already accepts them).
3. Set the prompt override resolver (T004 hook): `resolver(name)` returns the active `prompt_versions.body` for that name or `None`. It also exposes the active version id for the turn row (T078 records it).
4. `flags.py`: `flag(name) -> bool` from the platform settings flags with defaults (`web_search`, `skills`, `images`, `connectors`). Expose the flags to the frontend through `GET /v1/me` (`flags`).


**Acceptance**:
- [ ] A DB value overrides env, and an empty DB value falls back to env
- [ ] The prompt resolver returns the active version
- [ ] `GET /v1/me` includes `flags`

**Verify**: `uv run pytest tests/integration/test_admin.py -q -k settings`

---

<a id="t219"></a>
### T219 · Admin routes

**Depends on**: T218, T010 · **Parallel**: no · **Size**: M

**Read first**: contracts/rest-api.md › Platform admin (every row); `MAS/api/routes/admin.py`

**Files**: create `BE/api/routers/admin.py`

**Steps**:

1. Implement every row.
2. `POST /model-settings/check` runs `run_checks()` from T010 with the **candidate** settings in the body (not saved), returning `{plain, toolCalls, streamedToolCalls, error?}`.
3. Prompts: list the names (the files plus any DB versions), the versions with notes and authors, a create (it activates the new version), and activate. Bodies are stored as-is. Validate that they still contain the contract rule markers (the T064 test logic), and refuse with a 400 listing the missing rules.
4. Profiles: `GET` returns the effective profile (code defaults with DB overrides). `PUT` stores the overrides in `platform_settings.profiles` (jsonb).
5. Every write produces an audit entry with `workspace_id=NULL`. `audit_log.workspace_id` is nullable for platform events (data-model.md).


**Acceptance**:
- [ ] T217 passes
- [ ] Saving a prompt missing a contract rule gets 400 with the missing rules listed

**Verify**: `uv run pytest tests/integration/test_admin.py -q`

---

<a id="t220"></a>
### T220 · Usage rollup

**Depends on**: T075 · **Parallel**: no · **Size**: S

**Files**: create `BE/services/usage.py`, `BE/worker/tasks/usage_rollup.py`, and the table `usage_daily` (migration `0010_usage.py`)

**Steps**:

1. `usage_daily(day, workspace_id, model, turns, failed, input_tokens, output_tokens, cost_usd, p50_ms, p95_ms)` is built by an hourly upsert for today and yesterday, from `turns` (`percentile_cont` for latency).
2. `GET /v1/admin/usage?from&to&groupBy` reads `usage_daily`.


**Acceptance**:
- [ ] T217 case 5 passes
- [ ] Running the rollup twice for the same hour gives the same numbers

**Verify**: `uv run pytest tests/integration/test_admin.py -q -k usage`

---

<a id="t221"></a>
### T221 · Admin UI

**Depends on**: T219, T220 · **Parallel**: yes · **Size**: L

**Read first**: ux.md §5.13 (the tabs table); `MAF/pages/AdminPage.tsx`

**Files**: create `FE/pages/admin/{AdminLayout,Users,Model,Prompts,Profiles,Flags,Usage}.tsx`

**Steps**:

1. Port the MA AdminPage users table and extend it per the §5.13 Users row.
2. **Model**: a form with the write-only key ("•••• set" plus Replace). "Check connection" shows ✓/✗ for the three probes. Save.
3. **Prompts**: a list of names. A version list with notes. The editor is a monospace textarea with a **diff view** against the active version: a simple line diff with no library (write a small LCS diff in `FE/lib/diff.ts` with a unit test). "Save as new version" takes a note. Activate.
4. **Profiles**: checklists for skills, tools, and connectors, and an effort cap Select.
5. **Flags**: switches with descriptions.
6. **Usage**: KPI tiles (turns, tokens, cost, p95, failure %), a line chart over time (reuse the `LineChart` from `FP/slides`), and a breakdown table. Follow the dataviz guidance (one accent per series, labels with units).

**Acceptance**:
- [ ] quickstart.md › US14 passes end to end
