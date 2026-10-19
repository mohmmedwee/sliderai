# Feature Specification: Docu Builder GA

**Feature Branch**: `001-docu-builder-ga`
**Created**: 2026-10-19
**Status**: Draft
**Input**: User description: "An AI agent for decks and documents in the shape of the workspace in the screenshots. A prompt starts a conversation, the agent writes and edits the document, and the same thread stays beside the editor. Arabic and English. A production product with users, workspaces, sharing, export, attachments, image generation, and billing."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create a deck from one prompt (Priority: P1)

A signed-in user opens Create, which shows "What do you want to create together?". They pick a format (presentation, document, webpage, or social), type what they want, and press Send. The editor opens right away. The agent replies briefly in the user's language and writes a themed draft. Each slide appears on the canvas and in the filmstrip as it is written.

**Why this priority**: This is the core value of the product. Without it, nothing else matters.

**Independent Test**: Sign in, send "a 6-slide deck on the water cycle for grade 5" in English, then do the same in Arabic. Each time, a themed draft of 4 to 8 slides appears in one turn with no manual step.

**Acceptance Scenarios**:

1. **Given** a signed-in user on Create with Presentation selected, **When** they send a prompt, **Then** the editor opens and the first slide appears within 8 seconds (p95).
2. **Given** a turn in progress, **When** each slide is written, **Then** the canvas and the filmstrip update without a page reload.
3. **Given** the UI is in Arabic, **When** the user sends a prompt, **Then** the agent replies in Arabic, the slides are in Arabic, and the layout is right to left.
4. **Given** a turn in progress, **When** the user presses Stop, **Then** the turn ends and the document is exactly as it was before the turn.
5. **Given** the model provider fails, **When** a turn errors, **Then** the thread shows a plain-language error with Retry, and the document is unchanged.
6. **Given** a vague prompt such as "make a deck for my class", **When** the agent needs key facts, **Then** it asks one clarifying question with clickable options or a short form (audience, length, language) before drafting. Answering resumes the same turn.
7. **Given** a model that thinks before answering, **When** a turn runs, **Then** its thinking appears in a separate collapsible block, never mixed into the reply. Each tool step shows as a compact block that collapses when it finishes.

---

### User Story 2 - Refine by conversation and by hand (Priority: P1)

The user keeps the agent column open beside the editor and asks for changes, such as "make slide 3 shorter" or "add a slide about evaporation". The agent changes only what was asked. The user can also click any text on the canvas and edit it directly. They can undo any agent turn, browse version history, and come back to the thread later from Conversations.

**Why this priority**: A first draft is never final. Editing is where users spend most of their time.

**Independent Test**: On an existing deck, send "make slide 3 shorter". Only slide 3 changes, and the agent's message shows a preview of slide 3. Then undo that turn: slide 3 returns to how it was.

**Acceptance Scenarios**:

1. **Given** a deck of 6 slides, **When** the user asks to change slide 3, **Then** only slide 3 changes. On the eval set, edits must stay that local in at least 95% of cases.
2. **Given** an agent message that changed slides, **When** the user views it, **Then** small previews of the changed slides appear inside the message.
3. **Given** a slide on the canvas, **When** the user clicks a text block, edits it, and clicks away, **Then** the change is saved within 300 ms (p95) and the agent sees it on the next turn.
4. **Given** an agent turn in progress, **When** the user tries to edit the canvas, **Then** the canvas is read-only and a banner says the agent is editing, with a Stop button.
5. **Given** any revision in version history, **When** the user restores it, **Then** the document matches that revision, and the restore itself is a new revision.
6. **Given** past threads, **When** the user opens Conversations, **Then** Active and Archived tabs list them. Opening one restores the document and the chat. With no threads, the empty state is shown.
7. **Given** the editor, **When** the user presses Present, **Then** slides show fullscreen, arrow keys move between them, and Esc returns to the editor.
8. **Given** an earlier user message in the thread, **When** the user edits it and re-sends, **Then** the conversation rewinds to that point, the document goes back to the revision it had before that turn, and the agent runs again.
9. **Given** a deck with manual edits made since the last agent turn, **When** the agent wants to rewrite the whole deck, **Then** it first shows a before/after approval card. Allow applies the change. Deny keeps the deck, and the agent continues with targeted edits.
10. **Given** a turn finishes while the tab is in the background, **When** it completes, **Then** the user gets a browser notification (if they allowed notifications).

