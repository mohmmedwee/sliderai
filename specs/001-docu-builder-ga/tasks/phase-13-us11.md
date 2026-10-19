# Phase 13: US11, skills (task cards)

Before any card, read [IMPLEMENTER.md](../IMPLEMENTER.md). **Story test**: quickstart.md › US11. **License rule**: never copy `MA/skills/{docx,pptx,xlsx,pdf}`.

---

<a id="t196"></a>
### T196 · Skills tests (write first)

**Depends on**: T063 · **Parallel**: yes · **Size**: S

**Read first**: `MA/tests/test_cleverso_skill.py` (the structure only), `MAS/repositories/skills.py` (front matter parsing), `MAS/repositories/user_skills.py` (`_NAME_RE`, limits)

**Files**: create `BT/unit/test_skills.py` and `BT/integration/test_skill_routes.py`

**Cases**:

1. Parse a `SKILL.md` with front matter (`name`, `description`, `license?`). Missing front matter → skipped with a WARNING.
2. `index_line(skill)` → `- deck-writing: <description>` (MA format).
3. The index for profile `social` includes only the skills enabled for `social`, plus workspace skills enabled for it.
4. `read(name)` is cut at `settings.skills.max_chars` with the MA truncation marker.
5. `/deck-writing` in the request → the skill body is injected before the first model call (an `inject_selected_skill` port), and `skill_loaded` is emitted.
6. User skill name validation follows MA's `_NAME_RE` (`^[a-z][a-z0-9-]{0,62}$`). A body over 40k characters → 400.
7. Workspace skills on a non-Team plan → 403 `plan_required`.


**Acceptance**:
- [ ] Every case listed above is its own test function (`test_<short_name>`)
- [ ] The tests run and **fail for the expected reason** (missing module or not implemented) until the implementation task lands
- [ ] No production code is added in this task

---

<a id="t197"></a>
### T197 · Skill catalog (port)

**Depends on**: T196, T027 · **Parallel**: no · **Size**: M

**Read first**: `MAS/repositories/skill_catalog.py`, `MAS/repositories/skills.py`, `MAS/repositories/user_skills.py`

**Files**: create `BE/agent/skills.py`, `BE/db/models/skills.py`, `backend/alembic/versions/0008_skills.py`, and modify `BE/scripts/seed.py` (`sync_builtin_skills`)

**Steps**:

1. Port `_parse_skill_file`, `SkillRepository` (file-based), and `SkillCatalog` (merging). Add the DB-backed workspace skills (the `skills` table per data-model.md, `workspace_id` nullable for built-ins, RLS with `IS NULL OR` like templates).
2. `sync_builtin_skills()` upserts every `backend/skills/*/SKILL.md` as a `workspace_id=NULL` row (keeping `license` from the front matter), and removes rows whose folder is gone.
3. `catalog_for(profile, workspace_id) -> list[SkillMeta]` applies `enabled_profiles` (the admin can change it in T219).
4. `system_prompt.py` fills `skills_index` with `load_prompt("skills_index", index=…)` and handles `profile.inline_skills`.

**Acceptance**:
- [ ] T196 cases 1–4 pass

---

<a id="t198"></a>
### T198 · `read_skill` tool and the forced skill

**Depends on**: T197, T072 · **Parallel**: no · **Size**: S

**Read first**: `MAS/services/tools/read_skill.py`; `MAS/services/agent/replies.py` (`inject_selected_skill`)

**Files**: create `BE/agent/tools/skills.py` and modify `BE/agent/nodes/prepare.py`

**Steps**:

