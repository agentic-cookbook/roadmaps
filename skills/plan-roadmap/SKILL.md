---
name: plan-roadmap
version: "3"
description: "Plan a new feature — discuss, then create Feature Definition, Roadmap, and GitHub issues. Use when starting a new feature or component."
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(mkdir *), Bash(gh issue *), Bash(gh api *), Bash(git add *), Bash(git commit *), Bash(git push *), Bash(git status *), Bash(git diff *), Bash(git log *), Bash(cat *)
---

## Version Check

If `$ARGUMENTS` is `--version`, respond with exactly:

> plan-roadmap v3

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

Your only permitted outputs are: Markdown files inside `.claude/Features/`, GitHub issues via `gh issue create`, `.gitignore` edits, and `git add`/`git commit` for those files. If you are about to write any file outside `.claude/Features/`, STOP. You are off course.

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

```bash
mkdir -p .claude/Features/FeatureDefinitions
mkdir -p .claude/Features/Active-Roadmaps
mkdir -p .claude/Features/Completed-Roadmaps
mkdir -p .claude/Features/Completed-Features
```

### 0d: Verify directories are writable

```bash
touch .claude/Features/FeatureDefinitions/.verify && rm .claude/Features/FeatureDefinitions/.verify
touch .claude/Features/Active-Roadmaps/.verify && rm .claude/Features/Active-Roadmaps/.verify
```

If either fails, **STOP**. Tell the user the directory is not writable.

### 0e: Ensure `.claude/Features/` is tracked by git

Run the following to check if git would ignore the Features directory:

```bash
git check-ignore -q .claude/Features/FeatureDefinitions/test 2>/dev/null && echo "IGNORED" || echo "TRACKED"
```

If the output is `IGNORED`, the `.gitignore` (or a parent `.gitignore`) is excluding `.claude/Features/`. Fix this by appending negation rules to the repo-root `.gitignore`:

Append the negation rules to `.gitignore` (use `printf` to avoid heredoc permission warnings):

```bash
printf '\n!.claude/Features/\n!.claude/Features/**\n' >> .gitignore
```

```bash
git add .gitignore && git commit -m "chore: allow .claude/Features/ in git" && git push
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
  - .claude/Features/FeatureDefinitions/<FeatureName>-FeatureDefinition.md
  - .claude/Features/Active-Roadmaps/<FeatureName>-FeatureRoadmap.md
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

> **Goal**: Transform the discussion into structured planning artifacts. Only Markdown files in `.claude/Features/` and GitHub issues are created.

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

**Set the `Implementing` field to `No`.** This field is managed exclusively by `/implement-roadmap-interactively`.

**Set the `Phase` field to `Planning`.** This field will be updated to `Ready` only after all planning artifacts (including GitHub issues) are complete.

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

### 5e: Write both files

Write the Feature Definition to:
```
.claude/Features/FeatureDefinitions/<FeatureName>-FeatureDefinition.md
```

Write the Feature Roadmap to:
```
.claude/Features/Active-Roadmaps/<FeatureName>-FeatureRoadmap.md
```

### 5f: Verify both files exist and have content

```bash
wc -l ".claude/Features/FeatureDefinitions/<FeatureName>-FeatureDefinition.md"
head -5 ".claude/Features/FeatureDefinitions/<FeatureName>-FeatureDefinition.md"
wc -l ".claude/Features/Active-Roadmaps/<FeatureName>-FeatureRoadmap.md"
head -5 ".claude/Features/Active-Roadmaps/<FeatureName>-FeatureRoadmap.md"
```

If either file does not exist or is empty: **STOP. Tell the user. Re-attempt the write.**

### 5g: Commit and push both files

```bash
git add ".claude/Features/FeatureDefinitions/<FeatureName>-FeatureDefinition.md" ".claude/Features/Active-Roadmaps/<FeatureName>-FeatureRoadmap.md"
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
Feature Definition: `.claude/Features/FeatureDefinitions/<FeatureName>-FeatureDefinition.md`
Roadmap: `.claude/Features/Active-Roadmaps/<FeatureName>-FeatureRoadmap.md`

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

### 6e: Update Phase to Ready

All planning artifacts are now complete. Update the Roadmap's `Phase` field from `Planning` to `Ready`. This signals to `/implement-roadmap-interactively` that this feature is available for implementation.

### 6f: Commit and push the updated Roadmap

```bash
git add ".claude/Features/Active-Roadmaps/<FeatureName>-FeatureRoadmap.md"
git commit -m "docs: add GitHub issue numbers to <FeatureName> Roadmap, set Phase to Ready"
git push
```

---

## Step 7: Final Verification and Summary

### 7a: Run final verification

Execute all of the following checks. **Every check must pass.**

```bash
# Check Feature Definition exists and has content
test -s ".claude/Features/FeatureDefinitions/<FeatureName>-FeatureDefinition.md" && echo "PASS: Feature Definition exists" || echo "FAIL: Feature Definition missing"
```

```bash
# Check Roadmap exists and has content
test -s ".claude/Features/Active-Roadmaps/<FeatureName>-FeatureRoadmap.md" && echo "PASS: Roadmap exists" || echo "FAIL: Roadmap missing"
```

```bash
# Check Implementing field is No
grep -q "Implementing.*No" ".claude/Features/Active-Roadmaps/<FeatureName>-FeatureRoadmap.md" && echo "PASS: Implementing is No" || echo "FAIL: Implementing field incorrect"
```

```bash
# Check Phase field is Ready
grep -q "Phase.*Ready" ".claude/Features/Active-Roadmaps/<FeatureName>-FeatureRoadmap.md" && echo "PASS: Phase is Ready" || echo "FAIL: Phase field incorrect"
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
  File: .claude/Features/FeatureDefinitions/<FeatureName>-FeatureDefinition.md
  Sections: <list key sections>

Roadmap:
  File: .claude/Features/Active-Roadmaps/<FeatureName>-FeatureRoadmap.md
  Steps: <N> total
  Phase: Ready
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
