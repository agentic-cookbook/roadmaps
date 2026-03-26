---
name: repair-roadmap
version: "1"
description: "Repair an existing incomplete roadmap — re-plans steps using /plan-roadmap logic, preserves the roadmap ID, archives the old version. Use when a roadmap has stuck/incorrect steps."
disable-model-invocation: true
---

## Version Check

If `$ARGUMENTS` is `--version`, respond with exactly:

> repair-roadmap v1

Then stop. Do not continue with the rest of the skill.

---

# Repair Roadmap

Re-plans an existing incomplete roadmap. Reads the current roadmap as context, lets you specify what needs fixing, then produces a revised roadmap using the same planning logic as `/plan-roadmap`.

The original roadmap is preserved (renamed) for comparison. The repaired roadmap keeps the same ID, project, and github-user.

---

## ABSOLUTE RULE: NO IMPLEMENTATION CODE

**This skill produces planning documents. Nothing else.**

Your only permitted outputs are: Markdown files inside `~/.roadmaps/<project>/`. If you are about to write any file outside this directory, STOP. You are off course.

Before starting work, read `${CLAUDE_SKILL_DIR}/references/active-guards.md` for the complete list of hard-stop guardrails.

---

## Step 0: Startup Validation

### 0a: Verify git repository

```bash
git rev-parse --is-inside-work-tree
```

If this fails, **STOP**. Tell the user this skill must run inside a git repository.

### 0b: Repair log

The repair log lives inside the roadmap directory (set in Step 1 after resolving):

```bash
REPAIR_LOG="$ROADMAP_DIR/repair.log"
```

Write the header once the roadmap is resolved:
```
[YYYY-MM-DD HH:MM:SS] repair-roadmap v1 started
[YYYY-MM-DD HH:MM:SS] project: $PROJECT
[YYYY-MM-DD HH:MM:SS] roadmap: $ROADMAP_DIR
```

Throughout this skill, append to `$REPAIR_LOG` before every significant action (same format as plan-roadmap's planning log).

---

## Step 1: Resolve Roadmap

Find the roadmap to repair. Use the coordinator:

```bash
python3 "${CLAUDE_SKILL_DIR}/../implement-roadmap/references/coordinator" resolve $ARGUMENTS
```

This scans both `~/.roadmaps/<project>/` and `Roadmaps/` in the repo.

- If it has `"path"` — use that roadmap.
- If it has `"choose"` — present the list and ask the user to pick.
- If it has `"error"` — print the error and **STOP**.

**Log**: `RESOLVE: selected <roadmap_path>`

Store the roadmap directory path as `ROADMAP_DIR`.

---

## Step 2: Analyze Current Roadmap

Read the existing Roadmap.md and present a summary to the user:

```
=== ROADMAP REPAIR: <FeatureName> ===

Current state: <state from State/ directory>
Steps: <N> total, <complete> complete, <remaining> remaining
Manual steps: <list any Manual steps>
Last modified: <date from frontmatter>

Steps:
  1. [Complete] <description>
  2. [Not Started] <description> (Manual)
  3. [Not Started] <description>
  ...

What needs to be repaired?
  [1] Replan all remaining steps (keeps completed steps)
  [2] Fix specific steps (I'll tell you which)
  [3] Full replan (start from scratch, discard all progress)
```

**STOP. Wait for the user's response.**

**Log**: `USER_CHOICE: <option selected>`

---

## Step 3: Enter Plan Mode and Revise

Activate plan mode with deep thinking enabled.

Read the plan-roadmap template:
- `${CLAUDE_SKILL_DIR}/../plan-roadmap/references/feature-roadmap-template.md`

Using the existing roadmap as context and the user's repair instructions:

1. **Preserve** from the original: `id`, `project`, `github-user`, `created`
2. **Update**: `modified` to today, append to `change-history`, set `plan-version` to current plan-roadmap version
3. **For each step that may be Manual**, run the CLI readiness check from plan-roadmap v11:
   - Check if the tool is installed: `which <tool>`
   - Check if authenticated: `<tool> auth status` or equivalent
   - Report to user and let them decide Auto vs Manual
   - **Log**: `TOOL_CHECK: <tool> — installed: yes/no, authenticated: yes/no`
   - **Log**: `STEP_TYPE: Step N "<name>" — Auto/Manual (reason)`
4. **Ensure bookend steps**: Step 1 = "Create Draft PR", Step N = "Finalize & Merge PR"
5. **Renumber steps** sequentially starting from 1

---

## Step 4: Present Revised Roadmap

Print the **complete revised Roadmap** to the terminal. Not a summary — the full document.

Then ask:

```
Above is the revised Roadmap (<N> steps, <changes summary>).

Changes from original:
  - <list what changed>

[x] approved — write to disk
[ ] <describe changes needed>
```

**STOP. Wait for the user's response.**

- If changes requested: revise and re-present.
- If approved: proceed to write.

---

## Step 5: Write Revised Roadmap

### 5a: Archive the original

Rename the original Roadmap.md so it's preserved:

```bash
TODAY=$(date +%Y-%m-%d)
mv "$ROADMAP_DIR/Roadmap.md" "$ROADMAP_DIR/Roadmap.repaired-$TODAY.md"
```

**Log**: `ACTION: archived original as Roadmap.repaired-$TODAY.md`

### 5b: Write the new Roadmap.md

Write the revised roadmap to `$ROADMAP_DIR/Roadmap.md`.

### 5c: Add history entry

Write a history entry recording the repair:

```bash
NOW=$(date +%Y-%m-%d-%H%M%S)
```

Write to `$ROADMAP_DIR/History/$NOW-Repaired.md`:
```
---
event: repaired
date: $TODAY
---

Roadmap repaired. Original saved as Roadmap.repaired-$TODAY.md.
Changes: <brief summary of what was changed>
```

### 5d: Reset to Ready state

```bash
printf -- '---\nevent: ready\ndate: %s\n---\n' "$TODAY" > "$ROADMAP_DIR/State/$TODAY-Ready.md"
```

### 5e: Verify all files

Use the **Read tool** to verify:
- `$ROADMAP_DIR/Roadmap.md` exists and is not empty
- `$ROADMAP_DIR/Roadmap.repaired-$TODAY.md` exists (the original)
- `$ROADMAP_DIR/State/$TODAY-Ready.md` exists

---

## Step 6: Final Summary

Exit plan mode, then print:

```
=== REPAIR COMPLETE: <FeatureName> ===

Roadmap: $ROADMAP_DIR/Roadmap.md
Original: $ROADMAP_DIR/Roadmap.repaired-$TODAY.md
State: Ready
Steps: <N> total
Log: $ROADMAP_DIR/repair.log

Changes:
  - <list what changed>

Run /implement-roadmap to begin implementation.
```