---

### User Story 3 - Start from a template and restyle with themes (Priority: P2)

The user browses the template library and filters it by search, format, category, and color. They attach a template to the composer, where it shows as a card, as in the screenshot. The agent follows the template's structure and theme but writes content from the prompt. In the editor, Patterns opens a theme grid, and applying a theme restyles every slide instantly without calling the model.

**Why this priority**: Templates and themes are the main way users steer the visual quality of the output.

**Independent Test**: Attach the "Roadmap" template, then send a prompt about a different topic. The draft uses the template's layouts and theme, and none of the template's sample text.

**Acceptance Scenarios**:

1. **Given** the library, **When** the user filters by "education" and "green", **Then** only matching templates show, with counts. **When** nothing matches, **Then** an empty state offers to clear the filters.
2. **Given** a template is chosen and the composer already holds a prompt, **When** the user chooses it, **Then** a thread starts right away. **Given** the composer is empty, **Then** the user returns to Create with the template attached.
3. **Given** a document, **When** the user applies a theme from Patterns, **Then** every slide restyles within one frame, no credits are used, and a revision is recorded.

---

### User Story 4 - Accounts, workspaces, and team roles (Priority: P2)

A visitor signs up with email or Google and gets a personal workspace. They can create a team workspace, invite people by email, and give each one a role: Owner, Admin, Editor, or Viewer. Members see the workspace's documents according to their role. Users manage their profile, language, password, two-factor authentication, and sessions. They can export all their data or delete their account.

**Why this priority**: Required for teams and for paid plans. User Stories 1 to 3 work with only a personal account.

**Independent Test**: User A creates a team workspace and invites B as Viewer. B accepts, can open and present A's documents, and cannot edit them or run the agent on them.

**Acceptance Scenarios**:

1. **Given** a visitor, **When** they sign up with email, **Then** they must verify the email before creating documents.
2. **Given** an Admin, **When** they invite an email address, **Then** the invite expires after 7 days and can be revoked.
3. **Given** every role, **When** that role calls every protected action, **Then** the result matches the permissions matrix in data-model.md.
4. **Given** a user in workspace X, **When** they request any resource in workspace Y without membership, **Then** they get "not found". Its existence is never revealed.
5. **Given** a user, **When** they request deletion, **Then** the account is disabled immediately and all their data is gone after 30 days.

---

### User Story 5 - Share and present via link (Priority: P2)

From Share, the user sets general access to Private, Workspace, or Anyone with the link (view only). They can also invite specific people with view or edit access. The link opens a read-only viewer with Present mode and a link preview (title and first-slide image) when pasted into chat apps.

**Why this priority**: Sharing is how documents create value outside the editor, and it drives growth.

**Independent Test**: Set a deck to "Anyone with the link" and open the link in a private browser window. The deck renders and presents. Revoke the link, and the same URL then shows "link no longer available".

**Acceptance Scenarios**:

1. **Given** a public link, **When** an anonymous visitor opens it, **Then** the deck renders read-only, works on a phone, and offers Present.
2. **Given** a public link pasted into a messaging app, **When** the app fetches a preview, **Then** it shows the document title and a first-slide image.
3. **Given** a revoked link, **When** anyone opens it, **Then** no document content is shown.

---

### User Story 6 - Ground the deck in attached files (Priority: P3)

The user attaches files (PDF, DOCX, PPTX, TXT, MD, or CSV) in the composer. The files are listed by name in the thread, and each shows a processing state. The agent writes from their content and can look up details while drafting or editing.

**Why this priority**: Using your own material makes the drafts trustworthy, but the product is still useful without it.

