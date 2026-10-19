# Phase 6: US4, accounts, workspaces, and roles (task cards)

Before any card, read [IMPLEMENTER.md](../IMPLEMENTER.md). **Story test**: quickstart.md › US4.

**Exit check**: the permissions matrix test is green (SC-007). Invite → accept → a viewer is read-only, in both languages.

---

## Tests first (T122–T125)

<a id="t122"></a>
### T122 · Permissions matrix test (write first)

**Depends on**: T034, T095 · **Parallel**: yes · **Size**: L

**Read first**: data-model.md › Permissions matrix (every row and note); contracts/rest-api.md (every route with a Role column)

**Files**: create `BT/integration/test_permissions_matrix.py` and `BT/fixtures/matrix.py`

**Steps**:

1. **Fixture world**:
   - Workspace W with users `owner`, `admin`, `editor`, `viewer`.
   - `outsider_edit` and `outsider_view` (invited per document).
   - `stranger` (no access).
   - `platform_admin` (not a member of W).
   - Document D (owned by `editor`) and private document P (owned by `editor`).
2. **Table-driven test**: build `CASES = [(method, path_template, body_factory, actor, expected_status)]` covering **every route** in rest-api.md that has a Role column. Generate the expected statuses from the matrix (`2xx` / `403` / `404`).
   - `stranger` always gets 404 for workspace resources.
   - `platform_admin` gets 404 for workspace content and 2xx for `/v1/admin/*`.
3. For routes from later stories that don't exist yet, add the case with `pytest.mark.skipif(route_missing(...))`. The test then grows automatically as routes land. **Remove the skips at Phase 17.**
4. Private doc P: viewer, admin, and editor-not-owner rules follow the data-model.md note.

**Acceptance**:
- [ ] Every role column has at least one case per action row
- [ ] The test fails if a route returns 200 for a forbidden actor

---

<a id="t123"></a>
### T123 · Invitation tests (write first)

**Depends on**: T024 · **Parallel**: yes · **Size**: S

**Files**: create `BT/integration/test_invitations.py`

**Cases**:

1. An admin invites `x@y.com` as editor → an email is sent (memory outbox) with a token link.
2. Accept while logged in as `x@y.com` → a membership is created and the invitation is `accepted`.
3. Accept as a different email → 403 `forbidden`, `details.reason="email_mismatch"`.
4. An expired invitation (8 days) → 410 and the status `expired`.
5. Revoke → accepting gives 410.
6. Demoting the last owner → 409 `invalid_request`, `details.reason="last_owner"`.
7. A per-document invite → a `document_access` row, and the person sees only that doc.


**Acceptance**:
- [ ] Every case listed above is its own test function (`test_<short_name>`)
- [ ] The tests run and **fail for the expected reason** (missing module or not implemented) until the implementation task lands
- [ ] No production code is added in this task

---

<a id="t124"></a>
### T124 · Auth extension tests (write first)

**Depends on**: T031 · **Parallel**: yes · **Size**: M

**Files**: create `BT/integration/test_auth_ext.py`

**Cases**:

1. Google callback (Authlib mocked with respx):
   - a new email → user, identity, and personal workspace are created, `email_verified_at` is set, and the session is set
   - an existing email user → the identity is linked, with no duplicate user
2. TOTP:
   - setup returns the secret and a QR `otpauth://` URI
   - enable with a valid code → `totp_secret_sealed` is set and 10 recovery codes are returned once
   - login without TOTP → 401 `totp_required`
   - a valid code → OK
   - a recovery code works once
3. Sessions: list shows the current session marked `current`. Revoking another session → it can't call `/v1/me` (401).
4. A password reset revokes every session (already in T031; assert it again here with 2 sessions).


**Acceptance**:
- [ ] Every case listed above is its own test function (`test_<short_name>`)
- [ ] The tests run and **fail for the expected reason** (missing module or not implemented) until the implementation task lands
- [ ] No production code is added in this task

---

<a id="t125"></a>
### T125 · e2e test: workspaces (write first)

**Depends on**: T049 · **Parallel**: yes · **Size**: S

**Files**: create `frontend/apps/web/tests/e2e/workspaces.spec.ts`

**Cases**:

1. A creates the team workspace "Acme" and invites B as Viewer.
2. B opens the invite link from the memory outbox (test endpoint `GET /v1/_test/outbox?to=` in test env), accepts, and switches to Acme.
3. B opens A's document. There is no composer, Patterns is hidden, and the viewer banner is shown. Present works.

