# Data Model: Docu Builder GA

**Feature**: `001-docu-builder-ga` | **Date**: 2026-10-19
**Source of truth**: `backend/src/docu/db/models/*.py` (SQLAlchemy 2, migrations in `backend/alembic/`) and `backend/src/docu/domain/*.py` (Pydantic v2)

**Conventions**:
- Every table has an `id` (UUIDv7), `created_at`, and `updated_at`.
- Every tenant-owned table has `workspace_id` and a row-level security policy `workspace_id = current_setting('app.workspace_id')::uuid`.
- Tables marked "soft delete" also have `deleted_at`.

## Document content (JSONB, validated by Pydantic)

```python
Layout = Literal["hero", "title", "points", "quote", "split", "table", "chart"]

class TableData(BaseModel):
    columns: list[Annotated[str, Field(max_length=40)]] = Field(min_length=1, max_length=8)
    rows: list[list[str | float | None]] = Field(min_length=1, max_length=12)   # each row len == len(columns)

class ChartSeries(BaseModel):
    name: str = Field(max_length=40)
    values: list[float | None] = Field(min_length=1, max_length=24)

class ChartData(BaseModel):
    kind: Literal["bar", "line", "pie", "donut"]
    labels: list[Annotated[str, Field(max_length=40)]] = Field(min_length=1, max_length=24)
    series: list[ChartSeries] = Field(min_length=1, max_length=6)   # pie/donut: exactly 1
    unit: str | None = Field(None, max_length=12)

class SlideImage(BaseModel):
    asset_id: UUID
    alt: str = Field(min_length=1, max_length=200)
    focal: tuple[float, float] | None = None

class Slide(BaseModel):
    id: str                                   # nanoid(10)
    layout: Layout
    kicker: str | None = Field(None, max_length=60)
    title: str = Field(min_length=1, max_length=140)
    body: str | None = Field(None, max_length=600)
    points: list[Annotated[str, Field(max_length=160)]] | None = Field(None, max_length=6)
    button: str | None = Field(None, max_length=40)
    field: CssField | None = None             # CSS color or linear-gradient(); allow-list grammar validator
    image: SlideImage | None = None
    table: TableData | None = None            # layout == "table"
    chart: ChartData | None = None            # layout == "chart"
    notes: str | None = Field(None, max_length=2000)   # speaker notes; agent cites sources here

class DocumentContent(BaseModel):
    slides: list[Slide] = Field(min_length=1, max_length=60)
```

The API serializes these models with camelCase aliases (`alias_generator=to_camel`), so the generated TypeScript types use camelCase.

- **Layout rules**:
  - `points` requires `points.length ≥ 1`.
  - `quote` uses `title` as the quote and `body` as the attribution.
  - `hero` and `split` use `field` or `image`. When both are missing, the theme's default gradient is used.
  - `table` requires `table`, and every row has the same length as `columns`.
  - `chart` requires `chart`. Every series has the same length as `labels`, and `pie` and `donut` take exactly one series.
- **Direction** is not stored. Each text block renders with `dir="auto"`.

## Entities

### users (self-hosted auth, ported from agent_console)
| Column | Type | Notes |
|---|---|---|
| email | citext unique | |
| email_verified_at | timestamptz null | documents and threads can't be created until it is set (FR-020) |
| password_hash | text null | argon2id, rehashed when parameters change. Null for Google-only accounts. |
| name | text | |
| image | text null | avatar URL |
| locale | `'en' \| 'ar'` | |
| digits | `'latn' \| 'arab'` | |
| totp_secret_sealed | bytea null | sealed with the same key scheme as connector secrets |
| totp_recovery | jsonb null | argon2 hashes of 10 one-time recovery codes |
| is_platform_admin | bool | the first user when `FIRST_USER_IS_ADMIN` is set (FR-055) |
| is_active | bool | admins can deactivate a user |
| deleted_at | timestamptz null | 30-day soft delete (FR-026) |

### sessions
id (random 256-bit, stored as a hash), user_id, created_at, last_seen_at, expires_at, ip, user_agent, revoked_at. The cookie holds the raw id. Revoking is per session, or all of a user's sessions on a password reset.

### identities
user_id, provider (`'google'`), subject (unique per provider), email. Links Google sign-in to a user.

### auth_tokens
user_id, kind (`'verify_email' \| 'password_reset'`), token_hash, expires_at, used_at. Single use.