**Independent Test**: Attach a 10-page Arabic PDF report and ask for a summary deck. On the grounding eval, at least 90% of the facts in the deck must trace to the file.

**Acceptance Scenarios**:

1. **Given** a file over 25 MB or of an unsupported type, **When** it is attached, **Then** it is refused with a clear message before upload.
2. **Given** a file that fails the malware scan or can't be parsed, **When** processing ends, **Then** the thread shows it as failed and the agent is not given it.
3. **Given** an attachment that contains instructions such as "ignore previous instructions", **When** the agent reads it, **Then** the agent treats it as content and does nothing outside the current document.
4. **Given** an existing PPTX or DOCX, **When** the user picks Import on Create, **Then** a new editable deck is built from the file's outline (titles, bullets, speaker notes), keeping the file's language and direction.
5. **Given** a spreadsheet or CSV attachment, **When** the user asks for a chart, **Then** the agent builds a `chart` or `table` slide from the data, and that slide exports as a native PPTX chart or table.

---

### User Story 7 - Export to PDF, PPTX, and PNG (Priority: P3)

From Export, the user downloads the document as PDF, as PPTX with editable text, or as one PNG per slide. The export looks like the editor, including Arabic text.

**Why this priority**: Needed when users present or submit elsewhere. It's not needed for creation.

**Independent Test**: Export an Arabic deck to PDF and PPTX. Both open with correct RTL text, and the PDF matches the editor in a visual snapshot comparison.

**Acceptance Scenarios**:

1. **Given** a deck, **When** the user exports it, **Then** progress shows and the download is ready within 20 s (p95).
2. **Given** a Free plan, **When** the user exports, **Then** the export carries a small watermark. Paid plans have none.
3. **Given** a PPTX export, **When** it is opened in a presentation app, **Then** titles, body text, and points are editable text boxes.

---

### User Story 8 - Images on slides (Priority: P3)

The user asks the agent for an image, for example "add a picture of a rain cloud to the first slide", or uploads one into a hero or split slide. Generated images pass moderation and cost image credits.

**Why this priority**: Images improve how slides look, but the product works without them.

**Independent Test**: Ask for an image on slide 1. An image appears in slide 1's field, and the credit balance drops by the image cost.

**Acceptance Scenarios**:

1. **Given** a request for a disallowed image, **When** moderation rejects it, **Then** the agent explains why and uses no credits.
2. **Given** an uploaded image, **When** it is placed, **Then** it is resized for display and served from the CDN.

---

### User Story 9 - Plans, credits, and billing (Priority: P3)

Each workspace is on a plan (Free, Pro, or Team) with monthly credits. The top bar shows the credit balance. Agent turns use credits based on actual usage. Images cost a fixed amount, and exports are free. The user upgrades through checkout and manages the plan in a billing portal. When credits run out, the composer shows an upgrade prompt instead of starting a turn.

**Why this priority**: Required for GA revenue, but not for proving the product works.

**Independent Test**: On Free with 5 credits left, send a prompt. The turn is refused before it starts, with an upgrade prompt. Upgrade to Pro in test mode, and the balance increases while the turn now runs.

**Acceptance Scenarios**:

1. **Given** a paid subscription, **When** a monthly invoice is paid, **Then** credits are granted exactly once, even if the payment event arrives more than once.
2. **Given** a turn, **When** it ends (committed, failed, or cancelled), **Then** the reserved credits are settled to actual usage or refunded, and the ledger balances.
3. **Given** usage reaches 80% and 100% of the month's credits, **Then** the workspace owner is notified once at each threshold.

---

### User Story 10 - The agent remembers my preferences and brand (Priority: P2)

The agent remembers durable facts the user shares, such as "I teach grade 5 science", "keep slides minimal", or "our brand color is #0B5FFF", and applies them in later documents. Workspace admins set brand memory (colors, tone, words to avoid) for everyone. Users view, edit, and delete what the agent remembers on a Memory page.

**Why this priority**: Repeated preferences are the biggest source of edit turns. Remembering them raises first-draft quality.

**Independent Test**: Say "always use formal Arabic and our color #0B5FFF". In a new document, the draft uses formal Arabic and the brand color without being asked.

