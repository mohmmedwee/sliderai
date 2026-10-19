# Phase 7: US5, share and present via link (task cards)

Before any card, read [IMPLEMENTER.md](../IMPLEMENTER.md). **Story test**: quickstart.md › US5.

---

<a id="t140"></a>
### T140 · Sharing tests (write first)

**Depends on**: T128 · **Parallel**: yes · **Size**: S

**Read first**: contracts/rest-api.md › Sharing

**Files**: create `BT/integration/test_sharing.py`

**Cases**:

1. `PUT /sharing {publicLink:true}` → a link is created, and `GET /sharing` returns the `link.url` (`{PUBLIC_BASE_URL}/s/<token>`).
2. `GET /v1/public/<token>` (no cookie) → 200 with `{title, format, themeId, slides}` **and no other fields**. Assert the exact key set: no ids of users or workspaces, and no notes.
3. Rotate → the old token gives 404 and the new one works.
4. `publicLink:false` → the token gives 404.
5. Visibility `private` → a workspace viewer can't open it (404). `workspace` → they can.
6. Per-document invite by email → an existing user gets access, and an unknown email gets an invitation (T130).
7. Public endpoint rate limit: 121 requests in a minute from one IP → 429.
8. `view_count` increments, at most once per IP per 10 min (Redis set).


**Acceptance**:
- [ ] Every case listed above is its own test function (`test_<short_name>`)
- [ ] The tests run and **fail for the expected reason** (missing module or not implemented) until the implementation task lands
- [ ] No production code is added in this task

---

<a id="t141"></a>
### T141 · Share links model and sharing service

**Depends on**: T140 · **Parallel**: no · **Size**: M

**Read first**: data-model.md › share_links, documents.visibility

**Files**: create `BE/db/models/share.py`, `backend/alembic/versions/0003_share_links.py`, and `BE/services/sharing.py`

**Steps**:

1. `share_links` is a tenant table and gets the RLS block. But the **public lookup by token** must work without a workspace scope. Add `async def resolve_public(factory, token) -> PublicDoc | None` that uses `system_session` **in the service layer**, with a narrow query that returns only the public fields. This is the one sanctioned exception to "no system_session in the API": the API calls the service, not the session. Document it in the function docstring. The T025 guard checks only `BE/api`.
2. The token is 24 bytes urlsafe, and only its sha256 is stored.
3. Service functions: `get_sharing(doc)`, `set_visibility(doc, v)`, `enable_link(doc)`, `disable_link(doc)`, `rotate_link(doc)`, `invite(doc, email, role)` (calls T130), `remove_access(doc, user_id)`. Every one writes an audit entry (`share.*`).

**Acceptance**:
- [ ] T140 cases 1, 3, 4, and 5 pass at the service level

---

<a id="t142"></a>
### T142 · Sharing routes

**Depends on**: T141 · **Parallel**: no · **Size**: S

**Files**: create `BE/api/routers/sharing.py`

**Steps**: implement the Sharing rows of the contract (everything except the public routes, which are T143). Permission `doc.share`. `GET /sharing` returns the people list (`document_access` joined with users), pending invites, the visibility, and the link.

**Acceptance**:
- [ ] T140 cases 1, 5, and 6 pass

---

<a id="t143"></a>
### T143 · Public share page and public API

**Depends on**: T141, T144 · **Parallel**: no · **Size**: M

**Read first**: ux.md §5.11; contracts/rest-api.md (`GET /s/:token`, `GET /v1/public/:token`)

**Files**: create `BE/api/share_page.py`, `BE/api/routers/public.py`, and `BE/templates/share.html` (Jinja2)

**Steps**:

1. `GET /v1/public/{token}`: rate limited (120/min per IP), `Cache-Control: public, max-age=60`, and the view count (T140 case 8).
2. `GET /s/{token}` returns HTML:
   - `<html lang dir>` from the doc's language (detect by the Arabic ratio of the titles)
   - `<title>`, `og:title`, `og:description` (the first slide's body, 160 characters), `og:image` (the thumbnail URL from T144, absolute), `twitter:card=summary_large_image`
   - the script and style tags of the **share-viewer entry** from the Vite manifest (T146 builds `share.html` as a separate entry; read `web/dist/.vite/manifest.json` to find the hashed files)
   - an invalid token → a 404 page with the same shell and the "link unavailable" message (localized by `Accept-Language`)
3. No auth, no CSRF, and `X-Robots-Tag: noindex` (public link documents shouldn't be indexed at GA).

**Acceptance**:
- [ ] The page source contains the OG tags
- [ ] It works in the single-host Docker image
- [ ] T140 cases 2 and 7 pass

---

<a id="t144"></a>
### T144 · Thumbnail task

**Depends on**: T075, T165 (the export route renderer). **Until T165 exists, build the minimal `/_export/{id}?slide=0` route yourself here, and T165 extends it.** · **Parallel**: no · **Size**: M

**Files**: create `BE/worker/tasks/thumbnail.py` and `BE/worker/render.py` (shared with T166)

**Steps**:

1. `render.py`:
   - `async def open_render_page(doc_id, version, *, slide: int | None, watermark: bool)` launches a Playwright Chromium (one browser per worker process, reused) and opens `${INTERNAL_WEB_URL}/_export/{doc_id}?v={version}&slide={n}&token={signed}`.
   - The token is `itsdangerous`, 5 min, bound to doc and version.
   - It waits for `window.__DOCU_READY__ === true`, which T165 sets after fonts load.
2. The `thumbnail` task:
   - debounced: enqueued after each commit with `countdown=10`, skipped if the doc version changed since enqueue
   - renders slide 0 at 1280×720, screenshots it, resizes to 640×360 WebP (Pillow)
   - stores it as an `assets` row (`kind=thumbnail`); create the minimal `assets` model now if T170 hasn't, and T170 extends it
   - sets `documents.thumbnail_asset_id`
3. Enqueue it from `commit_turn` (T075) and from manual saves (T096, debounced).

**Acceptance**:
- [ ] After a commit, the document has a thumbnail within about 15 s

---

<a id="t145"></a>
### T145 · Share dialog

**Depends on**: T142 · **Parallel**: yes · **Size**: M

**Read first**: ux.md §5.10 (the wireframe)

**Files**: create `FE/features/sharing/ShareDialog.tsx`, and enable the editor's Share button

**Steps**: build the wireframe exactly.
- **Invite row**: email, role Select (Can view or Can edit), and Invite.
- **People list**: an avatar, the name, and a role Select or Remove. The owner row is fixed.
- **General access Select**: Private, Workspace, or Anyone with the link, with a one-line explanation of each.
- **Copy link** (only when the public link is on), with a toast.
- **Reset link** with a confirm Dialog.
- **Done**.

Viewers see the dialog read-only (Copy link only).

**Acceptance**:
- [ ] T147 case 1 passes

---

<a id="t146"></a>
### T146 · Share viewer entry

**Depends on**: T143, T108 · **Parallel**: yes · **Size**: M

**Read first**: ux.md §5.11; plan.md Constraints (viewer ≤ 120 KB)

**Files**: create `frontend/apps/web/share.html`, `FE/share/main.tsx`, and `FE/share/ShareViewer.tsx`. Modify `vite.config.ts` (multi-page `build.rollupOptions.input = {main: 'index.html', share: 'share.html'}`).

**Steps**:

1. `main.tsx` does **not** import the router, React Query, or the app's i18n bundle. It uses a tiny local dictionary for its 6 strings, keyed by `navigator.language` and the doc direction.
2. It reads the token from `location.pathname`, fetches `/v1/public/{token}`, and renders a header (title and `Present`), slides stacked (`<Slide>` from `FP/slides`, max 1100px), and on the Free plan a "Made with Docu Builder" badge at the bottom-end. Add `badge: boolean` to the public payload from the workspace plan (T143).
3. Present reuses `Present.tsx` (T108). Make sure that component has no app-only imports.
4. Mobile: full-width slides with 16px gutters.

**Acceptance**:
- [ ] `share` entry JS is ≤ 120 KB gzip (check `vite build` output)
- [ ] It renders correctly in a private window

---

<a id="t147"></a>
### T147 · e2e test: sharing

**Depends on**: T145, T146 · **Parallel**: yes · **Size**: S

**Files**: create `frontend/apps/web/tests/e2e/share.spec.ts`

**Cases**:

1. In the editor, Share → Anyone with the link → Copy. Open the link in a **new browser context** (no cookies); the slides render and Present works.
2. Check that the page HTML has `og:title`.
3. Reset the link; the old URL shows "link unavailable".
4. Mobile project: the viewer renders without horizontal scrolling.

**Acceptance**:
- [ ] All 4 cases pass

**Verify**: `pnpm test:e2e -- share`
