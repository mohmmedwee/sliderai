# Docu Builder Constitution

## Core Principles

### I. The Agent Edits Through Typed Tools

The agent changes a document only through typed document tools: `set_title`, `set_theme`, `add_slide`, `update_slide`, `delete_slide`, `move_slide`, `replace_slides`, and `generate_image`. Other tools (skills, memory, attachments, web, connectors, `ask_user`) can't touch the document. It never pastes free text into placeholder cards, and the document is never built by parsing prose. Every tool argument is validated against the shared schema before it is applied. An invalid call returns an error to the model and never crashes the turn.

### II. Arabic and English Parity (NON-NEGOTIABLE)

Every feature ships in Arabic (RTL) and English (LTR) at the same time. That covers:

- UI copy
- layout direction
- fonts
- plural rules
- dates and numbers
- templates
- agent replies
- exports
- e2e tests

A feature that works in only one language is not done.

### III. One Schema, Shared Everywhere

The Pydantic models in `backend/src/docu/domain/` are the single source of truth for slides, documents, tool arguments, API payloads, and stream events.

- The API, worker, agent, and exporter import those models directly.
- The frontend's TypeScript types in `frontend/packages/api-types` are generated from the OpenAPI document. Nobody edits them by hand.
- CI fails when the generated types are out of date.
- No layer defines its own copy of a shape.

### IV. Every Agent Turn Is Reversible

A turn works on a draft copy of the document and commits a new revision only when it succeeds. Failure, cancellation, or a credit shortfall leaves the document exactly as it was before the turn. Every revision can be restored.

### V. Test-First Where It Hurts

Tests are written before the implementation, and fail first, for:

- tool reducers
- the permissions matrix
- the credit ledger
- Stripe webhooks
- the turn lifecycle

Agent evals in Arabic and English gate any change to prompts, tools, or model configuration. A regression of more than 3 points on any scorer blocks the merge.

### VI. Tenant Isolation and Privacy by Default

Every tenant-owned row carries `workspace_id`. Repositories always filter by it, and Postgres row-level security enforces it a second time. Attachment content is treated as data, never as instructions. Model providers run under agreements that disable training on customer data. Users can export and delete their data.

### VII. Observable and Accountable

Every turn is traced from the click to the model call, using OpenTelemetry and LangSmith. Every credit movement is a ledger entry with an idempotency key. Cost per turn and per workspace is measured from day one.

### VIII. Simplicity Over Generality

Slides use five structured layouts until after GA. New infrastructure, new services, and new abstractions must be justified in the plan's Complexity Tracking table. YAGNI applies.

## Additional Constraints

- **Backend stack:** Python 3.12. FastAPI, Pydantic v2, SQLAlchemy 2 + Alembic, Celery workers, LangChain + LangGraph (checkpointer, Store, interrupts), PostgreSQL 16 + pgvector, Redis, S3-compatible storage. Type checked with `mypy --strict` and linted with `ruff`.
- **Frontend stack:** TypeScript (strict), React 19 SPA built on the agent_console frontend. API types are generated, never hand-written.
- **Lineage:** The agent concepts come from agent_console (`my_agent`): typed events, profiles, skills, memory, MCP, human-in-the-loop, compaction, and guards. Port its seams (BlobStore, auth, MCP OAuth and sealing, prompts loader, frontend components) before inventing new ones. Never copy third-party material whose license forbids reuse.
- **Accessibility:** WCAG 2.2 AA. Every theme's contrast is checked by a test.
- **Performance budgets:** app JS under 250 KB gzip, share viewer under 120 KB gzip, time to first slide p95 under 8 s.
- **Brand:** no third-party product artwork, names, or logos. The reference screenshots are for layout only.

## Development Workflow

- Spec-driven development: `spec.md` → `plan.md` → `tasks.md` → implement. Changes to scope go through the spec first.
- Each pull request references task IDs, passes lint, typecheck, unit, integration, and e2e tests in both locales, and runs evals when agent files change.
- Database migrations must stay backward compatible for one release. They run before new code is deployed.
- Feature flags gate model changes, new tools, and plan-gated features.

## Governance

This constitution overrides other practices. Amendments need a written rationale, a version bump, and an update to every affected spec or plan. Reviewers check each PR against these principles. Any violation must be listed in Complexity Tracking with a justification.

**Version**: 1.2.0 | **Ratified**: 2026-10-19 | **Last Amended**: 2026-10-19

**Amendment 1.1.0**: The backend moves from TypeScript to Python, because LangChain and LangGraph are Python-first and Python has stronger file parsing and PPTX libraries. Principle III now uses Pydantic as the source of truth, with generated TypeScript types on the frontend.

**Amendment 1.2.0**: The agent design is built on the agent_console concepts, re-implemented on LangChain + LangGraph. Principle I now separates document tools from the other tools. A lineage rule is added to Additional Constraints.
