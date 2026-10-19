# UX Specification: Docu Builder GA

**Feature**: `001-docu-builder-ga` | **Date**: 2026-10-19
**Inputs**:
- the screenshots in `/screen_shots/` (layout reference only; reuse no artwork, names, or logo)
- agent_console's frontend (`MAF`): its component library and token **names**, which are kept so ported components work
- spec.md user stories

**Rule**: Every UI task card points to a section here. If a screen isn't described here, it isn't built. Raise it as BLOCKED (IMPLEMENTER.md §9).

Wireframes are drawn **LTR (English)**. In Arabic the whole layout mirrors (§3.3), except slide content, whose direction comes from each text block's own content.

---

## 1. Design principles

1. **The document is the hero.** On the editor screen the canvas gets the most space, and the chrome stays quiet: neutral surfaces, one accent color, and thin borders.
2. **The agent is a collaborator, not a chat app.** Its column sits beside the work. Tool steps are compact and collapse when done. Thinking is hidden by default.
3. **Calm while the agent works.** The canvas updates in place, with no spinners over the slides. Progress shows as a short status line and a filmstrip pulse on the slide being written.
4. **One accent.** Violet is the brand. Blue appears only for selected navigation (as in the screenshots). Red is for destructive actions only.
5. **Arabic is equal.** Arabic is not a translation layer. Spacing, fonts, and icons are checked in both directions.

---

## 2. Design tokens (UI chrome)

These are separate from **slide themes** (FP/slides). Slide themes style document content only. These tokens style the app.

They are defined in `FE/styles/tokens.css` with Tailwind 4 `@theme`. **Keep MA's token names**, so ported components (Composer, Blocks, ChoiceForm, …) need no class changes. Values marked *changed* differ from MA.

### 2.1 Color: light (default)

