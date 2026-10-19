# Phase 9: US7, export (task cards)

Before any card, read [IMPLEMENTER.md](../IMPLEMENTER.md). **Story test**: quickstart.md › US7.

**Exit check**: PDF pages match the editor (visual snapshots), PPTX opens with editable RTL text and native tables and charts, and 95% of exports finish in under 20 s.

---

<a id="t162"></a>
### T162 · Visual export tests (write first)

**Depends on**: T018 · **Parallel**: yes · **Size**: M

**Files**: create `BT/integration/test_export_visual.py` and `BT/fixtures/export_docs/*.json`

**Steps**:

1. Fixtures: 7 layouts × 4 themes (`paper`, `midnight`, `ember`, `lagoon`) × {en, ar} = 56 slides, grouped into 8 documents.
2. For each document:
   - render the editor reference by opening `/_export/{id}?slide=n` in Playwright and taking a screenshot at 1280×720
   - export to PDF through the export task (T166)
   - rasterize each PDF page at 1280×720 (`fitz` `get_pixmap(dpi)` scaled)
   - compare with `pixelmatch`-like logic (a Python implementation: per-pixel delta over 0.1 counts as different), allowing at most 0.5% different pixels
3. Store the baselines under `BT/fixtures/export_baselines/`. A `--update-baselines` flag regenerates them.

Mark the test `slow`. CI runs it in the nightly job (add a `nightly.yml` with `schedule: cron`).


**Acceptance**:
- [ ] Every case listed above is its own test function (`test_<short_name>`)
- [ ] The tests run and **fail for the expected reason** (missing module or not implemented) until the implementation task lands
- [ ] No production code is added in this task

---

<a id="t163"></a>
### T163 · PPTX structure tests (write first)

**Depends on**: T014 · **Parallel**: yes · **Size**: S

**Files**: create `BT/unit/test_pptx.py`

**Cases** (open the output with python-pptx):

1. Every slide's title is a text frame (placeholder or textbox) containing the exact title.
2. Arabic paragraphs have `a:pPr/@rtl="1"` and `algn="r"`.
3. A `table` slide has a `GraphicFrame` with `has_table`, with the right rows and columns and the header text.
4. A `chart` slide has `has_chart`, with the chart type mapped (bar → `COLUMN_CLUSTERED`, line → `LINE`, pie → `PIE`, donut → `DOUGHNUT`) and the series values equal to the data.
5. Speaker notes contain `slide.notes`.
6. A watermark on the Free plan is a small textbox with "Docu Builder".


**Acceptance**:
- [ ] Every case listed above is its own test function (`test_<short_name>`)
- [ ] The tests run and **fail for the expected reason** (missing module or not implemented) until the implementation task lands
- [ ] No production code is added in this task

---

<a id="t164"></a>
### T164 · Exports model and routes

**Depends on**: T024 · **Parallel**: no · **Size**: S

**Read first**: contracts/rest-api.md › Export; data-model.md › exports (the state machine)

**Files**: create `BE/db/models/exports.py`, `backend/alembic/versions/0005_exports.py`, and `BE/api/routers/exports.py`

**Steps**:

1. The model per data-model.md, plus `workspace_id`, plus the RLS block.
2. `POST /v1/documents/{id}/exports {format}` requires `doc.export`.
   - Dedupe: if a `ready` export exists for the same `(document_id, version, format, watermark)`, return it.
   - Otherwise create the row `queued` and enqueue `export_pdf` (for pdf and png) or `export_pptx`.
   - `watermark = plan == "free"` (until T178, always true for Free).
3. `GET /v1/exports/{id}` returns `{status, url?}`, where `url` is a presigned GET (24 h) with `filename = <title>.<ext>` (safe Unicode).
4. Rate limit: 20/hour per user.


**Acceptance**:
- [ ] Dedupe returns the existing ready export for the same version and format
- [ ] Rate limit of 20 per hour per user is enforced
- [ ] The RLS block is in the migration

**Verify**: `uv run pytest tests/integration/test_exports.py -q -m db` (write this file: dedupe, permission, rate limit)

---

<a id="t165"></a>
### T165 · Internal export render route

**Depends on**: T018 · **Parallel**: no · **Size**: M

**Read first**: ux.md §7; T144 `render.py` (the token and `__DOCU_READY__` contract)

**Files**: create `FE/pages/ExportRender.tsx` (the route `/_export/:id`, outside the shell and outside the auth guard) and `BE/api/routers/export_render.py` (`GET /v1/_export/{id}?v&token`)

**Steps**:

