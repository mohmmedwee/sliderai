# Quickstart: Docu Builder GA

**Feature**: `001-docu-builder-ga`

## Prerequisites

- Python 3.12 with `uv`, Node.js 22 LTS with pnpm 9, Docker Desktop, and the Stripe CLI.
- A tool-calling model on any OpenAI-compatible endpoint (`UPSTREAM`, `UPSTREAM_API_KEY`, `MODEL`, `CONTEXT_WINDOW`, the same names as in agent_console), or an Anthropic key. Check it with `uv run python -m docu.scripts.check_endpoint`.
- Optional: Google OAuth client credentials (redirect URI `http://localhost:8000/v1/auth/google/callback`).
- Optional: a LangSmith API key for tracing and evals.

## Run locally

```bash
# infrastructure
docker compose -f infra/compose.yaml up -d   # postgres+pgvector, redis, minio, mailpit, clamav

# backend
cd backend
uv sync
cp .env.example .env              # SECRET_KEY, UPSTREAM, UPSTREAM_API_KEY, MODEL, CONTEXT_WINDOW, FIRST_USER_IS_ADMIN=true, STRIPE_*, LANGSMITH_* …
uv run alembic upgrade head       # schema, RLS policies, extensions
uv run python -m docu.scripts.setup_langgraph      # LangGraph checkpointer + Store tables
uv run python -m docu.scripts.seed                 # themes, 24 templates, built-in skills sync
uv run python -m docu.scripts.check_endpoint       # model replies, emits tool_calls, and still does when streaming
uv run uvicorn docu.api.app:create_app --factory --reload --port 8000
uv run celery -A docu.worker.celery_app worker -Q turns,files,exports,default -l info
uv run celery -A docu.worker.celery_app beat -l info
stripe listen --forward-to localhost:8000/v1/webhooks/stripe

# frontend
cd ../frontend
pnpm install
pnpm gen:api                      # regenerate packages/api-types from http://localhost:8000/v1/openapi.json
pnpm dev                          # web on :5173, proxies /v1 and /s to :8000
cd ..
playwright install chromium       # the export worker needs a local browser
```

- Mailpit at http://localhost:8025 catches invite and notification emails.
- MinIO at http://localhost:9001 holds the files.
- With `AGENT_FAKE_MODEL=1`, the worker uses a scripted `GenericFakeChatModel`, so the whole UI works offline and with no API cost.

## Test commands

```bash
# backend
cd backend
uv run ruff check . && uv run ruff format --check . && uv run mypy src
uv run pytest tests/unit
uv run pytest tests/integration          # testcontainers: real Postgres + Redis
uv run schemathesis run http://localhost:8000/v1/openapi.json   # contract fuzzing
cd ..

# frontend
cd frontend
pnpm lint && pnpm typecheck && pnpm test
pnpm test:e2e                            # projects: en-desktop, ar-desktop, en-mobile, ar-mobile
pnpm gen:api && git diff --exit-code packages/api-types   # type drift check (also in CI)
cd ..

# agent evals (needs real model keys)
uv run --project backend python -m evals.run --suite all
```

## Validation scenarios (one per user story)

**US1: Create from one prompt**
1. Register at `/register`. The first user becomes platform admin. Verify your email through Mailpit, then open Create.
2. Choose Presentation and send: `A 6-slide deck on the water cycle for grade 5`.
3. ✅ The editor opens, the first slide appears in under 8 s, the filmstrip fills in, and the agent replies in English.
4. Switch the language to العربية and send: `عرض من ٥ شرائح عن الطاقة الشمسية`.
5. ✅ The layout is RTL and the reply and slides are in Arabic.
6. Start another prompt and press **Stop** mid-turn.
7. ✅ The document is unchanged and the thread shows "Cancelled".

**US2: Refine**
1. In the deck from US1, send `make slide 3 shorter`.
2. ✅ Only slide 3 changes, and the message shows a preview of slide 3.
3. Click "Undo this turn". ✅ Slide 3 is back to how it was.
4. Click a title on the canvas, edit it, and press Esc. ✅ The change is saved and appears in Version history as a manual revision.
5. Open the same document in a second tab, edit both, and save. ✅ The second save shows the conflict banner.

