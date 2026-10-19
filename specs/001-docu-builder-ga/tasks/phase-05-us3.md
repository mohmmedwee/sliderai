# Phase 5: US3, templates and themes (task cards)

Before any card, read [IMPLEMENTER.md](../IMPLEMENTER.md). **Story test**: quickstart.md › US3.

---

<a id="t111"></a>
### T111 · Template API tests (write first)

**Depends on**: T027 · **Parallel**: yes · **Size**: S

**Read first**: contracts/rest-api.md › Templates and themes

**Files**: create `BT/integration/test_templates.py`

**Cases**:

1. `GET /v1/templates` returns 24 system templates. `facets.category`, `facets.color`, `facets.format`, and `facets.lang` counts add up correctly.
2. `?category=education&color=green` returns only matches, and the **facets are computed over the other filters**. A facet's own dimension ignores its own filter: the category counts honor `color` and `format` but not `category`.
3. `?q=water` matches `name_en`, `name_ar`, and card titles (ILIKE).
4. `POST /v1/templates {documentId, name, category}` as admin → 201 and visible only in that workspace. As an editor → 403.
5. `DELETE` of a system template → 403. A workspace template → 204.
6. `GET /v1/themes` returns 26 system themes plus the workspace's own.


**Acceptance**:
- [ ] Every case listed above is its own test function (`test_<short_name>`)
- [ ] The tests run and **fail for the expected reason** (missing module or not implemented) until the implementation task lands
- [ ] No production code is added in this task

---

<a id="t112"></a>
### T112 · Template-following eval (write first)

**Depends on**: T088 · **Parallel**: yes · **Size**: M

**Files**: create `evals/datasets/templates.jsonl` and fill in `evals/scorers/no_template_copy.py`

**Steps**:

1. 20 cases: `{template_id, prompt (on a different topic than the template), locale}`.
2. Scorers:
   - **follows_layouts**: the share of the draft's first N slides whose layout equals the template's card layouts in order
   - **theme_match**: `draft.theme_id == template.theme_id`
   - **no_template_copy**: 1 − (the share of template card titles and bodies with more than 60% token overlap with any draft text)

**Acceptance**:
- [ ] Baseline recorded. Target follows_layouts ≥ 0.8, no_template_copy ≥ 0.95.

---

<a id="t113"></a>
### T113 · Template and theme routes

**Depends on**: T111 · **Parallel**: no · **Size**: M

**Files**: create `BE/api/routers/{templates,themes}.py`, `BE/db/repositories/templates.py`, and `BE/domain/api/templates.py`

**Steps**:

1. The list query covers system templates (`workspace_id IS NULL`) and the current workspace's. Apply the filters. Compute the facets with one SQL per dimension, each using the **other** filters (see T111 case 2).
2. Response item: `{id, name: {en, ar}, category, format, themeId, colors, lang, firstCard, cardCount, workspaceOwned}`. `firstCard` is for the CSS preview. `GET /v1/templates/{id}` returns all the cards.
3. `POST /v1/templates` (admin): copy the document's slides as `cards` (strip ids), plus the name, category, `format` from the doc, `theme_id`, `colors` (the theme's tags), and `lang` (detect by Arabic ratio).
4. Themes route: system plus workspace themes.

**Acceptance**:
- [ ] T111 passes

---

<a id="t114"></a>
### T114 · Template in the agent context

**Depends on**: T113, T068 · **Parallel**: no · **Size**: S

**Read first**: contracts/agent-tools.md › Context message (`template`); the prompt rule 5

**Files**: modify `BE/agent/context.py` and `BE/worker/turn_runtime.py`

**Steps**:

1. When `thread.template_id` is set, load the template and pass `{id, themeId, cards:[{layout, kicker?, title, body?, points?}]}` into the context message. Card text is kept, because the model needs to see the structure, but cut to 120 characters per field.
2. Add a line inside the `<document_context>` block: `"templateRule": "Follow this card order and layouts and use themeId. Do not reuse its text."`
3. Only for the **first** turn of a thread, or when the user mentions the template. After the first commit, the doc already has the structure. Pass `template=None` afterwards, to keep the prompt small.

**Acceptance**:
- [ ] The template eval (T112) meets its targets with the real model (eval comment on the PR)

---

<a id="t115"></a>
### T115 · Template library page

**Depends on**: T113, T043, T044 · **Parallel**: yes · **Size**: L

**Read first**: ux.md §5.6 (the wireframe and every bullet); §4.10 TemplateCard

**Files**: create `FE/pages/Templates.tsx`, `FE/features/library/{TemplateGrid,TemplateFilters,TemplateCard}.tsx`, and `FE/features/library/useTemplateQuery.ts`

**Steps**:

1. Filters and query state live in the URL (`useSearchParams`): `q`, `format`, `category` (multi, comma separated), `color` (multi), `lang` (multi), `sort`.
2. `TemplateFilters` (260px, on the end side):
   - **Format**: Radio
   - **Category**: Checkboxes with counts. Show 5, then "Show N more".
   - **Color**: Swatches, multi-select
   - **Language**: Checkboxes with counts
   - Each section collapses with ˄/˅.
