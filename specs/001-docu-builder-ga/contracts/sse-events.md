# Contract: Turn Event Stream (SSE)

**Endpoint**: `GET /v1/turns/{turnId}/events`
**Auth**: session cookie. The caller must be able to view the turn's document.
**Source of truth**: `backend/src/docu/domain/events.py` (Pydantic, discriminated on `type`). TypeScript types are generated into `frontend/packages/api-types`.
**Lineage**: The event names and shapes match agent_console `models/events.py`, so its `Blocks`, `ChoiceForm`, `ChoicePrompt`, and `ApprovalDiffCard` components render them unchanged. Document and turn lifecycle events are added for the editor.

## Transport

- `Content-Type: text/event-stream`.
- A `: ping` comment is sent every 15 s, as in agent_console's `iter_job_sse_frames`.
- Each event is framed as `id: <redis-stream-id>`, then `data: <json with "type">`.
- **Resume**: on reconnect with `Last-Event-ID`, the server replays everything after that id, then continues live.
- The stream closes after a terminal event (`turn_committed`, `turn_failed`, or `turn_cancelled`). It also closes after `waiting_input`. A later resume continues on the **same** stream id.
- Streams are kept for 1 h after a terminal event. After that the endpoint returns `410 Gone`.
- **Producer**: the worker maps the LangGraph `astream(stream_mode=["messages", "updates", "custom"])` stream:
  - `messages` gives `text_delta`, `reasoning_delta`, and `tool_call_delta`.
  - `updates` gives `tool_call`, `tool_result`, and `__interrupt__`.
  - `custom` (from `get_stream_writer()`) gives `doc_patch`, `status`, and `memory_saved`.

## Events

### From agent_console (same shapes)

| `type` | Fields | UI |
|---|---|---|
| `text_delta` | `text` | Appended to the reply |
| `reasoning_delta` | `text` | Collapsible "Thinking" block. It is never sent back to the model. |
| `tool_call_delta` | `index`, `id`, `name`, `argumentsChars` | Progress while the arguments stream (e.g. "Writing 6 slides… 4.2k chars") |
| `tool_call` | `id`, `name`, `arguments` | A tool block opens |
| `tool_approval` | `id`, `name`, `arguments`, `approvalCard` | Approval card with Allow, Deny, and "Always allow in this thread". See below. |
| `ask_user` | `id`, `question`, `options?`, `fields?`, `allowFreeText` | ChoicePrompt or ChoiceForm |
| `tool_result` | `id`, `name`, `result`, `ok` | The tool block closes and collapses when done |
| `status` | `message` (i18n key + params) | A transient line, e.g. "Compacting context…" |
| `error` | `message`, `code` | Inline error |
| `done` | `steps` | Sent right before `turn_committed` |

### Added for Docu Builder

| `type` | Fields | UI |
|---|---|---|
| `turn_started` | `turnId`, `baseVersion`, `model`, `effort`, `profile` | Composer switches to Stop |
| `doc_patch` | `toolCallId`, `ops: DocOp[]`, `changedSlideIds`, `draftVersion` | Applied to the draft on the canvas and filmstrip |
| `memory_saved` | `memoryId`, `text` | "Remembered" chip in the thread |
| `skill_loaded` | `name` | "Using skill: …" chip |
| `step_limit` | `steps` | Note that the turn hit its step budget (wrap-up follows) |
| `waiting_input` | `turnId`, `expiresAt` | Canvas stays read-only, and the card waits for an answer |
| `turn_committed` | `turnId`, `version`, `revisionId`, `creditsCharged`, `changedSlideIds`, `usage` | Terminal |
| `turn_failed` | `turnId`, `code: TurnErrorCode`, `message`, `retryable` | Terminal. The client rolls back to `baseVersion`. |
| `turn_cancelled` | `turnId`, `reason: 'user' \| 'expired'` | Terminal. The client rolls back to `baseVersion`. |

### `approvalCard`

```ts
type ApprovalCard =
  | { kind: 'replace_slides'; before: SlideSummary[]; after: SlideSummary[]; manualEditsLost: number }
  | { kind: 'delete_slides'; slides: SlideSummary[] }
  | { kind: 'generate_image'; slideId: string; prompt: string; credits: number }
  | { kind: 'mcp_write'; server: string; tool: string; argumentsPreview: string };
type SlideSummary = { id: string; index: number; layout: string; title: string };
```

### `ask_user`

This follows agent_console `ask_user` and its limits:
- `options`: at most 64. A long list switches the UI to a searchable dropdown.
- `fields`: at most 6, each `{ key, label, type: 'choice' | 'text' | 'number', options? }`.

The answer is sent through `POST /v1/turns/{id}/resume` with `{ answers: Record<string, string> }`.

### `DocOp`

```ts
type DocOp =
  | { op: 'set_title'; title: string }
  | { op: 'set_theme'; themeId: string }
  | { op: 'insert_slide'; slide: Slide; afterSlideId: string | null }
  | { op: 'update_slide'; slideId: string; slide: Slide }
  | { op: 'delete_slide'; slideId: string }
  | { op: 'move_slide'; slideId: string; afterSlideId: string | null }
  | { op: 'replace_slides'; slides: Slide[] };
```

The client keeps `committed` and `draft` copies of the document and renders `draft` while a turn runs.

### `TurnErrorCode`

| Code | User message (en) | Retryable |
|---|---|---|
| `insufficient_credits` | You're out of credits for this month. | no |
| `doc_busy` | The agent is already working on this document. | yes |
| `upstream_unreachable` | The AI service can't be reached. | yes |
| `provider_auth` | The AI service rejected our request. We're on it. | no |
| `provider_rate_limited` | The AI service is busy. Try again in a moment. | yes |
| `context_overflow` | This thread no longer fits the model. Start a new thread from this document. | no |
| `version_conflict` | This document changed while the agent was working. | yes |
| `worker_lost` | Something interrupted this turn. Nothing was changed. | yes |
| `content_blocked` | This request can't be completed because it may break the content rules. | no |
| `internal` | Something went wrong. Nothing was changed. | yes |

Arabic messages live in `frontend/apps/web/src/i18n/ar.json` under `errors.turn.*`.