**Acceptance Scenarios**:

1. **Given** the user states a lasting preference, **When** the agent saves it, **Then** the thread shows a small "Remembered" note, and the item appears on the Memory page.
2. **Given** 50 saved memories, **When** the agent tries to save another, **Then** it asks the user which one to replace.
3. **Given** workspace brand memory, **When** any member creates a document, **Then** the brand rules apply, and members can't edit them.

---

### User Story 11 - Skills: writing playbooks the agent follows (Priority: P3)

The agent has built-in skills, such as deck writing, report writing, pitch decks, lesson decks, bilingual replies, and themes. It loads them when relevant, and a user can force one with `/skill-name` in the composer. Team workspaces can create their own skills, such as "our quarterly board report format", by writing a playbook or describing it and letting the agent draft it.

**Why this priority**: Skills make quality controllable without code changes. Custom skills are a Team-plan differentiator.

**Independent Test**: Create the workspace skill "board report: 7 slides, KPIs first, risks last", then send `/board-report Q3 results`. The deck follows the skill.

**Acceptance Scenarios**:

1. **Given** the skill index, **When** a request matches a skill's description, **Then** the agent loads that skill before drafting, and the thread shows "Using skill: …".
2. **Given** a user picks `/skill` in the composer, **When** they send, **Then** that skill is loaded even if the model wouldn't have chosen it.
3. **Given** a skill description, **When** an admin clicks Generate, **Then** a draft `SKILL.md` is produced for review before it is saved.

---

### User Story 12 - Connectors: pull content from other apps (Priority: P3)

Admins connect outside apps through MCP connectors (for example, Google Drive, Notion, or a company system), using OAuth or a token. The agent can then look up and pull content from those apps while drafting, loading only the tool groups it needs.

**Why this priority**: Content often lives elsewhere. Connectors cut copy and paste, but the core product works without them.

**Independent Test**: Connect a test MCP server that exposes `get_report`, then ask "make a deck from the Q3 report in our wiki". The agent calls the connector, and the deck contains its content.

**Acceptance Scenarios**:

1. **Given** a connector with OAuth, **When** an admin adds it, **Then** the sign-in completes and the connector shows healthy with its tool groups.
2. **Given** a connector tool that writes data, **When** the agent wants to call it, **Then** the user sees an approval card first.
3. **Given** a connector that keeps failing with the same call, **When** the agent repeats it, **Then** the repeat is refused and the agent tells the user what failed.

---

### User Story 13 - Web research with sources (Priority: P3)

The user switches on web search for a thread. The agent searches and reads pages to gather facts, then lists the sources in the speaker notes of the slides that use them.

**Why this priority**: Fresh facts make decks more credible. The feature is off by default to control cost and risk.

**Independent Test**: Switch on web search and ask for "a 5-slide deck on this year's solar capacity in the GCC". The slides cite sources in their speaker notes.

**Acceptance Scenarios**:

1. **Given** web search is off, **When** a turn runs, **Then** no web tools are available and the agent says when a fact may be out of date.
2. **Given** web search is on, **When** the agent uses a page, **Then** its URL and title appear in the notes of the slides that use it.

---

### User Story 14 - Platform administration (Priority: P2)

Platform admins manage users (activate, deactivate, roles), model settings (endpoint, model, context window, effort limits, thinking), versioned prompts, skills switched on per profile, connectors allowed, feature flags, and see usage and cost.

**Why this priority**: Running the product in production needs these controls. my_agent already proved this admin surface.

**Independent Test**: Change the default model in Admin and edit the `deck` prompt as a new version. The next turn uses the new model and prompt version, and both are recorded on the turn.

**Acceptance Scenarios**:

1. **Given** the first user on a new install with `FIRST_USER_IS_ADMIN=true`, **When** they register, **Then** they become the platform admin.
2. **Given** a prompt edit, **When** an admin saves it, **Then** a new version is created, the old one can be restored, and every turn records the version it used.
3. **Given** the usage page, **When** an admin opens it, **Then** it shows tokens, cost, turns, latency, and failure rate per day, per model, and per workspace.

