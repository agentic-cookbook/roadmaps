# plan-roadmap Permission & Prompt Fixes

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate all Claude Code permission prompts during plan-roadmap execution and standardize user-facing prompts.

**Architecture:** Remove the `allowed-tools` whitelist from SKILL.md frontmatter (rely on settings.json + active guards for safety), replace Bash file-write commands with Write/Glob tools, fix brace expansion and /tmp path issues. Standardize all user prompts to checkbox format.

**Tech Stack:** Claude Code skill (Markdown), Bash, gh CLI

**Issues resolved:** #1, #19, #21, #23, #24, #25, #26

---

## File Structure

- Modify: `skills/plan-roadmap/SKILL.md` — all changes are in this one file

---

### Task 1: Remove `allowed-tools` from frontmatter

This is the root cause of most permission prompts. The skill whitelist is too narrow and every new Bash pattern requires a manual addition. Safety is already enforced by active guards + settings.json.

**Files:**
- Modify: `skills/plan-roadmap/SKILL.md:1-7`

- [ ] **Step 1: Remove allowed-tools line and bump version**

Replace the frontmatter:

```yaml
---
name: plan-roadmap
version: "5"
description: "Plan a new feature — discuss, then create Feature Definition, Roadmap, and GitHub issues. Use when starting a new feature or component."
disable-model-invocation: true
---
```

The `allowed-tools` line is deleted entirely. Version bumps from 4 → 5.

- [ ] **Step 2: Update version check response**

In the Version Check section (~line 13), change:

```
> plan-roadmap v5
```

- [ ] **Step 3: Commit**

```bash
git add skills/plan-roadmap/SKILL.md
git commit -m "fix(plan-roadmap): remove allowed-tools whitelist, bump to v5

Closes #19"
```

---

### Task 2: Fix brace expansion in mkdir (Step 5e)

`mkdir -p ".../{State,History}"` triggers Claude Code's glob pattern warning. Use two separate mkdir calls.

**Files:**
- Modify: `skills/plan-roadmap/SKILL.md:239-242`

- [ ] **Step 1: Replace the mkdir command**

Find the Step 5e section. Replace the single mkdir with brace expansion:

```bash
mkdir -p "Roadmaps/YYYY-MM-DD-<FeatureName>/{State,History}"
```

With two separate calls:

```bash
mkdir -p "Roadmaps/YYYY-MM-DD-<FeatureName>/State" "Roadmaps/YYYY-MM-DD-<FeatureName>/History"
```

- [ ] **Step 2: Commit**

```bash
git add skills/plan-roadmap/SKILL.md
git commit -m "fix(plan-roadmap): avoid brace expansion in mkdir

Closes #24"
```

---

### Task 3: Replace printf→Bash with Write tool for state files (Steps 5f, 6e)

`printf '...' > Roadmaps/.../State/...` via Bash triggers permission prompts because it's a Bash write operation. The Write tool is already available and covered by `Write(Roadmaps/**)` in settings.json.

**Files:**
- Modify: `skills/plan-roadmap/SKILL.md:254-261` (Step 5f)
- Modify: `skills/plan-roadmap/SKILL.md:355-359` (Step 6e)

- [ ] **Step 1: Replace Step 5f state file creation**

Replace the bash printf block in Step 5f with:

```markdown
### 5f: Create initial state files

After writing both documents, create state marker files to record the lifecycle events. Use the **Write tool** (not Bash) for each file:

Write to `Roadmaps/YYYY-MM-DD-<FeatureName>/State/YYYY-MM-DD-Created.md`:
```
---
event: created
date: YYYY-MM-DD
---
```

Write to `Roadmaps/YYYY-MM-DD-<FeatureName>/State/YYYY-MM-DD-Planning.md`:
```
---
event: planning
date: YYYY-MM-DD
---
```
```

- [ ] **Step 2: Replace Step 6e Ready state file creation**

Replace the bash printf block in Step 6e with:

```markdown
### 6e: Create Ready state file

All planning artifacts are now complete. Use the **Write tool** to create a `Ready` state file signaling this feature is available for `/implement-roadmap`:

Write to `Roadmaps/YYYY-MM-DD-<FeatureName>/State/YYYY-MM-DD-Ready.md`:
```
---
event: ready
date: YYYY-MM-DD
---
```
```

- [ ] **Step 3: Commit**

```bash
git add skills/plan-roadmap/SKILL.md
git commit -m "fix(plan-roadmap): use Write tool for state files instead of printf

Closes #23"
```

---

### Task 4: Move issue body temp file out of /tmp (Step 6a)

Writing to `/tmp/gh-issue-body.md` triggers a permission prompt because `/tmp/` is outside the project. Write the temp file inside the roadmap directory instead, and clean it up after.

**Files:**
- Modify: `skills/plan-roadmap/SKILL.md:291-331` (Step 6a)

- [ ] **Step 1: Replace /tmp path with roadmap-local path**

In Step 6a, replace all references to `/tmp/gh-issue-body.md` with `Roadmaps/YYYY-MM-DD-<FeatureName>/.gh-issue-body.md`.

Update the instruction text to explain:

```markdown
### 6a: Create issues one at a time

For each step in the Roadmap, create a GitHub issue.

Use the **Write tool** to write the issue body to a temp file inside the roadmap directory, then create the issue using `--body-file` to avoid quoted-newline permission warnings:

Write to `Roadmaps/YYYY-MM-DD-<FeatureName>/.gh-issue-body.md`:
```

Keep the existing body template content (the `## Context`, `## Step Details`, `## Acceptance Criteria`, `## Complexity`, and `## Dependencies` sections from the original `cat > ... <<'EOF' ... EOF` heredoc). Replace the `cat` heredoc with a Write tool instruction — the body content itself is unchanged, only the delivery mechanism changes from Bash heredoc to Write tool.

Update both `gh issue create` commands to use the new path:

```bash
gh issue create --title "Feature: [<FeatureName>] Step <N>: <StepDescription>" --body-file "Roadmaps/YYYY-MM-DD-<FeatureName>/.gh-issue-body.md"
```

```bash
gh issue create --title "Feature: [<FeatureName>] Step <N>: <StepDescription> [Manual]" --body-file "Roadmaps/YYYY-MM-DD-<FeatureName>/.gh-issue-body.md" --assignee @me
```

- [ ] **Step 2: Add cleanup after all issues are created**

At the end of Step 6d (after verifying Roadmap has no remaining placeholders), add:

```markdown
Clean up the temp file:

```bash
rm "Roadmaps/YYYY-MM-DD-<FeatureName>/.gh-issue-body.md"
```
```

- [ ] **Step 3: Commit**

```bash
git add skills/plan-roadmap/SKILL.md
git commit -m "fix(plan-roadmap): write issue body inside roadmap dir, not /tmp

Closes #25
Closes #1"
```

---

### Task 5: Replace Bash verification with proper tools (Step 5g, 7a)

Steps 5g and 7a use `test -f`, `test -s`, `wc -l`, `head`, and `ls` via Bash. Some of these (especially `test -f .../*-Ready.md` with a glob) trigger permission prompts. Use Read and Glob tools where possible.

**Files:**
- Modify: `skills/plan-roadmap/SKILL.md:263-271` (Step 5g)
- Modify: `skills/plan-roadmap/SKILL.md:375-401` (Step 7a)

- [ ] **Step 1: Replace Step 5g verification**

Replace the current Step 5g with:

```markdown
### 5g: Verify all files exist and have content

Use the **Read tool** to read the first few lines of each file. If any file does not exist or is empty, **STOP. Tell the user. Re-attempt the write.**

Read: `Roadmaps/YYYY-MM-DD-<FeatureName>/Definition.md`
Read: `Roadmaps/YYYY-MM-DD-<FeatureName>/Roadmap.md`

Use the **Glob tool** to verify state files exist:

Glob: `Roadmaps/YYYY-MM-DD-<FeatureName>/State/*.md`

Expected: two files (Created.md and Planning.md).
```

- [ ] **Step 2: Replace Step 7a verification**

Replace the current Step 7a with:

```markdown
### 7a: Run final verification

Execute all of the following checks. **Every check must pass.**

Use the **Read tool** to verify each file exists and has content:

Read: `Roadmaps/YYYY-MM-DD-<FeatureName>/Definition.md`
— PASS if file exists and is not empty.

Read: `Roadmaps/YYYY-MM-DD-<FeatureName>/Roadmap.md`
— PASS if file exists and is not empty.

Use the **Glob tool** to verify state files:

Glob: `Roadmaps/YYYY-MM-DD-<FeatureName>/State/*-Ready.md`
— PASS if exactly one match.

Glob: `Roadmaps/YYYY-MM-DD-<FeatureName>/State/*.md`
— PASS if at least three files (Created, Planning, Ready).

Verify GitHub issues:

```bash
gh issue list --search "Feature: [<FeatureName>]" --json number,title,state
```

— PASS if issue count matches roadmap step count.

If **any check fails**, **STOP. Tell the user which check failed. Fix the issue before continuing.**
```

- [ ] **Step 3: Commit**

```bash
git add skills/plan-roadmap/SKILL.md
git commit -m "fix(plan-roadmap): use Read/Glob tools for verification instead of Bash

Closes #26"
```

---

### Task 6: Standardize user-facing prompts

All user-facing prompts should use checkbox format with `[x]` marking the default action (what happens on bare Enter).

**Files:**
- Modify: `skills/plan-roadmap/SKILL.md:147-162` (Step 3)
- Modify: `skills/plan-roadmap/SKILL.md:219-227` (Step 5c)
- Modify: `skills/plan-roadmap/SKILL.md:412-436` (Step 7c)

- [ ] **Step 1: Update Step 3 phase gate prompt**

Replace the prompt at the end of Step 3:

```
Here's what I heard:

<summary>

Proposed feature name: <FeatureName>

If this looks right, I'll move to Planning and create:
  - Roadmaps/YYYY-MM-DD-<FeatureName>/Definition.md
  - Roadmaps/YYYY-MM-DD-<FeatureName>/Roadmap.md
  - GitHub issues (one per implementation step)

No implementation code will be written. Only planning documents.

[x] yes — move to Planning
[ ] revise name
[ ] keep discussing
```

- [ ] **Step 2: Update Step 5c draft approval prompt**

Replace the prompt at the end of Step 5c:

```
Above are the draft Feature Definition and Feature Roadmap (<N> implementation steps).

Sections marked _NEEDS INPUT_ need your input.

[x] approved — write to disk and commit
[ ] <describe changes needed>
```

Update Step 5d to match — "If the user selects approved" instead of "If the user says approved".

- [ ] **Step 3: Update Step 7c implementation prompt**

Replace the prompt at the end of Step 7c:

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

[x] yes — run /implement-roadmap
[ ] no — I'll run it later
```

- [ ] **Step 4: Commit**

```bash
git add skills/plan-roadmap/SKILL.md
git commit -m "fix(plan-roadmap): standardize prompts to checkbox format

Closes #21"
```

---

### Task 7: Final verification

- [ ] **Step 1: Verify no remaining /tmp references**

```bash
grep -n "/tmp/" skills/plan-roadmap/SKILL.md
```

Expected: no matches.

- [ ] **Step 2: Verify no remaining printf for file writes**

```bash
grep -n "printf" skills/plan-roadmap/SKILL.md
```

Expected: only the `.gitignore` append in Step 0e (that one is fine — it appends to an existing file, not writing to `Roadmaps/`).

- [ ] **Step 3: Verify no brace expansion**

```bash
grep -n '{State,History}' skills/plan-roadmap/SKILL.md
```

Expected: no matches.

- [ ] **Step 4: Verify version is 5**

```bash
head -5 skills/plan-roadmap/SKILL.md
```

Expected: `version: "5"`.

- [ ] **Step 5: Push**

```bash
git push
```
