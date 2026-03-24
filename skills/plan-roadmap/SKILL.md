---
name: plan-roadmap
version: "5"
description: "Plan a new feature — discuss, then create Feature Definition, Roadmap, and GitHub issues. Use when starting a new feature or component."
disable-model-invocation: true
---

## Version Check

If `$ARGUMENTS` is `--version`, respond with exactly:

> plan-roadmap v5

Then stop. Do not continue with the rest of the skill.

---

# Plan Roadmap

Two-phase collaborative planning workflow for new features.

**Phase 1 — Discussion**: Conversational exploration of the feature idea.
**Phase 2 — Planning**: Structured creation of planning artifacts.

Produces exactly **three deliverables** (all in Phase 2):

1. A **Feature Definition** file (written to disk, committed)
2. A **Feature Roadmap** file (written to disk, committed)
3. **GitHub issues** (one per roadmap step, confirmed via `gh issue view`)

When planning is complete, tell the user to run `/implement-roadmap` to begin implementation.

---

## ABSOLUTE RULE: NO IMPLEMENTATION CODE

**This skill produces planning documents and GitHub issues. Nothing else.**

Your only permitted outputs are: Markdown files inside `Roadmaps/`, GitHub issues via `gh issue create`, `.gitignore` edits, and `git add`/`git commit` for those files. If you are about to write any file outside `Roadmaps/`, STOP. You are off course.

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

### 0b: Verify GitHub CLI

```bash
gh auth status
```

If this fails, **STOP**. Tell the user to run `gh auth login` first.

### 0c: Create directory structure

The per-directory roadmap layout uses `Roadmaps/YYYY-MM-DD-<FeatureName>/` with subdirectories for state and history. The directory cannot be created until the feature name is known (Step 3), so this step only ensures the top-level `Roadmaps/` directory exists.

```bash
mkdir -p Roadmaps
```

### 0d: Verify directory is writable

```bash
touch Roadmaps/.verify && rm Roadmaps/.verify
```

If this fails, **STOP**. Tell the user the directory is not writable.

### 0e: Ensure `Roadmaps/` is tracked by git

Run the following to check if git would ignore the Roadmaps directory:

```bash
git check-ignore -q Roadmaps/test 2>/dev/null && echo "IGNORED" || echo "TRACKED"
```

If the output is `IGNORED`, the `.gitignore` (or a parent `.gitignore`) is excluding `Roadmaps/`. Fix this by appending negation rules to the repo-root `.gitignore`:

Append the negation rules to `.gitignore` (use `printf` to avoid heredoc permission warnings):

```bash
printf '\n!Roadmaps/\n!Roadmaps/**\n' >> .gitignore
```

```bash
git add .gitignore && git commit -m "chore: allow Roadmaps/ in git" && git push
```

After adding the rules, re-run the `git check-ignore` check to confirm the path is now tracked. If it still reports `IGNORED`, **STOP** and tell the user — a higher-level `.gitignore` rule may need manual attention.

If the output is `TRACKED`, no changes are needed.

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
  - Roadmaps/YYYY-MM-DD-<FeatureName>/Definition.md
  - Roadmaps/YYYY-MM-DD-<FeatureName>/Roadmap.md
  - GitHub issues (one per implementation step)

No implementation code will be written. Only planning documents.