1. The `read_skill` runner returns the body and emits `skill_loaded`. It is an **uncharged** tool (it doesn't count toward steps).
2. Forced skill: when `state.skill` is set and the turn is at step 0, `prepare` appends (once per turn) an AIMessage tool call `read_skill(name)` plus its ToolMessage with the body, before the model call. That's MA's approach: the model sees that the skill was loaded. Emit `skill_loaded`.

**Acceptance**:
- [ ] T196 case 5 passes

---

<a id="t199"></a>
### T199 · Copy reusable skills

**Depends on**: T197 · **Parallel**: yes · **Size**: S

**Read first**: research.md R21 (the list); each source skill's LICENSE

**Files**: create `backend/skills/{replying-bilingually,answering-well,planning-with-intention,writing-deliverables,doc-coauthoring,research,working-with-documents,theme-factory,brand-guidelines}/` and modify `NOTICE`

**Steps**:

1. Copy each folder from `MA/skills/`. **Edit out** any mention of `run_python`, `write_file`, `edit_docx`, Cleverso, or the proprietary `docx`/`pptx` skills. Point to the slide tools instead (e.g. in `working-with-documents`, "use read_attachment and search_attachments").
2. `theme-factory` and `brand-guidelines` keep their Apache LICENSE files. Add the attribution to `NOTICE`.
3. Set `enabled_profiles` in each front matter (an added key): `replying-bilingually` gets every profile, and the rest per R20.

**Acceptance**:
- [ ] `grep -rE "run_python|write_file|edit_docx|cleverso" backend/skills` is empty

---

<a id="t200"></a>
### T200 · New writing skills

**Depends on**: T197 · **Parallel**: yes · **Size**: L (writing)

**Files**: create `backend/skills/{deck-writing,report-writing,pitch-deck,lesson-deck,landing-page-writing,social-post-writing}/SKILL.md`

**Steps**: each skill is 80–200 lines, in English with Arabic examples. Front matter `name`, `description` (1–2 sentences: **when** to use it; this drives selection), and `enabled_profiles`. Body sections:
1. Goal
2. Structure (an ordered list of slides with layouts)
3. Writing rules (length, tone)
4. Arabic notes (formal register, numerals, RTL considerations)
5. One worked example (a short outline)
6. Common mistakes

**Acceptance**:
- [ ] The drafts eval with the skills enabled is not worse than baseline (an eval PR comment)
- [ ] Each description is under 300 characters

---

<a id="t201"></a>
### T201 · Skills routes and skill generation

**Depends on**: T197, T178 · **Parallel**: no · **Size**: M

**Read first**: contracts/rest-api.md › Skills; `MAS/services/skill_generate.py` (`generate_skill_draft`, `_parse_draft`); `MA/prompts/skill_generate_contract.md`

**Files**: create `BE/api/routers/skills.py` and `BE/services/skill_generate.py` (port), and copy `backend/prompts/skill_generate_contract.md`

**Steps**:

1. The rows exactly as in the contract. Creating and editing require admin and the Team plan (`feature(ws,"workspace_skills")`).
2. Port `generate_skill_draft` using the small model. Its creator body comes from `backend/skills/skill-creator/SKILL.md`; port MA's `skill-creator` skill **only if** it has no proprietary license (check it; it has no LICENSE in MA, so it's MA's own). Return the draft without saving it.

**Acceptance**:
- [ ] T196 cases 6–7 pass

---

<a id="t202"></a>
### T202 · Skills page

**Depends on**: T201 · **Parallel**: yes · **Size**: M

**Read first**: ux.md §5.8; `MAF/pages/SkillsPage.tsx`

**Files**: create `FE/pages/Skills.tsx` (ported and extended) and `FE/features/skills/SkillEditor.tsx`

**Steps**:

1. Tabs Built-in and Workspace. On a non-Team plan, Workspace shows an upgrade EmptyState.
2. Rows show the mono `/name`, the 2-line description, profile chips, and a source badge.
3. The editor: name, description, and body (a textarea with a Markdown preview toggle using the ported `Markdown`). "Generate from description" fills a draft with the label "Draft – review before saving". Save and Delete (confirm).


**Acceptance**:
- [ ] Built-in and workspace tabs work
- [ ] Generate fills a draft that isn't saved until Save
- [ ] Non-Team plans see the upgrade state

**Verify**: `pnpm test:e2e -- skills`

---

<a id="t203"></a>
### T203 · `/` skill picker and chip

**Depends on**: T198, T081 · **Parallel**: yes · **Size**: S

**Read first**: ux.md §5.2 (`⚙` popover and `/`), §6.3 (the `skill_loaded` row)

**Files**: create `FE/components/chat/SkillPicker.tsx` and modify the Composer

**Steps**:

1. Typing `/` at position 0 opens a filtered list of skills (`GET /v1/skills`, filtered by the current profile). Enter picks one, and the composer shows a removable `/name` token. The send request includes `skill`.
2. The `⚙` popover also lists skills.
3. Turn the `skills` feature flag on (from T081).
4. The chip "✦ Using skill: {name}" comes from `skill_loaded`.


**Acceptance**:
- [ ] `/` opens the picker only at position 0
- [ ] The `skill` field is sent with the turn
- [ ] The chip appears

**Verify**: `pnpm test:e2e -- skills`

---

<a id="t204"></a>
### T204 · e2e test: skills

**Depends on**: T202, T203 · **Parallel**: yes · **Size**: S

**Files**: create `frontend/apps/web/tests/e2e/skills.spec.ts`

**Cases**:

1. As an admin on a Team test workspace (seeded plan), generate "board-report", edit it, and save it.
2. Type `/board` in the composer, pick it, and send with `#script:echo_skill`. The chip shows, and the reply echoes "SKILL:board-report" (a fake script hook).
3. A Free workspace sees the upgrade state on the Workspace tab.

**Acceptance**:
- [ ] All 3 cases pass

**Verify**: `pnpm test:e2e -- skills`