### workspaces
| Column | Type | Notes |
|---|---|---|
| name | text 1..80 | |
| slug | text unique | |
| kind | `'personal' \| 'team'` | exactly one personal workspace per user |
| plan | `'free' \| 'pro' \| 'team'` | mirrors the subscription |
| stripe_customer_id | text null | |
| credit_balance | int | cache; the ledger is the truth |
| data_region | text | from FR-037 |

### memberships
| Column | Type | Notes |
|---|---|---|
| workspace_id, user_id | uuid | unique pair |
| role | `'owner' \| 'admin' \| 'editor' \| 'viewer'` | exactly one owner per workspace |

### invitations
| Column | Type | Notes |
|---|---|---|
| workspace_id | uuid | |
| document_id | uuid null | set for a per-document invite |
| email | citext | |
| role | workspace role, or `'view' \| 'edit'` for documents | |
| token_hash | text | SHA-256 of a 32-byte token |
| invited_by | uuid | |
| expires_at | timestamptz | created_at + 7 days |
| status | `'pending' \| 'accepted' \| 'revoked' \| 'expired'` | |

### documents (soft delete)
| Column | Type | Notes |
|---|---|---|
| workspace_id | uuid | |
| owner_id | uuid | |
| title | text 1..140 | |
| format | `'presentation' \| 'document' \| 'webpage' \| 'social'` | |
| theme_id | text | references `themes.id` |
| content | jsonb | `DocumentContent` |
| version | int | increments on every commit; used by optimistic saves |
| visibility | `'private' \| 'workspace'` | general access for members |
| active_turn_id | uuid null | mirrors the Redis lease |
| manual_edits_since_agent | int default 0 | incremented by manual saves, reset by an agent commit. Drives the `replace_slides` approval policy (research.md R22). |
| thumbnail_asset_id | uuid null | first slide |

### document_revisions
| Column | Type | Notes |
|---|---|---|
| document_id | uuid | |
| version | int | unique per document |
| content, title, theme_id | snapshot | |
| source | `'agent_turn' \| 'manual' \| 'restore' \| 'theme'` | |
| turn_id | uuid null | |
| author_id | uuid | |

Revisions are immutable. They are kept for the life of the document.

### document_access
document_id, user_id, role `'view' | 'edit'`. Grants access to people outside the workspace.

### threads (soft delete)
| Column | Type | Notes |
|---|---|---|
| workspace_id, document_id | uuid | one thread per document at GA |
| template_id | text null | |
| title | text | set by the small model after the first turn |
| archived | bool | |
| web_search | bool default false | the thread's web toggle (US13) |
| checkpoint_ns | text default '' | changed when a rewind has no checkpoint to fork from (a fresh agent state) |
| created_by | uuid | |

### messages
| Column | Type | Notes |
|---|---|---|
| thread_id | uuid | |
| turn_id | uuid null | |
| role | `'user' \| 'assistant' \| 'tool'` | |
| text | text | |
| tool_name | text null | |
| tool_args | jsonb null | |
| tool_ok | bool null | |
| slide_ids | text[] | used for the slide previews inside messages |
| attachment_ids | uuid[] | on user messages |
| blocks | jsonb null | assistant messages only: the UI blocks collected from the turn's events, in agent_console's `chat_turn._collect` format. Kinds: `reasoning` (capped at 12,000 chars), `tool` (`{id, name, argsPreview, result (clipped 3,000), ok}`), `ask_user`, `approval`, `chip` (`memory` / `skill`), `note`. The UI re-renders past turns from these. |
| workspace_id | uuid | denormalized for RLS (Conventions) |

### turns
| Column | Type | Notes |
|---|---|---|
| thread_id, document_id, user_id | uuid | |
| status | see the state machine below | |
| base_version | int | |
| committed_version | int null | |
| model, fallback_used | text, bool | |
| profile | `'deck' \| 'document' \| 'webpage' \| 'social' \| 'import' \| 'assistant'` | |
| effort | `'fast' \| 'standard' \| 'deep'` | |
| prompt_version_id | uuid | the prompt version used (FR-054) |
| skill, web_search | text null, bool | composer choices |
| steps, max_steps | int | the step budget comes from effort, plus one auto-continue |
| latency_ms, ttft_ms | int | |
| langsmith_run_id | uuid null | set only when the turn was traced |
| heartbeat_at | timestamptz null | updated every 20 s by the worker. The reaper fails turns with no heartbeat for 90 s. |
| input_tokens, output_tokens, cached_tokens, reasoning_tokens | int | from LangChain `usage_metadata` |
| cost_usd | numeric(10,6) | from the price table |
| credits_reserved, credits_charged | int | |
| error_code | text null | one of the `TurnErrorCode` values in contracts/sse-events.md |
| started_at, finished_at | timestamptz | |

