---
name: plan-roadmap
version: "14"
description: "Plan a feature as a structured Roadmap with steps and PRs. Use when planning a feature, converting a plan to a roadmap, organizing work into steps, or saving a plan as a roadmap."
---

## Version Check

If `$ARGUMENTS` is `--version`, respond with exactly:

> plan-roadmap v14

Then stop. Do not continue with the rest of the skill.

---

# Plan Roadmap

Two-phase collaborative planning workflow for new features.

**Phase 1 — Discussion**: Conversational exploration of the feature idea.
**Phase 2 — Planning**: Structured creation of planning artifacts.

Produces exactly **one deliverable** (in Phase 2):

1. A **Feature Roadmap** file (written to `~/.roadmaps/`) — contains the feature definition (goal, scope, acceptance criteria) and the implementation steps

GitHub issues are **not** created during planning — the Roadmap uses `{{REPO}}#{{ISSUE_NUMBER}}` placeholders. Issues are created by `/implement-roadmap`.

When planning is complete, tell the user to run `/implement-roadmap` to begin implementation.

---

## ABSOLUTE RULE: NO IMPLEMENTATION CODE

**This skill produces planning documents. Nothing else.**

Your only permitted outputs are: Markdown files inside `~/.roadmaps/<project>/`. If you are about to write any file outside this directory, STOP. You are off course.

Before starting work, read `${CLAUDE_SKILL_DIR}/references/active-guards.md` for the complete list of hard-stop guardrails.

---

# PHASE 1: DISCUSSION

> **Goal**: Understand what the user wants through natural conversation. No files are created in this phase.

---

## Step 0: Startup Validation

Before doing anything else, validate the environment.

### 0a: Verify git repository

```bash
git rev-parse --is-inside-work-tree
```

If this fails, **STOP**. Tell the user this skill must run inside a git repository.

### 0b: Create drafts directory

Drafts are written to `~/.roadmaps/<project>/`. The feature subdirectory is created in Step 5f once the feature name is known.

```bash
PROJECT=$(basename $(git rev-parse --show-toplevel))
mkdir -p "$HOME/.roadmaps/$PROJECT"
```

### 0c: Verify directory is writable

```bash
PROJECT=$(basename $(git rev-parse --show-toplevel))
touch "$HOME/.roadmaps/$PROJECT/.verify" && rm "$HOME/.roadmaps/$PROJECT/.verify"
```

If this fails, **STOP**. Tell the user the directory is not writable.

### 0d: Planning log

This skill writes a planning log that records every decision, action, command, and user interaction. The log lives inside the roadmap directory for debugging and analysis.

The log file is created in Step 5f when the roadmap directory is created. Until then, accumulate log entries in memory. Once the directory exists:

```bash
PLAN_LOG="$HOME/.roadmaps/$PROJECT/YYYY-MM-DD-<FeatureName>/planning.log"
```

Write the accumulated entries plus the header:
```
[YYYY-MM-DD HH:MM:SS] plan-roadmap v14 started
[YYYY-MM-DD HH:MM:SS] project: $PROJECT
[YYYY-MM-DD HH:MM:SS] repo: $(git rev-parse --show-toplevel)
[YYYY-MM-DD HH:MM:SS] user: $(git config user.name) <$(git config user.email)>
```

**Throughout this skill, log every significant action** (append to `$PLAN_LOG` once it exists):

- `[timestamp] DECISION: <what was decided and why>`
- `[timestamp] ACTION: <what was done>`
- `[timestamp] USER_INPUT: <what the user said>` (summarize)
- `[timestamp] USER_CHOICE: <which option the user picked>`
- `[timestamp] TOOL_CHECK: <tool> — installed: yes/no, authenticated: yes/no`
- `[timestamp] STEP_TYPE: Step N "<name>" — Auto (reason) | Manual (reason)`
- `[timestamp] ERROR: <what went wrong>`

---

## Step 1: Open the Discussion

Ask the user:

```
What feature would you like to plan?
```

**STOP. Wait for the user to describe their idea. Do NOT proceed until they respond.**

---

## Step 2: Explore the Idea

Have a natural conversation with the user about their feature idea. Your goals:

- **Understand the problem** they're trying to solve
- **Clarify scope** — what's in, what's out
- **Identify unknowns** — what needs research, what assumptions are being made
- **Ask clarifying questions** — but don't interrogate. Follow the user's lead.

Keep the conversation going as long as the user has more to share. Do not rush to summarize.

---

## Step 3: Summarize, Propose a Name, and Request Transition

