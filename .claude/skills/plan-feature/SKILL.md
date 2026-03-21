---
name: plan-feature
description: "Plan a new feature — create Feature Definition, Roadmap, and GitHub issues. Use when starting a new feature, component, subsystem, refactor, or test suite. Triggers on requests like 'let's plan', 'plan a feature', 'design a new component', or /plan-feature."
---

# Plan Feature

Collaborative planning workflow for new features. Produces exactly **three deliverables**:

1. A **Feature Definition** file (written to disk, committed)
2. A **Feature Roadmap** file (written to disk, committed)
3. **GitHub issues** (one per roadmap step, confirmed via `gh issue view`)

When planning is complete, tell the user to run `/implement-feature` to begin implementation.

---

## ABSOLUTE RULE: NO IMPLEMENTATION CODE

**This skill produces planning documents and GitHub issues. Nothing else.**

You MUST NOT:
- Write any implementation code (no `.kt`, `.swift`, `.ts`, `.tsx`, `.py`, `.go`, `.rs`, `.java`, `.css`, `.html`, or any other source file)
- Create any source directories
- Modify any existing source files
- Create build configurations, package manifests, or infrastructure files

You MUST ONLY:
- Create/edit Markdown files inside `.claude/Features/`
- Create GitHub issues via `gh issue create`
- Edit `.gitignore` (only to add the `.claude/Features/` tracking rule)
- Run `git add`, `git commit` for the above files

**If you find yourself about to write any file outside `.claude/Features/`, STOP IMMEDIATELY. You are off course. Return to the current step and produce only planning artifacts.**

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

Check if `.gitignore` contains a rule that would exclude `.claude/Features/`. If so, add `!.claude/Features/` to `.gitignore`. If `.gitignore` doesn't exist or doesn't ignore `.claude`, no change is needed.

### 0f: Detect the feature name

Ask the user what feature they want to plan. **Do not proceed until they provide a name or description.** Derive a `<FeatureName>` slug (PascalCase, no spaces) from their response.

**STOP. Confirm the feature name with the user before proceeding.**

Print:
```
Feature name: <FeatureName>
Files that will be created:
  - .claude/Features/FeatureDefinitions/<FeatureName>-FeatureDefinition.md
  - .claude/Features/Active-Roadmaps/<FeatureName>-FeatureRoadmap.md
  - GitHub issues: one per implementation step (created in Step 4)

Proceed? (yes/no)
```

Wait for user confirmation before continuing.

---

## Step 1: Enter Plan Mode

Activate plan mode with deep thinking enabled. All design work happens in plan mode.

**Reminder to yourself: You are now in planning mode. You will NOT write any implementation code. Your only outputs are Markdown planning files and GitHub issues.**

---

## Step 2: Create Feature Definition

### 2a: Read the template

Read the template at `${CLAUDE_SKILL_DIR}/references/feature-definition-template.md`. This is your structural guide. Every section in the template must appear in the final file.

### 2b: Draft the Feature Definition

Using everything the user has told you so far, fill in as many sections of the template as you can. Leave sections you cannot fill marked with `_NEEDS INPUT_`.

### 2c: Present the draft to the user

Print the **complete draft** to the terminal. Not a summary. Not highlights. The full document.

Then explicitly ask:

```
Above is the draft Feature Definition. Please review every section.

Sections that need your input are marked _NEEDS INPUT_.

What changes, additions, or corrections do you want?
```

**STOP. Wait for the user's feedback. Do NOT proceed until they respond.**

### 2d: Revise based on feedback

Incorporate the user's feedback. If the changes are significant, print the revised draft and ask for another round of feedback. Repeat until the user is satisfied.

### 2e: Get explicit approval

Ask the user:

```
Is this Feature Definition approved? I will now write it to disk and commit it. (yes/no)
```

**STOP. Wait for explicit "yes" before writing anything.**

### 2f: Write the file

