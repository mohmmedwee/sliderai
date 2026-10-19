# Phase 10: US8, images on slides (task cards)

Before any card, read [IMPLEMENTER.md](../IMPLEMENTER.md). **Story test**: quickstart.md › US8.

---

<a id="t169"></a>
### T169 · `generate_image` tests (write first)

**Depends on**: T071 · **Parallel**: yes · **Size**: S

**Files**: create `BT/unit/test_image_tool.py` and `BT/integration/test_image_flow.py`

**Cases**:

1. Policy `ask`: the approval card has `kind=generate_image`, the prompt, `slideId`, and `credits=IMAGE_CREDITS`.
2. Deny → no provider call and no charge.
3. Allow, but moderation flags the prompt → "Error: moderation_blocked: …" and no charge.
4. Allow, and the provider (respx mock) returns an image → an asset is stored, the ledger has an `image` entry with key `image:{turn}:{call}`, `slide.image` is set with `alt`, and a `doc_patch` is emitted.
5. Provider 500 → "Error: provider_error" and no charge.
6. Balance below `IMAGE_CREDITS` → "Error: insufficient_credits" before the provider is called.
7. A Free plan workspace → the tool is not in `build_tools` specs (once T178 lands; until then gate with the flag `images`).


**Acceptance**:
- [ ] Every case listed above is its own test function (`test_<short_name>`)
- [ ] The tests run and **fail for the expected reason** (missing module or not implemented) until the implementation task lands
- [ ] No production code is added in this task

---

<a id="t170"></a>
### T170 · Assets model and image provider adapter

**Depends on**: T024 · **Parallel**: no · **Size**: M

**Read first**: data-model.md › assets

**Files**: create `BE/db/models/assets.py` (or extend the minimal one from T144), `backend/alembic/versions/0006_assets.py`, `BE/agent/images/{__init__,provider,openai_images}.py`, and `BE/services/assets.py`

**Steps**:

1. `assets` per data-model.md, plus `workspace_id` and RLS.
2. `ImageProvider` protocol: `async generate(prompt: str, *, aspect: Literal["16:9","1:1","4:5"]) -> bytes`. One adapter for an OpenAI-compatible `/images/generations` (configurable `IMAGES_BASE_URL`, `IMAGES_MODEL`, `IMAGES_API_KEY`), and a `FakeImageProvider` that returns a generated gradient PNG.
3. `assets.save_image(bytes, kind, meta) -> Asset`: Pillow validates and strips EXIF, stores the original as WebP plus the variants 1280w, 640w, and 320w, and records width and height.
4. `assets.url(asset, variant)` returns a CDN or presigned URL.


**Acceptance**:
- [ ] `save_image` strips EXIF and creates the 3 variants with the correct widths
- [ ] `FakeImageProvider` works offline
- [ ] The RLS block is in the migration

**Verify**: `uv run pytest tests/unit/test_assets.py -q` (write it: EXIF strip, variants)

---

<a id="t171"></a>
### T171 · `generate_image` tool

**Depends on**: T169, T170 · **Parallel**: no · **Size**: M

**Read first**: contracts/agent-tools.md (`generate_image`); IMPLEMENTER §6.6 (I/O tools run only after approval)

**Files**: create `BE/agent/tools/image.py` and modify `BE/agent/tools/__init__.py` and `BE/agent/nodes/tools.py`

**Steps**:

1. The runner is `async def run(args: GenerateImageArgs, ctx) -> tuple[str, list[DocOp]]`. It runs only after the approval returns `allow`. Its steps, in order:
   1. check the slide exists and its layout is `hero` or `split` (otherwise error `"Error: invalid_slide: images only on hero or split"`)
   2. moderation (T160)
   3. balance check
   4. provider call
   5. save the asset
   6. `ledger.charge_image`
   7. return an `update_slide` op setting `image: {assetId, alt}`
2. The tools node treats the returned ops like a document tool: it applies them to the draft through the reducer and emits `doc_patch`.
3. Register it in `build_tools` only when the plan allows images.

**Acceptance**:
- [ ] T169 passes

---

<a id="t172"></a>
### T172 · Image upload

**Depends on**: T170 · **Parallel**: no · **Size**: S

**Read first**: contracts/rest-api.md (`POST /v1/assets/uploads`)

**Files**: create `BE/api/routers/assets.py` and `BE/worker/tasks/image.py`

**Steps**:

1. Presign an upload (images only: `image/png`, `jpeg`, `webp`, ≤ 10 MB).
2. `POST /v1/assets/{id}/complete` checks the magic bytes and enqueues `docu.image_variants`, which builds the variants.
3. Return `{assetId, url}`. The editor sets `slide.image` with a normal PATCH.


**Acceptance**:
- [ ] A PNG renamed `.pdf` is rejected at complete
- [ ] Variants exist after the task runs

**Verify**: `uv run pytest tests/integration/test_asset_upload.py -q -m db`

---

<a id="t173"></a>
### T173 · Render slide images

**Depends on**: T018, T170 · **Parallel**: yes · **Size**: S

**Read first**: ux.md §7 (`hero`, `split`)

**Files**: modify `FP/slides/src/layouts/{Hero,Split}.tsx` and add `FP/slides/src/ImageField.tsx`

**Steps**:

1. When `slide.image` is set, render `<img src={resolveAssetUrl(assetId, width)} alt={alt}>` with `object-fit: cover` and `object-position: {focal.x*100}% {focal.y*100}%` (default 50% 50%) inside the field box.
2. `resolveAssetUrl` is passed in as a prop to `<Slide>` (`assetUrl?: (id, w) => string`), so the package stays free of app imports.
3. The export render page passes a resolver that uses signed URLs.


**Acceptance**:
- [ ] `<Slide>` with `image` renders `<img>` with the right `object-position`
- [ ] Without `assetUrl` it falls back to the field gradient

**Verify**: `pnpm --filter slides test`

---

<a id="t174"></a>
### T174 · Image picker in the editor

**Depends on**: T172, T173, T099 · **Parallel**: yes · **Size**: M

**Files**: create `FE/features/editor/ImageField.tsx`

**Steps**:

1. On a selected hero or split slide, show a floating toolbar over the field with: Upload, Replace, Remove, Alt text (an inline input), and Focal point (click on the image to set it).
2. Upload follows the T172 flow, then a PATCH sets `image`.
3. Show a "Generate with AI" item that inserts the composer text "Add an image of … to slide N" (it helps users discover the agent tool, without calling it directly).

**Acceptance**:
- [ ] Upload, alt, and focal point persist and render in the editor, the share viewer, and the PDF