---

## Backend (T126–T131)

**Acceptance**:
- [ ] Every case listed above is its own test function (`test_<short_name>`)
- [ ] The tests run and **fail for the expected reason** (missing module or not implemented) until the implementation task lands
- [ ] No production code is added in this task
<a id="t126"></a>
### T126 · Google sign-in

**Depends on**: T124 · **Parallel**: no · **Size**: M

**Read first**: contracts/rest-api.md (the Google rows); data-model.md › identities

**Files**: create `BE/auth/google.py` and modify `BE/api/routers/auth.py`

**Steps**:

1. Use an Authlib `AsyncOAuth2Client` with the OIDC discovery URL `https://accounts.google.com/.well-known/openid-configuration` and the scopes `openid email profile`, with PKCE.
2. `/start`: store `state`, `code_verifier`, and `next` in a signed short-lived cookie (`itsdangerous`, 10 min). Redirect.
3. `/callback`:
   - verify the state, exchange the code, and validate the ID token (`iss`, `aud`, `exp`, `email_verified`)
   - find the identity by `(google, sub)`, else the user by email (link it), else create the user (with `email_verified_at=now`) and the personal workspace through onboarding
   - create the session and redirect to `next` (allow only relative paths)
4. Disable the routes (404) when `GOOGLE_CLIENT_ID` isn't set. The UI hides the button (T049 reads `GET /v1/auth/providers`, which returns `{google: bool}`; add that route here).

**Acceptance**:
- [ ] T124 case 1 passes
- [ ] An open redirect is impossible (test `next=https://evil.com` → `/`)

---

<a id="t127"></a>
### T127 · TOTP and sessions

**Depends on**: T124 · **Parallel**: no · **Size**: M

**Read first**: contracts/rest-api.md (the TOTP and sessions rows)

**Files**: create `BE/auth/totp.py` and `BE/auth/seal.py` (shared with T208), and modify `BE/api/routers/auth.py`

**Steps**:

1. `seal.py`:
   - `seal(plaintext: bytes) -> bytes` / `unseal(b) -> bytes` with `cryptography` Fernet. The key is derived from `SECRET_KEY` with HKDF, `info=b"docu-seal-v1"`.
   - Port `MAS/services/mcp/secrets.py` if it's equivalent. Prefer the port.
2. TOTP: `pyotp.TOTP(secret)`, valid window ±1. Setup stores the pending secret in Redis for 10 min. Enable verifies a code, seals and stores the secret, and generates 10 recovery codes (8 characters, stored as argon2 hashes in `users.totp_recovery`, per data-model.md). Disable needs the password and a code.
3. Login (T031) now enforces TOTP when it's enabled.
4. Sessions: `GET /v1/auth/sessions` returns `{id, createdAt, lastSeenAt, ip, userAgent, current}`. `DELETE /v1/auth/sessions/{id}` only for your own sessions. Add `POST /v1/auth/sessions/revoke-others`.

**Acceptance**:
- [ ] T124 cases 2–3 pass

---

<a id="t128"></a>
### T128 · Invitations and document access models

**Depends on**: T024 · **Parallel**: no · **Size**: S

**Read first**: data-model.md › invitations, document_access

**Files**: create `BE/db/models/{invitations,access}.py` and `backend/alembic/versions/0002_invitations.py`

**Steps**: the models are exactly as data-model.md. `document_access` is a tenant table, so it gets `workspace_id` and **the RLS block** (T024 template). Invitations are **not** RLS: the accept flow reads them by token before any workspace scope exists.

**Acceptance**:
- [ ] The migration upgrades and downgrades cleanly

---

<a id="t129"></a>
### T129 · Workspace and member routes

**Depends on**: T128, T034 · **Parallel**: no · **Size**: M

**Read first**: contracts/rest-api.md › Workspaces and members

**Files**: create `BE/api/routers/workspaces.py` and `BE/services/workspaces.py`

**Steps**: implement every row of the contract.
- `POST /v1/workspaces` creates a team workspace with the caller as owner and grants the Free credits (T041 hook).
- Changing a role checks the last-owner rule.
- Removing a member deletes their `document_access` rows in that workspace and revokes nothing else.
- Deleting is refused while there's an active subscription (`409`, `details.reason="active_subscription"`).
- Membership changes call `seats.sync(workspace)`, a no-op hook until T181.