When the user has shared enough context (they've slowed down, said something like "that's about it", or you feel you have a solid understanding), do the following in a **single prompt**:

1. **Summarize** what you've heard — the problem, the proposed solution, key requirements, and any decisions made during discussion.
2. **Propose a feature name** — a PascalCase slug (no spaces) derived from the discussion.
3. **Ask to proceed to Planning**.

```
Here's what I heard:

<summary>

Proposed feature name: <FeatureName>

If this looks right, I'll move to Planning and create:
  - Roadmap.md (feature definition + implementation steps with issue placeholders)

No implementation code will be written. No GitHub issues will be created.
Issues are created later by /implement-roadmap.

[x] yes — move to Planning
[ ] revise name
[ ] keep discussing
```

**STOP. Wait for the user's response.**

- If they say **yes**: proceed to Phase 2.
- If they **revise the name**: update the name and re-ask "Proceed?" (no need to repeat the full summary).
- If they want to **keep discussing**: return to Step 2.

**If you are about to skip this prompt — STOP. You MUST ask. This is not optional.**

---

## Step 3b: Write Discussion Summary

Once the user approves the transition to Planning, **immediately** write the approved summary to memory as a structured file. This captures the user's intent before any planning transformation occurs.

Accumulate this in memory (it will be written to disk in Step 5e when the directory is created):

**File: `discussion-summary.md`**

```markdown
---
feature: <FeatureName>
date: YYYY-MM-DD
---

# Discussion Summary

## Problem
<What problem the user described>

## Proposed Solution
<The solution approach discussed>

## Key Requirements
- <Requirement 1>
- <Requirement 2>
- ...

## Decisions Made
- <Decision 1 and rationale>
- <Decision 2 and rationale>
- ...

## Constraints and Scope
- **In scope**: <what's included>
- **Out of scope**: <what's explicitly excluded>
- **Constraints**: <technical, timeline, or other constraints mentioned>

## User's Exact Words (Key Quotes)
> <Direct quotes from the user that capture intent, priorities, or non-obvious requirements>
> <Include anything the user emphasized or repeated>
```

**Rules for the Discussion Summary:**
- Write it from the user's perspective — this is what THEY said, not your interpretation
- Include direct quotes for anything that could be misinterpreted
- Do not add requirements the user didn't mention
- Do not reframe the user's problem statement
- If the user said "simple" or "just X", capture that — it constrains scope

Log: `[timestamp] ACTION: Discussion summary captured`

---

# PHASE 2: PLANNING

> **Goal**: Transform the discussion into structured planning artifacts. Files are written to `~/.roadmaps/<project>/`.

---

## Step 4: Enter Plan Mode

Activate plan mode with deep thinking enabled. All design work happens in plan mode.

---

## Step 5: Create Roadmap

Draft the Roadmap, present it for approval.

### 5a: Read the template

Read: `${CLAUDE_SKILL_DIR}/references/feature-roadmap-template.md`

### 5b: Draft the document

Set the `plan-version` field in the frontmatter to the current version of this skill (`14`).

Set the `project` field to the git repo name (`basename $(git rev-parse --show-toplevel)`).

Set the `github-user` field to the GitHub username of the user. Get it with:
```bash
gh api user --jq .login
```
This is used to assign GitHub issues for manual steps.

**Feature definition sections** (top of file): Using everything from the Discussion phase, fill in Goal and Purpose, Extended Description, and other definition sections. Leave sections you cannot fill marked with `_NEEDS INPUT_`.

**`description` frontmatter field**: Write a single sentence (~80 chars) summarizing what this feature does, written for someone unfamiliar with the project. This appears on the dashboard overview.

**Verification Strategy**: Fill in the build and test commands for this project.

Break the feature into ordered implementation steps. Each step must be:

- **Small enough for a single PR** (reviewable in one sitting)
- **Independently testable** with clear acceptance criteria
- **Clear about what "done" means**

For each step, fill in: Description, Type (Auto or Manual), Complexity estimate (S/M/L), Dependencies, Acceptance criteria, Testing/verification approach.

**Step types:**
- **Auto** — Claude can implement this step autonomously (code changes, tests, PRs). **Default to Auto** unless the step literally cannot be performed via code or CLI.
- **Manual** — Only for actions that require human-only access: physical device provisioning, app store submissions, signing into web UIs that have no CLI, purchasing licenses. During implementation, a GitHub issue is created and assigned to the `github-user` from the frontmatter.

**Automation readiness check** — Before marking any step as Manual, check if the required tool or service has a CLI:

1. Identify the external tool/service the step depends on (e.g., `gh`, `gcloud`, `aws`, `brew`, `npm`, `firebase`, etc.)
2. Check if it's installed:
   ```bash
   which <tool> 2>/dev/null && echo "INSTALLED" || echo "NOT_INSTALLED"
   ```
3. If installed, check if it's authenticated/working:
   ```bash
   <tool> auth status 2>/dev/null || <tool> whoami 2>/dev/null || echo "UNKNOWN"
   ```
4. Report the result to the user:
   - `INSTALLED + AUTHENTICATED` → mark as **Auto**
   - `INSTALLED + NOT AUTHENTICATED` → ask the user: "Tool X is installed but not authenticated. Want to set it up now, or mark this step as Manual?"
   - `NOT INSTALLED` → ask the user: "Tool X is needed but not installed. Want me to install it (e.g., `brew install X`), or mark this step as Manual?"

The user can always override to Manual if they prefer. Log the decision and reasoning in the planning log.

**Required first and last steps:**

Every Roadmap must include these two bookend steps. Implementation steps go between them.

**Step 1 (always first):**

```markdown
### Step 1: Create Draft PR

- **Type**: Auto
- **Status**: Not Started
- **Complexity**: S
- **Dependencies**: None
- **Acceptance Criteria**:
  - [ ] Feature branch pushed
  - [ ] Draft PR created
```

**Step N (always last):**

```markdown
### Step N: Finalize & Merge PR

- **Type**: Auto
- **Status**: Not Started
- **Complexity**: M
- **Dependencies**: Step N-1
- **Acceptance Criteria**:
  - [ ] Change History populated in roadmap
  - [ ] Roadmap copied to repo as <Name>-Roadmap.md
  - [ ] PR marked as ready
  - [ ] CI passed
  - [ ] Code review passed
  - [ ] PR merged with --merge
  - [ ] Worktree cleaned up
```

**Do NOT include `Implementing`, `Phase`, or `Status` fields in the Roadmap.** Lifecycle state is tracked solely via files in the `State/` directory.

### 5c: Alignment review — compare Roadmap against Discussion Summary

Before presenting the draft to the user, review the Roadmap against the Discussion Summary (from Step 3b) to catch any divergence.

**Check each of these:**

1. **Goal match** — Does the Roadmap's Goal and Purpose section match the Problem and Proposed Solution from the discussion summary? Flag if the goal has been reframed, expanded, or narrowed.
2. **Requirements coverage** — Is every Key Requirement from the discussion summary addressed by at least one implementation step? Flag any missing requirements.
3. **Nothing skipped** — Walk through the discussion summary line by line. Is there anything the user mentioned — a requirement, a constraint, a preference, a specific technical choice — that does not appear anywhere in the Roadmap? Even minor items ("make sure it supports dark mode", "keep it simple") count. Flag anything omitted.
4. **No scope creep** — Are there steps or requirements in the Roadmap that were NOT discussed? Flag anything added that the user didn't ask for.
5. **Constraints honored** — Are the Out of Scope items and Constraints from the discussion summary respected? Flag any violations.
6. **User quotes check** — Re-read the User's Exact Words section. Does the Roadmap honor the intent behind those quotes? Flag if something was "reinterpreted" away from what the user said.

**If ANY check fails — this is a hard stop. No exceptions.**

1. **Do NOT present the draft to the user.**
2. **Do NOT attempt to fix it in place.** The draft is tainted — patching it risks carrying forward the same misunderstanding.
3. **Warn the user** — tell them exactly which checks failed and what was wrong:

```
⚠️ ALIGNMENT FAILURE — Roadmap does not match the discussion.

Violations:
- <check name>: <what was wrong>
- <check name>: <what was wrong>

The Roadmap draft has been discarded. Restarting planning from Step 5b
with the discussion summary as the source of truth.
```

4. **Discard the draft entirely** and return to Step 5b to redraft from scratch, using the discussion summary as the authoritative input.
5. **Re-run this alignment review** on the new draft. If it fails again, warn the user and restart again. After 3 consecutive failures, **STOP** and ask the user for guidance.

Log every failure:
```
[timestamp] ALIGNMENT_FAILURE: <check name> — <what was wrong>
[timestamp] ACTION: Draft discarded, restarting from Step 5b (attempt <N>)
```

If all checks pass: `[timestamp] ALIGNMENT_REVIEW: PASSED — Roadmap aligns with discussion summary`

### 5d: Present draft and request approval

Print the **complete Roadmap** to the terminal. Not a summary — the full document.

If the alignment review found and corrected divergences, mention them briefly:

```
Note: The alignment review caught <N> divergence(s) between the discussion
and the initial draft. These have been corrected:
- <brief description of each fix>
```

Then ask:

```
Above is the draft Feature Roadmap (<N> implementation steps).

Sections marked _NEEDS INPUT_ need your input.

[x] approved — write to disk
[ ] <describe changes needed>
```

**STOP. Wait for the user's response. Do NOT proceed until they respond.**

### 5e: Revise or write

- If the user requests changes: incorporate them, re-present the document with the same prompt from 5d. Repeat until approved.
- If the user selects **approved**: proceed to write the file.

### 5f: Create the draft directory and write the Roadmap

Use today's date (YYYY-MM-DD) for the directory prefix. Write to the **draft directory**, not the repo:

```bash
PROJECT=$(basename $(git rev-parse --show-toplevel))
DRAFT_DIR="$HOME/.roadmaps/$PROJECT/YYYY-MM-DD-<FeatureName>"
mkdir -p "$DRAFT_DIR/State" "$DRAFT_DIR/History"
```

Write the Feature Roadmap to:
```
~/.roadmaps/<project>/YYYY-MM-DD-<FeatureName>/Roadmap.md
```

Write the Discussion Summary (accumulated from Step 3b) to:
```
~/.roadmaps/<project>/YYYY-MM-DD-<FeatureName>/discussion-summary.md
```

### 5g: Create initial state files

After writing the Roadmap, create state marker files to record the lifecycle events. Use the **Write tool** (not Bash) for each file:

Write to `~/.roadmaps/<project>/YYYY-MM-DD-<FeatureName>/State/YYYY-MM-DD-Created.md`:

```
---
event: created
date: YYYY-MM-DD
---
```

Write to `~/.roadmaps/<project>/YYYY-MM-DD-<FeatureName>/State/YYYY-MM-DD-Planning.md`:

```
---
event: planning
date: YYYY-MM-DD
---
```

### 5h: Verify all files exist and have content

Use the **Read tool** to read the first few lines of the Roadmap and Discussion Summary. If either file does not exist or is empty, **STOP. Tell the user. Re-attempt the write.**

Read: `~/.roadmaps/<project>/YYYY-MM-DD-<FeatureName>/Roadmap.md`
Read: `~/.roadmaps/<project>/YYYY-MM-DD-<FeatureName>/discussion-summary.md`

Use the **Glob tool** to verify state files exist:

Glob: `~/.roadmaps/<project>/YYYY-MM-DD-<FeatureName>/State/*.md`

Expected: two files (Created.md and Planning.md).

### 5i: Create Ready state file and validate draft

Create the Ready state file in the draft directory. Use the **Write tool**:

Write to `~/.roadmaps/<project>/YYYY-MM-DD-<FeatureName>/State/YYYY-MM-DD-Ready.md`:

```
---
event: ready
date: YYYY-MM-DD
---
```

Validate the draft: verify all five files exist (Roadmap.md, discussion-summary.md, Created state, Planning state, Ready state) and none are empty. Placeholders like `{{REPO}}#{{ISSUE_NUMBER}}` are expected and acceptable.

Print: **"Draft complete."**

---

## Step 6: Final Verification and Summary

### 6a: Run final verification

Execute all of the following checks. **Every check must pass.**

Use the **Read tool** to verify the Roadmap exists and has content:

Read: `~/.roadmaps/<project>/YYYY-MM-DD-<FeatureName>/Roadmap.md`
— PASS if file exists and is not empty.

Use the **Glob tool** to verify state files:

Glob: `~/.roadmaps/<project>/YYYY-MM-DD-<FeatureName>/State/*-Ready.md`
— PASS if exactly one match.

Glob: `~/.roadmaps/<project>/YYYY-MM-DD-<FeatureName>/State/*.md`
— PASS if at least three files (Created, Planning, Ready).

If **any check fails**, **STOP. Tell the user which check failed. Fix the issue before continuing.**

### 6b: Exit plan mode

Exit plan mode.

### 6c: Present final summary and offer implementation

Print the complete summary, then ask:

```
=== PLANNING COMPLETE: <FeatureName> ===

Roadmap:
  File: ~/.roadmaps/<project>/YYYY-MM-DD-<FeatureName>/Roadmap.md
  Discussion: ~/.roadmaps/<project>/YYYY-MM-DD-<FeatureName>/discussion-summary.md
  Steps: <N> total (<N-2> implementation + issue creation + PR)
  Alignment: Verified (discussion summary matches roadmap)
  State: Ready
  Estimated scope: <S/M/L breakdown>
  Dependencies: <summary>

Note: GitHub issues have NOT been created yet.
      Issue placeholders ({{REPO}}#{{ISSUE_NUMBER}}) will be resolved
      by /implement-roadmap Step 1.

      Roadmap files are in ~/.roadmaps/ and will be moved to the
      repo by /implement-roadmap when implementation is complete.

All artifacts verified.

[x] yes — run /implement-roadmap
[ ] no — I'll run it later
```

**STOP. Wait for the user's response.**

### 6d: Launch implementation (if requested)

If the user says **yes**, invoke the `/implement-roadmap` skill using the Skill tool.

If the user says **no**, end the skill.