| Token | Value | Use |
|---|---|---|
| `--color-canvas` | `#F7F8FC` *(changed)* | App background (the screenshots' very light blue-grey) |
| `--color-surface` | `#FFFFFF` | Cards, panels, composer |
| `--color-elevated` | `#FFFFFF` | Menus, dialogs (with `--shadow-md`) |
| `--color-line` | `#E6E8F0` *(changed)* | Default 1px borders |
| `--color-line-soft` | `#EEF0F6` *(changed)* | Dividers inside panels |
| `--color-ink` | `#14162B` *(changed)* | Primary text (screenshot headings are near-navy) |
| `--color-ink-2` | `#4A4E66` *(changed)* | Secondary text |
| `--color-ink-3` | `#7A7F96` *(changed)* | Placeholder, captions, counts |
| `--color-primary` | `#673CDB` | Brand. Send button active, primary buttons, links. |
| `--color-primary-25/50/100/200/300/400/600` | MA values | Tints. **`--color-primary-200` is the composer focus ring** (the lavender border in the screenshot). |
| `--color-nav-active-bg` | `#DCE6FF` *(new)* | Selected sidebar item and selected pill tab (the screenshot's light blue) |
| `--color-nav-active-ink` | `#1F3FBF` *(new)* | Text and icon on the selected nav item |
| `--color-rail` | `#FFFFFF` *(changed, MA is dark)* | Icon rail background (light in the screenshots) |
| `--color-rail-active` | `#DCE6FF` *(changed)* | Rail item active background |
| `--color-rail-icon` | `#4A4E66` *(changed)* | Rail icons |
| `--color-success`, `--color-warning`, `--color-error` + tints | MA values | Status |
| `--color-overlay` | `rgba(20,22,43,0.45)` *(new)* | Dialog backdrop |

### 2.2 Color: dark (`html.dark`)

| Token | Value |
|---|---|
| `--color-canvas` | `#0F1018` |
| `--color-surface` | `#171826` |
| `--color-elevated` | `#1E2032` |
| `--color-line` | `#2A2D42` |
| `--color-line-soft` | `#22243A` |
| `--color-ink` | `#EEF0FA` |
| `--color-ink-2` | `#B4B8CC` |
| `--color-ink-3` | `#8086A0` |
| `--color-nav-active-bg` | `#26305C` |
| `--color-nav-active-ink` | `#C9D5FF` |
| `--color-rail` | `#13141F` |
| `--color-rail-active` | `#26305C` |
| `--color-rail-icon` | `#B4B8CC` |
| primary tints | MA dark values |

Dark mode follows the system by default. Settings › Profile offers System / Light / Dark (ported `useTheme`).

### 2.3 Typography

| Token | Value |
|---|---|
| `--font-sans` | `"IBM Plex Sans Arabic", "Inter", system-ui, sans-serif` *(changed from Noto Kufi, which is too wide for dense lists)*. Both are self-hosted from `FE/assets/fonts/`. |
| `--font-mono` | `"IBM Plex Mono", ui-monospace, monospace` |

| Style | Size / line height | Weight | Use |
|---|---|---|---|
| `display` | 32 / 40 | 600 | Create heading ("What do you want to create together?") |
| `h1` | 24 / 32 | 600 | Page titles (Conversations, Template explorer) |
| `h2` | 18 / 26 | 600 | Section titles, dialog titles |
| `h3` | 15 / 22 | 600 | Card titles, panel headers |
| `body` | 14 / 22 | 400 | Default |
| `body-strong` | 14 / 22 | 500 | Nav items, buttons |
| `small` | 13 / 20 | 400 | Secondary text, chips |
| `caption` | 12 / 16 | 400 | Counts, timestamps, filmstrip numbers |

Arabic uses the same sizes. Line height is **+2px** for `body` and `small` when `lang="ar"`, to fit the taller glyphs.

### 2.4 Spacing, radius, shadow, motion

- **Spacing**: 4px base. Use the Tailwind scale (`1` = 4px). Page gutters are 24px on desktop and 16px on mobile.
- **Radius**:

| Token | Value | Use |
|---|---|---|
| `--radius-sm` | 6px | Inputs, small buttons |
| `--radius-md` | 10px | Cards, menus |
| `--radius-lg` | 16px | Composer, dialogs, slide canvas |
| `--radius-pill` | 999px | Chips, pill tabs, credit pill |

- **Shadow**: MA's `--shadow-sm`, `--shadow-md`, `--shadow-lg`, `--shadow-composer`. The slide canvas uses `--shadow-md`.
- **Motion**: `--ease-out: cubic-bezier(.2,.8,.2,1)`. Durations: 120 ms (hover, press), 200 ms (panels, menus), 300 ms (dialogs, sheets). Honor `prefers-reduced-motion`: no transforms, only opacity changes.
- **z-index**:

| Layer | z-index |
|---|---|
| base | 0 |
| sticky top bar | 20 |
| side sheet | 40 |
| dialog | 50 |
| toast | 60 |
| tooltip | 70 |

### 2.5 Breakpoints

| Name | Min width | Behavior |
|---|---|---|
| `sm` | 0 | Single column. Rail and sidebar become a bottom tab bar plus a drawer (§3.2). |
| `md` | 768 | Rail visible. Sidebar collapsible (hidden by default). |
| `lg` | 1024 | Rail and sidebar visible |
| `xl` | 1440 | Editor shows the agent column at its full 400px |

### 2.6 Icons

Lucide icons (`lucide-react`), at 16px in dense lists and 20px in the rail and top bar, with a 1.75 stroke. Directional icons (arrows, chevrons, send, undo/redo) flip in RTL with `rtl:-scale-x-100`.

---

## 3. Layout system

### 3.1 App shell (every page except the editor, present mode, share viewer, and auth)

```
┌────┬──────────────────┬──────────────────────────────────────────────────────────┐
│Rail│ Sidebar (240)    │ Top bar (56): [page title / breadcrumbs]   [credits ✦][+ New blank][avatar] │
│(64)│ ┌──────────────┐ ├──────────────────────────────────────────────────────────┤
│ ⌂  │ │Workspace ▾   │ │                                                          │
│ 🗎 │ │ Free         │ │                     Main content                         │
│ ▦  │ ├──────────────┤ │                (max-width per page, centered)            │
│ 🧠 │ │+ Create      │ │                                                          │
│ ⚙  │ │💬 Conversations│                                                          │
│ …  │ │🗎 Documents   │ │                                                          │
│    │ │──────────────│ │                                                          │
│    │ │🔍 Search ⌘K  │ │                                                          │
│    │ │▦ Templates   │ │                                                          │
│    │ │🧠 Memory     │ │                                                          │
│    │ │✦ Skills      │ │                                                          │
│    │ │⇄ Connectors  │ │                                                          │
│    │ │──────────────│ │                                                          │
│ 👤 │ │🗑 Trash       │ │                                                          │
│ ?  │ └──────────────┘ │                                                          │
└────┴──────────────────┴──────────────────────────────────────────────────────────┘
```

- **Rail (64px)**: logo (our own mark), Home (Create), Documents, Templates, Memory, Settings, More (…). At the bottom: Invite (team workspaces), Feedback, Avatar menu, Help "?" (matching the screenshots). Each item is a 40×40 button with a caption under it (`caption`), and the active item uses `--color-rail-active`.
- **Sidebar (240px)**:
  - **Workspace switcher** at the top: avatar initials, name, and plan badge, with a chevron that opens the switcher menu (§4.14).
  - **Primary group**: `+ Create`, `Recent conversations`, `Recent documents`.
  - **Secondary group**: `Search ⌘K`, `Templates`, `Memory`, `Skills`, `Connectors`, and `Admin` (platform admins only).
  - **At the bottom**: `Trash`.
  - The active item uses `--color-nav-active-bg` and `--color-nav-active-ink`. Items are 36px high with 12px horizontal padding and a 16px icon.
- **Top bar (56px)**, sticky, transparent over the canvas color:
  - **Start side**: the page title, or nothing on Create.
  - **End side**:
    - **Credit pill** (`400 ✦`). Clicking it opens Billing.
    - **`+ New blank`**: a secondary button that creates a blank document and opens the editor.
    - **Avatar menu.**
  - **Upgrade banner pill**: on the Free plan, Create shows a centered pill "✦ Upgrade for more AI" (screenshot 1) that links to Billing. It can be dismissed per session.

### 3.2 Mobile shell (`sm`)

- The rail and sidebar are replaced by a **bottom tab bar** (Create, Documents, Conversations, Templates, More), 56px high, with labels.
- "More" opens a full-height drawer holding the rest of the sidebar items.
- The top bar shows the page title, the credit pill, and the avatar.

### 3.3 RTL mirroring

- `<html dir="rtl" lang="ar">` mirrors everything through logical CSS. The rail moves to the **right** edge, and the sidebar sits beside it (screenshot 1).
- These do **not** mirror: slide content (each block is `dir="auto"`), charts' numeric axes (values grow upward; categories follow the document direction), media controls, and code or URLs.
- Numbers follow the user's digits setting: `latn` (default) or `arab` (٠١٢).

### 3.4 Editor shell (focused; no rail or sidebar)

See §5.4.

---

## 4. Component inventory

**P** = port from MAF (adapt tokens only). **E** = port and extend. **N** = new.

| # | Component | Src | Anatomy / variants | States |
|---|---|---|---|---|
| 4.1 | `Button` | N | Variants `primary` (violet fill), `secondary` (white with line border), `ghost`, `danger`. Sizes `sm` 32, `md` 36, `lg` 44. Optional leading icon. | hover, active, focus-visible (2px `--color-primary-200` ring), disabled, loading (spinner replaces the icon, label stays) |
| 4.2 | `IconButton` | N | Square, sizes 32/36/40, required `aria-label` (i18n) | same as Button |
| 4.3 | `Pill` / `Chip` | N | Height 32, `--radius-pill`, 1px line border, icon + label. Used for the format chips on Create. A selected chip gets the violet tint background and a violet border. | hover, selected, disabled |
| 4.4 | `PillTabs` | N | A segmented row of pills. The selected tab gets the nav-active colors (Conversations "Active/Archived", Patterns "Coordinated/Custom"). | |
| 4.5 | `TextInput` / `SearchInput` | N | Height 36, leading search icon, clear button | focus ring, error (red border + message under), disabled |
| 4.6 | `Select` / `Dropdown` | N | Button that opens a menu (§4.13). Used by the sort control and the style picker. | |
| 4.7 | `Checkbox`, `Radio` | N | 16px, with a label and an optional count at the end (the Templates filter) | |
| 4.8 | `ColorSwatch` | N | 24px circle. Selected state gets a 2px ring. "Multi" is a conic gradient (screenshot 3). | |
| 4.9 | `Card` | N | Surface, `--radius-md`, line border. Hover raises it to `--shadow-sm`. | |
| 4.10 | `TemplateCard` | N | A 16:10 thumbnail (rendered with `<Slide scale>` from FP/slides, never an image file). Below it: the name and a format icon at the end (screenshot 3). | hover (ring + "Use" button overlay), focus |
| 4.11 | `DocumentCard` | N | Thumbnail (16:9), title (1 line), "Edited 2h ago", format icon, ⋯ menu (Open, Duplicate, Rename, Move to trash) | hover, menu open |
| 4.12 | `Dialog` | N | Centered, max width 560, `--radius-lg`, title, body, footer with buttons at the end. Esc and the backdrop close it, unless the dialog is destructive. | |
| 4.13 | `Menu` / `Popover` | N | Elevated surface, 8px padding, 32px items, keyboard navigation | |
| 4.14 | `WorkspaceSwitcher` | N | Menu that lists workspaces (avatar, name, role), then "Create team workspace", then "Workspace settings" | |
| 4.15 | `Sheet` / `Drawer` | N | Slides in from the end side (the left in RTL). Width 400 on desktop, full screen on `sm`. | |
| 4.16 | `Toast` | N | Bottom-center, auto-hides after 4 s, optional action ("Undo") | success, error, info |
| 4.17 | `Tooltip` | N | 500 ms delay, `small` text, on every icon button | |
| 4.18 | `Badge` | N | Plan (`Free`, `Pro`, `Team`) and status (`Connected`, `Needs sign-in`) | |
| 4.19 | `CreditPill` | N | `400 ✦`. Turns warning color below 10%, error color at 0. | |
| 4.20 | `EmptyState` | N | Illustration (original SVG, §9), title (`h2`), subtitle, optional primary action | |
| 4.21 | `Skeleton` | N | Shimmer blocks matching the final layout. Never use a page spinner. | |
| 4.22 | `Banner` | N | Full width inside its container. Variants info, warning, error. Icon, text, optional action. | |
| 4.23 | `Composer` | E (MAF `Composer.tsx`) | See §6.2 | |
| 4.24 | `BlockView` | P (MAF `Blocks.tsx`) | Renders thread blocks. See §6.3. | |
| 4.25 | `ChoicePrompt`, `ChoiceForm` | P | `ask_user` UI. See §6.4. | |
| 4.26 | `ApprovalCard` | E (MAF `ApprovalDiffCard.tsx`) | Slide before/after variant. See §6.5. | |
| 4.27 | `ModelEffortPicker` | E | Shows only Fast, Standard, and Deep, with no model ids. It is the "Standard ▾" control in the screenshot composer. | |
| 4.28 | `LanguageToggle` | P | EN / ع | |
| 4.29 | `Markdown` | P | Used inside assistant text | |
| 4.30 | `Kbd` | N | Shortcut hints (⌘K, Esc) | |

---

## 5. Screens

Every screen lists: **route**, **wireframe**, **regions**, **data**, **states**, **interactions**, **test ids**. All routes are lazy loaded. The title format is `"<Page> · Docu Builder"`.

### 5.1 Auth (`/login`, `/register`, `/verify`, `/forgot`, `/reset`)

```
┌──────────────────────────────── canvas ─────────────────────────────────┐
│                         [logo]                     [EN | ع]             │
│                ┌───────────────────────────────┐                        │
│                │ h1  Sign in                   │                        │
│                │ [Continue with Google]        │                        │
│                │ ───────── or ─────────        │                        │
│                │ Email      [______________]   │                        │
│                │ Password   [__________ 👁]    │                        │
│                │ (TOTP code — only if required)│                        │
│                │ [        Sign in        ]     │                        │
│                │ Forgot password? · Create account                      │
│                └───────────────────────────────┘                        │
└─────────────────────────────────────────────────────────────────────────┘
```

- Port MAF `AuthLayout`, `LoginPage`, `RegisterPage`, and `PasswordField`.
- The card is 400px wide, `--radius-lg`, with `--shadow-sm`.
- **Errors** are shown inline under the field (`invalid_credentials` shows under the password field). A rate limit shows a banner at the top of the card.
- **Register** has name, email, password (strength hint: at least 10 characters), and language. On success it shows a "Check your email" state with Resend (60 s cooldown).
- **Test ids**: `auth-email`, `auth-password`, `auth-submit`, `auth-google`, `auth-totp`.

### 5.2 Create (`/`), matching screenshot 1 and screenshot 5

```
┌ shell ─────────────────────────────────────────────────────────────────────────────┐
│ top bar:                 (✦ Upgrade for more AI)            [400 ✦] [+ New blank] │
│                                                                                     │
│                              [ original illustration 120×90 ]                       │
│                     display: What do you want to create together?                   │
│        ┌──────────────────────────────────────────────────────────────────┐        │
│        │ [template card: ▣ thumb | name · "Template" ✕]   (only if attached)│        │
│        │ Placeholder: "Turn your latest meeting notes into a short deck…"   │        │
│        │                                                                    │        │
│        │ [+]  [⚙ sliders]                  [Standard ▾] [🎤] [ (↑) send ]   │        │
│        └──────────────────────────────────────────────────────────────────┘        │
│   (Presentation) (Document) (Webpage) (Social) (Import) (✦ Polish existing)         │
│                                                                                     │
│                              caption: Suggested templates                           │
│        [thumb][thumb][thumb][thumb][thumb][thumb]     (6 × 180px, names under)      │
│                              ( View all templates )                                 │
│                                                                                     │
│   ─────────────────────────────────────────────────────────────────────────────    │
│   PillTabs: [Recent documents] [Recent conversations]                               │
│   grid of DocumentCard (4 per row) / conversation rows                              │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

**Composer** (max width 720, `--radius-lg`, focus ring `--color-primary-200`):
- **Textarea**: auto-grows from 2 to 10 lines. Enter sends and Shift+Enter adds a newline. The placeholder rotates through 3 examples per format (i18n).
- **`+`** opens a menu: Upload file, Choose template, Import PPTX/DOCX.
- **`⚙`** opens a popover with the web search toggle and a skill picker (also triggered by typing `/` at the start).
- **`Standard ▾`** is the effort picker (§4.27).
- **🎤** dictation is **hidden at GA** (it's after GA). Keep the slot so the layout matches.
- **Send** is a 36px round button, `--color-secondary-200` when there is no text and `--color-primary` when there is.

**Format chips**: exactly one is selected (Presentation by default). The selection sets `format` and the profile.
- **Import** opens a file picker for `.pptx`/`.docx` and goes straight to the import flow (US6).
- **Polish existing** opens the document picker, then a thread on that document with the `assistant` profile.

**Attached template**: a card inside the composer with the thumbnail, name, and "Template" label with an icon (screenshot 5). The ✕ removes it.

**Suggested templates**: 6 cards that match the locale and the selected format. Clicking one attaches it, and if the composer has text, sends right away.

**Bottom tabs**: Recent documents (8) and Recent conversations (8 rows: title, format icon, time).

**States**:
- No documents: the tab shows "Your documents will appear here".
- Out of credits: Send is disabled, and a warning Banner above the composer says "You're out of credits" with an `Upgrade` link.
- Unverified email: Send is disabled, with the banner "Verify your email to start" and `Resend`.

**Test ids**: `create-composer`, `composer-input`, `composer-send`, `composer-plus`, `composer-settings`, `effort-picker`, `format-chip-presentation` …, `suggested-template-<id>`, `create-tab-documents`.

### 5.3 Documents (`/documents`)

- **Header**: `h1 Documents`, a SearchInput (300px), a format Select, and a sort Select (Last edited, Created, Title).
- **Grid**: DocumentCard, 4 columns on `xl`, 3 on `lg`, 2 on `md`, 1 on `sm`, paged infinitely with the cursor.
- **Empty state**: illustration, "No documents yet", and a `Create` button.
- **Test ids**: `documents-search`, `document-card-<id>`.

### 5.4 Editor (`/doc/:id`)

This is the most important screen.

```
┌ top bar (56) ──────────────────────────────────────────────────────────────────────────────────┐
│ [← back] [title (inline editable)] · Saved ✓        [⟲ history] [🎨 Patterns] [▶ Present] [Share] [⇩ Export] [avatar] │
├──────────┬──────────────────────────────────────────────────────────────┬─────────────────────┤
│Filmstrip │                         Canvas                               │  Agent column (400) │
│ (148)    │   ┌──────────────────────────────────────────────────────┐   │ ┌─────────────────┐ │
│ ┌─1───┐  │   │                                                      │   │ │ thread (scroll) │ │
│ │thumb│◀ │   │              active slide (16:9, max 1100w)          │   │ │  user bubble    │ │
│ └─────┘  │   │                                                      │   │ │  agent text     │ │
│ ┌─2───┐  │   │                                                      │   │ │  ▸ Thinking     │ │
│ │thumb│  │   └──────────────────────────────────────────────────────┘   │ │  ▣ tool block   │ │
│ └─────┘  │   hint: Select a card or element to edit  [Esc]              │ │  [slide preview]│ │
│ ┌─3───┐  │   ┌──────────────────────────────────────────────────────┐   │ │  ask/approval   │ │
│ │thumb│  │   │      next slide (peeks 120px, 60% opacity)          │   │ └─────────────────┘ │
│ └─────┘  │                                                              │ [status line]       │
│ [+ slide]│                                                              │ ┌ composer (small)┐ │
│          │                                                              │ └─────────────────┘ │
└──────────┴──────────────────────────────────────────────────────────────┴─────────────────────┘
```

#### Top bar

- **Back** goes to Documents.
- **Title** can be edited inline: click to edit, Enter or blur saves, Esc cancels. It is limited to 140 characters.
- **Save status**: `Saving…` / `Saved ✓` / `Offline – retrying` / `Conflict` (red, with Reload).
- **History** opens the Version history drawer (§5.4.7).
- **Patterns** opens the theme panel (§5.4.6).
- **Present** enters present mode (§5.4.8).
- **Share** opens the dialog (§5.10).
- **Export** opens a menu (§5.4.9).
- Viewers see no Patterns, no composer, and a "View only" badge.

#### 5.4.1 Canvas

- Logical slide size is **1280×720**, scaled with a CSS transform to fit the canvas width (max 1100px), centered, with `--radius-lg` and `--shadow-md`.
- The column scrolls vertically and shows every slide stacked with 32px gaps. The **active slide** is the one whose center is nearest the viewport center. The filmstrip follows the scroll, and clicking a filmstrip item scrolls smoothly to that slide.
- The next slide peeks below the active one (the natural stacking gives this).
- **Selection**: hovering a text block shows a 1px dashed `--color-primary-200` outline. Clicking selects it (2px solid outline) and focuses a `contenteditable` with plain text only. Pasting strips formatting.
  - Points: Enter adds a point and Backspace on an empty point removes it.
  - Esc deselects. Clicking outside deselects and saves.
- **The hint** "Select a card or element to edit" with an `Esc` key cap shows under the active slide when nothing is selected (localized).
- **While a turn runs**, editing is disabled (§5.4.5). Slides changed by the latest `doc_patch` get a 1.2 s violet glow (`box-shadow` animation, none under reduced motion).
- **Empty document** (New blank): one `title` slide with placeholder text "Untitled", and the agent column shows the composer focused with the hint "Describe what to create".

#### 5.4.2 Filmstrip (148px)

- **Items**: a number (`caption`, at the start), a thumbnail (128×72, `<Slide scale>`), and a 2px active border in `--color-primary`.
- **Drag** to reorder: the drop indicator is a 2px violet line. This sends a `move_slide` op.
- **Context menu** (right-click or ⋯ on hover): Duplicate, Delete (confirm when the slide has edits), Move up, Move down.
- **`+ slide`** at the bottom opens a layout picker popover with 7 layouts, each a mini thumbnail and a name.
- **During a turn**: the slide currently being written pulses its number badge. New slides fade in.

#### 5.4.3 Agent column (400px; 360px between `lg` and `xl`)

- **Header**: the thread title (truncated), a ⋯ menu (Rename thread, Archive, Copy link to doc), and the context indicator from the ported `contextEstimate`. The indicator shows only when the thread is above 70% of context.
- **The thread**: §6.
- **The composer** is the small variant: no format chips, but the same `+`, `⚙`, effort, and send/stop.

#### 5.4.4 Status line

This is one line above the composer, shown only while a turn is active:

| Situation | Text |
|---|---|
| `status` events | the event's message (e.g. "Compacting context…") |
| a tool is running | "Writing slide 3 of 6…" or "Reading report.pdf…" |
| `waiting_input` | "Waiting for your answer" |

#### 5.4.5 Banners (above the canvas, full canvas width)

| When | Variant | Text | Action |
|---|---|---|---|
| Turn running | info | "The agent is editing this document" | `Stop` |
| `waiting_input` | info | "The agent needs your answer" | `Go to question` (scrolls the thread) |
| Save conflict (409) | error | "This document changed somewhere else" | `Reload` |
| Viewer role | info | "You can view and present this document" | none |
| Offline | warning | "You're offline – changes will sync" | none |

#### 5.4.6 Patterns panel (screenshot 4)

- It opens **over the agent column**, at the same width with a slide-in. It has a ✕ close button and a header "Themes" with the subtitle "Choose a theme and background colors".
- **PillTabs**: `Coordinated` (system themes) and `Custom` (after GA: a disabled "Coming soon" tab).
- **Filter chips**: All, Light, Dark, then the color tags Red, Orange, Yellow, Green, Blue, Purple, Pink, Neutral, matching the theme `tags`.
- **Grid**: 3 columns of theme tiles, each a mini slide showing the theme's paper, ink lines, and an accent bar (as in the screenshot). The current theme has a violet ring.
- **Hover** previews the theme on the canvas, and leaving the tile restores it. **Clicking** applies it: one PATCH (`set_theme`) and the toast "Theme applied" with `Undo`.
- **Continue** at the bottom closes the panel.

#### 5.4.7 Version history drawer (end side, 400px)

- A list grouped by day. Each row shows time, source icon (agent ✦, manual ✎, theme 🎨, restore ⟲), author, and slide count.
- **Clicking a row** previews it: the canvas switches to read-only showing that revision, with the banner "Viewing version from 14:32" and `[Restore] [Back to current]`.
- **Restore** opens a confirm dialog, then creates a new revision.

#### 5.4.8 Present mode

- Fullscreen (Fullscreen API) on a black backdrop, with slides scaled to fit.
- **Keys**: ←/→ (mirrored in RTL), Space, PageUp/PageDown, Home/End, Esc to exit, F to toggle fullscreen.
- After 2 s idle the cursor hides, and moving it shows a minimal bottom bar: `‹ 3 / 12 ›`, ✕.
- Speaker notes are not shown at GA. The presenter view comes after GA.

#### 5.4.9 Export menu

- Items: PDF, PowerPoint (.pptx), Images (.png, zip).
- Clicking one shows progress inside the menu item, then a download toast with `Download`.
- On the Free plan, each item has a caption "Includes small watermark".

#### Editor test ids

`editor-title`, `save-status`, `btn-history`, `btn-patterns`, `btn-present`, `btn-share`, `btn-export`, `canvas`, `slide-<index>`, `slide-<index>-title`, `filmstrip`, `filmstrip-item-<index>`, `filmstrip-add`, `agent-column`, `banner-<kind>`, `patterns-panel`, `theme-tile-<id>`, `history-drawer`, `present`.

#### Editor on mobile (`sm`)

- The top bar keeps Back, Title, and the ⋯ menu (which holds Patterns, Present, Share, Export, History).
- The canvas is full width, and the filmstrip becomes a slide counter `3 / 12` with prev/next buttons.
- The agent column becomes a **bottom sheet** with three heights: closed (shows only the composer bar), half, and full. A pill handle drags between them.

### 5.5 Conversations (`/conversations`), matching screenshot 2

- **Header**: `h1 Conversations` with an icon, and PillTabs `[Active] [Archived]` (the selected tab uses the nav-active colors).
- **List rows** (port MAF `ConversationList` with `groupConversations` → Today, Yesterday, Previous 7 days, Older). Each row shows:
  - the format icon,
  - the title,
  - the document title (secondary),
  - the time,
  - on hover: an Archive or Restore button, and a Delete button that confirms first.
- Clicking a row opens `/doc/:documentId` with the thread.
- **Empty state** (screenshot 2): a centered original "balloon over clouds" illustration (§9), the title "No conversations yet", and the subtitle "Conversations you start will appear here".

### 5.6 Templates (`/templates`), matching screenshot 3

```
┌ shell ─────────────────────────────────────────────────────────────────────────────────┐
│ h1 Template explorer  · subtitle: Templates designed to help you start fast           │
│ [🔍 Search templates______________]                           [⇅ Created ▾]           │
│ ┌────────────────────────── grid (3–6 cols) ───────────────────┐ ┌ Filters (260) ────┐ │
│ │ [TemplateCard] [TemplateCard] [TemplateCard] ...              │ │ Format            │ │
│ │                                                               │ │ (•) All formats   │ │
│ │                                                               │ │ ( ) Presentation  │ │
│ │                                                               │ │ ( ) Document …    │ │
│ │                                                               │ │ Category ˄        │ │
│ │                                                               │ │ [ ] Lesson   213  │ │
│ │                                                               │ │ … Show 4 more     │ │
│ │                                                               │ │ Color ˄           │ │
│ │                                                               │ │ ●●●●●●●●●  ◐      │ │
│ │                                                               │ │ Language ˄        │ │
│ │                                                               │ │ [ ] Arabic   418  │ │
│ └───────────────────────────────────────────────────────────────┘ └───────────────────┘ │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

- **Filter sections**: Format (radio), Category (checkboxes with counts; 5 shown, then "Show N more"), Color (swatches, multi-select), Language (checkboxes with counts). Each section collapses with ˄/˅.
- **Facet counts** update as filters change. Filters are kept in the URL query (`?format=presentation&color=green`).
- **Sidebar group** (inside the app sidebar, while on this page): Workspace templates, Recent, Created by you, Template explorer (screenshot 3's left panel).
- **Clicking a card** opens a **preview dialog**: a large slide carousel of the template cards, the name, category, and `[Use template]` button. Use template follows the spec US3 scenario 2.
- **Empty state**: "No templates match these filters" with `Clear filters`.
- **On mobile**, the filters move into a `Filters` button that opens a sheet.

### 5.7 Memory (`/memory`), porting MAF `MemoryPage`

- `h1 Memory` with the subtitle "What the agent remembers about you", and the counter `12 / 50`.
- **List**: each item shows its text, its source chip (`Saved by agent` / `Added by you`), and the date, plus Edit (inline) and Delete actions. `+ Add` opens an inline input.
- **Brand section** (visible to workspace admins; read-only for others): "Brand rules for <workspace>", a list of up to 30 items, and Edit.
- **Empty state**: "Nothing remembered yet. Tell the agent your preferences, like tone or brand colors."

### 5.8 Skills (`/skills`), porting MAF `SkillsPage`

- **Tabs**: `Built-in` and `Workspace` (Team plan; other plans see an upgrade empty state).
- **Rows** show the name (mono, e.g. `/deck-writing`), the description (2 lines), the profiles it is enabled for (chips), and the source badge.
- **Workspace skill editor**, opened from `+ New skill`: Name, Description, Body (Markdown editor with preview), and a `Generate from description` button, which fills the body as a draft labeled "Draft – review before saving".

### 5.9 Connectors (`/connectors`), porting MAF `ConnectorsPage`, `McpServerDialog`, `McpConnectorDetails`

- **Cards** per connector show the name, URL host, status badge, and tool group count, plus `Reconnect`, `Details`, and `Remove` actions.
- **The Add dialog** asks for Name, URL, and Auth (OAuth / Token / None). OAuth opens a popup (ported `mcpOAuth.ts`).
- Non-admins see the list read-only.

### 5.10 Share dialog (from the editor)

```
┌ Share "Water cycle" ────────────────────────────── ✕ ┐
│ Invite people  [email@…        ] [Can view ▾] [Invite]│
│ People with access                                   │
│  (A) Ahmed (you)                         Owner       │
│  (S) sara@…                      [Can edit ▾] [✕]    │
│ General access                                       │
│  [🔒 Private ▾]  Only people invited                  │
│  options: Private · Workspace · Anyone with the link  │
│ ─────────────────────────────────────────────────── │
│ [🔗 Copy link]                 [Reset link]  [Done]  │
└──────────────────────────────────────────────────────┘
```

- **Reset link** asks for confirmation ("The old link will stop working").
- **Copy link** shows the toast "Link copied".

### 5.11 Share viewer (`/s/:token`)

- Minimal chrome: the document title at the start and `[▶ Present]` at the end. Slides are stacked full width (max 1100px). On Free, a small badge "Made with Docu Builder" sits at the bottom-end.
- A revoked or invalid link shows the full page "This link is no longer available".
- This page must **not** import the editor bundle. It uses a separate entry chunk (budget 120 KB).

### 5.12 Settings (`/settings/*`), porting and extending MAF `SettingsPage`

- **Layout**: a left tab list (Profile, Security, Members, Billing, Data) and the content on the right, max width 720.
- **Profile**: name, avatar, language (EN/ع), digits (123 / ١٢٣), theme (System/Light/Dark).
- **Security**:
  - Change password.
  - Two-factor: enable flow with a QR code, a code input, and recovery codes to download.
  - Sessions: a table of device, IP, and last seen, each row with `Sign out`, plus `Sign out of all other sessions`.
- **Members** (team workspaces):
  - An invite form.
  - A table of members (name, email, role select, remove).
  - Pending invites (resend, revoke).
  - Brand memory link.
- **Billing**:
  - A plan card (the current plan, price, renewal date, and `Manage` / `Upgrade`).
  - A credits meter with the balance and the monthly allowance.
  - A usage chart (30 days, bars per day; use the dataviz rules: one series, the violet accent).
  - A ledger table.
- **Data**: `Export my data` (shows status, then emails the link) and a `Delete account` danger zone that requires typing the email to confirm.

### 5.13 Admin (`/admin/*`, platform admins only), porting and extending MAF `AdminPage`

| Tab | Content |
|---|---|
| Users | Search and table: email, name, created, last seen, active toggle, platform-admin toggle |
| Model | A form for upstream URL, API key (write-only: "•••• set"), model, vision model, small model, fallback, context window, max completion tokens, thinking toggle, and effort cap per plan. `Check connection` runs the probe and shows ✓/✗ for "plain reply", "tool calls", and "streamed tool calls". |
| Prompts | Prompt names on the start side. A version list plus an editor (monospace) with **diff against the active version**. `Save as new version` takes a note. Activate or Roll back. |
| Profiles | For each profile: a skills checklist, a tools checklist, a connectors checklist, and the effort cap |
| Flags | Key/value toggles with descriptions |
| Usage | Date range and group-by. KPI tiles (turns, tokens, cost, p95 latency, failure %), a line chart over time, and a breakdown table. |

### 5.14 Trash (`/trash`), Invite accept (`/invite/:token`), Not found

- **Trash** is a document grid with `Restore` and `Delete forever` (confirm). Items are kept 30 days, and a banner says so.
- **Invite accept** shows a card: "<Inviter> invited you to <Workspace> as <role>" with `[Accept]`. If you're not logged in, it goes to login and comes back. An expired invite shows an expired state.
- **Not found** is an EmptyState with `Go home`.

---

## 6. Agent thread UI (editor column)

### 6.1 Message layout

- **User message**: a bubble at the end side, `--color-primary-25` background, `--radius-md`, max 85% width. Attachments show as chips under the text. Hover actions: `Edit` (rewind; turns the bubble into a textarea with `Cancel` / `Send`).
- **Assistant message**: no bubble, full width. It contains, in order: the blocks (§6.3), the text (Markdown), and the slide previews row. Hover actions: 👍 👎, `Undo this turn` (only on the latest committed turn, and only when no newer revision exists).
- A gap of 16px between messages. Day separators are `caption`, centered.

### 6.2 Composer states

| State | Input | Send/Stop button | Other |
|---|---|---|---|
| idle, empty | enabled | Send (grey, disabled) | |
| idle, has text | enabled | Send (violet) | |
| running | enabled (draft text kept) | **Stop** (square icon, `--color-ink`) | status line visible |
| waiting_input | disabled, placeholder "Answer the question above" | hidden | |
| out of credits | disabled | hidden | Banner with Upgrade |
| viewer | not rendered | — | |

### 6.3 Event → UI mapping (`BlockView`)

| Event(s) | Component | Behavior |
|---|---|---|
| `text_delta` | Markdown text | Streams in, with a caret at the end while running |
| `reasoning_delta` | "Thinking" disclosure | Collapsed by default with the label "Thought for 4s". Expanding shows `--color-ink-3` text. |
| `tool_call_delta` → `tool_call` → `tool_result` | Tool block | A one-line row: an icon per tool and a **human label** (§6.6). It shows a spinner while running, ✓ when done, ⚠ on `ok:false` (error text on expand). Finished blocks in a finished turn collapse into "6 steps ▸". |
| `doc_patch` | none in the thread (the canvas updates) | The slide previews row gets the changed slides at the end of the turn |
| `ask_user` | ChoicePrompt / ChoiceForm | §6.4 |
| `tool_approval` | ApprovalCard | §6.5 |
| `memory_saved` | Chip `🧠 Remembered: "formal Arabic"` | It links to Memory |
| `skill_loaded` | Chip `✦ Using skill: deck-writing` | |
| `step_limit` | Note row | "Reached the step limit for this effort – summarizing." |
| `status` | Status line (§5.4.4) | Not stored |
| `turn_failed` | Error block | The message from `TurnErrorCode` (i18n), plus `Retry` when retryable |
| `turn_cancelled` | Muted row | "Stopped" or "Expired – no answer in 30 min" |

### 6.4 `ask_user` card (port of ChoicePrompt / ChoiceForm)

- The question in `body-strong`.
- **Options**: up to 6 show as pills. With more than 6, a searchable dropdown appears (MAF behavior). With `allowFreeText`, an "Other…" input shows.
- **Fields form**: one row per field. Labels are on the start side and inputs on the end side, with a `Submit` button.
- After answering, the card collapses to "You chose: Grade 5 · 8 slides".

### 6.5 Approval card (extends ApprovalDiffCard)

| `approvalCard.kind` | Body |
|---|---|
| `replace_slides` | Two columns, **Before** and **After**, of mini slide titles with numbers, plus the warning "Your manual edits on 3 slides will be replaced". |
| `delete_slides` | A list of slide thumbnails with titles |
| `generate_image` | The prompt text, the target slide thumbnail, and "Uses 20 credits" |
| `mcp_write` | The connector name, tool, and arguments preview (monospace, 6 lines max) |

- **Buttons**: `[Allow]` (primary), `[Deny]` (secondary), and the checkbox "Always allow in this thread".
- After deciding, the card collapses to "Allowed" or "Denied".

### 6.6 Tool labels (i18n keys `tool.<name>.running` / `.done`)

| Tool | Running | Done |
|---|---|---|
| `replace_slides` | Writing {count} slides… | Wrote {count} slides |
| `add_slide` | Adding a slide… | Added slide {index} |
| `update_slide` | Editing slide {index}… | Edited slide {index} |
| `delete_slide` | Removing slide {index}… | Removed slide {index} |
| `move_slide` | Reordering… | Moved slide {index} |
| `set_theme` | Choosing a theme… | Theme: {name} |
| `set_title` | Naming the document… | Titled "{title}" |
| `read_attachment` | Reading {file}… | Read {file} |
| `search_attachments` | Searching your files… | Found {n} passages |
| `web_search` | Searching the web… | {n} results |
| `fetch_url` | Reading {host}… | Read {host} |
| `read_skill` | Loading skill… | (chip instead) |
| `remember` | Saving to memory… | (chip instead) |
| `generate_image` | Creating image… | Image added to slide {index} |
| `list_mcp_tools` / `use_mcp_tools` / `mcp_*` | Using {connector}… | Used {connector} |

---

## 7. Slide canvas visual spec (FP/slides)

- **Coordinates**: 1280×720 logical units. All positions below are percentages of that box. Padding is 6% horizontal and 8% vertical, called the "safe area".
- **Theme tokens**: `bg`, `paper`, `ink`, `accent`, `tone`, `font` (`sans` = IBM Plex Sans Arabic/Inter, `serif` = Noto Naskh Arabic/Fraunces).
- **Type scale** (logical px): kicker 22 (uppercase in Latin script only, accent color), title 64 (hero and title layouts) or 48 (others), body 26, points 28, caption 18.
- **Text fitting**: if a title overflows its box, step the size down 10% at a time to a minimum of 70%. After that, clip with an ellipsis and show a ⚠ in the filmstrip.

| Layout | Composition |
|---|---|
| `hero` | The field (color/gradient/image) fills the slide. A paper panel sits at the bottom-end, 46% wide, 48% tall, radius 24, 5% inset, holding the kicker, title, body, and button (accent fill, ink-contrast text). This matches the screenshot composition. |
| `title` | Paper background. Kicker, title, and body are centered vertically, aligned to the start, 70% wide. A 6px accent bar sits above the kicker. |
| `points` | Title at the top (48). Up to 6 points in one column, or 2 columns when there are more than 4. Bullets are accent dots. |
| `quote` | Large quote mark (accent, 160) at the start. The quote is 44 italic for serif themes and 40 for sans. Attribution is a caption at the end. |
| `split` | The field or image fills 50% on the end side (the left in RTL). The text side holds the kicker, title, body, and an optional button. |
| `table` | Title on top. The table fills the rest, with an accent header row, 1px `ink` 12% lines, numbers aligned to the end, and at most 8×12 cells. |
| `chart` | Title on top. SVG chart at 85% width. Series colors come from the theme accent and then fixed tints. Legend on top when there are 2 or more series. Labels in the chart's language. Values carry `unit`. |

The filmstrip and template thumbnails render the same component with `scale` (no separate thumbnail art).

---

## 8. Motion and feedback

| Event | Feedback |
|---|---|
| Slide changed by the agent | 1.2 s violet glow on the slide and its filmstrip item |
| Slide added | Filmstrip item expands from 0 to its full height in 200 ms. Canvas fades in. |
| Save | "Saving…" → "Saved ✓" (fades after 2 s) |
| Theme applied | Canvas cross-fades over 200 ms |
| Turn finished in a background tab | Browser notification (ported `notify.ts`), and the tab title gets the prefix `✓` |

With `prefers-reduced-motion`, drop every scale and translate animation and keep opacity changes only.

---

## 9. Illustrations and brand assets (original only)

| Asset | Where | Brief |
|---|---|---|
| Logo mark + wordmark | Rail, auth, share badge | Original. **No** resemblance to the reference product's "G" mark. Deliver as SVG with light and dark versions. |
| Create illustration (120×90) | Create | An original painted-style scene (e.g. a paper boat on layered waves). Deliver as SVG or a 2× WebP under 40 KB. |
| Empty conversations | Conversations | An original "paper plane over clouds", a different motif from the reference balloon |
| Empty documents, Empty templates filter, Not found, Link unavailable | respective screens | One consistent flat style, 160×120 |

Until the final art arrives, use simple placeholder SVGs from `FE/assets/illustrations/placeholder-*.svg`, keeping the same sizes.

---

## 10. Accessibility (WCAG 2.2 AA)

- **Focus**: every interactive element shows `focus-visible` with a 2px `--color-primary-200` ring and a 2px offset. Focus order follows the visual order in both directions.
- **Canvas**:
  - Each slide is a `region` with `aria-label="Slide 3 of 12: <title>"`.
  - Editable blocks are `textbox` elements while selected.
  - Keyboard: Tab moves between blocks in the active slide, Enter edits, Esc exits, and Alt+↑/↓ moves to the previous or next slide.
- **Filmstrip**: a `listbox` with `option` items. ↑/↓ move between items, and Space picks one up to reorder it (announced through an aria-live message).
- **Thread**: an `aria-live="polite"` region announces only the start and end of a turn ("Agent finished: wrote 6 slides"), never each token.
- **Dialogs**: focus trap, labelled by the title, and focus returns to the trigger on close.
- **Contrast**: every token pair in §2 is checked with a unit test (T020 covers slide themes; T042 adds the UI tokens).
- **Touch targets**: at least 40×40 on mobile.

---

## 11. Copy and i18n

- Keys use the form `area.component.key`. One `en.json` and one `ar.json`, with ICU plurals (Arabic needs `zero`, `one`, `two`, `few`, `many`, `other`).
- Tone: short and plain, with second person "you". No exclamation marks except in success toasts.
- Arabic: Modern Standard Arabic, a neutral register, and no transliterated English where an Arabic term exists (*عرض تقديمي*, not *برزنتيشن*). A native reviewer signs off (T219).
- **Never** put user content or model output into an i18n string. Pass it as a parameter.
- Dates use relative time ("2h ago" / "قبل ساعتين") for under 7 days, then a short date, all through `Intl.RelativeTimeFormat` and `Intl.DateTimeFormat` with the user's digits setting.

---

## 12. Out of scope for GA (don't build)

- A notifications center or bell. Invites and usage alerts go by email, and the credit pill changes color.
- Dictation (🎤). Keep only the slot so the layout matches.
- The Custom tab in Patterns, the presenter view with notes, and freeform element dragging.
