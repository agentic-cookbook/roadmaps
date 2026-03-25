---
name: plan-roadmap
version: "10"
description: "Plan a new feature — discuss, then create a Roadmap. Use when starting a new feature or component."
disable-model-invocation: true
---

## Version Check

If `$ARGUMENTS` is `--version`, respond with exactly:

> plan-roadmap v10

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

Drafts are written to `~/.roadmaps/<project>/`. The feature subdirectory is created in Step 5e once the feature name is known.

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

Set the `plan-version` field in the frontmatter to the current version of this skill (`10`).

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
- **Auto** — Claude can implement this step autonomously (code changes, tests, PRs).
- **Manual** — Requires developer action (e.g., provisioning infrastructure, configuring third-party services, app store submissions). During implementation, a GitHub issue is created and assigned to the `github-user` from the frontmatter. The agent skips the step and moves on.

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

### 5c: Present draft and request approval

Print the **complete Roadmap** to the terminal. Not a summary — the full document.

Then ask:

```
Above is the draft Feature Roadmap (<N> implementation steps).

Sections marked _NEEDS INPUT_ need your input.

[x] approved — write to disk
[ ] <describe changes needed>
```

**STOP. Wait for the user's response. Do NOT proceed until they respond.**

### 5d: Revise or write

- If the user requests changes: incorporate them, re-present the document with the same prompt from 5c. Repeat until approved.
- If the user selects **approved**: proceed to write the file.

### 5e: Create the draft directory and write the Roadmap

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

### 5f: Create initial state files

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

### 5g: Verify all files exist and have content

Use the **Read tool** to read the first few lines of the Roadmap. If the file does not exist or is empty, **STOP. Tell the user. Re-attempt the write.**

Read: `~/.roadmaps/<project>/YYYY-MM-DD-<FeatureName>/Roadmap.md`

Use the **Glob tool** to verify state files exist:

Glob: `~/.roadmaps/<project>/YYYY-MM-DD-<FeatureName>/State/*.md`

Expected: two files (Created.md and Planning.md).

### 5h: Create Ready state file and validate draft

Create the Ready state file in the draft directory. Use the **Write tool**:

Write to `~/.roadmaps/<project>/YYYY-MM-DD-<FeatureName>/State/YYYY-MM-DD-Ready.md`:

```
---
event: ready
date: YYYY-MM-DD
---
```

Validate the draft: verify all four files exist (Roadmap.md, Created state, Planning state, Ready state) and none are empty. Placeholders like `{{REPO}}#{{ISSUE_NUMBER}}` are expected and acceptable.

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
  Steps: <N> total (<N-2> implementation + issue creation + PR)
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