1. Backend: verify the token (doc, version, 5 min), and return the doc content at **that version** (from `document_revisions`) plus the theme and `watermark`. No cookie needed.
2. The page renders `<Slide width={1280}>` for every slide, each in its own 1280×720 box with `page-break-after: always`. With `?slide=n`, it renders only slide n.
3. Print CSS: `@page { size: 1280px 720px; margin: 0 }`, no shadows, and `-webkit-print-color-adjust: exact`.
4. After `document.fonts.ready` and every image has loaded, set `window.__DOCU_READY__ = true`.
5. Exclude it from the main router guard. It must not call `/v1/me`.

**Acceptance**:
- [ ] Opening the route with a valid token renders the slides with no app chrome

---

<a id="t166"></a>
### T166 · PDF and PNG export task

**Depends on**: T164, T165, T144 · **Parallel**: no · **Size**: M

**Files**: create `BE/worker/tasks/export_pdf.py` (it uses `BE/worker/render.py` from T144)

**Steps**:

1. `docu.export_pdf(export_id)` on the `exports` queue: set the status `rendering`, open the render page (all slides), then:
   - **pdf**: `page.pdf(width="1280px", height="720px", print_background=True)`
   - **png**: screenshot each slide box (`locator.screenshot`), then zip them as `01.png`, `02.png`, …
2. Upload, set `asset_id`, and set the status `ready`. Errors → `failed`, with the error code logged.
3. Timeout 60 s. One browser per worker process, with a new context per job.

**Acceptance**:
- [ ] T162 passes (nightly), and a 20-slide export takes under 20 s locally

---

<a id="t167"></a>
### T167 · PPTX export task

**Depends on**: T163, T164 · **Parallel**: no · **Size**: L

**Read first**: ux.md §7 (layout geometry); research.md R14

**Files**: create `BE/worker/tasks/export_pptx.py` and `BE/export/pptx_builder.py`

**Steps**:

1. `build_pptx(doc: DocumentState, theme: Theme, *, watermark: bool) -> bytes` uses `Presentation()` with `slide_width=Emu(12192000)` and `slide_height=Emu(6858000)` (16:9), and the blank layout for every slide.
2. Geometry: convert the ux.md §7 percentages to EMU with the helper `box(x%, y%, w%, h%)`.
3. Per layout: text boxes at the §7 positions, the theme colors (`RGBColor.from_string`), and fonts (`font.name` = "IBM Plex Sans Arabic" or "Noto Naskh Arabic" for Arabic runs, "Inter" or "Fraunces" for Latin).
   - **Font substitution**: if the viewer doesn't have the font, PowerPoint falls back. Also set `a:latin`, `a:cs` (complex script) typefaces on each run through lxml, so Arabic picks the `cs` font.
4. **RTL**: for any paragraph whose text is more than 30% Arabic letters, set `pPr.set("rtl","1")` and `algn="r"` (in RTL, "r" is the start). Bullets keep the RTL order.
5. **Hero and split field**: a full or half rectangle with a solid fill. For a gradient, use `fill.gradient()` with 2 stops from the parsed `CssField`. For an image (US8), `add_picture` cropped to cover.
6. **Table**: `shapes.add_table(rows, cols, …)`. The header row is filled with the accent color, and numeric cells are aligned to the end.
7. **Chart**: `CategoryChartData()` with categories and series, then `add_chart(XL_CHART_TYPE…)`. Series colors come from T019's palette logic (port the TS function to Python in `BE/export/palette.py`).
8. Notes: `slide.notes_slide.notes_text_frame.text = notes`.
9. Watermark: a small textbox at the bottom-end, 10pt, 40% transparency.
10. The `docu.export_pptx` task builds, uploads, and sets `ready`.

**Acceptance**:
- [ ] T163 passes
- [ ] The file opens in PowerPoint and Keynote, and LibreOffice imports it (smoke test with `soffice --headless --convert-to pdf` in the nightly job)

---

<a id="t168"></a>
### T168 · Export menu

**Depends on**: T164 · **Parallel**: yes · **Size**: S

**Read first**: ux.md §5.4.9

**Files**: create `FE/features/export/ExportMenu.tsx`, and enable the editor's Export button

**Steps**:

1. The Menu items are PDF, PowerPoint (.pptx), and Images (.png, zip). On Free, each item shows the caption "Includes small watermark".
2. Click: `POST`, then poll `GET /v1/exports/{id}` every 1 s, showing a spinner and "Preparing…" in the item, then a toast with Download (an `<a download>` to the signed URL).
3. Failure shows a toast error with Retry.

**Acceptance**:
- [ ] Downloads work for all 3 formats in both languages
