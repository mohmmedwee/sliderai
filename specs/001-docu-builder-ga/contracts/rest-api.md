# Contract: REST API v1

**Base**: `/v1`
**Auth**: Self-hosted, ported from agent_console (research.md R10). It uses argon2id password hashes and an opaque session id in an `HttpOnly; Secure; SameSite=Lax` cookie, with session rows in Postgres. Writes need the `x-csrf-token` header (double-submit).
**Workspace scope**: the `x-workspace-id` header is required on workspace-scoped routes. The API checks the caller's membership and sets `app.workspace_id` for row-level security.
**Validation**: Pydantic v2 models in `backend/src/docu/domain/api/*.py`. FastAPI generates OpenAPI at `/v1/openapi.json`. `openapi-typescript` turns it into `frontend/packages/api-types`. Schemathesis contract tests run against it in CI.

## Errors

Every error uses this shape:
```json
{ "error": { "code": "not_found", "message": "…", "details": {} } }
```
| Status | Codes |
|---|---|
| 400 | `invalid_request` |
| 401 | `unauthenticated` |
| 403 | `forbidden`, `email_unverified`, `plan_required` |
| 404 | `not_found` (also returned for other workspaces' resources) |
| 409 | `version_conflict`, `doc_busy` |
| 402 | `insufficient_credits` |
| 413 | `too_large` |
| 415 | `unsupported_type` |
| 429 | `rate_limited` (with `Retry-After`) |
| 500 | `internal` |

Lists are paginated with a cursor: `?cursor=&limit=` (default 20, max 100). Responses have the form `{ items, nextCursor }`.

## Auth and me

| Method | Path | Role | Body / Response |
|---|---|---|---|
| POST | `/v1/auth/register` | public | `{ email, password, name, locale }` → `201`. Sends a verification email. The first user becomes platform admin when `FIRST_USER_IS_ADMIN=true`. |
| POST | `/v1/auth/login` | public | `{ email, password, totp? }` → sets the session cookie. Returns `401 invalid_credentials` or `401 totp_required`. |
| POST | `/v1/auth/logout` | user | `204`. Revokes the current session. |
| POST | `/v1/auth/verify-email` | public | `{ token }` |
| POST | `/v1/auth/password/forgot` | public | `{ email }` → always `202` |
| POST | `/v1/auth/password/reset` | public | `{ token, password }`. Revokes all sessions. |
| GET | `/v1/auth/google/start` | public | Redirects to Google (Authlib OIDC, PKCE) |
| GET | `/v1/auth/google/callback` | public | Links or creates the user and sets the cookie |
| POST | `/v1/auth/totp/setup` · `/v1/auth/totp/enable` · `/v1/auth/totp/disable` | user | TOTP enrollment (`pyotp`) with recovery codes |
| GET | `/v1/auth/sessions` · DELETE `/v1/auth/sessions/:id` | user | List and revoke your own sessions |
| POST | `/v1/auth/sessions/revoke-others` | user | Revokes every session except the current one |
| POST | `/v1/auth/verify-email/resend` | user | 60 s cooldown per user (`429` otherwise) |
| POST | `/v1/auth/password/change` | user | `{ current, new }`. Revokes the other sessions. |
| GET | `/v1/auth/providers` | public | `{ google: boolean }`. The UI hides the providers that aren't configured. |
| GET | `/v1/me` | user | `{ user, workspaces: [{ id, name, kind, role, plan, creditBalance }], flags: Record<string, boolean> }`. Sets the `docu_csrf` cookie if it's missing. |
| PATCH | `/v1/me` | user | `{ name?, locale?, digits? }` |
| POST | `/v1/me/export` | user | → `202 { jobId }`. Emails a download link. |
| DELETE | `/v1/me` | user | Requires re-authentication within the last 5 minutes. Starts the 30-day soft delete. |

## Workspaces and members

| Method | Path | Role | Notes |
|---|---|---|---|
| POST | `/v1/workspaces` | user | `{ name }`. Creates a team workspace with the caller as owner. |
| PATCH | `/v1/workspaces/:id` | admin | `{ name? }` |
| DELETE | `/v1/workspaces/:id` | owner | Not allowed while a subscription is active. |
| GET | `/v1/workspaces/:id/members` | viewer | |
| PATCH | `/v1/workspaces/:id/members/:userId` | admin | `{ role }`. Can't demote the last owner. |
| DELETE | `/v1/workspaces/:id/members/:userId` | admin | Updates seats. |
| POST | `/v1/workspaces/:id/invitations` | admin | `{ email, role }`. Sends an email. |
| DELETE | `/v1/invitations/:id` | admin | Revoke. |
| POST | `/v1/invitations/accept` | user | `{ token }` |
| GET | `/v1/invitations/:token/preview` | public | `{ workspaceName, documentTitle?, inviterName, role, status }` |
| POST | `/v1/invitations/:id/resend` | admin | 1 per minute |

## Documents and revisions

| Method | Path | Role | Notes |
|---|---|---|---|
| GET | `/v1/documents` | viewer | `?q=&format=&cursor=&limit=&deleted=false`. `deleted=true` (Trash) lists the soft-deleted documents the caller owns, or every one for admins. |
| POST | `/v1/documents` | editor | `{ title?, format, themeId? }` creates a blank document ("New blank") with a thread |
| GET | `/v1/documents/:id` | view | `{ document, thread, activeTurnId, permissions }` |
| PATCH | `/v1/documents/:id` | edit | `{ baseVersion, title?, themeId?, ops?: DocOp[], revisionSource?: 'theme' }` → `{ version }`. Returns 409 `version_conflict` or `doc_busy`. |
| POST | `/v1/documents/:id/duplicate` | edit (source) + editor (workspace) | → `201 { documentId }`. Copies the title (plus " (copy)" or " (نسخة)" by locale), theme, and content at the current version. Creates a new empty thread. |
| DELETE | `/v1/documents/:id` | doc owner / admin | Soft delete (Trash) |
| POST | `/v1/documents/:id/restore` | doc owner / admin | Restore from Trash |
| GET | `/v1/documents/:id/revisions/:revId` | view | `{ id, version, source, content, title, themeId, createdAt }`, used by the history preview |
| GET | `/v1/documents/:id/revisions` | view | `{ items: [{ id, version, source, authorName, createdAt }] }` |
| POST | `/v1/documents/:id/revisions/:revId/restore` | edit | → `{ version }`. The restore is itself a new revision. |

## Threads, turns, messages

| Method | Path | Role | Notes |
|---|---|---|---|
| GET | `/v1/threads` | viewer | `?archived=false&cursor=` |
| POST | `/v1/threads` | editor | `{ prompt, format, templateId?, attachmentIds?, draftKey?, importAttachmentId?, effort?, skill?, webSearch? }`. `draftKey` moves draft attachments onto the new thread. `importAttachmentId` runs the `import` profile. → `201 { threadId, documentId, turnId }`. Starts the first turn. |
| GET | `/v1/threads/:id/messages` | view | Paginated, oldest first. |
| PATCH | `/v1/threads/:id` | edit | `{ archived?, title?, webSearch? }` |
| DELETE | `/v1/threads/:id` | doc owner / admin | Also deletes attachments. |
| POST | `/v1/threads/:id/turns` | edit | `{ text, attachmentIds?, effort?: 'fast'\|'standard'\|'deep', skill?: string, webSearch?: boolean }` → `202 { turnId }`. Returns 402, 409 `doc_busy`, or 429. |
| GET | `/v1/turns/:id` | view | Turn row (status, usage, error). |
| GET | `/v1/turns/:id/events` | view | SSE. See sse-events.md. |
| POST | `/v1/turns/:id/cancel` | edit | → `202` |
| POST | `/v1/turns/:id/undo` | edit | Restores `base_version` as a new revision. Only allowed if no newer revision exists. |
| POST | `/v1/turns/:id/resume` | edit | `{ toolCallId, decision?: 'allow' \| 'deny' \| 'allow_thread', answers?: Record<string,string> }` → `202`. Valid only while the turn is `waiting_input` and before `expiresAt`. Enqueues the resume task, which emits on the same stream. |
| POST | `/v1/threads/:id/rewind` | edit | `{ messageId, text }` → `202 { turnId }`. Deletes messages after `messageId`, restores the document to that turn's `base_version` as a new revision, then starts a turn with the edited text. |
| GET | `/v1/threads/:id/active-turn` | view | `{ turnId \| null, status }`. Used on page load to re-attach to a running turn (agent_console `/chat/active`). |
| POST | `/v1/messages/:id/feedback` | view | `{ rating: 'up' \| 'down', comment? }` → LangSmith feedback |

## Attachments and assets

| Method | Path | Role | Notes |
|---|---|---|---|
| POST | `/v1/attachments` | edit | `{ threadId \| null, draftKey?, filename, mime, size }`. `threadId: null` needs a `draftKey` (a client UUID), used on Create before the thread exists. → `{ attachmentId, uploadUrl, fields }` (presigned POST, size-limited) |
| POST | `/v1/attachments/:id/complete` | edit | Starts the scan and parse job. |
| GET | `/v1/attachments/:id` | view | Status and summary. |
| DELETE | `/v1/attachments/:id` | edit | |
| POST | `/v1/assets/uploads` | edit | Image upload (presigned). Returns `{ assetId, uploadUrl }`. |
| POST | `/v1/assets/:id/complete` | edit | Checks the magic bytes and enqueues the variants. Returns `{ assetId, url }`. |

## Sharing

| Method | Path | Role | Notes |
|---|---|---|---|
| GET | `/v1/documents/:id/sharing` | view | `{ visibility, link: { url, createdAt } \| null, access: [{ user, role }], pendingInvites }` |
| PUT | `/v1/documents/:id/sharing` | share | `{ visibility?, publicLink?: boolean }`. Turning `publicLink` on creates a link. |
| POST | `/v1/documents/:id/share-links/rotate` | share | Revokes the old link and creates a new one. |
| POST | `/v1/documents/:id/invites` | share | `{ email, role: 'view' \| 'edit' }` |
| DELETE | `/v1/documents/:id/access/:userId` | share | |
| GET | `/s/:token` | public | HTML shell with OG tags. Unknown or revoked tokens return a 404 page. |
| GET | `/v1/public/:token` | public | `{ title, format, themeId, slides, badge }` (slides without `notes`) (read-only). Rate limited by IP. |

## Export

| Method | Path | Role | Notes |
|---|---|---|---|
| POST | `/v1/documents/:id/exports` | view | `{ format: 'pdf' \| 'pptx' \| 'png' }` → `202 { exportId }` |
| GET | `/v1/exports/:id` | view | `{ status, url? }` (signed URL valid for 24 h) |

## Templates and themes

| Method | Path | Role | Notes |
|---|---|---|---|
| GET | `/v1/templates/:id` | viewer | The full template, with every card |
| GET | `/v1/templates` | viewer | `?q=&format=&category=&color=&lang=&owned=workspace&createdBy=me&recent=1&limit=` → `{ items, facets: { category: {k:n}, color: {k:n}, format: {k:n} } }` |
| POST | `/v1/templates` | admin | Saves a document as a workspace template. |
| DELETE | `/v1/templates/:id` | admin | Workspace templates only. |
| GET | `/v1/themes` | viewer | |

## Billing

| Method | Path | Role | Notes |
|---|---|---|---|
| GET | `/v1/billing/usage` | owner | `?days=30` → `[{ day, credits }]` |
| GET | `/v1/billing` | viewer | `{ plan, seats, status, balance, monthlyAllowance, periodEnd, usage: { thisPeriod } }` |
| POST | `/v1/billing/checkout` | owner | `{ plan, seats? }` → `{ url }` (Stripe Checkout) |
| POST | `/v1/billing/portal` | owner | → `{ url }` |
| GET | `/v1/billing/ledger` | owner | Paginated ledger entries. |
| POST | `/v1/webhooks/stripe` | Stripe signature | Stores the event in `stripe_events` (insert-or-ignore), then processes it. |

## Memory (FR-047, FR-048)

| Method | Path | Role | Notes |
|---|---|---|---|
| GET | `/v1/memory` | user | Your memories (Store namespace `("memories", user_id)`) |
| POST | `/v1/memory` | user | `{ text }`. Capped at 50. |
| PATCH / DELETE | `/v1/memory/:id` | user | |
| GET / PUT | `/v1/workspaces/:id/brand-memory` | viewer / admin | `{ items: string[] }`. Namespace `("brand", workspace_id)`. |

## Skills (FR-049)

| Method | Path | Role | Notes |
|---|---|---|---|
| GET | `/v1/skills` | viewer | Built-in and workspace skills `{ name, description, source, enabledProfiles }` |
| GET | `/v1/skills/:name` | viewer | The body |
| POST | `/v1/skills` | admin (Team plan) | `{ name, description, body }`. Validated like agent_console `user_skills`. |
| POST | `/v1/skills/generate` | admin (Team plan) | `{ description }` → a draft `{ name, description, body }`, not saved |
| PATCH / DELETE | `/v1/skills/:name` | admin | Workspace skills only |

## Connectors (FR-050)

| Method | Path | Role | Notes |
|---|---|---|---|
| GET | `/v1/connectors` | viewer | `{ id, name, url, status, groups, lastError }` |
| POST | `/v1/connectors` | admin | `{ name, url, auth: 'oauth' \| 'bearer', token? }`. Secrets are sealed. |
| POST | `/v1/connectors/:id/oauth/start` · GET `/v1/connectors/oauth/callback` | admin | Ported OAuth flow |
| POST | `/v1/connectors/:id/reconnect` | admin | |
| DELETE | `/v1/connectors/:id` | admin | |

## Models (FR-044)

| Method | Path | Role | Notes |
|---|---|---|---|
| GET | `/v1/models` | user | `{ efforts: [...allowed for plan], default, thinking: boolean }`. Model ids are not shown to end users. |

## Search, support, internal

| Method | Path | Role | Notes |
|---|---|---|---|
| GET | `/v1/search` | viewer | `?q` → `{ documents: [...8], threads: [...5] }` |
| POST | `/v1/support` | user | `{ subject, body }` → emailed to the support inbox. 3 per hour. |
| GET | `/v1/_export/:id` | signed token | Internal render data for the export and thumbnail worker: `?v=&token=` → the doc content at that version, the theme, `watermark`. No cookie. |
| * | `/v1/_test/*` | — | Only when `ENV=test`: `POST /v1/_test/verify`, `GET /v1/_test/outbox`, `POST /v1/_test/credits`. Never registered in other environments. |

## Platform admin (FR-053 – FR-055)

Requires `users.is_platform_admin`.

| Method | Path | Notes |
|---|---|---|
| GET / PATCH | `/v1/admin/users` · `/v1/admin/users/:id` | List, search, activate or deactivate, set `is_platform_admin` |
| GET / PUT | `/v1/admin/model-settings` | Upstream, model, vision model, small model, fallback, context window, max completion tokens, thinking, effort caps per plan. The API key is write-only. |
| POST | `/v1/admin/model-settings/check` | Runs the `check_endpoint` probe: a plain reply, tool_calls, and tool_calls while streaming |
| GET | `/v1/admin/prompts` · `/v1/admin/prompts/:name/versions` | |
| POST | `/v1/admin/prompts/:name/versions` | `{ body, note }` creates a new version and activates it |
| POST | `/v1/admin/prompts/:name/versions/:v/activate` | Roll back |
| GET / PUT | `/v1/admin/profiles/:id` | Skills, tools, and connectors switched on, effort cap |
| GET / PUT | `/v1/admin/flags` | Feature flags |
| GET | `/v1/admin/usage` | `?from&to&groupBy=day\|model\|workspace` → tokens, cost, turns, p50/p95 latency, failure rate |

## Rate limits (defaults; set in config)

| Scope | Limit |
|---|---|
| `/v1/auth/login`, `/v1/auth/register`, `/v1/auth/password/*` | 10 per minute per IP, and 5 per minute per email |
| Turns | 20 per minute per user, 200 per hour per workspace |
| Uploads | 30 per hour per user |
| Exports | 20 per hour per user |
| Public viewer | 120 per minute per IP |
| `fetch_url` and `web_search` (agent) | 30 per turn, 300 per hour per workspace |