Write the approved content to:
```
.claude/Features/FeatureDefinitions/<FeatureName>-FeatureDefinition.md
```

### 2g: Verify the file exists and has content

**Immediately** after writing, read the file back:

```bash
wc -l ".claude/Features/FeatureDefinitions/<FeatureName>-FeatureDefinition.md"
```

```bash
head -5 ".claude/Features/FeatureDefinitions/<FeatureName>-FeatureDefinition.md"
```

If the file does not exist, has 0 lines, or `head` returns nothing: **STOP. Something went wrong. Tell the user the file was not created and attempt to write it again.**

### 2h: Commit the file

```bash
git add ".claude/Features/FeatureDefinitions/<FeatureName>-FeatureDefinition.md"
git commit -m "docs: add Feature Definition for <FeatureName>"
```

Verify the commit succeeded by checking the exit code. If it failed, tell the user.

---

### CHECKPOINT GATE 1 — Feature Definition Complete

Print the following to the user:

```
=== CHECKPOINT: Feature Definition ===
File: .claude/Features/FeatureDefinitions/<FeatureName>-FeatureDefinition.md
Lines: <N>
Commit: <hash>
Status: CREATED AND COMMITTED

Proceeding to Step 3: Feature Roadmap.
```

**STOP. Do NOT proceed to Step 3 until the user acknowledges this checkpoint.**

---

## Step 3: Create Feature Roadmap

### 3a: Read the template

Read the template at `${CLAUDE_SKILL_DIR}/references/feature-roadmap-template.md`.

### 3b: Draft the Roadmap

Break the feature into ordered implementation steps. Each step must be:

- **Small enough for a single PR** (reviewable in one sitting)
- **Independently testable** with clear acceptance criteria
- **Clear about what "done" means**

For each step, fill in:
- Description
- Complexity estimate (S/M/L)
- Dependencies on other steps
- Acceptance criteria
- Testing/verification approach

**Set the `Implementing` field to `No`.** This field is managed exclusively by `/implement-feature`.

### 3c: Present the complete draft to the user

Print the **full roadmap** to the terminal. Not a summary.

Then ask:

```
Above is the draft Feature Roadmap with <N> implementation steps.

Review the step breakdown, ordering, complexity estimates, and acceptance criteria.

What changes do you want?
```

**STOP. Wait for the user's feedback. Do NOT proceed until they respond.**

### 3d: Revise based on feedback

Incorporate feedback. Re-present if changes are significant. Repeat until satisfied.

### 3e: Get explicit approval

```
Is this Feature Roadmap approved? I will now write it to disk and commit it. (yes/no)
```

**STOP. Wait for explicit "yes" before writing.**

### 3f: Write the file

Write to:
```
.claude/Features/Active-Roadmaps/<FeatureName>-FeatureRoadmap.md
```

### 3g: Verify the file exists and has content

```bash
wc -l ".claude/Features/Active-Roadmaps/<FeatureName>-FeatureRoadmap.md"
```

```bash
head -5 ".claude/Features/Active-Roadmaps/<FeatureName>-FeatureRoadmap.md"
```

If the file does not exist or is empty: **STOP. Tell the user. Re-attempt the write.**

### 3h: Commit the file

```bash
git add ".claude/Features/Active-Roadmaps/<FeatureName>-FeatureRoadmap.md"
git commit -m "docs: add Feature Roadmap for <FeatureName>"
```

---

### CHECKPOINT GATE 2 — Feature Roadmap Complete

```
=== CHECKPOINT: Feature Roadmap ===
File: .claude/Features/Active-Roadmaps/<FeatureName>-FeatureRoadmap.md
Lines: <N>
Steps: <N> implementation steps
Commit: <hash>
Status: CREATED AND COMMITTED

Proceeding to Step 4: GitHub Issues.
```

**STOP. Do NOT proceed to Step 4 until the user acknowledges this checkpoint.**

---

## Step 4: Create GitHub Issues

### 4a: Create issues one at a time