---

### Edge Cases

- The tab closes during a turn: the turn keeps running and commits, and reopening the document shows the result.
- The network drops during streaming: the client reconnects and continues from the last event without duplicating slides.
- Two tabs edit the same document: the second save gets a conflict and the user sees "this document changed, reload".
- A second turn is sent on the same document while one is running: it is refused with "the agent is already working on this document".
- The model calls a tool with an unknown slide id or an invalid layout: the agent gets an error message and corrects itself. After 8 steps the turn stops and says so.
- The model replies with text only: the reply is shown, and the document and its revisions are unchanged.
- One slide mixes Arabic and English: each text block takes its direction from its own content.
- A member is removed while editing: the next request fails with "no access" and the editor becomes read-only.
- Credits run out mid-turn: the turn finishes the current step, commits, and the balance may go briefly negative up to the reservation. It never goes below that.
- A Stripe payment event arrives out of order or twice: the final state matches Stripe.

## Requirements *(mandatory)*

### Functional Requirements

**Agent and documents**

- **FR-001**: System MUST start a conversation thread and a document when the user sends a prompt from Create, and open the editor with the agent already working.
- **FR-002**: System MUST change documents only through typed agent tools (title, theme, add/update/delete/move slide, replace all slides, search attachments, generate image) and validate every call before applying it.
- **FR-003**: System MUST stream the agent's reply text and each document change to the editor as it happens.
- **FR-004**: System MUST apply a turn's changes as one new revision on success, and discard them on failure, cancel, or insufficient credits.
- **FR-005**: System MUST let users cancel a running turn and undo any completed agent turn.
- **FR-006**: System MUST cap a turn at 8 model steps and tell the user when the cap is reached.
- **FR-007**: System MUST allow only one running turn per document, and make the canvas read-only while it runs.
- **FR-008**: System MUST send each turn the format, UI language, attached template structure and theme, attachment summaries, the current document, and the conversation history.
- **FR-009**: Agent MUST reply in the UI language unless the user writes in the other language.
- **FR-010**: System MUST support seven structured slide layouts: hero, title, points, quote, split, table, and chart.
  - Each slide has fields for kicker, title, body, points, button, color field, image, and speaker notes.
  - Table and chart slides also hold structured data.
- **FR-011**: Users MUST be able to edit any text block or button on the canvas directly. Saves use version checks to detect conflicts.
- **FR-012**: System MUST keep a version history per document and let users restore any revision.
- **FR-013**: System MUST continue a turn when the browser disconnects, and let the client resume the stream.

**Editor and screens**

- **FR-014**: Editor MUST show the active slide large with the next slide peeking underneath, a numbered filmstrip that supports reordering by drag, and the agent thread beside the canvas.
- **FR-015**: Editor MUST provide Present mode (fullscreen, arrow keys, Esc to exit), Patterns (theme grid), Share, Export, and Version history.
- **FR-016**: Conversations MUST list threads in Active and Archived tabs, with archive, restore, and delete. Delete asks for confirmation.
- **FR-017**: Template library MUST support search plus format, category, and color filters with counts, and show system and workspace templates.
- **FR-018**: On narrow screens (under 900px), the filmstrip MUST collapse into a slide counter and the agent MUST open as a panel.
- **FR-019**: Every screen MUST be fully usable in Arabic (RTL) and English (LTR), with a language switch saved per user.

**Users, workspaces, sharing**

- **FR-020**: Users MUST be able to sign up and sign in with email and password (with email verification and password reset) or with Google, and optionally turn on two-factor authentication. Identity data MUST be stored in the product's own database.
- **FR-021**: System MUST give every user a personal workspace and let them create team workspaces and switch between them.
- **FR-022**: System MUST support workspace roles Owner, Admin, Editor, and Viewer, and per-document view or edit invitations.
- **FR-023**: System MUST isolate workspaces so that no user can read or detect another workspace's data without membership.
- **FR-024**: Users MUST be able to set general access to Private, Workspace, or Anyone with the link, and revoke and regenerate links.
- **FR-025**: Public links MUST render a read-only viewer with Present mode and a link preview (title and first-slide image).
- **FR-026**: Users MUST be able to export all their data and delete their account. Deletion is permanent after 30 days.

