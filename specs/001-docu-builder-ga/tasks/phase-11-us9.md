# Phase 11: US9, plans, credits, and billing (task cards)

Before any card, read [IMPLEMENTER.md](../IMPLEMENTER.md). **Story test**: quickstart.md › US9. **Blocked on FR-034 (prices)** for the real values. Build everything with placeholder prices from config.

---

<a id="t175"></a>
### T175 · Stripe webhook tests (write first)

**Depends on**: T039 · **Parallel**: yes · **Size**: M

**Files**: create `BT/integration/test_stripe_webhooks.py` and `BT/fixtures/stripe/*.json` (captured with `stripe trigger` or hand-written from the Stripe docs)

**Cases**:

1. A bad signature → 400, and nothing is stored.
2. `checkout.session.completed` (Pro) → a subscription row, `workspace.plan='pro'`, and `stripe_customer_id` set.
3. `invoice.paid` → `grant(4000, key=grant:{invoice_id})`. Sending the same event twice gives one grant.
4. `customer.subscription.updated` (seats 5) → seats updated. `deleted` → the plan reverts to `free` at `current_period_end` (a scheduled downgrade field), not right away.
5. Out of order: `invoice.paid` arrives before `checkout.session.completed` → the grant still applies once the workspace is resolvable (store the event and retry it from a beat job every 5 min until it resolves).
6. `invoice.payment_failed` → status `past_due`. After 7 days (frozen time), the downgrade job sets `free`.


**Acceptance**:
- [ ] Every case listed above is its own test function (`test_<short_name>`)
- [ ] The tests run and **fail for the expected reason** (missing module or not implemented) until the implementation task lands
- [ ] No production code is added in this task

---

<a id="t176"></a>
### T176 · Plan gating tests (write first)

**Depends on**: T041 · **Parallel**: yes · **Size**: S

**Files**: create `BT/integration/test_plans.py`

**Cases**, per plan (free, pro, team):

| Feature | Free | Pro | Team |
|---|---|---|---|
| Export watermark | yes | no | no |
| `generate_image` in toolset | no | yes | yes |
| Attachments per thread | 3 | 10 | 10 |
| Workspace skills | no | no | yes |
| Max effort | `standard` | `deep` | `deep` |
| Workspace templates | no | no | yes |


**Acceptance**:
- [ ] Every case listed above is its own test function (`test_<short_name>`)
- [ ] The tests run and **fail for the expected reason** (missing module or not implemented) until the implementation task lands
- [ ] No production code is added in this task

---

<a id="t177"></a>
### T177 · Billing models

**Depends on**: T024 · **Parallel**: no · **Size**: S

**Files**: create `BE/db/models/billing.py` and `backend/alembic/versions/0007_billing.py`

**Steps**:
- `subscriptions` per data-model.md, plus `downgrade_at`.
- `stripe_events`: the primary key is the Stripe event id, plus `processed_at`, `attempts`, and `last_error`.
- No RLS on either; access goes through the service layer.


**Acceptance**:
- [ ] The migration upgrades and downgrades cleanly
- [ ] The `stripe_events` primary key is the Stripe event id

**Verify**: `uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head`

---

<a id="t178"></a>
### T178 · Plan definitions

**Depends on**: T177 · **Parallel**: no · **Size**: S

**Read first**: spec.md FR-033/FR-034 (placeholders); the T176 table

**Files**: create `BE/billing/plans.py` and `backend/src/docu/data/plans.json`

**Steps**:

1. `plans.json` holds `{free:{monthly_credits:400, seat_credits:null, features:{…}}, pro:{monthly_credits:4000, stripe_price_id:"price_…", …}, team:{seat_credits:6000, stripe_price_id:"…", …}}`. Mark it `"_note": "PLACEHOLDER — FR-034"`.
2. `plan_for(workspace) -> Plan` and `feature(workspace, name) -> bool|int|str`.
3. **Wire the gates now**:
   - watermark (T164)
   - images (`build_tools`, T171)
   - attachments limit (T153)
   - workspace skills (T201)
   - effort cap (T078 and `GET /v1/models`)
   - workspace templates (T113)

