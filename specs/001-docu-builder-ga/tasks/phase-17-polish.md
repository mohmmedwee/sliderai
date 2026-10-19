# Phase 17: Polish, hardening, and launch (task cards)

Before any card, read [IMPLEMENTER.md](../IMPLEMENTER.md). These tasks start once every GA story is merged, apart from those marked [P], which can start earlier.

**Exit check (GA sign-off)**: T242 is complete with every SC-001 to SC-012 checkbox ticked.

---

<a id="t222"></a>
### T222 · ⌘K search

**Depends on**: T095, T106 · **Parallel**: yes · **Size**: M

**Read first**: ux.md §3.1 (`Search ⌘K` in the sidebar), §4.30 Kbd

**Files**: create `BE/api/routers/search.py`, a migration `0011_search.py`, and `FE/components/CommandK.tsx`

**Steps**:

1. Backend: add `documents.search_tsv tsvector GENERATED ALWAYS AS (to_tsvector('simple', title || ' ' || coalesce(jsonb_path_query_array(content, '$.slides[*].title')::text,''))) STORED` with a GIN index. `GET /v1/search?q` returns the top 8 documents (title match first) and the top 5 threads (title ILIKE). (Both are in the contract and data-model.md.)
2. Frontend: ⌘K or Ctrl+K opens a Dialog with an input and grouped results (Documents, Conversations, Actions: New blank, Templates, Settings). Arrow keys plus Enter. Esc closes. The sidebar "Search" item opens it too.


**Acceptance**:
- [ ] ⌘K and Ctrl+K open it from any shell page
- [ ] Results are keyboard navigable
- [ ] Search ignores documents from other workspaces

**Verify**: `pnpm test:e2e -- smoke (add a ⌘K case) and uv run pytest tests/integration/test_search.py -q`

---

<a id="t223"></a>
### T223 · Schemathesis contract tests

**Depends on**: every route task · **Parallel**: yes · **Size**: S

**Files**: create `BT/contract/test_openapi.py`

**Steps**: `schemathesis.from_asgi("/v1/openapi.json", app)` with an authenticated session fixture and `x-workspace-id`. Run the checks `not_a_server_error`, `status_code_conformance`, and `response_schema_conformance`. Exclude `/v1/webhooks/*`, `/v1/_*`, and SSE. Fix whatever it finds, or add explicit `responses=` to the routes.


**Acceptance**:
- [ ] Schemathesis runs on CI with zero failures

**Verify**: `uv run pytest tests/contract -q`

---

<a id="t224"></a>
### T224 · axe accessibility checks in every e2e spec

**Depends on**: the e2e specs exist · **Parallel**: yes · **Size**: S

**Files**: create `frontend/apps/web/tests/e2e/a11y.ts`, and call it from every spec

**Steps**: `export async function checkA11y(page, name)` runs `@axe-core/playwright` with the tags `wcag2a`, `wcag2aa`, `wcag21aa`, `wcag22aa`, and fails on any violation (allow-list only with a comment and a task id). Call it at each key state of every spec, in both `ar` and `en`.


**Acceptance**:
- [ ] Every e2e spec calls `checkA11y` at least once per page state, in both locales
- [ ] No violations remain

**Verify**: `pnpm test:e2e`

---

<a id="t225"></a>
### T225 · Manual screen reader pass

**Depends on**: T224 · **Parallel**: yes · **Size**: M

**Files**: create `docs/a11y-audit.md`

**Steps**:

1. With VoiceOver (macOS Safari) and NVDA (Windows Firefox), in English and Arabic, run these flows:
   - register and log in
   - create a deck
   - answer a question
   - approve
   - edit a title inline
   - reorder by keyboard
   - present
   - share
2. Log each issue as a row (screen, step, expected, actual, severity), and file fixes as `T225-n` follow-ups.

**Acceptance**:
- [ ] No blocker-severity issues remain open

---

<a id="t226"></a>
### T226 · Bundle budgets

**Depends on**: T146 · **Parallel**: yes · **Size**: S

**Files**: modify `frontend/apps/web/vite.config.ts` and create `frontend/scripts/check-bundle.mjs`

**Steps**: after `vite build`, compute the gzip size of each entry's JS (follow the manifest's `imports`). Fail when `main` is over 250 KB or `share` is over 120 KB (plan.md Constraints). Add it to the CI `frontend` job.


**Acceptance**:
- [ ] CI fails when either budget is exceeded (prove it with a temporary large import)