3. `TemplateCard`: the thumbnail is `<Slide width={card width} slide={firstCard} theme={…}>`, never an image. Under it, the localized name and a format icon. Hover shows a ring and a "Use" overlay button.
4. Grid: 3 to 6 columns by width. Empty state with `Clear filters`.
5. Mobile: the filters move into a `Filters` button that opens a `Sheet`.
6. **Pick mode** (`?pick=1`, from the composer's "Choose template"): clicking a card attaches it (T117) and navigates back to `/`.

**Acceptance**:
- [ ] Filters, counts, and the URL stay in sync
- [ ] It matches the ux.md §5.6 wireframe in en and ar

---

<a id="t116"></a>
### T116 · Template preview dialog

**Depends on**: T115 · **Parallel**: yes · **Size**: S

**Read first**: ux.md §5.6 ("Clicking a card opens a preview dialog")

**Files**: create `FE/features/library/TemplatePreview.tsx`

**Steps**: a `Dialog` of size `lg`. A carousel of every card (`GET /v1/templates/{id}`) with ‹ › and dots, mirrored in RTL. Show the name, category, format, and the `Use template` primary button. Use template follows spec US3 scenario 2: if the composer draft (kept in `sessionStorage`) has text, start a thread right away. Otherwise attach the template and go to Create.

**Acceptance**:
- [ ] The keyboard works (arrows switch cards, Esc closes)

---

<a id="t117"></a>
### T117 · Attached template card in the composer

**Depends on**: T081, T113 · **Parallel**: yes · **Size**: S

**Read first**: ux.md §5.2 ("Attached template" bullet; screenshot 5)

**Files**: create `FE/components/chat/TemplateCard.tsx` and `FE/stores/composerDraft.ts`

**Steps**:

1. `composerDraft` store (persisted in sessionStorage): `{text, format, templateId, attachments}`.
2. When `templateId` is set, render a card inside the composer above the textarea: a thumbnail (`<Slide width={96}>` of the first card), the name, the label "Template" with an icon, and ✕ to remove. Set the format from the template.
3. `POST /v1/threads` includes `templateId`.

**Acceptance**:
- [ ] Attach, remove, and send with a template all work, and the template survives a page refresh

---

<a id="t118"></a>
### T118 · Suggested templates on Create

**Depends on**: T117 · **Parallel**: yes · **Size**: S

**Read first**: ux.md §5.2 (Suggested templates)

**Files**: create `FE/features/library/Suggested.tsx`

**Steps**: `GET /v1/templates?format=<selected>&lang=<ui locale>&limit=6` falls back to any language when there are fewer than 6. Show 6 cards (180px) with names under them. Click: attach, and if the draft has text, send right away. Below them, the `View all templates` button goes to `/templates`.

**Acceptance**:
- [ ] The suggestions change with the format chip and the UI language

---

<a id="t119"></a>
### T119 · Save as template

**Depends on**: T113, T084 · **Parallel**: yes · **Size**: S

**Files**: create `FE/features/library/SaveAsTemplate.tsx`. Modify the editor's ⋯ menu and `FE/pages/Templates.tsx` (the Workspace templates section).

**Steps**:

1. Editor ⋯ menu → "Save as template" (only for workspace admins) opens a Dialog with name (en, ar) and category, then `POST /v1/templates`, then a toast.
2. On the Templates page, the app sidebar section from ux.md §5.6 gets "Workspace templates" (the `owned=workspace` filter, in the contract) and "Created by you" (`createdBy=me`). "Recent" lists templates used in the last 30 days (`threads.template_id` by the user).

**Acceptance**:
- [ ] A saved template appears under Workspace templates, and other workspaces can't see it

---

<a id="t120"></a>
### T120 · Patterns (theme) panel

**Depends on**: T099, T096 · **Parallel**: no · **Size**: M

**Read first**: ux.md §5.4.6 (every bullet; screenshot 4)

**Files**: create `FE/features/editor/Patterns.tsx` and `FE/features/editor/ThemeTile.tsx`

**Steps**:

1. The panel replaces the agent column, at the same width, sliding in from the end side. It has a header, a subtitle, ✕, PillTabs (Coordinated, Custom (disabled, "Coming soon")), and filter chips.
2. `ThemeTile`: a mini slide with a paper rectangle, 3 ink lines, and an accent bar, drawn from the tokens (no `<Slide>`, for speed). The current theme has a violet ring.
3. **Hover preview**: set a temporary `previewThemeId` in the store, which the Canvas uses instead of the doc theme. It reverts on mouse leave.
4. **Click**: `PATCH {baseVersion, ops:[{op:'set_theme', themeId}], revisionSource:'theme'}`, then the toast "Theme applied" with `Undo` (Undo PATCHes the previous theme back).
5. No model call and no credits.
6. Disabled during turns.

**Acceptance**:
- [ ] The theme changes instantly, a revision with source `theme` exists, and the credit balance is unchanged

---

<a id="t121"></a>
### T121 · e2e test: templates and themes

**Depends on**: T115–T120 · **Parallel**: yes · **Size**: S

**Files**: create `frontend/apps/web/tests/e2e/templates.spec.ts`

**Cases** (en and ar desktop):

1. Filter Education and Green; the counts update and the URL holds the filters.
2. Open a preview, then Use template; the card appears in the composer.
3. Send `#script:from_template` (a fake script that uses the template's layouts) and the editor opens.
4. Patterns: hover changes the canvas, click applies it, and the toast Undo restores it.
5. Save as template (as admin); it appears under Workspace templates.

**Acceptance**:
- [ ] All 5 cases pass in `en-desktop` and `ar-desktop`

**Verify**: `pnpm test:e2e -- templates`