**Files, images, export**

- **FR-027**: Users MUST be able to attach PDF, DOCX, PPTX, TXT, MD, and CSV files, up to 25 MB each and 10 per thread. Each file is scanned, parsed, and made searchable for the agent.
- **FR-028**: System MUST treat attachment content as data, never as instructions.
- **FR-029**: Users MUST be able to generate images (with moderation) or upload images into a slide's field.
- **FR-030**: Users MUST be able to export to PDF, PPTX (with editable text), and PNG per slide, with output matching the editor and correct RTL.

**Billing**

- **FR-031**: System MUST meter agent turns by actual model usage and images at a fixed price, and record every credit change in an append-only ledger with idempotency keys.
- **FR-032**: System MUST refuse to start a turn when the workspace balance can't cover the reservation, and show an upgrade prompt.
- **FR-033**: System MUST support Free, Pro, and Team plans with upgrades through checkout and changes through a billing portal. Team plans bill per seat.
- **FR-034**: Plan prices and monthly credit allowances MUST be [NEEDS CLARIFICATION: final prices and credit allowances per plan. Placeholders: Free 400, Pro 4,000, Team 6,000 per seat].

**Operations and compliance**

- **FR-035**: System MUST rate-limit sign-in, turns, uploads, and exports per IP, user, and workspace.
- **FR-036**: System MUST keep an audit log of membership, sharing, billing, and deletion events.
- **FR-037**: Customer data MUST be stored in [NEEDS CLARIFICATION: data residency region. A Middle East region for Gulf customers under PDPL, or the EU?].
- **FR-038**: Attachments MUST be kept for [NEEDS CLARIFICATION: retention period for attachments on Free and Pro. Proposed: until the thread is deleted]. After that they are deleted.

**Agent behavior (carried over from agent_console)**

- **FR-039**: System MUST stream typed events that keep reply text, thinking, tool progress, tool calls, tool results, approvals, questions, and status separate, so the UI can render each one in its own way.
- **FR-040**: Agent MUST be able to pause a turn to ask the user a question (options or a short form) or to request approval, and resume the same turn from the answer. A paused turn MUST survive server restarts and expire after 30 minutes without an answer.
- **FR-041**: System MUST apply an approval policy per tool (always, ask, never), with defaults defined in research.md R22, and let the user allow a tool for the rest of a thread.
- **FR-042**: System MUST keep long threads within the model's context. It summarizes older turns (showing a "Compacting context…" status), clips old tool outputs, and retries once on context overflow with a smaller budget.
- **FR-043**: System MUST stop runaway repeated text, refuse a tool call that repeats an identical failing call, and recover from empty model replies.
- **FR-044**: Users MUST be able to choose an effort level (fast, standard, deep). The maximum depends on plan and profile, and the step budget scales with it.
- **FR-045**: Users MUST be able to edit an earlier message and re-run from that point, with the document restored to the revision before that turn.
- **FR-046**: System MUST notify the user in the browser when a background turn finishes, if notifications are allowed.

**Memory, skills, connectors, research**

- **FR-047**: Agent MUST be able to remember and forget durable user preferences (up to 50 per user) and apply them in later turns. Users MUST be able to view, edit, and delete them.
- **FR-048**: Workspace admins MUST be able to set brand memory that applies to every member's documents.
- **FR-049**: System MUST provide built-in skills that the agent loads when relevant, a `/skill` picker that forces one, and (on the Team plan) workspace skills, either written by hand or generated from a description.
- **FR-050**: Admins MUST be able to add MCP connectors (OAuth or token), with secrets encrypted at rest. The agent loads connector tool groups on demand, and connector write tools require approval.
- **FR-051**: Users MUST be able to switch web search on per thread. Sources the agent uses MUST be cited in the speaker notes of the slides that use them.
- **FR-052**: Users MUST be able to import an existing PPTX or DOCX into a new editable document.