**Acceptance**:
- [ ] T176 passes

---

<a id="t179"></a>
### T179 · Billing routes

**Depends on**: T178 · **Parallel**: no · **Size**: M

**Read first**: contracts/rest-api.md › Billing

**Files**: create `BE/api/routers/billing.py` and `BE/billing/stripe_client.py`

**Steps**:

1. `GET /v1/billing` → `{plan, seats, status, balance, monthlyAllowance, periodEnd, usage:{thisPeriod}}`. `thisPeriod` is the sum of the negative ledger deltas since the period start.
2. `POST /checkout {plan, seats?}` (owner only) creates or reuses the Stripe customer and a Checkout Session (`mode=subscription`, `success_url=/settings/billing?ok=1`, `cancel_url=…`, `client_reference_id=workspace_id`, `metadata.workspace_id`). Returns `{url}`.
3. `POST /portal` → a Customer Portal session `{url}`.
4. `GET /ledger` is paginated, owner only.


**Acceptance**:
- [ ] Checkout returns a Stripe URL in test mode
- [ ] Non-owners get 403 on checkout, portal, and ledger
- [ ] `GET /v1/billing` matches the contract shape

**Verify**: `uv run pytest tests/integration/test_billing_routes.py -q -m db` (stripe mocked with respx)

---

<a id="t180"></a>
### T180 · Stripe webhook handler

**Depends on**: T175, T179 · **Parallel**: no · **Size**: M

**Files**: create `BE/billing/stripe_webhooks.py` and `BE/api/routers/webhooks.py`

**Steps**:

1. `POST /v1/webhooks/stripe`: read the **raw body**, `stripe.Webhook.construct_event(body, sig, secret)`, then `INSERT … ON CONFLICT DO NOTHING` into `stripe_events`. If it was new, process it in the same transaction. Return 200 fast (keep the processing light; the grant is a single ledger insert).
2. Handlers per the T175 cases. Resolve the workspace through `metadata.workspace_id` or `stripe_customer_id`. If it can't be resolved, leave `processed_at` null, and the beat job `docu.stripe_retry` reprocesses.
3. Audit `billing.plan_changed`, `billing.payment_failed`, `billing.canceled`.
4. Beat `docu.billing_downgrades`, daily: apply `downgrade_at` (canceled and past_due grace).

**Acceptance**:
- [ ] T175 passes

---

<a id="t181"></a>
### T181 · Seat sync

**Depends on**: T180, T129 · **Parallel**: no · **Size**: S

**Files**: create `BE/services/seats.py` (replacing the no-op from T129)

**Steps**: on a member add or remove in a Team workspace, `stripe.Subscription.modify(sub_id, items=[{id, quantity=member_count}], proration_behavior="create_prorations")`. Run it async in a Celery task (`docu.seats_sync`) with retry. Never block the request.


**Acceptance**:
- [ ] Adding a member to a Team workspace enqueues `docu.seats_sync` with the right quantity
- [ ] Stripe failures retry, and the member add still succeeds

**Verify**: `uv run pytest tests/integration/test_seats.py -q`

---

<a id="t182"></a>
### T182 · Plan-aware monthly grant

**Depends on**: T180 · **Parallel**: no · **Size**: S

**Files**: modify `BE/worker/tasks/credits.py` (replacing T041)

**Steps**: Free workspaces keep the T041 top-up. Paid workspaces are granted only by `invoice.paid` (T180). Team gets `seat_credits × seats`. Remove the `# Replaced by` comment.


**Acceptance**:
- [ ] Free top-up behavior from T041 is unchanged
- [ ] A Team workspace with 3 seats gets 18,000 credits on `invoice.paid`

**Verify**: `uv run pytest tests/integration/test_free_grant.py tests/integration/test_stripe_webhooks.py -q`

---

<a id="t183"></a>
### T183 · Daily reconciliation

**Depends on**: T180 · **Parallel**: no · **Size**: S

**Files**: create `BE/worker/tasks/reconcile.py`

**Steps**:

1. Daily, for each workspace with a subscription, compare the local `plan`, `status`, and `seats` with `stripe.Subscription.retrieve`, and compare `credit_balance` with `SUM(credit_ledger.delta)`.
2. Any mismatch → a structured log at ERROR plus a Sentry event, with **no auto-fix** (SC-008 needs zero unexplained differences, so humans look).


**Acceptance**:
- [ ] A seeded mismatch (plan or balance) logs an ERROR and sends one Sentry event
- [ ] Nothing is changed automatically

**Verify**: `uv run pytest tests/integration/test_reconcile.py -q`

---

<a id="t184"></a>
### T184 · Usage alerts

**Depends on**: T178, T032 · **Parallel**: no · **Size**: S

**Files**: create `BE/worker/tasks/usage_alerts.py` and `BE/emails/usage_{80,100}.{en,ar}.html`

**Steps**: hourly, find the workspaces whose period usage crossed 80% or 100% of the allowance, with no alert sent yet this period (Redis key `alert:{ws}:{period}:{level}`). Email the owner(s).


**Acceptance**:
- [ ] Crossing 80% sends exactly one email per period
- [ ] Crossing 100% sends exactly one more
- [ ] Arabic owners get the Arabic template

**Verify**: `uv run pytest tests/integration/test_usage_alerts.py -q`

---

<a id="t185"></a>
### T185 · Settings › Billing

**Depends on**: T179 · **Parallel**: yes · **Size**: M

**Read first**: ux.md §5.12 (Billing); the dataviz guidance for the usage chart (single series, violet accent)

**Files**: create `FE/pages/settings/Billing.tsx` and `FE/features/billing/UsageChart.tsx`

**Steps**:

1. A plan card (name, price from the plans config through `GET /v1/billing`, renewal date, `Upgrade` or `Manage` (portal)).
2. A credits meter (balance and allowance, with the threshold colors from CreditPill).
3. The usage chart: 30 days of daily totals (`GET /v1/billing/usage?days=30`, in the contract). Reuse the `BarChart` from `FP/slides` with the UI tokens.
4. A ledger table, owner only.
5. Upgrade cards per plan with feature bullets (from `plans.json`, localized names). `Upgrade` posts to checkout and redirects.
6. `?ok=1` → a success toast and a refetch.


**Acceptance**:
- [ ] Every section in ux.md §5.12 Billing renders with real data
- [ ] Upgrade redirects to Stripe test Checkout, and `?ok=1` shows the success toast

**Verify**: `pnpm test:e2e -- billing`

---

<a id="t186"></a>
### T186 · Upgrade banner and out-of-credits states

**Depends on**: T185 · **Parallel**: yes · **Size**: S

**Read first**: ux.md §3.1 (upgrade pill), §5.2 (out of credits), §6.2

**Files**: create `FE/features/billing/{UpgradePill,OutOfCredits}.tsx`

**Steps**:

1. On Create, for Free: the centered pill "✦ Upgrade for more AI", dismissible for the session.
2. With a balance ≤ 0, the composer is disabled and a warning Banner shows with an Upgrade link. In the editor, the same state shows in the agent column.
3. `turn_failed(insufficient_credits)` shows the Upgrade link (T086 already does this; verify it).


**Acceptance**:
- [ ] With a balance of 0, the composer is disabled with the banner on Create and in the editor
- [ ] The Free pill is dismissible for the session

**Verify**: `pnpm test:e2e -- billing`

---

<a id="t187"></a>
### T187 · e2e test: billing

**Depends on**: T185, T186 · **Parallel**: yes · **Size**: S

**Files**: create `frontend/apps/web/tests/e2e/billing.spec.ts`

**Cases** (Stripe test mode with the Stripe CLI forwarding, in a separate CI job with secrets, `@billing` tag):

1. Free with balance 0 (seeded through a test endpoint): send is disabled and the banner shows.
2. Upgrade: the Checkout page (test card 4242…), then a redirect back. The balance increases and the plan is Pro.
3. The portal opens.

**Acceptance**:
- [ ] All 3 cases pass in the `@billing` CI job

**Verify**: `pnpm test:e2e -- billing`