Proceed? (yes / revise name / keep discussing)
```

**STOP. Wait for the user's response.**

- If they say **yes**: proceed to Phase 2.
- If they **revise the name**: update the name and re-ask "Proceed?" (no need to repeat the full summary).
- If they want to **keep discussing**: return to Step 2.

**If you are about to skip this prompt — STOP. You MUST ask. This is not optional.**

---

# PHASE 2: PLANNING

> **Goal**: Transform the discussion into structured planning artifacts. Only Markdown files in `Roadmaps/` and GitHub issues are created.

---

## Step 4: Enter Plan Mode

Activate plan mode with deep thinking enabled. All design work happens in plan mode.

---

## Step 5: Create Planning Documents

Draft both the Feature Definition and Roadmap together, present them for a single approval.

### 5a: Read both templates

Read:
- `${CLAUDE_SKILL_DIR}/references/feature-definition-template.md`
- `${CLAUDE_SKILL_DIR}/references/feature-roadmap-template.md`

### 5b: Draft both documents

**Feature Definition**: Using everything from the Discussion phase, fill in as many sections of the template as you can. The discussion content should be captured in the Extended Description and Goal sections. Leave sections you cannot fill marked with `_NEEDS INPUT_`.

**Feature Roadmap**: Break the feature into ordered implementation steps. Each step must be:

- **Small enough for a single PR** (reviewable in one sitting)
- **Independently testable** with clear acceptance criteria
- **Clear about what "done" means**

For each step, fill in: Description, Type (Auto or Manual), Complexity estimate (S/M/L), Dependencies, Acceptance criteria, Testing/verification approach.

**Step types:**
- **Auto** — Claude can implement this step autonomously (code changes, tests, PRs).
- **Manual** — Requires developer action (e.g., provisioning infrastructure, configuring third-party services, UI/UX decisions that need human judgment, app store submissions). The GitHub issue for manual steps will be assigned to the user.

**Do NOT include `Implementing`, `Phase`, or `Status` fields in the Roadmap.** Lifecycle state is tracked solely via files in the `State/` directory.

### 5c: Present both drafts and request approval

Print the **complete Feature Definition** followed by the **complete Feature Roadmap** to the terminal. Not summaries — the full documents.

Then ask:

```
Above are the draft Feature Definition and Feature Roadmap (<N> implementation steps).

Sections marked _NEEDS INPUT_ need your input.

If both look good, say "approved" and I'll write them to disk and commit.
Otherwise, tell me what to change in either document.
```

**STOP. Wait for the user's response. Do NOT proceed until they respond.**

### 5d: Revise or write

- If the user requests changes: incorporate them, re-present both documents with the same prompt from 5c. Repeat until "approved."
- If the user says "approved": proceed to write both files.

### 5e: Create the roadmap directory and write both files

Use today's date (YYYY-MM-DD) for the directory prefix:

```bash
mkdir -p "Roadmaps/YYYY-MM-DD-<FeatureName>/State" "Roadmaps/YYYY-MM-DD-<FeatureName>/History"
```

Write the Feature Definition to:
```
Roadmaps/YYYY-MM-DD-<FeatureName>/Definition.md
```

Write the Feature Roadmap to:
```
Roadmaps/YYYY-MM-DD-<FeatureName>/Roadmap.md
```

### 5f: Create initial state files

After writing both documents, create state marker files to record the lifecycle events:

```bash
printf -- '---\nevent: created\ndate: YYYY-MM-DD\n---\n' > "Roadmaps/YYYY-MM-DD-<FeatureName>/State/YYYY-MM-DD-Created.md"
printf -- '---\nevent: planning\ndate: YYYY-MM-DD\n---\n' > "Roadmaps/YYYY-MM-DD-<FeatureName>/State/YYYY-MM-DD-Planning.md"
```

### 5g: Verify all files exist and have content

```bash
wc -l "Roadmaps/YYYY-MM-DD-<FeatureName>/Definition.md"
head -5 "Roadmaps/YYYY-MM-DD-<FeatureName>/Definition.md"
wc -l "Roadmaps/YYYY-MM-DD-<FeatureName>/Roadmap.md"
head -5 "Roadmaps/YYYY-MM-DD-<FeatureName>/Roadmap.md"
ls "Roadmaps/YYYY-MM-DD-<FeatureName>/State/"
```

If any file does not exist or is empty: **STOP. Tell the user. Re-attempt the write.**

### 5h: Commit and push all files

```bash
git add "Roadmaps/YYYY-MM-DD-<FeatureName>/"
git commit -m "docs: add Feature Definition and Roadmap for <FeatureName>"
git push
```

Verify the commit and push succeeded. If either failed, tell the user.

---

## Step 6: Create GitHub Issues

The user already approved the Roadmap content. Issues are a mechanical translation — create them without prompting.

### 6a: Create issues one at a time

For each step in the Roadmap, create a GitHub issue:

Write the issue body to a temp file, then create the issue using `--body-file` to avoid quoted-newline permission warnings:

```bash
cat > /tmp/gh-issue-body.md <<'EOF'
## Context

Part of the <FeatureName> feature.
Feature Definition: `Roadmaps/YYYY-MM-DD-<FeatureName>/Definition.md`
Roadmap: `Roadmaps/YYYY-MM-DD-<FeatureName>/Roadmap.md`

