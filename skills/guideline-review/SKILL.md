---
name: guideline-review
version: "1"
description: "Review all code in the current repo against the coding guidelines. Runs a comprehensive audit using multiple review agents in parallel."
---

## Version Check

If `$ARGUMENTS` is `--version`, respond with exactly:

> guideline-review v1

Then stop. Do not continue with the rest of the skill.

---

# Guideline Review

Reviews the entire codebase (or a subset) against the installed coding guidelines. Launches multiple review agents in parallel, each checking compliance with specific guideline categories.

This is a read-only audit — it does not fix anything. It produces a report of findings with severities.

---

## Step 0: Detect Project and Guidelines

```bash
PROJECT=$(basename $(git rev-parse --show-toplevel))
REPO_ROOT=$(git rev-parse --show-toplevel)
```

**Detect the platform** from file extensions in the repo:

```bash
# Count files by extension to determine primary language
find "$REPO_ROOT" -type f -name "*.swift" | head -1 && echo "swift"
find "$REPO_ROOT" -type f -name "*.kt" | head -1 && echo "kotlin"
find "$REPO_ROOT" -type f -name "*.ts" -o -name "*.tsx" | head -1 && echo "typescript"
find "$REPO_ROOT" -type f -name "*.py" | head -1 && echo "python"
find "$REPO_ROOT" -type f -name "*.cs" | head -1 && echo "csharp"
```

**Build the guideline list:**
- Always include: `~/.claude/guidelines/general.md`, `~/.claude/guidelines/engineering-principles.md`
- Add platform-specific: `~/.claude/guidelines/<platform>.md`
- If multiple languages detected, include all matching platform guidelines

**Determine scope:**
- If `$ARGUMENTS` is empty: review the entire repo
- If `$ARGUMENTS` is a path: review only that directory or file
- If `$ARGUMENTS` is `--changed`: review only uncommitted changes (`git diff --name-only`)
- If `$ARGUMENTS` is `--branch`: review only changes on the current branch vs main (`git diff --name-only main...HEAD`)

Print:

```
Guideline Review: <PROJECT>
Scope: <entire repo | path | changed files | branch diff>
Guidelines: general.md, engineering-principles.md, <platform>.md
```

---

## Step 1: Gather Files

Based on the scope, collect the list of files to review:

```bash
# Entire repo (exclude common non-code dirs)
find "$REPO_ROOT" -type f \( -name "*.swift" -o -name "*.kt" -o -name "*.ts" -o -name "*.tsx" -o -name "*.py" -o -name "*.cs" -o -name "*.js" -o -name "*.jsx" \) \
  -not -path "*/node_modules/*" -not -path "*/.build/*" -not -path "*/build/*" -not -path "*/__pycache__/*" -not -path "*/venv/*"
```

If the file count is very large (>100 files), ask the user:

```
Found <N> source files. Review all of them, or narrow the scope?

[x] review all
[ ] review only changed files (git diff)
[ ] review a specific directory
```

**STOP. Wait for the user's response.**

---

## Step 2: Launch Review Agents

Read each guideline file and launch review agents in parallel using the **Agent tool**.

### Agent 1: General Coding Guidelines

- **subagent_type**: `pr-review-toolkit:code-reviewer`
- **prompt**:
  ```
  Review the following files for compliance with the coding guidelines.

  Project: <PROJECT>
  Files: <file list or "all files in <path>">

  Read and check against these guidelines:
  - ~/.claude/guidelines/general.md (21 rules — native controls, main thread,
    progress, testing, commits, verification, logging, deep linking, accessibility,
    localization, RTL, privacy, feature flags, analytics, debug mode, linting)

  For each violation, report:
  - File and line (approximate)
  - Rule number and name
  - Severity: high (must fix), medium (should fix), low (nice to have)
  - Brief description

  Focus on the most impactful violations. Do not report more than 30 findings.
  ```

### Agent 2: Engineering Principles

- **subagent_type**: `feature-dev:code-reviewer`
- **prompt**:
  ```
  Review the following files for compliance with engineering principles.

  Project: <PROJECT>
  Files: <file list or "all files in <path>">

  Read and check against these principles:
  - ~/.claude/guidelines/engineering-principles.md (15 principles — simplicity,
    composition over inheritance, dependency injection, immutability, fail fast,
    idempotency, design for deletion, YAGNI, explicit over implicit, separation
    of concerns, least astonishment, boundaries)

  For each violation, report:
  - File and line (approximate)
  - Principle number and name
  - Severity: high, medium, low
  - Brief description

  Focus on architectural issues. Do not report more than 20 findings.
  ```

### Agent 3: Platform-Specific Guidelines

- **subagent_type**: `pr-review-toolkit:code-reviewer`
- **prompt**:
  ```
  Review the following files for compliance with platform-specific conventions.

  Project: <PROJECT>
  Files: <file list or "all files in <path>">

  Read and check against:
  - ~/.claude/guidelines/<platform>.md

  For each violation, report:
  - File and line (approximate)
  - Convention violated
  - Severity: high, medium, low
  - Brief description

  Focus on platform-specific issues (logging framework, secure storage, accessibility
  settings, linting, localization, concurrency patterns). Do not report more than 20 findings.
  ```

### Agent 4: Silent Failure Hunt

- **subagent_type**: `pr-review-toolkit:silent-failure-hunter`
- **prompt**:
  ```
  Scan the following files for silent failures, swallowed exceptions, and
  inadequate error handling.

  Project: <PROJECT>
  Files: <file list or "all files in <path>">

  Check against Rule 6 (fail fast) from ~/.claude/guidelines/engineering-principles.md
  and Rule 16 (privacy/security) from ~/.claude/guidelines/general.md.

  Report findings with severity (high/medium/low).
  Do not report more than 15 findings.
  ```

**Launch all 4 agents in parallel** (single message, multiple Agent tool calls).

---

## Step 3: Aggregate and Report

Wait for all agents to return. Aggregate findings by severity.

Print the report:

```
═══════════════════════════════════════════════════
  GUIDELINE REVIEW: <PROJECT>
  Scope: <scope>
  Files reviewed: <N>
═══════════════════════════════════════════════════

HIGH (<N>)
─────────
  1. [general.md Rule 4] src/api/handler.ts:42
     Blocking main thread with synchronous database call
  2. [engineering Rule 6] src/auth/login.swift:118
     Empty catch block swallows authentication error
  ...

MEDIUM (<N>)
────────────
  1. [general.md Rule 12] src/components/Button.tsx:15
     Missing accessibility label on interactive element
  ...

LOW (<N>)
─────────
  1. [swift.md] src/views/Settings.swift:30
     Using String literal instead of String(localized:)
  ...

═══════════════════════════════════════════════════
  SUMMARY: <total> findings
  <high> high · <medium> medium · <low> low
  Reviewed against: general.md, engineering-principles.md, <platform>.md
═══════════════════════════════════════════════════
```

---

## Step 4: Offer to Fix

After presenting the report, ask:

```
Would you like me to fix any of these?

[x] Fix all high-severity findings
[ ] Fix specific findings (enter numbers)
[ ] No — this was just an audit
```

**STOP. Wait for the user's response.**

If the user wants fixes:
- Fix each finding one at a time
- Commit after each fix: `fix: <guideline rule> — <description>`
- Re-run the relevant review agent on the fixed files to verify