**Verify**: `pnpm build && node scripts/check-bundle.mjs`

---

<a id="t227"></a>
### T227 · Arabic copy review

**Depends on**: every UI and copy task · **Parallel**: yes · **Size**: M (with a native reviewer)

**Steps**:

1. Export every `ar.json` key with its English source to `docs/i18n/review.csv`. Include the template names and content, the skill descriptions, the email templates, and the user-visible error messages.
2. The reviewer edits the CSV. A script imports it back.
3. No `__TODO_AR__` may remain; the CI release check (T012) enforces it.
4. Check ux.md §11 rules: MSA, neutral register, no transliteration.


**Acceptance**:
- [ ] No `__TODO_AR__` remains
- [ ] The reviewer signs off in the PR

**Verify**: `grep -r __TODO_AR__ frontend/apps/web/src/i18n backend || echo clean`

---

<a id="t228"></a>
### T228 · LangSmith in production

**Depends on**: T075 · **Parallel**: yes · **Size**: S

**Read first**: research.md R17

**Files**: create `BE/agent/tracing.py`

**Steps**:

1. When `LANGSMITH_TRACING` is set, configure `langsmith.Client(hide_inputs=redact, hide_outputs=redact)`, where `redact` removes attachment content, `<web_content>`, and email-like and phone-like strings, keeping only the structure, tool names, and sizes.
2. Sampling is the setting `LANGSMITH_SAMPLE`, default `1.0` (trace every turn; the data is already redacted). Per turn, `tracing_context(enabled=random() < rate)`. Store `turns.langsmith_run_id` only when the turn was traced. A thumbs-down on an untraced turn is still stored in the DB, but has no LangSmith run, and that is acceptable. Document this trade-off in `docs/runbooks/README.md`.
3. An annotation queue `docu-thumbs-down`: the feedback route (T103) adds the run to the queue.


**Acceptance**:
- [ ] Traces in LangSmith contain no attachment or web content (inspect 5 traces)
- [ ] Thumbs-down adds the run to the annotation queue

**Verify**: Manual check on staging

---

<a id="t229"></a>
### T229 · Dashboards and alerts

**Depends on**: T051, T220 · **Parallel**: yes · **Size**: M

**Files**: create `infra/observability/{dashboards/*.json,alerts.yaml,README.md}`

**Steps**:

1. **Dashboards** (Grafana JSON, or the vendor's format; pick one in the README):
   - SLOs: availability, turn success %, time-to-first-slide p95, save p95, export p95
   - Celery queue depth per queue
   - the count of `waiting_input` turns
   - provider error rate
   - cost per day per workspace (from `usage_daily`)
2. **Alerts**:
   - turn failure > 5% over 15 min
   - `turns` queue depth > 200 for 5 min
   - Stripe webhook failures > 0 for 10 min
   - reconcile mismatches > 0
   - upstream 5xx > 10% over 5 min


**Acceptance**:
- [ ] Every listed dashboard panel and alert exists
- [ ] A test alert fires to the on-call channel

**Verify**: Manual check on staging

---

<a id="t230"></a>
### T230 · Product analytics

**Depends on**: T084 · **Parallel**: yes · **Size**: S

**Read first**: the Product metrics in docs/Plan.md and spec.md SC-001

**Files**: create `FE/lib/analytics.ts`

**Steps**: a thin `track(event, props)` that is a no-op unless `VITE_ANALYTICS_KEY` is set (provider adapter). The events are `signup_completed`, `first_prompt_sent`, `draft_completed`, `edit_turn_sent`, `manual_edit`, `share_enabled`, `export_downloaded`, `upgrade_clicked`, and `upgrade_completed`. **Never** include prompt text or document content in the props.


**Acceptance**:
- [ ] Events fire in the right places
- [ ] No event props contain user text (unit test on `track` callers)

**Verify**: `pnpm test -- analytics`

---

<a id="t231"></a>
### T231 · Model bake-off

**Depends on**: T088, T093, T112, T150, T189 · **Parallel**: no · **Size**: M

**Read first**: research.md R8

**Steps**:

1. Run `evals/run.py --suite all` on each candidate: the self-hosted OpenAI-compatible model used by agent_console, Claude Sonnet 5.5, and at least one other OpenAI-compatible option.
2. Record the scores, cost per turn, p95 latency, and time to first slide.
3. Write the results table into research.md R8 › Follow-up, and set the production defaults in `.env.example` and the platform settings seed.


**Acceptance**:
- [ ] The results table is in research.md R8
- [ ] The production defaults are set in config

**Verify**: `uv run python evals/run.py --suite all` (per candidate)

---

<a id="t232"></a>
### T232 · Load test

**Depends on**: T075, T146 · **Parallel**: no · **Size**: M

**Files**: create `infra/load/{turns.js,viewers.js,resume.js,README.md}`

**Steps** (k6 against staging with `AGENT_FAKE_MODEL=1` plus a 5% real-model sample):

1. `turns.js`: 500 virtual users, each creating a thread and reading the SSE to the terminal event.
2. `viewers.js`: 5,000 VUs on `/s/{token}` and `/v1/public/{token}`.
3. `resume.js`: 200 turns paused on `ask_user`, then all resumed within 10 s.
4. Size the Celery `--concurrency` and the ECS task counts from the results, and record them in the README.

**Acceptance**:
- [ ] SC-002, SC-004, and the plan's performance goals hold under load

---

<a id="t233"></a>
### T233 · Pen test

**Depends on**: T238 (staging) · **Parallel**: no · **Size**: M (external)

**Steps**:

1. Brief the testers on the scope: auth (sessions, CSRF, TOTP, Google), the tenant isolation and RLS, `fetch_url` SSRF, MCP connectors (OAuth, secrets), uploads (magic bytes, malware, zip bombs in DOCX and PPTX), share links, Stripe webhooks, and prompt injection through attachments.
2. Track the findings in `docs/security/pentest-<date>.md`. Fix every High and Critical, and add a regression test per fix.


**Acceptance**:
- [ ] Every High and Critical finding is fixed, with a regression test

**Verify**: Review docs/security/pentest-<date>.md

---

<a id="t234"></a>
### T234 · Legal pages and NOTICE

**Depends on**: none · **Parallel**: yes · **Size**: S

**Files**: create `FE/pages/legal/{Terms,Privacy,Dpa,Subprocessors}.tsx` and a `/legal/third-party` page that renders `NOTICE`

**Steps**: render Markdown from `frontend/apps/web/src/content/legal/{en,ar}/*.md`, with placeholder text marked `LEGAL REVIEW REQUIRED`. The subprocessor list comes from config: model provider(s), email, hosting, Stripe, and analytics. Link them in the auth pages' footer and in Settings.


**Acceptance**:
- [ ] The pages render in both languages
- [ ] NOTICE lists every Apache and OFL component
- [ ] The footer links work

**Verify**: Manual check

---

<a id="t235"></a>
### T235 · Status page and Help menu

**Depends on**: T047 · **Parallel**: yes · **Size**: S

**Read first**: ux.md §3.1 ("?" at the bottom of the rail)

**Files**: create `FE/components/Help.tsx`

**Steps**: the "?" opens a Menu with Help center (an external docs URL from config), Keyboard shortcuts (a Dialog listing them), Contact support (`mailto`, or a form that posts to `POST /v1/support`; email to the support inbox, rate limited; in the contract), Status (an external status page URL), and What's new.


**Acceptance**:
- [ ] Every menu item works
- [ ] The support form is rate limited and emails the inbox

**Verify**: Manual check

---

<a id="t236"></a>
### T236 · Final brand art

**Depends on**: T046 · **Parallel**: yes · **Size**: M (design)

**Read first**: ux.md §9

**Steps**:

1. Replace the placeholders with the final **original** logo and illustrations, at the same file names and sizes, with light and dark variants.
2. Have a reviewer check that nothing resembles the reference product's logo or artwork.
3. Keep the file sizes within the limits in §9.


**Acceptance**:
- [ ] The final assets are in place at the same sizes
- [ ] Dark variants exist
- [ ] A reviewer confirms nothing resembles the reference product

**Verify**: Manual check in `/__ui`

---

<a id="t237"></a>
### T237 · Single-host deploy guide

**Depends on**: T013 · **Parallel**: no · **Size**: S

**Read first**: `MA/docs/DEPLOYMENT.md`, `MA/README.md` (Production deploy, Reverse proxy, Release checklist)

**Files**: create `docs/DEPLOYMENT.md`

**Steps**:

1. Port MA's structure: prerequisites, `.env` (link to ENV.md), Compose up (api, worker, beat, db, redis, clamav), the reverse proxy with SSE buffering off, health checks, first admin (`FIRST_USER_IS_ADMIN`), backups, and upgrading (migrations run automatically).
2. **Remove** MA's "single API process" limit. Here the API scales horizontally, and the workers too.


**Acceptance**:
- [ ] A new engineer can deploy single-host from the guide alone (dry run on a clean VM)

**Verify**: Follow docs/DEPLOYMENT.md on a fresh VM

---

<a id="t238"></a>
### T238 · Terraform for staging

**Depends on**: T013 · **Parallel**: no · **Size**: L

**Read first**: research.md R16

**Files**: create `infra/terraform/{modules/*,envs/staging/*}`

**Steps**:

1. Modules: `network` (VPC with 2 AZs, private and public subnets, NAT), `db` (RDS Postgres 16 Multi-AZ, the pgvector parameter group, 14-day PITR), `redis` (ElastiCache), `storage` (S3 buckets for uploads and exports with versioning, CloudFront for assets), `ecs` (cluster, the services api, worker-turns, worker-files, worker-exports, beat, and clamav, an ALB with sticky sessions **off** and an SSE idle timeout of 300 s), `secrets` (Secrets Manager entries wired as env), `ses` (domain identity, DKIM, a configuration set with bounce SNS), and `waf` (managed rules plus a rate rule).
2. The `worker-files` security group allows egress only to S3, ClamAV, Postgres, Redis, and the embeddings endpoint (R13: "no egress").


**Acceptance**:
- [ ] `terraform plan` is clean
- [ ] Staging serves `/v1/health`
- [ ] The worker-files egress restriction is verified (curl to the internet fails)

**Verify**: `terraform -chdir=infra/terraform/envs/staging plan`

---

<a id="t239"></a>
### T239 · Production environment

**Depends on**: T238, FR-037 resolved · **Parallel**: no · **Size**: M

**Steps**: `envs/prod` uses the same modules in the FR-037 region. Add cross-region snapshot copy for RDS and S3 replication for uploads. Set the alarms from T229 and deletion protection on. Record the region decision in research.md R16.


**Acceptance**:
- [ ] Prod is up in the chosen region with deletion protection
- [ ] Snapshot copy and replication are verified

**Verify**: `terraform -chdir=infra/terraform/envs/prod plan`

---

<a id="t240"></a>
### T240 · Deploy workflow

**Depends on**: T238 · **Parallel**: no · **Size**: M

**Files**: create `.github/workflows/deploy.yml`

**Steps**:

1. On merge to `main`: build and push the images (tags `sha`), run the migration task on staging (an ECS run-task with `alembic upgrade head` and `setup_langgraph`), then deploy the services (CodeDeploy blue/green for api, rolling for workers). Smoke test `/v1/health` and one fake-model turn.
2. Production uses `workflow_dispatch` with an approval environment. The same steps, plus automatic rollback when the 5xx rate rises over 2% within 10 min.


**Acceptance**:
- [ ] A merge deploys to staging automatically
- [ ] Production requires approval
- [ ] The rollback triggers on an injected 5xx spike

**Verify**: Watch a real deploy run

---

<a id="t241"></a>
### T241 · Restore drill and runbooks

**Depends on**: T239 · **Parallel**: no · **Size**: M

**Files**: create `docs/runbooks/{upstream-outage,stuck-queue,waiting-input-backlog,webhook-backlog,restore,rotate-secrets}.md`

**Steps**:

1. Do one point-in-time restore into a scratch instance and time it. Record the RTO and RPO.
2. Each runbook covers symptoms, the dashboards to check, the steps, and rollback. Upstream outage covers switching to the fallback model in Admin › Model.


**Acceptance**:
- [ ] The restore is completed and timed
- [ ] The RTO and RPO are recorded
- [ ] Every runbook exists

**Verify**: Review docs/runbooks/

---

<a id="t242"></a>
### T242 · GA sign-off

**Depends on**: everything · **Parallel**: no · **Size**: M

**Files**: create `docs/ga-signoff.md`

**Steps**:

1. On staging, run quickstart.md end to end in **both** languages, on desktop and mobile, and tick each step.
2. Fill in a table for SC-001 to SC-012 with the measured value, the source (eval run, dashboard, test), and pass or fail.
3. Remove the `skipif(route_missing)` markers from the T122 matrix and make sure it's green.
4. Confirm the three `[NEEDS CLARIFICATION]` items (FR-034, FR-037, FR-038) are resolved and reflected in config.

**Acceptance**:
- [ ] Every SC passes, or has a signed exception from the product owner in the doc
