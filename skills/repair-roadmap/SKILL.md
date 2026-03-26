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

## ABSOLUTE RULE: NO SCOPE REDUCTION

The repair skill NEVER removes steps, features, or acceptance criteria unless the user explicitly names a specific step to remove by number or name.

- Do NOT drop steps because of complexity (L is valid and expected for significant features)
- Do NOT merge steps to "simplify" unless the user explicitly asks to merge specific steps
- Do NOT filter by complexity, size, or estimated effort
- Do NOT reduce scope to make the roadmap "more manageable"
- "Fix the large steps" means fix them IN PLACE, not delete them
- "Replan all remaining steps" means replan them, not reduce them

**Complexity (S/M/L) is a DESCRIPTOR, not a FILTER.** The roadmap contains exactly the steps the user approved during planning. Removing any of them without explicit per-step user consent is data destruction.

---

## Step 3: Enter Plan Mode and Revise

Activate plan mode with deep thinking enabled.

Read the plan-roadmap template:
- `${CLAUDE_SKILL_DIR}/../plan-roadmap/references/feature-roadmap-template.md`

**Before making any changes, record the original step inventory:**

```
ORIGINAL STEPS:
  Step 1: <name> (S/M/L)
  Step 2: <name> (S/M/L)
  ...
  Step N: <name> (S/M/L)
  Total: N steps (S:x M:x L:x)
```

Using the existing roadmap as context and the user's repair instructions:

1. **Preserve** from the original: `id`, `project`, `github-user`, `created`, **and ALL steps not explicitly marked for change by the user**
2. **Update**: `modified` to today, append to `change-history`, set `plan-version` to current plan-roadmap version
3. **For each step that may be Manual**, run the CLI readiness check:
   - Check if the tool is installed: `which <tool>`
   - Check if authenticated: `<tool> auth status` or equivalent
   - Report to user and let them decide Auto vs Manual
   - **Log**: `TOOL_CHECK: <tool> — installed: yes/no, authenticated: yes/no`
   - **Log**: `STEP_TYPE: Step N "<name>" — Auto/Manual (reason)`
4. **Ensure bookend steps**: Step 1 = "Create Draft PR", Step N = "Finalize & Merge PR"
5. **Renumber steps** sequentially starting from 1
6. **Verify no steps were lost**: compare the revised step list against the original inventory. Every original step MUST appear in the revised version (possibly renumbered or modified, but present). If any step is missing, add it back.

---

## Step 4: Present Revised Roadmap

**BEFORE presenting the revised roadmap**, print a step-count comparison:

```
=== STEP COUNT COMPARISON ===

Original: <N> steps (S:<n> M:<n> L:<n>)
Revised:  <N> steps (S:<n> M:<n> L:<n>)

Steps added:    <list or "none">
Steps removed:  <list or "none">
Steps modified: <list or "none">
```

**If ANY steps were removed**, print a prominent warning:

```
⚠ WARNING: <N> steps were REMOVED from the roadmap:
  - Step <X>: <name> (<complexity>)
  - Step <Y>: <name> (<complexity>)

This requires your explicit confirmation. Steps should only be
removed if you specifically asked for them to be removed.
```

Then print the **complete revised Roadmap** to the terminal. Not a summary — the full document.

Then ask:

```
Above is the revised Roadmap (<N> steps).

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

### 5a: Move the original to Trash

Move the original Roadmap.md to the system Trash so it can be recovered if needed:

```bash
TODAY=$(date +%Y-%m-%d)
```

On macOS:
```bash
mv "$ROADMAP_DIR/Roadmap.md" "$HOME/.Trash/Roadmap-$(basename $ROADMAP_DIR)-$TODAY.md"
```

On Linux (freedesktop trash):
```bash
TRASH_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/Trash/files"
mkdir -p "$TRASH_DIR"
mv "$ROADMAP_DIR/Roadmap.md" "$TRASH_DIR/Roadmap-$(basename $ROADMAP_DIR)-$TODAY.md"
```

**Log**: `ACTION: moved original to Trash as Roadmap-$(basename $ROADMAP_DIR)-$TODAY.md`

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

Roadmap repaired. Original moved to Trash.
Changes: <brief summary of what was changed>
```

### 5d: Reset to Ready state

```bash
printf -- '---\nevent: ready\ndate: %s\n---\n' "$TODAY" > "$ROADMAP_DIR/State/$TODAY-Ready.md"
```

### 5e: Verify all files

Use the **Read tool** to verify:
- `$ROADMAP_DIR/Roadmap.md` exists and is not empty
- `$ROADMAP_DIR/State/$TODAY-Ready.md` exists
- Original is no longer in `$ROADMAP_DIR/` (moved to Trash)

---

## Step 6: Final Summary

Exit plan mode, then print:

```
=== REPAIR COMPLETE: <FeatureName> ===

Roadmap: $ROADMAP_DIR/Roadmap.md
Original: moved to Trash
State: Ready
Steps: <N> total
Log: $ROADMAP_DIR/repair.log

Changes:
  - <list what changed>

Run /implement-roadmap to begin implementation.
```