For each step in the Roadmap, create a GitHub issue:

```bash
gh issue create --title "Feature: [<FeatureName>] Step <N>: <StepDescription>" --body "$(cat <<'EOF'
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
)"
```

### 4b: Verify each issue was created

After each `gh issue create`, capture the issue number from stdout. Then verify:

```bash
gh issue view <number> --json number,title,state
```

If verification fails for any issue, **STOP. Tell the user which issue failed and retry.**

Collect all issue numbers in a list.

### 4c: Update the Roadmap with issue numbers

For each step in the Roadmap file, replace the `{{REPO}}#{{ISSUE_NUMBER}}` placeholder with the actual issue reference (e.g., `#42`).

### 4d: Verify the Roadmap update

Read the Roadmap file back. Confirm that every step has a real issue number (not a placeholder). If any placeholder remains, fix it.

### 4e: Commit the updated Roadmap

```bash
git add ".claude/Features/Active-Roadmaps/<FeatureName>-FeatureRoadmap.md"
git commit -m "docs: add GitHub issue numbers to <FeatureName> Roadmap"
```

---

### CHECKPOINT GATE 3 — GitHub Issues Complete

```
=== CHECKPOINT: GitHub Issues ===
Issues created:
  - #<N1>: Feature: [<FeatureName>] Step 1: <Description>
  - #<N2>: Feature: [<FeatureName>] Step 2: <Description>
  - ... (list all)
Roadmap updated: Yes
Commit: <hash>
Status: ALL ISSUES CREATED AND VERIFIED
```

**STOP. Do NOT proceed to Step 5 until the user acknowledges this checkpoint.**

---

## Step 5: Final Verification and Exit

### 5a: Run final verification

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
# List all issues for this feature
gh issue list --search "Feature: [<FeatureName>]" --json number,title,state
```

If **any check fails**, **STOP. Tell the user which check failed. Fix the issue before continuing.**

### 5b: Exit plan mode

Exit plan mode.

### 5c: Present final summary

Print the complete summary:

```
=== PLANNING COMPLETE: <FeatureName> ===

Feature Definition:
  File: .claude/Features/FeatureDefinitions/<FeatureName>-FeatureDefinition.md
  Sections: <list key sections>

Roadmap:
  File: .claude/Features/Active-Roadmaps/<FeatureName>-FeatureRoadmap.md
  Steps: <N> total
  Estimated scope: <S/M/L breakdown>
  Dependencies: <summary>

GitHub Issues:
  - #<N1>: Step 1 — <Description>
  - #<N2>: Step 2 — <Description>
  - ... (all issues)

All artifacts verified. All commits saved.

To begin implementation, run: /implement-feature
```

---

## REMINDER: NO IMPLEMENTATION CODE

This skill is complete. You produced:
- One Feature Definition markdown file
- One Feature Roadmap markdown file
- GitHub issues

You did NOT produce any implementation code. If you wrote any source files during this session, something went wrong. Tell the user immediately.

---

## Active Guards

These are not suggestions. These are hard stops.

- **If you are about to create a file outside `.claude/Features/`** — STOP. You are writing implementation code. Return to the current step.
- **If you are about to skip presenting a draft to the user** — STOP. Every draft must be shown in full and approved before writing to disk.
- **If you are about to proceed past a CHECKPOINT GATE without user acknowledgment** — STOP. Print the checkpoint and wait.
- **If you wrote a file but did not read it back to verify** — STOP. Go back and verify.
- **If you created a GitHub issue but did not run `gh issue view` to confirm** — STOP. Go back and verify.
- **If you are about to set `Implementing` to anything other than `No`** — STOP. Only `/implement-feature` manages that field.
- **If the user asks you to "just start coding" or "skip the planning"** — STOP. Tell them this skill only produces plans. If they want to skip planning, they should not use this skill.
- **If a file write fails silently** — You will catch this because you verify every write. Re-attempt the write. If it fails again, tell the user and stop.