**Platform administration**

- **FR-053**: Platform admins MUST be able to manage users and roles, model settings, prompt versions, the skills switched on per profile, the connectors allowed, and feature flags.
- **FR-054**: System MUST record, for every turn, the model, prompt version, effort, steps, tokens, latency, and cost, and show totals per day, model, and workspace to admins.
- **FR-055**: The first registered user MUST become platform admin when `FIRST_USER_IS_ADMIN` is set.

### Key Entities

- **User**: A person with an email, a name, a language preference, and security settings. Belongs to one or more workspaces.
- **Workspace**: The unit of ownership and billing. It has members with roles, a plan, and a credit balance.
- **Document**: A titled deck, document, webpage, or social post with a format, a theme, an ordered list of slides, a version, and a visibility setting.
- **Slide**: A structured card with a layout and text fields, plus an optional color field or image.
- **Revision**: An immutable snapshot of a document, made by an agent turn, a manual edit session, or a restore.
- **Thread**: The conversation bound to one document. It holds messages, turns, an optional template, and attachments.
- **Message**: A user, assistant, or tool entry in a thread. It may reference the slides that were changed.
- **Turn**: One agent run. It has a status, the model used, usage, credits, and its outcome.
- **Attachment**: An uploaded file with a processing status, a summary, and searchable chunks.
- **Template**: A named, bilingual example structure with a format, category, colors, and theme.
- **Theme**: A named set of color and font tokens.
- **Share link**: A revocable token that grants view access to one document.
- **Subscription**: A workspace's plan, seat count, and billing status.
- **Credit ledger entry**: One signed credit movement (grant, reservation, settlement, or refund) with an idempotency key.
- **Memory**: A short durable fact or preference owned by a user, or brand memory owned by a workspace.
- **Skill**: A named playbook with a description (used for selection) and a body (instructions). It is either built in or owned by a workspace.
- **Connector**: An outside app connected through MCP. It has encrypted credentials, tool groups, and a health status.
- **Agent profile**: The prompt, tools, skills, memory, and effort limits used for one document format.
- **Prompt version**: An immutable version of a system prompt, recorded on each turn.
- **Pending input**: A question or approval a paused turn is waiting on, with an expiry time.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 70% of new users who send a first prompt finish a draft without an error.
- **SC-002**: Time to first slide is under 8 s and a full first draft is under 45 s, both at p95.
- **SC-003**: Edits stay local (only the requested slides change) in at least 95% of eval cases, in both languages.
- **SC-004**: At least 98% of turns succeed, not counting user cancels.
- **SC-005**: 100% of failed or cancelled turns leave the document byte-identical to its state before the turn.
- **SC-006**: Exports match the editor in visual snapshot tests, and 95% of exports are ready within 20 s.
- **SC-007**: Zero data leaks across workspaces in the permissions matrix tests and the pen test.
- **SC-008**: The credit ledger reconciles with Stripe every day with zero unexplained differences.
- **SC-009**: Every screen passes automated accessibility checks (WCAG 2.2 AA) and e2e tests in both Arabic and English.
- **SC-010**: API availability is at least 99.9% per month.
- **SC-011**: 100% of paused turns (questions and approvals) resume correctly after a worker restart, in integration tests.
- **SC-012**: Documents made in a thread with saved memories need at least 25% fewer follow-up edit turns than the baseline without memory, measured on the eval set.

## Assumptions

- Web only (desktop and mobile browsers) for GA. No native apps.
- Text models are reached through a provider-agnostic layer. Any OpenAI-compatible endpoint (including the self-hosted model used by agent_console) or Anthropic works through configuration. The production default is chosen by the Arabic/English eval suite.
- The agent design follows the proven agent_console (`my_agent`) concepts, re-implemented on LangChain and LangGraph. See research.md Part A.
- Real-time co-editing, comments, brand kits, freeform elements, SSO/SCIM, and a public API come after GA.
- "Docu Builder" is a working name.