### pending_inputs
turn_id, tool_call_id, kind (`'approval' \| 'ask_user'`), payload (jsonb: the approval card or question), expires_at (created_at + 30 min), answered_at, answer (jsonb). The unique pair `(turn_id, tool_call_id)` makes a resume single-use, matching agent_console's `take_payload` semantics.

### LangGraph Store (memories)
The `store` and `store_vectors` tables are created by `AsyncPostgresStore.setup()`.

| Namespace | Key | Value | Limit |
|---|---|---|---|
| `("memories", user_id)` | memory id | `{ text, kind, createdAt, source: 'agent' \| 'user' }` | 50 per user |
| `("brand", workspace_id)` | `"rules"` | `{ items: string[], updatedBy }` | 30 items |

### skills
id, workspace_id (null for built-in skills, which are synced from `backend/skills/*/SKILL.md` at startup), name (slug, unique per workspace), description (≤ 1024 chars, used for selection), body (≤ 40k chars), license, enabled_profiles (text[]), created_by, and timestamps.

### connectors (MCP)
id, workspace_id, name (slug), url, auth (`'oauth' \| 'bearer' \| 'none'`), headers_sealed (bytea), oauth_tokens_sealed (bytea), status (`'connected' \| 'needs_auth' \| 'error'`), groups (jsonb cache of tool groups), last_error, allowed_profiles. Ported from agent_console `mcp_servers`, but scoped to a workspace.

### prompt_versions
id, name (`deck`, `document`, …), version (int), body, note, created_by, created_at, is_active (only one active per name). Files in `backend/prompts/` are the version-0 defaults.

### platform_settings
A single row of jsonb: model settings (upstream, model, vision, small, fallback, context window, max completion tokens, thinking, effort caps per plan), the sealed API key, feature flags, and per-profile overrides (`profiles`: skills, tools, connectors, effort cap). Cached in-process for 30 s.

### usage_daily
day, workspace_id, model, turns, failed, input_tokens, output_tokens, cost_usd, p50_ms, p95_ms. An hourly upsert from `turns`, used by the admin usage page. The primary key is `(day, workspace_id, model)`.

### LangGraph checkpoint tables
`checkpoints`, `checkpoint_blobs`, `checkpoint_writes`, and `checkpoint_migrations` are created by `AsyncPostgresSaver.setup()` (`langgraph-checkpoint-postgres`), keyed by `thread_id = threads.id`. They don't use row-level security. Access always goes through a thread the user is already authorized for.

### attachments
| Column | Type | Notes |
|---|---|---|
| workspace_id | uuid | |
| thread_id | uuid null | null while it's a draft on Create |
| draft_key | uuid null | client key that moves the draft onto the new thread |
| filename | text | |
| mime | enum of 6 types | checked against the file's actual bytes |
| size | int ≤ 26,214,400 | |
| s3_key | text | |
| status | see the state machine below | |
| summary | text null | |
| error_code | text null | |

### attachment_chunks
workspace_id, attachment_id, ordinal, text, tokens, page_start, page_end, embedding `vector(N)` (HNSW, cosine), and `tsv` (a generated tsvector, `simple` config) for hybrid search.

### assets
workspace_id, kind `'generated' | 'upload' | 'thumbnail' | 'export'`, s3_key, mime, width, height, bytes, and meta (jsonb: prompt, model, moderation).

### documents.search_tsv
A generated `tsvector` over the title and slide titles, with a GIN index, used by `GET /v1/search`.

### exports
document_id, version, format `'pdf' | 'pptx' | 'png'`, status, asset_id, watermark bool, requested_by, and error_code.

### templates
| Column | Type | Notes |
|---|---|---|
| id | text | system ids are stable slugs |
| workspace_id | uuid null | null means a system template |
| name_en, name_ar | text | |
| category | `'pitch' \| 'report' \| 'education' \| 'marketing' \| 'event' \| 'planning' \| 'personal'` | |
| format | Format | |
| theme_id | text | |
| colors | text[] | color tags |
| lang | `'en' \| 'ar'` | |
| cards | jsonb | `Omit<Slide, 'id'>[]` |

### themes
id (text), workspace_id null, name, and tokens jsonb `{ bg, paper, ink, accent, tone, font }`. A unit test checks that ink-on-paper contrast is at least 4.5:1.

### share_links
document_id, token_hash, access `'view'`, created_by, revoked_at, view_count, and last_viewed_at. At most one active link per document.