**Acceptance**:
- [ ] T123 case 6 passes, and the T122 workspace rows pass

---

<a id="t130"></a>
### T130 · Invitation service, routes, and emails

**Depends on**: T129, T032 · **Parallel**: no · **Size**: M

**Files**: create `BE/services/invitations.py`, `BE/emails/invite.{en,ar}.html`, and modify the routers per the contract

**Steps**:

1. Create: the token is 32 bytes and only its sha256 is stored, expiring in 7 days. Email the inviter's name, the workspace (or document) name, the role, and a button to `/invite/{token}`.
2. `GET /v1/invitations/{token}/preview` (public) returns `{workspaceName, documentTitle?, inviterName, role, status}`, for the accept page. This route is in the contract.
3. Accept: requires login, the email must match (case-insensitive), the status must be pending and not expired. Creates the membership or `document_access`, then sets the status.
4. Resend (`POST /v1/invitations/{id}/resend`) has a 1/min limit. Revoke.

**Acceptance**:
- [ ] T123 passes

---

<a id="t131"></a>
### T131 · Audit log

**Depends on**: T129 · **Parallel**: no · **Size**: S

**Read first**: data-model.md › audit_log; FR-036

**Files**: create `BE/services/audit.py` and call it from the workspace, invitation, and auth routes

**Steps**:

1. `async def record(s, *, workspace_id, actor_id, action, target_type, target_id, meta, request)` stores the IP and user agent.
2. Actions:
   - `member.invited`, `member.joined`, `member.role_changed`, `member.removed`
   - `invite.revoked`
   - `auth.login`, `auth.password_reset`, `auth.totp_enabled`, `auth.totp_disabled` (with `workspace_id` = the personal workspace)
3. Never put secrets or tokens in `meta`.

**Acceptance**:
- [ ] Every listed action writes one row (tests in `BT/integration/test_audit.py`)

---

## Frontend (T132–T139)

<a id="t132"></a>
### T132 · Workspace switcher

**Depends on**: T129, T047 · **Parallel**: yes · **Size**: S

**Read first**: ux.md §4.14, §3.1 (switcher at the top of the sidebar)

**Files**: create `FE/components/WorkspaceSwitcher.tsx`

**Steps**:

1. The trigger shows the avatar initials, the workspace name, and the plan badge.
2. The Menu lists workspaces from `me.workspaces` (name, role), a divider, "Create team workspace" (a Dialog with a name field → POST → switch), and "Workspace settings" (→ `/settings/members`).
3. Switching sets `workspaceStore`, invalidates every query, and navigates to `/`.

**Acceptance**:
- [ ] Switching updates every list (documents, threads, templates)

---

<a id="t133"></a>
### T133 · Settings › Members

**Depends on**: T130 · **Parallel**: yes · **Size**: M

**Read first**: ux.md §5.12 (Members)

**Files**: create `FE/pages/settings/Members.tsx`

**Steps**:

1. An invite form (email plus role Select).
2. A members table: name, email, role Select (disabled for yourself if you're the last owner), and Remove (confirm).
3. Pending invites: email, role, sent date, Resend, Revoke.
4. A "Brand memory" link (→ `/memory#brand`).
5. Hidden for personal workspaces (show the note "Create a team workspace to invite people").

**Acceptance**:
- [ ] Every action works, and the errors (last owner) show localized messages

---

<a id="t134"></a>
### T134 · Settings › Profile and Security

**Depends on**: T127 · **Parallel**: yes · **Size**: M

**Read first**: ux.md §5.12 (Layout, Profile, Security); `MAF/pages/SettingsPage.tsx`, `MAF/components/ProfileMenu.tsx`

**Files**: create `FE/pages/settings/{SettingsLayout,Profile,Security}.tsx` (port and extend)

**Steps**:

1. `SettingsLayout`: a tab list (Profile, Security, Members, Billing, Data) on the start side and content up to 720px.
2. Profile: name, language (EN/ع), digits (123/١٢٣), theme (System/Light/Dark through the ported `useTheme`). Save → `PATCH /v1/me`.
3. Security:
   - Change password: current and new (add `POST /v1/auth/password/change {current, new}`; it revokes the other sessions)
   - 2FA enable flow: show the QR (render the `otpauth` URI with a tiny QR encoder; add the `qrcode` npm dependency (approved for this task)), a code input, and the recovery codes shown once with Download (.txt)
   - Disable 2FA
   - Sessions table with Sign out and Sign out of all others

**Acceptance**:
- [ ] The whole 2FA enable → logout → login with code flow works

---

<a id="t135"></a>
### T135 · Invite accept page

**Depends on**: T130 · **Parallel**: yes · **Size**: S

**Read first**: ux.md §5.14

**Files**: create `FE/pages/InviteAccept.tsx` (the route `/invite/:token`, outside the shell)

**Steps**:

1. Load the preview, and show the card "{inviter} invited you to {workspace} as {role}" with Accept.
2. Not logged in → `Sign in to accept` → `/login?next=/invite/:token`.
3. Expired, revoked, or invalid → an EmptyState.
4. After accepting → switch to that workspace and go to `/`.

**Acceptance**:
- [ ] T125 passes

---

<a id="t136"></a>
### T136 · Data export

**Depends on**: T166 (PDF export) — **until T166 exists, export JSON only and add the PDFs when it lands** · **Parallel**: no · **Size**: M

**Read first**: contracts/rest-api.md (`POST /v1/me/export`); FR-026

**Files**: create `BE/worker/tasks/account.py` (`docu.account_export`) and modify `BE/api/routers/me.py`

**Steps**:

1. `POST /v1/me/export` → 202 `{jobId}`. One per 24 h per user (otherwise 429).
2. The task builds a zip:
   - `profile.json`
   - `memberships.json`
   - `documents/<id>.json` (the content and revisions list) for documents the user owns
   - `threads/<id>.json` (messages without blocks' reasoning)
   - `memories.json`
   - later, `documents/<id>.pdf`
3. Upload it to blob storage, then email a signed link valid for 24 h.

**Acceptance**:
- [ ] The zip opens and contains only the requesting user's data (test with 2 users)

---

<a id="t137"></a>
### T137 · Account deletion

**Depends on**: T131 · **Parallel**: no · **Size**: M

**Read first**: contracts/rest-api.md (`DELETE /v1/me`); FR-026; data-model.md › users.deleted_at

**Files**: modify `BE/api/routers/me.py` and create `BE/worker/tasks/account.py` (`docu.account_purge`, daily)

**Steps**:

1. `DELETE /v1/me {password or totp}` re-authenticates (the session is under 5 min old, **or** the password is supplied).
   - If the user is the **only owner** of a team workspace with other members → 409 `details.reason="transfer_ownership"`.
   - Set `deleted_at`, `is_active=false`, revoke all sessions, and write the audit entry `account.deleted`.
2. Purge (`system_session`) after 30 days:
   - delete the personal workspace (cascade)
   - delete memberships, identities, and auth tokens
   - delete Store memories `("memories", user_id)`
   - anonymize the user row (email `deleted+<id>@invalid`, name "Deleted user")
   - documents in team workspaces stay, with their owner reassigned to the workspace owner

**Acceptance**:
- [ ] After purge, no personal data remains (the test checks every table for the email)

---

<a id="t138"></a>
### T138 · Settings › Data

**Depends on**: T136, T137 · **Parallel**: yes · **Size**: S

**Read first**: ux.md §5.12 (Data)

**Files**: create `FE/pages/settings/Data.tsx`

**Steps**:

1. "Export my data" → a status ("We'll email you a link").
2. A danger zone: "Delete account" opens a destructive Dialog where the user types their email to confirm and enters the password or TOTP, then `DELETE /v1/me`, then logout, then a goodbye page.


**Acceptance**:
- [ ] Export shows the status message and an email arrives (Mailpit)
- [ ] Delete requires the exact email and the password, then logs out and shows the goodbye page

**Verify**: Manual check in both languages, plus the T137 tests

---

<a id="t139"></a>
### T139 · Role-aware UI

**Depends on**: T084 · **Parallel**: no · **Size**: S

**Files**: create `FE/lib/permissions.ts` and update the editor, create, and library components

**Steps**:

1. `usePermissions(doc?)` returns the doc's `permissions` (from the API) plus workspace-role checks (`canInvite`, `canManageTemplates`, `canEditBrand`, `canManageConnectors`).
2. Apply them:
   - viewers see no composer, inline edit, Patterns, or Delete
   - editors get no Save as template
   - non-admins see no member management or connector add
3. Never rely on this for security. It's UI only; the API enforces.

**Acceptance**:
- [ ] T125 passes, and no forbidden action is visible for a viewer