## Step Details

<Step description from the roadmap>

## Acceptance Criteria

<Acceptance criteria from the roadmap for this step>

## Complexity

<S/M/L>

## Dependencies

<Dependencies from the roadmap>
EOF
```

For **Auto** steps:
```bash
gh issue create --title "Feature: [<FeatureName>] Step <N>: <StepDescription>" --body-file /tmp/gh-issue-body.md
```

For **Manual** steps, assign to the current user:
```bash
gh issue create --title "Feature: [<FeatureName>] Step <N>: <StepDescription> [Manual]" --body-file /tmp/gh-issue-body.md --assignee @me
```

### 6b: Verify each issue was created

After each `gh issue create`, capture the issue number from stdout. Then verify:

```bash
gh issue view <number> --json number,title,state
```

If verification fails for any issue, **STOP. Tell the user which issue failed and retry.**

Collect all issue numbers in a list.

### 6c: Update the Roadmap with issue numbers

For each step in the Roadmap file, replace the `{{REPO}}#{{ISSUE_NUMBER}}` placeholder with the actual issue reference (e.g., `#42`).

### 6d: Verify the Roadmap update

Read the Roadmap file back. Confirm that every step has a real issue number (not a placeholder). If any placeholder remains, fix it.

### 6e: Create Ready state file

All planning artifacts are now complete. Create a `Ready` state file to signal that this feature is available for `/implement-roadmap`:

```bash
printf -- '---\nevent: ready\ndate: YYYY-MM-DD\n---\n' > "Roadmaps/YYYY-MM-DD-<FeatureName>/State/YYYY-MM-DD-Ready.md"
```

### 6f: Commit and push the updated Roadmap and state

```bash
git add "Roadmaps/YYYY-MM-DD-<FeatureName>/"
git commit -m "docs: add GitHub issue numbers to <FeatureName> Roadmap, mark Ready"
git push
```

---

## Step 7: Final Verification and Summary

### 7a: Run final verification

Execute all of the following checks. **Every check must pass.**

```bash
# Check Feature Definition exists and has content
test -s "Roadmaps/YYYY-MM-DD-<FeatureName>/Definition.md" && echo "PASS: Feature Definition exists" || echo "FAIL: Feature Definition missing"
```

```bash
# Check Roadmap exists and has content
test -s "Roadmaps/YYYY-MM-DD-<FeatureName>/Roadmap.md" && echo "PASS: Roadmap exists" || echo "FAIL: Roadmap missing"
```

```bash
# Check State/Ready file exists
test -f "Roadmaps/YYYY-MM-DD-<FeatureName>/State/"*"-Ready.md" && echo "PASS: Ready state exists" || echo "FAIL: Ready state missing"
```

```bash
# Check State/ directory has Created, Planning, and Ready markers
ls "Roadmaps/YYYY-MM-DD-<FeatureName>/State/"
```

```bash
# List all issues for this feature
gh issue list --search "Feature: [<FeatureName>]" --json number,title,state
```

If **any check fails**, **STOP. Tell the user which check failed. Fix the issue before continuing.**

### 7b: Exit plan mode

Exit plan mode.

### 7c: Present final summary and offer implementation

Print the complete summary, then ask:

```
=== PLANNING COMPLETE: <FeatureName> ===

Feature Definition:
  File: Roadmaps/YYYY-MM-DD-<FeatureName>/Definition.md
  Sections: <list key sections>

Roadmap:
  File: Roadmaps/YYYY-MM-DD-<FeatureName>/Roadmap.md
  Steps: <N> total
  State: Ready
  Estimated scope: <S/M/L breakdown>
  Dependencies: <summary>

GitHub Issues:
  - #<N1>: Step 1 — <Description>
  - #<N2>: Step 2 — <Description>
  - ... (all issues)

All artifacts verified. All commits saved.

Ready to implement? (yes/no)
  yes — I'll run /implement-roadmap to launch the agent in the background.
  no  — Run /implement-roadmap when you're ready.
```

**STOP. Wait for the user's response.**

### 7d: Launch implementation (if requested)

If the user says **yes**, invoke the `/implement-roadmap` skill using the Skill tool.

If the user says **no**, end the skill.