### subscriptions
workspace_id unique, stripe_subscription_id, plan, seats, status `'active' | 'trialing' | 'past_due' | 'canceled' | 'incomplete'`, current_period_end, cancel_at_period_end, and downgrade_at (a scheduled downgrade to Free after cancel or past_due grace).

### credit_ledger (append-only)
| Column | Type | Notes |
|---|---|---|
| workspace_id | uuid | |
| user_id | uuid null | |
| delta | int | positive for grants and refunds, negative for reservations and charges |
| kind | `'grant' \| 'reserve' \| 'settle' \| 'refund' \| 'image' \| 'adjust'` | |
| turn_id, asset_id, stripe_invoice_id | refs null | |
| idempotency_key | text unique | e.g. `grant:{invoice_id}`, `reserve:{turn_id}` |

The balance is `SUM(delta)`, and `workspaces.credit_balance` is updated in the same transaction. Ledger rows are never updated or deleted, which is enforced with a trigger.

### stripe_events
`id` (the Stripe event id, primary key), type, payload, received_at, processed_at, attempts, and last_error (unresolved events are retried by a beat job). A unique primary key makes processing exactly-once.

### audit_log
workspace_id (null for platform-admin events), actor_id, action (for example `member.invited`, `share.link_created`, `doc.deleted`, `billing.plan_changed`), target_type, target_id, meta, ip, and user_agent.

## Permissions matrix

| Action | Owner | Admin | Editor | Viewer | Doc edit invite | Doc view invite | Public link |
|---|---|---|---|---|---|---|---|
| View document / present | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Edit content / run agent | ✅ | ✅ | ✅ | — | ✅ | — | — |
| Create document | ✅ | ✅ | ✅ | — | — | — | — |
| Delete document | ✅ | ✅ | owner of doc | — | — | — | — |
| Share settings / links | ✅ | ✅ | owner of doc | — | — | — | — |
| Export | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| Manage members / invites | ✅ | ✅ | — | — | — | — | — |
| Workspace templates | ✅ | ✅ | — | — | — | — | — |
| Billing | ✅ | — | — | — | — | — | — |
| Delete / transfer workspace | ✅ | — | — | — | — | — | — |
| Answer the agent's questions and approvals on a turn | turn starter | turn starter | turn starter | — | turn starter | — | — |
| Edit brand memory | ✅ | ✅ | — | — | — | — | — |
| Create or edit workspace skills (Team plan) | ✅ | ✅ | — | — | — | — | — |
| Add or remove connectors | ✅ | ✅ | — | — | — | — | — |

- Personal memory belongs to its user only. Nobody else, workspace admins included, can read it.
- **Platform admin** (`users.is_platform_admin`) is separate from workspace roles. It grants the `/v1/admin/*` routes (users, model settings, prompts, profiles, flags, usage) and **never** grants access to workspace content.

- Credits for a turn are always charged to the workspace that owns the document.
- Documents with `visibility = 'private'` are visible only to their owner, Admins, the Owner, and people with `document_access`.

## State machines

**Turn**
```
queued → running → committed
                 ↘ failed          (provider error, context overflow, internal)
                 ↘ cancelled       (user stop)
                 ↘ waiting_input → running (resume) …
                                 ↘ cancelled (expired after 30 min, reason 'expired')
queued → rejected                 (no credits, lease held, permission)
```
- `running` with no worker heartbeat for 90 s becomes `failed` with `error_code = 'worker_lost'`, and the reservation is refunded.
- `waiting_input` keeps the document lease and the credit reservation. The lease TTL is extended to the interrupt's expiry.

**Attachment**
```
uploading → uploaded → scanning → parsing → embedding → ready
                         ↘ rejected (malware)   ↘ failed (parse_error | too_large_after_extract)
```

**Invitation**
```
pending → accepted | revoked | expired
```

**Export**
```
queued → rendering → ready | failed
```

**Subscription** mirrors Stripe status. Going to `canceled` downgrades the workspace to `free` at the end of the period. Going to `past_due` keeps the plan for 7 days, then downgrades.

## Indexes (non-obvious)

- `documents (workspace_id, updated_at desc) where deleted_at is null`
- `threads (workspace_id, archived, created_at desc)`
- `messages (thread_id, created_at)`
- `attachment_chunks using hnsw (embedding vector_cosine_ops)`, plus a GIN index on `tsv`
- `credit_ledger (workspace_id, created_at)`, and the unique index on `idempotency_key`
- `share_links (token_hash) where revoked_at is null`