**US3: Templates and themes**
1. Open Templates and filter by Education + Green. ✅ The counts update.
2. Choose "Roadmap", go back to Create, and send a prompt about a book club.
3. ✅ The draft uses the template's layouts and theme, and none of its sample text.
4. In the editor, open Patterns and apply "Midnight". ✅ Every slide restyles instantly and the credit balance is unchanged.

**US4: Accounts and roles**
1. As user A, create the team workspace "Acme" and invite B as Viewer.
2. B accepts the invite from Mailpit. ✅ B sees A's workspace documents and can present them, but editing and the agent composer are disabled.
3. Run `uv run pytest tests/integration/test_permissions_matrix.py` to execute the matrix test.

**US5: Share**
1. Open Share and choose "Anyone with the link". Copy the link and open it in a private window.
2. ✅ The deck is read-only, Present works, and the page source has OG tags.
3. Rotate the link. ✅ The old URL shows the 404 page.

**US6: Attachments**
1. Attach `evals/fixtures/ar_annual_report.pdf` and send `لخص هذا التقرير في ٦ شرائح`.
2. ✅ The attachment shows parsing, then ready. The deck uses figures from the report, and the LangSmith trace shows `search_attachments` calls.
3. Attach `evals/fixtures/injection.txt`. ✅ The agent doesn't follow the instructions inside the file.

**US7: Export**
1. Export the Arabic deck to PDF and to PPTX.
2. ✅ The PDF matches the editor. The PPTX opens in Keynote or PowerPoint with RTL text that can be edited.
3. On the Free plan, ✅ the watermark is present.

**US8: Images**
1. On a Pro test workspace, send `add an image of a rain cloud to slide 1`.
2. ✅ The image appears in slide 1, and the ledger has an `image` entry.

**US9: Billing**
1. On Free, spend credits until the balance is 0 (or seed `credit_ledger`), then send a prompt.
2. ✅ The turn is refused and an upgrade prompt appears.
3. Upgrade with the test card `4242 4242 4242 4242`. ✅ The webhook grants Pro credits, and resending the event with `stripe events resend` doesn't grant them twice.

**Agent behavior (ported from agent_console)**
1. Send `make a deck for my class`. ✅ The agent asks one question with options (grade, subject, length), and answering resumes the same turn.
2. While it waits, restart the worker container, then answer. ✅ The turn resumes and commits (SC-011).
3. Manually edit two slides, then send `rewrite the whole deck in a more formal tone`. ✅ An approval card shows before and after. Deny keeps the deck.
4. Edit your first message in the thread and re-send. ✅ The document goes back to the earlier revision and the agent re-runs.
5. Choose the "deep" effort with a thinking model. ✅ "Thinking" appears in a collapsible block, and finished tool blocks collapse.

**US10: Memory**
1. Send `always use formal Arabic and our color #0B5FFF`. ✅ A "Remembered" chip appears, and the item shows on the Memory page.
2. Create a new deck. ✅ It is in formal Arabic and uses the brand color without being asked.

**US11: Skills**
1. As a workspace admin on a Team test workspace, generate the skill "board-report" from a description and save it.
2. Send `/board-report Q3 results`. ✅ A "Using skill: board-report" chip appears and the deck follows the skill.

**US12: Connectors**
1. As an admin, add the test MCP server `evals/fixtures/mcp_wiki` under Connectors. ✅ It shows Connected with its groups.
2. Ask `make a deck from the Q3 report in our wiki`. ✅ `list_mcp_tools`, then `use_mcp_tools`, then the connector call. The deck has the content.

**US13: Web research**
1. Switch web search on and ask for a deck on this year's GCC solar capacity. ✅ The sources are in the speaker notes.

**US14: Admin**
1. In Admin › Model, point to another upstream and click Check. ✅ The probe passes.
2. Edit the `deck` prompt as a new version. ✅ The next turn records the new `prompt_version_id`. The usage page shows tokens and cost.
