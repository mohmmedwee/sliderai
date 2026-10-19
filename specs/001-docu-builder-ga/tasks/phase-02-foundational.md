# Phase 2: Foundational (task cards)

Before any card, read [IMPLEMENTER.md](../IMPLEMENTER.md). No user-story work starts until this phase is merged.

**Exit check for the phase**:
- Register (the first user becomes admin), verify the email in Mailpit, log in, and see the shell in en and ar, light and dark.
- `/__ui` renders every primitive.
- `uv run pytest -m "db or redis or not slow"` and `pnpm test` pass.

---

## Domain models and shared types

<a id="t014"></a>
### T014 · Document domain models

**Depends on**: T003 · **Parallel**: no · **Size**: M

**Read first**: data-model.md › "Document content"; contracts/agent-tools.md › Document tools; ux.md §7 (layout limits)

**Files**: create `BE/domain/base.py`, `BE/domain/ids.py`, `BE/domain/document.py`, and `BT/unit/test_document_model.py`

**Steps**:

1. `base.py`: `ApiModel`, exactly as in IMPLEMENTER §5.2.
2. `ids.py`:
   - `new_slide_id() -> str` returns a 10-character `[A-Za-z0-9]` id from `secrets.choice`.
   - `new_uuid() -> UUID` uses `uuid6.uuid7()`.
3. `document.py` defines everything from data-model.md: `Layout`, `TableData`, `ChartSeries`, `ChartData`, `SlideImage`, `Slide`, `SlideInput` (the same as `Slide` without `id`), and `DocumentContent`. Add:

```python
Format = Literal["presentation", "document", "webpage", "social"]

class ThemeTokens(ApiModel):
    bg: str; paper: str; ink: str; accent: str
    tone: Literal["light", "dark"]
    font: Literal["sans", "serif"] = "sans"

class Theme(ApiModel):
    id: str; name: str; tokens: ThemeTokens; tags: list[str]

class DocumentState(ApiModel):
    """What a turn edits: the agent's draft and the editor's working copy."""
    title: str = Field(min_length=1, max_length=140)
    theme_id: str
    slides: list[Slide] = Field(min_length=1, max_length=60)
```

4. `CssField`: an `Annotated[str, AfterValidator(validate_css_field)]` that accepts **only**:
   - `#rgb`, `#rrggbb`
   - `rgb(r,g,b)` with 0–255 values
   - `hsl(h,s%,l%)`
   - `linear-gradient(<0-360>deg, <color> <0-100>%, <color> <0-100>%[, …up to 4 stops])`, where each `<color>` is one of the color forms above

   Anything else raises `ValueError("invalid_field")`. Write it as a small regex-based parser. **No** `url(`, `var(`, `;`, `}` or other CSS.
5. `Slide` `model_validator(mode="after")` enforces the layout rules from data-model.md:
   - `points` layout needs at least 1 point
   - `table` needs `table`, and every row has the same length as `columns`
   - `chart` needs `chart`, every series has the same length as `labels`, and pie and donut take exactly 1 series
   - `table` and `chart` fields are forbidden on other layouts

   Raise `ValueError` with these codes: `points_required`, `table_required`, `table_shape`, `chart_required`, `chart_shape`, `field_not_allowed`.
6. Tests: one valid sample per layout. Every error code is hit. `CssField` accepts 6 valid forms and rejects `url(x)`, `red; background:url()`, and `var(--a)`. Round-trip `model_dump(by_alias=True)` gives camelCase.

**Acceptance**:
- [x] Every rule in data-model.md › Layout rules is enforced and tested
- [x] `mypy --strict` is clean

**Verify**: `uv run pytest tests/unit/test_document_model.py -q`

---

<a id="t015"></a>
### T015 · Errors

**Depends on**: T014 · **Parallel**: yes · **Size**: S

**Read first**: contracts/rest-api.md › Errors; contracts/sse-events.md › TurnErrorCode

**Files**: create `BE/domain/errors.py` and `BT/unit/test_errors.py`

**Steps**:

1. `class DomainError(Exception)` with `code`, `status`, `message`, and `details`, as in IMPLEMENTER §5.3.
2. `ErrorBody(ApiModel)`: `{code: str, message: str, details: dict}`. `ErrorEnvelope(ApiModel)`: `{error: ErrorBody}`.
3. `ErrorCode = Literal[...]` listing **every** code in rest-api.md: `invalid_request`, `unauthenticated`, `forbidden`, `email_unverified`, `plan_required`, `not_found`, `version_conflict`, `doc_busy`, `insufficient_credits`, `too_large`, `unsupported_type`, `rate_limited`, `internal`, `invalid_credentials`, `totp_required`.
4. `TurnErrorCode = Literal[...]`, exactly the 9 codes in sse-events.md, plus `RETRYABLE: frozenset[str]` matching the Retryable column.
5. Test: every code in the contract tables is present. Copy the codes into the test as literal lists so contract drift is caught.

**Acceptance**:
- [x] The code lists match the contracts exactly

**Verify**: `uv run pytest tests/unit/test_errors.py -q`

---

<a id="t016"></a>
### T016 · Turn event models

**Depends on**: T014 · **Parallel**: yes · **Size**: M

**Read first**: contracts/sse-events.md (all of it); `MAS/models/events.py`

**Files**: create `BE/domain/events.py`, `BE/api/routers/schema_registry.py`, and `BT/unit/test_events.py`

**Steps**:

1. Port MA's event classes with the same `type` literals and fields, written as `ApiModel` (camelCase on the wire): `TextDeltaEvent`, `ReasoningDeltaEvent`, `ToolCallDeltaEvent` (`index`, `id`, `name`, `arguments_chars`), `ToolCallEvent`, `ToolApprovalEvent` (`approval_card: ApprovalCard`), `ToolResultEvent` (+ `ok: bool`), `ErrorEvent` (+ `code`), `StatusEvent`, `DoneEvent`.
2. Add `AskUserEvent` and `AskUserField`, using the limits in sse-events.md (`options` ≤ 64, each ≤ 120 characters; `fields` ≤ 6).
3. Add the Docu events: `TurnStartedEvent`, `DocPatchEvent`, `MemorySavedEvent`, `SkillLoadedEvent`, `StepLimitEvent`, `WaitingInputEvent`, `TurnCommittedEvent`, `TurnFailedEvent` (`code: TurnErrorCode`, `retryable`), `TurnCancelledEvent` (`reason`).
4. Add the `DocOp` union (7 ops, discriminated on `op`) and the `ApprovalCard` union (4 kinds, discriminated on `kind`, with `SlideSummary`).
5. `TurnEvent = Annotated[Union[...all...], Field(discriminator="type")]` and `turn_event_adapter = TypeAdapter(TurnEvent)`.
6. `schema_registry.py`: `GET /v1/_schema/turn-event`, `response_model=TurnEvent`, always raises 404. It exists only so FastAPI puts the union into OpenAPI for type generation. Include it in the schema.
7. Tests: every event round-trips through `turn_event_adapter` JSON, an unknown `type` fails, and a 65-option `AskUserEvent` fails.

**Acceptance**:
- [x] `/v1/openapi.json` contains every event model under `components.schemas`
- [x] The names and fields match contracts/sse-events.md exactly

**Verify**: `uv run pytest tests/unit/test_events.py -q && uv run python -c "from docu.api.app import create_app; import json; s=create_app().openapi(); assert 'DocPatchEvent' in s['components']['schemas']"`

---

<a id="t017"></a>
### T017 · TypeScript API types and the API client

**Depends on**: T008, T016 · **Parallel**: no · **Size**: S

**Files**: create `BE/scripts/dump_openapi.py`, `FP/api-types/{package.json,src/index.ts}`, `FP/api-types/openapi.json` (generated), `FP/api-types/src/schema.d.ts` (generated), and `FE/lib/api.ts`

**Steps**:

1. `dump_openapi.py` prints `json.dumps(create_app().openapi(), indent=1, sort_keys=True)`. It must not need a database (the lifespan doesn't run for `.openapi()`).
2. Root script `frontend/package.json` `gen:api`: `cd ../backend && uv run python -m docu.scripts.dump_openapi > ../frontend/packages/api-types/openapi.json && cd ../frontend/packages/api-types && npx openapi-typescript openapi.json -o src/schema.d.ts`.
3. `FP/api-types/src/index.ts` re-exports `paths` and `components`, plus helpers:

```ts
export type Schemas = components['schemas'];
export type TurnEvent = Schemas['TurnEvent'] // or the generated union name; check schema.d.ts
```

4. `FE/lib/api.ts`:
   - `export const api = createClient<paths>({ baseUrl: '' })`, plus middleware that:
     - adds `x-csrf-token` from the `docu_csrf` cookie on non-GET requests,
     - adds `x-workspace-id` from `useWorkspaceStore.getState().workspaceId` when set,
     - on 401, redirects to `/login?next=<current path>`,
     - on other errors, throws `ApiError {status, code, details}` built from the envelope.
   - Export `useApiQuery` and `useApiMutation` thin wrappers over TanStack Query.
5. Add `FE/stores/workspace.ts` (Zustand, persisted in localStorage under `docu.workspace`): `{workspaceId: string | null, setWorkspace(id)}`.

**Acceptance**:
- [x] `pnpm gen:api` regenerates with no diff on a clean tree
- [x] `pnpm typecheck` passes using `paths['/v1/health']['get']`

**Verify**: `cd frontend && pnpm gen:api && git diff --exit-code packages/api-types && pnpm typecheck`

---

## Slide renderer (FP/slides)

<a id="t018"></a>
### T018 · Slide renderer (7 layouts)

**Depends on**: T017 (types), T020 (themes) · **Parallel**: no · **Size**: L

**Read first**: ux.md §7 (the whole layout table and type scale); data-model.md › Document content

**Files**: create `FP/slides/src/index.ts`, `FP/slides/src/Slide.tsx`, `FP/slides/src/layouts/{Hero,Title,Points,Quote,Split,Table,Chart}.tsx`, `FP/slides/src/slide.css`, `FP/slides/src/useFitText.ts`, `FP/slides/src/types.ts`, and `FP/slides/tests/Slide.test.tsx`

**Steps**:

1. Public API:

```tsx
export interface SlideProps {
  slide: Slide;                    // generated type
  theme: Theme;                    // from themes.json (T020)
  width?: number;                  // rendered width in px; height = width * 9/16; default 1280
  mode?: 'view' | 'edit';          // edit: blocks are selectable
  selected?: FieldPath | null;     // e.g. 'title' | 'body' | 'points.2' | 'button'
  onSelect?(path: FieldPath): void;
  onChange?(path: FieldPath, value: string): void;   // only in edit mode, called on blur
  watermark?: boolean;
}
export function Slide(props: SlideProps): JSX.Element
```

2. Render a fixed 1280×720 box with `transform: scale(width/1280)` and `transform-origin: top left` inside a wrapper sized `width × width*9/16`. Theme tokens become CSS variables on the root: `--s-bg`, `--s-paper`, `--s-ink`, `--s-accent`, `--s-font`.
3. Each layout follows the ux.md §7 composition **exactly** (the percentages). Use **plain CSS in `slide.css`**, not Tailwind. The export route and the share viewer load this package without the app CSS.
4. Every text block has `dir="auto"` and `data-field="<path>"`. In edit mode, a block is a `contenteditable="plaintext-only"` element **only while selected**. Otherwise it's plain text with a hover outline class.
5. `useFitText(ref, {min: 0.7})`: if `scrollHeight > clientHeight`, reduce the font size by 10% per step down to 70%. Then add `data-overflow="true"`, and the filmstrip shows ⚠ (ux.md §7).
6. `field` renders as `background: <field>` (it's already validated by the backend grammar). `image` comes in T173. For now render `field` or the theme default `linear-gradient(135deg, accent, bg)`.
7. `watermark`: a small "Docu Builder" text at the bottom-end, 14px, 40% opacity.
8. Tests (Vitest + Testing Library):
   - each layout renders the expected `data-field` blocks
   - `dir="auto"` is on every text block
   - a long title gets `data-overflow` (mock `scrollHeight`)
   - edit mode calls `onSelect` and then `onChange`

**Acceptance**:
- [x] All 7 layouts render with the sample slides from `FP/slides/tests/fixtures.ts` (create it: one per layout, in en and ar)
- [x] The package has no import from `apps/web`
- [ ] It looks right in `/__ui` (T045 adds a slides section)

**Verify**: `cd frontend && pnpm --filter slides test`

---

<a id="t019"></a>
### T019 · SVG charts and table renderer

**Depends on**: T018 · **Parallel**: yes · **Size**: M

**Read first**: ux.md §7 (`table`, `chart` rows); data-model.md `ChartData`, `TableData`

**Files**: create `FP/slides/src/charts/{BarChart,LineChart,PieChart,scale.ts,index.ts}.tsx`, `FP/slides/src/table/DataTable.tsx`, and `FP/slides/tests/charts.test.tsx`

**Steps**:

1. `scale.ts`: `niceTicks(min, max, count=5)` (the classic "nice numbers" algorithm) and `formatValue(v, unit, locale, digits)` using `Intl.NumberFormat` with `numberingSystem` set to `arab` or `latn`.
2. **BarChart** (grouped bars), **LineChart**, and **PieChart** (`donut` = pie with a 55% inner radius) are pure SVG in a `viewBox="0 0 1000 560"`.
3. **Colors**: series 0 uses the theme accent. Series 1–5 use the accent mixed with ink at 25%, 45%, 60%, 75%, and 85% (compute it in TS; there's no `color-mix` in SVG for export safety).
4. **RTL**: when `dir === 'rtl'` (from the closest `[dir]`, or a prop), category order runs right to left and the value axis sits on the right. Numbers always grow upward.
5. **Legend**: on top, shown only when there are 2 or more series. Labels use `dir="auto"`.
6. **DataTable**: the header row has an accent background and paper text. Numbers (finite floats) align to the end. There are at most 8×12 cells, and longer text is ellipsized with a `title` attribute.
7. Tests: tick generation (0–97 gives `[0,20,40,60,80,100]`), the RTL order flips, and the pie sums to 360°.

**Acceptance**:
- [x] No chart library dependency is added
- [ ] Charts render correctly in the `/__ui` slides section in both directions

**Verify**: `pnpm --filter slides test`

---

<a id="t020"></a>
### T020 · Themes (one source of truth) and the contrast test

**Depends on**: T014 · **Parallel**: yes · **Size**: M

**Read first**: data-model.md › themes; `MA/skills/theme-factory/themes/*.md` and `MA/skills/theme-factory/LICENSE.txt` (Apache-2.0)

**Files**: create `backend/src/docu/data/themes.json`, `FP/slides/src/themes.ts`, `BT/unit/test_themes.py`, `FP/slides/tests/contrast.test.ts`, and `NOTICE` (repo root)

**Steps**:

1. **The source of truth is `backend/src/docu/data/themes.json`**: an array of `Theme` (T014 shape) with `id`, `name`, `tokens`, and `tags`.
2. Add these 16 base themes. These are the starting values; tune `ink` if the contrast test fails.

| id | bg | paper | ink | accent | tone | tags | font |
|---|---|---|---|---|---|---|---|
| paper | #f4f1ea | #ffffff | #1d1b16 | #2f2a22 | light | neutral | sans |
| ink | #0e0e10 | #18181b | #f4f4f5 | #e4e4e7 | dark | dark,neutral | sans |
| cobalt | #e8ecf8 | #ffffff | #0d1b4c | #1f3fff | light | blue | sans |
| midnight | #0b1230 | #121a3d | #e9ecff | #7c8cff | dark | blue,dark | sans |
| forest | #0f3b2e | #13473a | #eef6ef | #e8b86a | dark | green,dark | sans |
| mint | #e3f6ef | #ffffff | #103a2c | #16a37a | light | green | sans |
| ember | #c8331f | #fff5ef | #2a0d07 | #c8331f | light | red,orange | serif |
| clay | #e9dccb | #f8f2ea | #3b2a1c | #b0643a | light | orange,neutral | serif |
| saffron | #fff3cf | #fffaf0 | #3a2a00 | #b07d00 | light | yellow | sans |
| plum | #1b1030 | #24163f | #f2eaff | #b98bff | dark | purple,dark | sans |
| lilac | #ece6f7 | #ffffff | #2a1d47 | #7b4fd8 | light | purple | sans |
| rose | #fbe7ee | #fffafb | #4a1428 | #d6336c | light | pink | serif |
| slate | #2a2d34 | #33373f | #eceff4 | #f2c94c | dark | dark,yellow | sans |
| harbor | #d9e4ea | #f7fafc | #13293d | #e4572e | light | blue,orange | sans |
| lagoon | #d8f3f1 | #ffffff | #0c3b3a | #0f9d94 | light | green,blue | sans |
| noir | #000000 | #0d0d0d | #ffffff | #ffe14d | dark | dark,yellow | serif |

3. Convert the 10 `theme-factory` themes (Apache-2.0) into entries with the id prefix `tf-` (`tf-arctic-frost`, …). Map each palette's background, surface, text, and primary to `bg`, `paper`, `ink`, and `accent`, and pick the `tags` from its colors. Add the attribution to `NOTICE`: "Themes tf-* derived from theme-factory (Apache License 2.0)".
4. `FP/slides/src/themes.ts`: `import data from './generated/themes.json'`, then export `THEMES`, `getTheme(id)` (falls back to `paper`), and `defaultField(theme)`. Extend `gen:api` (T017) to also copy `backend/src/docu/data/themes.json` to `FP/slides/src/generated/themes.json`. The CI drift check covers it.
5. **Contrast tests** in both languages' test suites (Python and TS):
   - WCAG relative luminance contrast of `ink` on `paper` is at least 4.5
   - `paper` text on an `accent` button is at least 3.0 (large text)
6. `BT/unit/test_themes.py`: the JSON validates against `Theme`, the ids are unique, and contrast passes.

**Acceptance**:
- [x] 26 themes, all passing contrast
- [x] `NOTICE` has the Apache attribution
- [x] Only one JSON file is edited by hand

**Verify**: `uv run pytest tests/unit/test_themes.py -q && pnpm --filter slides test`

---

<a id="t021"></a>
### T021 · Slide fonts

**Depends on**: T018 · **Parallel**: yes · **Size**: S

**Files**: create `FP/slides/src/fonts/` (woff2 files and OFL license texts) and `FP/slides/src/fonts.css`

**Steps**:

1. Download the woff2 files (Latin and Arabic subsets) for these fonts, all under the SIL Open Font License, from Google Fonts or the official repos:
   - IBM Plex Sans Arabic (400, 600)
   - Inter (400, 600)
   - Noto Naskh Arabic (500, 700)
   - Fraunces (500, 700)
2. Write `@font-face` rules with `font-display: swap`. The `--s-font` stacks are:
   - sans: `"IBM Plex Sans Arabic","Inter",system-ui,sans-serif`
   - serif: `"Noto Naskh Arabic","Fraunces",Georgia,serif`
3. Put each `OFL.txt` next to its font files. `slide.css` imports `fonts.css`.

**Acceptance**:
- [ ] Arabic and Latin text render in the bundled fonts (check in DevTools › Rendered Fonts)
- [x] No request goes to Google Fonts at runtime

**Verify**: Manual check in `/__ui`. `grep -r fonts.googleapis frontend/` is empty.

---

## Database

<a id="t022"></a>
### T022 · SQLAlchemy models (core)

**Depends on**: T003, T014 · **Parallel**: no · **Size**: L

**Read first**: data-model.md › Entities (every table named below) and its Conventions line; IMPLEMENTER §5.4

**Files**: create `BE/db/base.py`, `BE/db/models/__init__.py`, and `BE/db/models/{users,auth,workspaces,documents,threads,turns,catalog,platform}.py`

**Steps**:

1. `base.py`: `class Base(DeclarativeBase)` with a naming convention for constraints (`ix_%(column_0_label)s`, `uq_%(table_name)s_%(column_0_name)s`, …). Also these mixins:
   - `UUIDPk` (`id: Mapped[UUID] = mapped_column(primary_key=True, default=new_uuid)`)
   - `Timestamps` (`created_at`, `updated_at` with `server_default=func.now()` and `onupdate=func.now()`)
   - `SoftDelete` (`deleted_at`)
   - `TenantMixin` (`workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)`)
2. Models, exactly as data-model.md, file by file:

| File | Tables |
|---|---|
| `users.py` | `users` |
| `auth.py` | `sessions`, `identities`, `auth_tokens` |
| `workspaces.py` | `workspaces`, `memberships` |
| `documents.py` | `documents`, `document_revisions` |
| `threads.py` | `threads`, `messages` |
| `turns.py` | `turns`, `pending_inputs` |
| `catalog.py` | `themes`, `templates` |
| `platform.py` | `prompt_versions`, `platform_settings` |

3. **Denormalized `workspace_id`** (`TenantMixin`, NOT NULL) on every tenant table, **including child tables**: `documents`, `document_revisions`, `threads`, `messages`, `turns`, `pending_inputs`. This is required for row-level security (data-model.md Conventions). Set it from the parent on insert in the services.
4. Enums are Postgres `TEXT` with a `CHECK` constraint (not native enums, which are easier to migrate). Example: `CheckConstraint("status in ('queued','running','waiting_input','committed','failed','cancelled','rejected')")`.
5. JSONB columns use `sqlalchemy.dialects.postgresql.JSONB`. `messages.slide_ids` is `ARRAY(Text)`.
6. Indexes from data-model.md › Indexes, plus a unique `(document_id, version)` on revisions and a unique `(turn_id, tool_call_id)` on `pending_inputs`.
7. `platform_settings` is a single row: `id: int = 1` with `CheckConstraint("id = 1")`.

**Acceptance**:
- [x] Every column in data-model.md exists with the right type and nullability
- [x] `uv run alembic revision --autogenerate` (in T024) produces the tables with no surprises
- [x] `mypy --strict` is clean

**Verify**: `uv run python -c "import docu.db.models as m; print(len(m.Base.metadata.tables))"` prints 18 or more

---

<a id="t023"></a>
### T023 · Ledger and audit models

**Depends on**: T022 · **Parallel**: no · **Size**: S

**Read first**: data-model.md › credit_ledger, audit_log

**Files**: create `BE/db/models/{ledger,audit}.py`

**Steps**:

1. `credit_ledger` has the columns listed in data-model.md, and `idempotency_key` is UNIQUE. There is no `updated_at`.
2. `audit_log` has the columns listed in data-model.md, with the index `(workspace_id, created_at desc)`.

**Acceptance**:
- [x] The models import, and their columns match data-model.md

**Verify**: covered by T024 and T038

---

<a id="t024"></a>
### T024 · Initial migration (with RLS)

**Depends on**: T022, T023 · **Parallel**: no · **Size**: M

**Read first**: data-model.md › Conventions; plan.md › Constitution Check VI

**Files**: create `backend/alembic.ini`, `backend/alembic/env.py` (async, ported from MA's `migrations/env.py`), and `backend/alembic/versions/0001_initial.py`

**Steps**:

1. Copy MA's async `env.py` pattern and point it at `docu.db.base.Base.metadata` and `settings.database.url`.
2. Run `uv run alembic revision --autogenerate -m initial`, then **edit** the file:
   - At the top: `op.execute("CREATE EXTENSION IF NOT EXISTS vector; CREATE EXTENSION IF NOT EXISTS citext;")`
   - **Ledger append-only trigger**:

```sql
CREATE FUNCTION ledger_no_mutation() RETURNS trigger AS $$
BEGIN RAISE EXCEPTION 'credit_ledger is append-only'; END $$ LANGUAGE plpgsql;
CREATE TRIGGER credit_ledger_immutable BEFORE UPDATE OR DELETE ON credit_ledger
FOR EACH ROW EXECUTE FUNCTION ledger_no_mutation();
```

   - **RLS** on the tenant tables: `documents`, `document_revisions`, `threads`, `messages`, `turns`, `pending_inputs`, `credit_ledger`, `audit_log`. Every later migration that adds a tenant table must repeat this block.

```sql
ALTER TABLE {t} ENABLE ROW LEVEL SECURITY;
ALTER TABLE {t} FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON {t}
  USING (current_setting('app.bypass_rls', true) = 'on'
         OR workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
  WITH CHECK (current_setting('app.bypass_rls', true) = 'on'
         OR workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid);
```

   - For catalog tables with a nullable `workspace_id` (`templates`, `themes`): the policy is `workspace_id IS NULL OR <same as above>`.
3. **Don't** put RLS on `users`, `sessions`, `identities`, `auth_tokens`, `workspaces`, `memberships`, `prompt_versions`, `platform_settings`, or `stripe_events`. Repositories protect those.
4. `downgrade()` drops everything in reverse order.

**Acceptance**:
- [x] `uv run alembic upgrade head` on an empty DB succeeds, and `alembic downgrade base` succeeds
- [x] `\d+ documents` in psql shows "Policies: tenant_isolation" and "Force row security"

**Verify**: `uv run alembic upgrade head && uv run alembic downgrade base && uv run alembic upgrade head`

---

<a id="t025"></a>
### T025 · Scoped sessions and the repository pattern

**Depends on**: T024 · **Parallel**: no · **Size**: M

**Read first**: IMPLEMENTER §5.4; `MAS/db/session.py`; `MAS/repositories/conversations.py` (the style of ownership in the signature)

**Files**: create `BE/db/session.py`, `BE/db/repositories/__init__.py`, `BE/db/repositories/documents.py` (a first example), and `BT/integration/conftest.py` (the `db` fixtures)

**Steps**:

1. `session.py`:

```python
def make_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]: ...

@asynccontextmanager
async def scoped_session(factory, workspace_id: UUID) -> AsyncIterator[AsyncSession]:
    """Transaction whose RLS scope is one workspace. Commits on success."""
    async with factory() as s, s.begin():
        await s.execute(text("SELECT set_config('app.workspace_id', :w, true)"), {"w": str(workspace_id)})
        yield s

@asynccontextmanager
async def unscoped_session(factory) -> AsyncIterator[AsyncSession]:
    """For non-tenant tables only (users, sessions, memberships…). RLS tables return 0 rows here."""

@asynccontextmanager
async def system_session(factory) -> AsyncIterator[AsyncSession]:
    """BYPASSES RLS. Only for worker beat tasks that must see all workspaces (reaper, expiry, rollups).
    Never import this in BE/api/."""
    # SET LOCAL app.bypass_rls = 'on'
```

2. Add an import-linter style test: `BT/unit/test_no_system_session_in_api.py` greps `BE/api/**` and fails if `system_session` appears.
3. `repositories/documents.py`: write two example functions that every later repository copies:

```python
async def get(s: AsyncSession, *, workspace_id: UUID, doc_id: UUID) -> Document | None
async def list_recent(s: AsyncSession, *, workspace_id: UUID, limit: int, cursor: str | None) -> Page[Document]
```

   The `Page[T]` generic (`items`, `next_cursor`) lives in `repositories/__init__.py`. The cursor is `base64(updated_at|id)`.
4. `BT/integration/conftest.py`: a session-scoped testcontainers `PostgresContainer("pgvector/pgvector:pg16")`, run `alembic upgrade head` once, and a `db` fixture that yields a factory and truncates the tables after each test. Add `redis` with `RedisContainer`. Mark these fixtures so they need the `db` or `redis` markers.

**Acceptance**:
- [ ] `scoped_session` sets the GUC per transaction (verified in T026)
- [ ] The API guard test passes

**Verify**: `uv run pytest tests/unit/test_no_system_session_in_api.py -q`

---

<a id="t026"></a>
### T026 · RLS isolation test

**Depends on**: T025 · **Parallel**: yes · **Size**: S

**Files**: create `BT/integration/test_rls.py`

**Tests** (marker `db`):

1. Create workspaces A and B and one document in each (insert with `system_session`).
2. `scoped_session(A)` → `select documents` returns only A's document.
3. `scoped_session(A)` → inserting a document with `workspace_id=B` raises (`WITH CHECK`).
4. `unscoped_session` → `select documents` returns **0** rows.
5. `system_session` → returns both.
6. A `messages` row of workspace B is invisible from A's scope.

**Acceptance**:
- [ ] All 6 cases pass

**Verify**: `uv run pytest tests/integration/test_rls.py -q -m db`

---

<a id="t027"></a>
### T027 · Seed script (themes, templates, built-in skills)

**Depends on**: T020, T024 · **Parallel**: yes · **Size**: M (plus content work)

**Read first**: data-model.md › templates, skills; spec.md US3

**Files**: create `BE/scripts/seed.py`, `backend/src/docu/data/templates.json`, and `BT/integration/test_seed.py`

**Steps**:

1. `seed.py` is idempotent (`INSERT … ON CONFLICT (id) DO UPDATE`). It loads `themes.json` into `themes` and `templates.json` into `templates` (with `workspace_id = NULL`). Skills sync is added in T197, so leave a call to `sync_builtin_skills()` behind `try/except ImportError` for now.
2. `templates.json` holds **24 templates**. Each is a `Template` with `id`, `name_en`, `name_ar`, `category`, `format`, `theme_id`, `colors`, `lang`, and `cards` (3–5 `SlideInput` each, valid against T014). Use this catalog, and write the card content yourself: short, realistic, and **original**.

| id | en / ar name | category | format | theme | lang |
|---|---|---|---|---|---|
| harbor-pitch | Harbor / مرفأ | pitch | presentation | harbor | en |
| annual-review-ar | Annual Review / المراجعة السنوية | report | presentation | ink | ar |
| rain-lesson | Wonder / دهشة | education | presentation | lagoon | en |
| water-ar | Groundwater / غيث | education | presentation | midnight | ar |
| pantry | Midnight Pantry / مخزن منتصف الليل | marketing | presentation | ember | en |
| nothing | Nothing / لا شيء | personal | presentation | paper | en |
| rebrand | Swatchbook / دفتر الألوان | pitch | presentation | paper | en |
| common-heat | Grainhouse / بيت الحبوب | event | presentation | cobalt | en |
| solar-ar | Solar / شعاع | education | presentation | slate | ar |
| season-ar | Heritage Season / روشن | event | presentation | forest | ar |
| lab-ar | Prismlet / منشور | education | presentation | lilac | ar |
| oud-ar | Rhythm / إيقاع | event | presentation | plum | ar |
| lookbook | Lookbook / كتالوج | marketing | presentation | clay | en |
| monsoon | Monsoon Modern / موسم المطر | marketing | presentation | ember | en |
| brutal | Office Hours / ساعات مكتبية | education | document | slate | en |
| open-house | Open House / بيت مفتوح | marketing | webpage | forest | en |
| retreat | Vista / إطلالة | marketing | webpage | lagoon | en |
| plate | Plate / طبق | marketing | social | ember | en |
| q3-review | Cobalt & Cream / كوبالت | report | presentation | cobalt | en |
| accountability | Contas / حسابات | report | document | midnight | en |
| roastery | Feriado / محمصة | pitch | presentation | noir | en |
| wedding | First Dance / الرقصة الأولى | personal | webpage | rose | en |
| teachers | Gold Star / نجمة ذهبية | personal | social | saffron | en |
| roadmap-ar | Roadmap / خارطة الطريق | planning | presentation | mint | ar |

   Include at least one `table` card and one `chart` card across the catalog (e.g. in `q3-review` and `annual-review-ar`).
3. Test: run the seed twice, and the count stays 24. Every template's cards validate as `SlideInput`, and every `theme_id` exists.

**Acceptance**:
- [ ] Running the seed twice is safe
- [ ] 24 templates and 26 themes are in the DB
- [ ] Arabic templates have Arabic content

**Verify**: `uv run python -m docu.scripts.seed && uv run pytest tests/integration/test_seed.py -q -m db`

---

<a id="t028"></a>
### T028 · LangGraph setup script

**Depends on**: T024 · **Parallel**: no · **Size**: S

**Read first**: IMPLEMENTER §6.1

**Files**: create `BE/scripts/setup_langgraph.py` and `BE/agent/persistence.py`

**Steps**:

1. `persistence.py`:
   - `@asynccontextmanager async def langgraph_persistence(settings) -> AsyncIterator[tuple[AsyncPostgresSaver, AsyncPostgresStore]]` opens both from `settings.database.url`. Convert `postgresql+asyncpg://` to `postgresql://`, because LangGraph uses psycopg.
   - The Store is created with `index=None` at GA. Memory search is by key and prefix only.
2. `setup_langgraph.py` calls `await saver.setup()` and `await store.setup()`, prints "ok", and is idempotent.
3. Add `psycopg[binary,pool]` to the dependencies if the checkpointer needs it (note it in the PR).

**Acceptance**:
- [ ] Running it twice works, and the `checkpoints` and `store` tables exist

**Verify**: `uv run python -m docu.scripts.setup_langgraph && uv run python -m docu.scripts.setup_langgraph`

---

## Auth (ported) and workspace scope

<a id="t029"></a>
### T029 · Port the password hasher

**Depends on**: T003 · **Parallel**: yes · **Size**: S

**Read first**: `MAS/services/security.py` (`PasswordHasherService`)

**Files**: create `BE/auth/passwords.py` and `BT/unit/test_passwords.py`

**Steps**:

1. Port `PasswordHasherService` (`hash`, `verify`, `needs_rehash`) unchanged. **Don't port** `SessionTokenService`; T030 replaces it.
2. Add `validate_password(pw) -> None`, which raises `DomainError("invalid_request", details={"field":"password","reason":"too_short"})` when the password is under 10 characters.
3. Tests: hash then verify works, a wrong password fails, `needs_rehash` is true for weaker parameters, and short passwords are rejected.

**Acceptance**:
- [ ] Tests pass

**Verify**: `uv run pytest tests/unit/test_passwords.py -q`

---

<a id="t030"></a>
### T030 · DB sessions and CSRF

**Depends on**: T025, T029 · **Parallel**: no · **Size**: M

**Read first**: data-model.md › sessions; contracts/rest-api.md › Auth header line

**Files**: create `BE/auth/sessions.py`, `BE/auth/csrf.py`, and `BT/integration/test_sessions.py`

**Steps**:

1. `sessions.py`:

```python
COOKIE = "docu_session"
async def create_session(s, *, user_id, ip, user_agent) -> str          # returns raw id (32 bytes urlsafe)
async def resolve_session(s, raw: str) -> Session | None                # by sha256(raw); not revoked; not expired; updates last_seen_at (at most once/min)
async def revoke(s, *, session_id) -> None
async def revoke_all(s, *, user_id, except_id=None) -> int
def set_cookie(resp, raw, settings) / clear_cookie(resp)                # HttpOnly; Secure=settings.auth.cookie_secure; SameSite=Lax; Path=/; Max-Age=TTL
```

   Only `sha256(raw)` is stored. The cookie carries `raw`.
2. `csrf.py`:
   - Cookie `docu_csrf`: random, **not** HttpOnly, SameSite=Lax. It is set whenever a session cookie is set, and on `GET /v1/me`.
   - Middleware: for `POST`, `PUT`, `PATCH`, `DELETE`, require the header `x-csrf-token` to equal the cookie, compared in constant time.
   - **Exempt**: `/v1/auth/login`, `/v1/auth/register`, `/v1/auth/password/*`, `/v1/auth/verify-email`, `/v1/auth/google/*`, `/v1/webhooks/*`, `/v1/public/*`, and `/v1/_local-upload/*`.
   - Failure → `403 forbidden` with `details.reason = "csrf"`.
3. Tests: create then resolve works, revoke means resolve returns None, an expired session returns None, a CSRF mismatch gets 403, and an exempt path passes.

**Acceptance**:
- [ ] The raw session id is never stored or logged
- [ ] Tests pass

**Verify**: `uv run pytest tests/integration/test_sessions.py -q -m db`

---

<a id="t031"></a>
### T031 · Auth routes (port and extend)

**Depends on**: T030, T032 · **Parallel**: no · **Size**: L

**Read first**: contracts/rest-api.md › Auth and me (every auth row except Google, TOTP, and sessions, which are T126/T127); `MAS/api/routes/auth.py`; data-model.md › users, auth_tokens

**Files**: create `BE/api/routers/auth.py`, `BE/services/onboarding.py`, `BE/auth/tokens.py`, `BE/emails/{verify,reset}.{en,ar}.html`, and `BT/integration/test_auth_routes.py`

**Steps**:

1. `tokens.py`: `issue(s, user_id, kind, ttl) -> raw` stores `sha256`. `consume(s, raw, kind) -> user_id | None` is single use and checks expiry. The TTLs are `verify_email` 48 h and `password_reset` 1 h.
2. `POST /v1/auth/register` `{email, password, name, locale}`:
   - validate the password (T029) and lowercase the email
   - 409 `invalid_request` with `details.field="email"` if the email exists
   - create the user
   - if `FIRST_USER_IS_ADMIN` and no users exist yet → `is_platform_admin=True`, and log it at WARNING
   - `onboarding.create_personal_workspace(user)`: name "<name>'s workspace", `kind="personal"`, owner membership
   - send the verification email
   - create the session, set the cookies, and return `201 MeOut`. **Define `MeOut` in `BE/domain/api/me.py` in this task** (shape in T050 step 1). T050 reuses it.
3. `POST /v1/auth/login` `{email, password, totp?}`:
   - verify; rehash if needed
   - if `totp_secret_sealed` is set and there's no `totp` → `401 totp_required` (TOTP is checked in T127; until then accept no TOTP)
   - wrong credentials → `401 invalid_credentials` (same message for an unknown email)
   - an inactive user gets `invalid_credentials` too
4. `POST /v1/auth/logout` revokes the current session and clears the cookies.
5. `POST /v1/auth/verify-email {token}` sets `email_verified_at`. `POST /v1/auth/verify-email/resend` (session needed) has a 60 s cooldown kept in Redis.
6. `POST /v1/auth/password/forgot {email}` always returns 202. It sends the email only if the user exists. `POST /v1/auth/password/reset {token,password}` sets the password and calls `revoke_all`.
7. Rate limits come from T036 (`10/min per IP` and `5/min per email` on login, register, and password routes). Until T036 merges, leave `# TODO(T036)` comments.
8. Emails use T032 templates in the user's locale: subject, one sentence, a button link to `${PUBLIC_BASE_URL}/verify?token=…` or `/reset?token=…`.

**Tests**:
- register → 201 with the cookie set
- the first user is admin only when the flag is on
- duplicate email → 409
- login wrong → 401 with the same body for an unknown user and a wrong password
- verify works once and a second use is invalid
- forgot for an unknown email → 202 and no email (check Mailpit or patch the mail client)
- reset revokes the other sessions

**Acceptance**:
- [ ] Every row in the contract is implemented with exact status codes
- [ ] No user enumeration through login or forgot

**Verify**: `uv run pytest tests/integration/test_auth_routes.py -q -m db`

---

<a id="t032"></a>
### T032 · Mail client

**Depends on**: T003 · **Parallel**: yes · **Size**: S

**Files**: create `BE/core/mail.py`, `BE/emails/base.html`, and `BT/unit/test_mail.py`

**Steps**:

1. `async def send_mail(to: str, template: str, locale: str, **ctx) -> None` renders `BE/emails/{template}.{locale}.html` (Jinja2, autoescape on), which extends `base.html`.
   - `base.html` has `<html lang dir>`, a 600 px table layout, the logo placeholder, and a footer.
   - The subject comes from `{% block subject %}`.
2. Backends:
   - `smtp` uses `aiosmtplib` (add it to deps) and points at Mailpit in dev.
   - `ses` uses `boto3` `send_email` in `asyncio.to_thread`.
3. In tests, `settings.mail.backend = "memory"` appends to `docu.core.mail.OUTBOX` (a list) for assertions.

**Acceptance**:
- [ ] An Arabic email renders `dir="rtl"`
- [ ] The memory backend works in tests

**Verify**: `uv run pytest tests/unit/test_mail.py -q`

---

<a id="t033"></a>
### T033 · `current_user` and `workspace_scope` dependencies

**Depends on**: T030 · **Parallel**: no · **Size**: M

**Read first**: contracts/rest-api.md header (the `x-workspace-id` rule); IMPLEMENTER §5.4

**Files**: create `BE/api/deps.py` and `BT/integration/test_deps.py`

**Steps**:

1. `async def current_user(request) -> AuthedUser` reads the `docu_session` cookie and calls `resolve_session`. A missing cookie or an inactive user → 401 `unauthenticated`. It returns `AuthedUser(id, email, locale, is_platform_admin, email_verified)`.
2. `async def workspace_scope(request, user=Depends(current_user)) -> AsyncIterator[WorkspaceCtx]`:
   - reads the `x-workspace-id` header (missing → 400 `invalid_request`)
   - loads the membership with an `unscoped_session` (missing → **404** `not_found`, so existence is never revealed)
   - opens a `scoped_session(workspace_id)` and yields `WorkspaceCtx(session, user, workspace_id, role)`
3. `def require_role(*roles)` is a dependency factory → 403 `forbidden`.
4. `def require_verified(user)` → 403 `email_unverified`. Use it on every create route (documents, threads, turns).
5. `def require_platform_admin(user)` → 403.

**Tests**: no cookie → 401; another workspace's id → 404; viewer on `require_role("editor")` → 403; unverified on a create route → 403 `email_unverified`.

**Acceptance**:
- [ ] Tests pass

**Verify**: `uv run pytest tests/integration/test_deps.py -q -m db`

---

<a id="t034"></a>
### T034 · Permission helper `can()`

**Depends on**: T033 · **Parallel**: no · **Size**: M

**Read first**: data-model.md › Permissions matrix (every row) and the notes under it

**Files**: create `BE/services/permissions.py` and `BT/unit/test_permissions_helper.py`

**Steps**:

1. Define `Action = Literal["doc.view","doc.edit","doc.create","doc.delete","doc.share","doc.export","turn.answer","ws.members","ws.templates","ws.billing","ws.delete","ws.brand","ws.skills","ws.connectors"]`.
2. `def can(ctx: PermCtx, action: Action, doc: DocAccess | None = None) -> bool` is a **pure function**:
   - `PermCtx` has `role`, `user_id`, and `is_platform_admin`.
   - `DocAccess` has `owner_id`, `visibility`, `invite_role` (`"view"`, `"edit"`, or `None`), and `turn_started_by` (for `turn.answer`).
3. Implement the matrix as a dict `{action: {role: rule}}`. **Platform admin grants nothing here** (data-model.md note).
4. Add `def doc_permissions(ctx, doc) -> dict[str, bool]`. It returns `{"view","edit","share","export","delete"}` and is sent to the UI as the `permissions` field (used by T139).
5. Tests: a parametrized table that copies **every cell** of the matrix.

**Acceptance**:
- [ ] Every matrix cell has a test row
- [ ] The function is pure (no I/O)

**Verify**: `uv run pytest tests/unit/test_permissions_helper.py -q`

---

<a id="t035"></a>
### T035 · Security headers and error handlers

**Depends on**: T015, T008 · **Parallel**: yes · **Size**: S

**Files**: create `BE/core/security.py` and `BE/core/errors.py`. Modify `BE/api/app.py`. Create `BT/integration/test_errors.py`.

**Steps**:

1. Middleware headers on every response:
   - `X-Content-Type-Options: nosniff`
   - `Referrer-Policy: strict-origin-when-cross-origin`
   - `X-Frame-Options: DENY`
   - except `/s/*` (share pages may be embedded later; GA keeps DENY there too)
2. CSP on HTML responses (the SPA and `/s/*`):

```
default-src 'self'; img-src 'self' data: blob: <S3/CDN host>; style-src 'self' 'unsafe-inline'; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'
```

3. Exception handlers:
   - `DomainError` → envelope with its status
   - `RequestValidationError` → 400 `invalid_request` with `details.errors` (field paths)
   - `HTTPException` → mapped code
   - anything else → 500 `internal`, logged with the traceback, and never leaking the message
4. Tests: each handler produces the envelope shape.

**Acceptance**:
- [ ] Every error response matches `ErrorEnvelope`

**Verify**: `uv run pytest tests/integration/test_errors.py -q`

---

<a id="t036"></a>
### T036 · Rate limiting

**Depends on**: T008 · **Parallel**: yes · **Size**: S

**Read first**: contracts/rest-api.md › Rate limits

**Files**: create `BE/core/ratelimit.py` and `BT/integration/test_ratelimit.py`

**Steps**:

1. A token bucket in Redis, implemented as a Lua script that is atomic and returns `(allowed, retry_after_s)`.
2. A dependency factory `rate_limit(name: str, per: Literal["ip","user","workspace","email"], limit: int, window_s: int)`. Over the limit → `429 rate_limited` with a `Retry-After` header.
3. `key_ip(request)` uses the `X-Forwarded-For` first hop **only** when `settings.web.trust_proxy` is true.
4. Apply it to the auth routes now (replacing the TODOs from T031). Each later card applies its own limits.

**Acceptance**:
- [ ] The 11th login in a minute from one IP → 429 with `Retry-After`

**Verify**: `uv run pytest tests/integration/test_ratelimit.py -q -m redis`

---

## Credit ledger core (test-first)

<a id="t037"></a>
### T037 · Credit math tests (write first)

**Depends on**: T014 · **Parallel**: yes · **Size**: S

**Read first**: research.md R15; data-model.md › credit_ledger

**Files**: create `BT/unit/test_credits.py`

**Tests** (they import `docu.billing.prices` and `docu.billing.ledger`, which don't exist yet, so they fail):

1. `credits_for_usage(model="m", input_tokens=1000, output_tokens=500, cached_tokens=0, prices={...}, margin=1.3)` equals `ceil((1000*in + 500*out)/1e6 * margin / CREDIT_USD)`. `CREDIT_USD = 0.001` (1 credit = $0.001 of cost at margin).
2. Cached tokens are charged at the cached price.
3. A Hypothesis property: for any reserve R and actual A ≥ 0, `settle_delta(R, A) + refund(R, A) == -A`, and the balance never goes below `-R`.
4. Idempotency key formats: `reserve:{turn_id}`, `settle:{turn_id}`, `refund:{turn_id}`, `grant:{invoice_id}`, `image:{turn_id}:{call_id}`.

**Acceptance**:
- [ ] The tests fail with ImportError or AssertionError before T039/T040 land

---

<a id="t038"></a>
### T038 · Ledger integration tests (write first)

**Depends on**: T024 · **Parallel**: yes · **Size**: S

**Files**: create `BT/integration/test_ledger.py`

**Tests** (marker `db`):

1. Grant 100, then reserve 30 twice concurrently (`asyncio.gather` on two sessions). Both succeed and the balance is 40. Then reserve 50 → `InsufficientCredits`.
2. The same `idempotency_key` twice → the second call is a no-op and returns the original entry.
3. `UPDATE credit_ledger SET delta=0` → raises (the trigger).
4. `workspaces.credit_balance` equals `SUM(delta)` after a random sequence of operations (Hypothesis, 30 examples).


**Acceptance**:
- [ ] Every case listed above is its own test function (`test_<short_name>`)
- [ ] The tests run and **fail for the expected reason** (missing module or not implemented) until the implementation task lands
- [ ] No production code is added in this task

---

<a id="t039"></a>
### T039 · Ledger service

**Depends on**: T037, T038 · **Parallel**: no · **Size**: M

**Files**: create `BE/billing/ledger.py`

**Steps**:

1. Every function runs inside the caller's session/transaction, and first does `SELECT … FROM workspaces WHERE id=:w FOR UPDATE`:

```python
class InsufficientCredits(DomainError): ...        # code "insufficient_credits", 402
async def grant(s, *, workspace_id, amount, key, user_id=None, stripe_invoice_id=None) -> LedgerEntry
async def reserve(s, *, workspace_id, user_id, turn_id, amount) -> LedgerEntry   # raises if balance < amount
async def settle(s, *, workspace_id, turn_id, reserved, actual) -> None          # writes settle (−(actual−reserved) if actual>reserved) or refund (+(reserved−actual))
async def refund_all(s, *, workspace_id, turn_id, reserved) -> None              # failure/cancel path
async def charge_image(s, *, workspace_id, user_id, turn_id, call_id, amount) -> LedgerEntry
async def balance(s, *, workspace_id) -> int                                      # reads workspaces.credit_balance
```

2. Each write inserts a ledger row with `ON CONFLICT (idempotency_key) DO NOTHING RETURNING *`. If nothing comes back, fetch the existing row and return it without changing the balance. Otherwise update `workspaces.credit_balance += delta`.
3. Tenant scoping: the caller passes a `scoped_session` (the worker uses `scoped_session` with the turn's workspace).

**Acceptance**:
- [ ] T037 and T038 pass

**Verify**: `uv run pytest tests/unit/test_credits.py tests/integration/test_ledger.py -q -m "db or not db"`

---

<a id="t040"></a>
### T040 · Price table

**Depends on**: T037 · **Parallel**: yes · **Size**: S

**Files**: create `BE/billing/prices.py` and `backend/src/docu/data/model_prices.json`

**Steps**:

1. `model_prices.json` maps `{model_id: {input_per_mtok_usd, output_per_mtok_usd, cached_input_per_mtok_usd}}`. Put **placeholder values** in it, with a top-level `"_note": "placeholder — set real prices before billing goes live (T178)"`. The self-hosted model gets the admin-configured cost (default 0.2/0.6).
2. `credits_for_usage(...)` as tested in T037. An unknown model uses `"default"` and logs a WARNING once.
3. `IMAGE_CREDITS = 20` and `CREDIT_USD = 0.001`.
4. `estimate_reservation(effort, context_window) -> int` is a conservative maximum: `steps(effort) × (context_window × in_price + max_completion × out_price)`, capped at 2,000 credits.

**Acceptance**:
- [ ] T037 price tests pass

---

<a id="t041"></a>
### T041 · Free credits grant (temporary)

**Depends on**: T039, T031 · **Parallel**: no · **Size**: S

**Files**: create `BE/worker/tasks/credits.py`, modify `BE/services/onboarding.py`, and create `BT/integration/test_free_grant.py`

**Steps**:

1. On workspace creation (onboarding): `grant(amount=400, key=f"grant:signup:{workspace_id}")`.
2. Beat task `docu.credits.monthly_free_grant`, daily at 00:10 UTC: for each Free workspace whose last grant was over 30 days ago, grant `400 - max(balance, 0)` (top-up, never above 400), with key `grant:free:{workspace_id}:{yyyymm}`. Use `system_session`.
3. Mark the module with `# Replaced by plan-aware grant in T182`.

**Acceptance**:
- [ ] A new workspace has a balance of 400
- [ ] Running the task twice in a month grants once

**Verify**: `uv run pytest tests/integration/test_free_grant.py -q -m db`

---

## UI foundation (ux.md §2–§4)

<a id="t042"></a>
### T042 · Design tokens, fonts, and icons

**Depends on**: T007 · **Parallel**: no · **Size**: M

**Read first**: ux.md §2 (all of it), §2.6; `MAF/styles.css` (the `@theme` block and `.dark` block, to keep the token names)

**Files**: create `FE/styles/tokens.css`, `FE/styles/base.css`, `FE/assets/fonts/{ibm-plex-sans-arabic,inter,ibm-plex-mono}/*.woff2` with `OFL.txt`, and `FE/styles/tokens.test.ts`. Modify `FE/main.tsx`.

**Steps**:

1. `tokens.css`: `@import "tailwindcss";`, then `@custom-variant dark (&:where(.dark, .dark *));`, then `@theme { … }` with **every** token from ux.md §2.1, §2.3, and §2.4 (MA names kept, changed values applied, new tokens added). Add the `html.dark { … }` overrides from §2.2.
2. Type scale utilities: `.text-display`, `.text-h1`, `.text-h2`, `.text-h3`, `.text-body`, `.text-body-strong`, `.text-small`, `.text-caption`, per §2.3. Add `:lang(ar) .text-body, :lang(ar) .text-small { line-height: calc(... + 2px) }`.
3. `base.css`: `body { background: var(--color-canvas); color: var(--color-ink); font-family: var(--font-sans) }`, the focus-visible ring (`outline: 2px solid var(--color-primary-200); outline-offset: 2px`), and the reduced-motion rule (§2.4).
4. Self-host the fonts (same approach as T021).
5. Install `lucide-react`. Add `FE/components/ui/Icon.tsx`, a wrapper that sets size 16/20, stroke 1.75, and a `flip` prop that adds `rtl:-scale-x-100`.
6. `tokens.test.ts`: parse `tokens.css`, and assert contrast ≥ 4.5 for `ink`/`canvas`, `ink`/`surface`, `ink-2`/`surface`, `nav-active-ink`/`nav-active-bg`, white/`primary`, in **both** light and dark.

**Acceptance**:
- [ ] Ported MA components render with the new colors and no class changes
- [ ] The contrast test passes for both modes
- [ ] No Google Fonts requests

**Verify**: `pnpm --filter web test -- tokens`

---

<a id="t043"></a>
### T043 · UI primitives, set A

**Depends on**: T042 · **Parallel**: yes · **Size**: L

**Read first**: ux.md §4 rows 4.1–4.8, 4.17, 4.18, 4.30; ux.md §10 (focus and keyboard)

**Files**: create `FE/components/ui/{Button,IconButton,Pill,PillTabs,TextInput,SearchInput,Select,Checkbox,Radio,ColorSwatch,Tooltip,Badge,Kbd,index}.tsx` and `FE/components/ui/__tests__/primitivesA.test.tsx`

**Steps**:

1. Build each component exactly per its ux.md row: variants, sizes, and states. The props follow the native element and add these:
   - `Button`: `variant: 'primary'|'secondary'|'ghost'|'danger'`, `size: 'sm'|'md'|'lg'`, `icon?: LucideIcon`, `loading?: boolean`. While `loading`, it is disabled and the spinner replaces the icon.
   - `IconButton`: a required `label: string` becomes `aria-label` and the Tooltip text.
   - `Pill`: `selected?: boolean`, `icon?`. It is a `button` with `aria-pressed`.
   - `PillTabs`: `items: {value,label,icon?}[]`, `value`, `onChange`. Use `role="tablist"`/`"tab"`, and arrow keys move the selection (mirrored in RTL).
   - `Select`: a button with a Menu. It must be keyboard operable. (The Menu is in T044, so build T044's Menu first if you work alone, or stub it.)
   - `Checkbox`/`Radio`: `label`, `count?: number` (shown at the end in `ink-3`).
   - `ColorSwatch`: `color: string | 'multi'`, `selected`.
   - `Tooltip`: a 500 ms delay on hover and focus, positioned with CSS anchor fallback logic (no new dependency). It flips sides in RTL.
2. **Use only logical Tailwind classes** (IMPLEMENTER §7).
3. Tests: Button `loading` disables it, IconButton has an `aria-label`, PillTabs arrow keys work in LTR and RTL (set `dir` on the container), and Checkbox shows its count.

**Acceptance**:
- [ ] Every state in ux.md is reachable and shown in `/__ui` (T045)
- [ ] axe has no violations in the gallery

**Verify**: `pnpm --filter web test -- primitivesA`

---

<a id="t044"></a>
### T044 · UI primitives, set B

**Depends on**: T042 · **Parallel**: yes · **Size**: L

**Read first**: ux.md §4 rows 4.9, 4.12–4.16, 4.19–4.22; ux.md §10 (dialogs)

**Files**: create `FE/components/ui/{Card,Dialog,Menu,Popover,Sheet,Toast,CreditPill,EmptyState,Skeleton,Banner}.tsx`, `FE/components/ui/toast-store.ts`, and `FE/components/ui/__tests__/primitivesB.test.tsx`

**Steps**:

1. `Dialog`: use the native `<dialog>` element with `showModal()`. That gives a focus trap and Esc. Add backdrop click to close (unless `destructive`), `title`, `footer`, `size: 'sm'|'md'|'lg'`, and return focus to the trigger.
2. `Menu`/`Popover`: anchored to a trigger, `role="menu"` with `menuitem`s, ↑/↓/Home/End/Esc/typeahead, and it closes on outside click. Position below the trigger, aligned to the start (mirrored in RTL), and flip above when there is no room.
3. `Sheet`: slides in from the **end** side (`inset-inline-end: 0`), width 400 or full on `sm`, with an overlay, focus trap, and Esc. The `side='bottom'` variant has the 3 heights (closed/half/full) and a drag handle (used by T110).
4. `Toast`: Zustand `toast-store` with `toast({kind, message, action?})`. A `<Toaster/>` sits bottom-center, auto-hides after 4 s, pauses on hover, and uses `role="status"` with `aria-live="polite"`.
5. `CreditPill`: `{balance, allowance}`. Warning color under 10% and error color at 0. Clicking it navigates to `/settings/billing`.
6. `EmptyState`: `{illustration, title, subtitle?, action?}`.
7. `Skeleton`: `{className}`, with a shimmer that is off under reduced motion.
8. `Banner`: `{variant: 'info'|'warning'|'error', icon?, children, action?}`.
9. Tests: Dialog Esc closes it and returns focus, Menu keyboard navigation works, a Toast auto-hides (fake timers), and the CreditPill thresholds apply.

**Acceptance**:
- [ ] Every component works with the keyboard alone
- [ ] No new UI library dependency

**Verify**: `pnpm --filter web test -- primitivesB`

---

<a id="t045"></a>
### T045 · Dev UI gallery (`/__ui`)

**Depends on**: T043, T044, T018 · **Parallel**: no · **Size**: M

**Files**: create `FE/pages/dev/UiGallery.tsx` and `frontend/apps/web/tests/e2e/ui-gallery.spec.ts`. Modify `FE/router.tsx` (the route only when `import.meta.env.DEV`).

**Steps**:

1. One page with sections:
   - **Tokens**: color swatches with names, and the type scale
   - **Buttons**: every variant × size × state
   - **Inputs**
   - **Pills & tabs**
   - **Menus & dialogs** (with trigger buttons)
   - **Toasts**
   - **Banners**
   - **Empty states**
   - **Skeletons**
   - **Slides**: every layout × 4 themes, in `en` and `ar` fixtures, at widths 320 and 1100
2. Top controls: language (en/ar) and theme (light/dark).
3. Playwright: load `/__ui` in `en-desktop` and `ar-desktop`, light and dark, and take a full-page screenshot comparison (`toHaveScreenshot`, max diff 0.1%). Run `@axe-core/playwright`, and expect 0 violations.

**Acceptance**:
- [ ] The gallery is excluded from the production build (check `dist` for "UiGallery")
- [ ] Screenshot baselines are committed

**Verify**: `pnpm test:e2e -- ui-gallery`

---

<a id="t046"></a>
### T046 · Placeholder illustrations and logo

**Depends on**: T042 · **Parallel**: yes · **Size**: S

**Read first**: ux.md §9

**Files**: create `FE/assets/illustrations/placeholder-{create,empty-conversations,empty-documents,empty-filter,not-found,link-unavailable}.svg` and `FE/assets/brand/{logo-mark,logo-wordmark}.svg` (+ `-dark` variants)

**Steps**:

1. Draw simple geometric SVGs at the sizes in ux.md §9. They should be visibly placeholders: a soft violet tint, simple shapes, no text.
2. The logo mark is a simple monogram "D" in a rounded square. **It must not resemble** the reference product's mark.
3. Export each as an optimized SVG (under 4 KB).

**Acceptance**:
- [ ] Every asset exists at the right size, and EmptyState uses them

---

## Web shell

<a id="t047"></a>
### T047 · App shell (desktop)

**Depends on**: T043, T044, T046, T017 · **Parallel**: no · **Size**: L

**Read first**: ux.md §3.1 (wireframe and bullets), §3.3; `MAF/components/{AppShell,NavRail}.tsx`

**Files**: modify `FE/components/{AppShell,NavRail}.tsx`. Create `FE/components/{Sidebar,TopBar}.tsx`. Modify `FE/router.tsx`.

**Steps**:

1. Restyle the ported `NavRail`, `AppShell`, and the new `Sidebar` and `TopBar` to the ux.md §3.1 wireframe and measurements: rail 64, sidebar 240, top bar 56, item 36px high.
2. **Rail items** and **sidebar groups**, exactly as listed in §3.1. Show Admin only when `me.isPlatformAdmin`. The active item is chosen by route match.
3. **Workspace switcher slot**: render the current workspace name and plan badge. The full menu comes in T132, so use a static button for now.
4. **TopBar**: a title slot (pages set it with `useTopBar({title})`), `CreditPill` (balance from `GET /v1/billing` once it exists; until T179 use `me.workspaces[current].creditBalance` from `GET /v1/me`), `+ New blank` (calls `POST /v1/documents`, then navigates to `/doc/:id`; wire it in T095, so it's disabled now), and the avatar menu (Profile, Language, Theme, Sign out).
5. Pages without the shell: `/doc/:id`, `/s/:token`, `/login`, `/register`, `/verify`, `/forgot`, `/reset`, and present mode.
6. RTL: the rail sits on the right, purely through logical properties (check it in `ar`).
7. **Test ids**: `rail-<item>`, `sidebar-<item>`, `topbar-credits`, `topbar-new-blank`, `topbar-avatar`.

**Acceptance**:
- [ ] Matches ux.md §3.1 at 1440×900 in en and ar
- [ ] Keyboard: Tab reaches every nav item in visual order
- [ ] Active states are correct for every route

**Verify**: `pnpm test:e2e -- smoke` (extend smoke.spec to click every sidebar item and assert the URL)

---

<a id="t048"></a>
### T048 · Mobile shell

**Depends on**: T047 · **Parallel**: yes · **Size**: M

**Read first**: ux.md §3.2, §2.5

**Files**: create `FE/components/{MobileTabBar,MoreDrawer}.tsx` and modify `FE/components/AppShell.tsx`

**Steps**:

1. Below `md` (768px), hide the rail and sidebar and show `MobileTabBar` (56px, 5 items with labels, safe-area padding at the bottom).
2. "More" opens `MoreDrawer` (a T044 `Sheet`, side end, full height) with the remaining sidebar items and the avatar menu entries.
3. The TopBar on mobile shows the title, CreditPill, and avatar.

**Acceptance**:
- [ ] At 390px width, every nav destination is reachable in both languages
- [ ] Touch targets are at least 40×40

**Verify**: `pnpm test:e2e --project=en-mobile --project=ar-mobile -- smoke`

---

<a id="t049"></a>
### T049 · Auth pages and `useAuth`

**Depends on**: T031, T043, T044, T047 · **Parallel**: yes · **Size**: M

**Read first**: ux.md §5.1; `MAF/hooks/useAuth.tsx`, `MAF/pages/{LoginPage,RegisterPage}.tsx`, `MAF/components/{AuthLayout,PasswordField}.tsx`; contracts/rest-api.md › Auth

**Files**: modify `FE/hooks/useAuth.tsx`. Create `FE/pages/auth/{Login,Register,Verify,Forgot,Reset}.tsx` and `FE/components/{AuthLayout,PasswordField}.tsx` (ported). Modify `frontend/apps/web/tests/e2e/fixtures.ts` (the real `login` helper).

**Steps**:

1. Port `useAuth` and point it at `/v1/me`, `/v1/auth/login`, `/v1/auth/logout`, `/v1/auth/register`. It exposes `{me, status: 'loading'|'authed'|'anon', login, logout, register}`.
2. Build the pages per the ux.md §5.1 wireframe. Map errors from codes: `invalid_credentials` shows under the password field, `rate_limited` shows a banner, and `totp_required` reveals the TOTP field.
3. Register success shows the "Check your email" state with Resend (60 s countdown).
4. `/verify?token=` posts on mount and shows success (with a Continue button to `/`) or an invalid/expired state.
5. `/forgot` → a neutral success message. `/reset?token=` takes a new password with the strength hint.
6. Route guard: anonymous users on shell routes go to `/login?next=…`, and authenticated users on `/login` go to `/`.
7. If T003 has no `ENV` setting (`dev|test|prod`, default `dev`), add it to `BE/core/config`.
8. e2e `login(page, user)` helper: create the user through the API (`POST /v1/auth/register`, then mark it verified through a test-only endpoint `POST /v1/_test/verify` that exists **only** when `settings.env == "test"`; add it in this task), then log in through the UI.

**Acceptance**:
- [ ] The full flow register → verify (Mailpit link) → login works in both languages
- [ ] Error codes show the localized messages

**Verify**: `pnpm test:e2e -- auth` (create `tests/e2e/auth.spec.ts`: register, login, wrong password, logout)

---

<a id="t050"></a>
### T050 · `/v1/me` and language persistence

**Depends on**: T033 · **Parallel**: yes · **Size**: S

**Read first**: contracts/rest-api.md › `GET/PATCH /v1/me`

**Files**: create `BE/api/routers/me.py`, `FE/lib/direction.ts`, and `BT/integration/test_me.py`

**Steps**:

1. `GET /v1/me` returns `MeOut {user: {id,email,name,locale,digits,isPlatformAdmin,emailVerified}, workspaces: [{id,name,kind,role,plan,creditBalance}]}`. It also sets the `docu_csrf` cookie if it's missing.
2. `PATCH /v1/me {name?, locale?, digits?}` validates and returns `MeOut`.
3. `direction.ts`: `applyLocale(locale)` sets `<html lang dir>`, calls `i18n.changeLanguage`, and (if logged in) `PATCH /v1/me`. On load, the priority is `me.user.locale`, then the stored setting, then the browser.
4. Digits: export `formatNumber(n)` and `formatDate(d)` helpers that read the user's `digits` (ux.md §11).

**Acceptance**:
- [ ] Changing the language persists across devices (it's stored on the user)

**Verify**: `uv run pytest tests/integration/test_me.py -q -m db`

---

## Observability

<a id="t051"></a>
### T051 · Backend logging, tracing, Sentry

**Depends on**: T008, T009 · **Parallel**: yes · **Size**: S

**Files**: create `BE/core/logging.py`, `BE/core/otel.py`, and `BT/unit/test_logging.py`

**Steps**:

1. structlog JSON in production and pretty output in dev. Bind `request_id` (from the `X-Request-Id` header or a generated one, returned in the response), `user_id`, `workspace_id`, `turn_id` when known, and the OTel `trace_id`.
2. A **redaction processor**: drop the keys `password`, `token`, `api_key`, `authorization`, `cookie`, `text`, `content`, `prompt`, and `args` above DEBUG.
3. OTel: instrument FastAPI, SQLAlchemy, Celery, Redis, and httpx. Export over OTLP when `OTEL_EXPORTER_OTLP_ENDPOINT` is set, and do nothing otherwise.
4. Sentry: init when `SENTRY_DSN` is set, with the FastAPI and Celery integrations, `send_default_pii=False`.
5. Test: logging a dict with `password` and `content` at INFO leaves them out of the output.

**Acceptance**:
- [ ] Every log line has `request_id`, and turn logs have `turn_id`

**Verify**: `uv run pytest tests/unit/test_logging.py -q`

---

<a id="t052"></a>
### T052 · Frontend Sentry and error boundary

**Depends on**: T047 · **Parallel**: yes · **Size**: S

**Files**: create `FE/lib/sentry.ts` and `FE/components/ErrorBoundary.tsx`

**Steps**:

1. Init `@sentry/react` only when `import.meta.env.VITE_SENTRY_DSN` is set. Use `sendDefaultPii: false`, and a `beforeSend` that strips request bodies.
2. `ErrorBoundary` wraps each route. The fallback is an EmptyState "Something went wrong" with `Reload`, localized.

**Acceptance**:
- [ ] Throwing inside a page shows the fallback, and the rest of the shell still works
