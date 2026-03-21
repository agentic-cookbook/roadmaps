---
name: review-claude-extension
version: "2"
description: "Review a Claude Code skill or agent against Anthropic's official best practices. Use when you want to validate a skill/agent design, check for anti-patterns, or ensure compliance with the skills specification. Triggers on 'review this skill', 'check my agent', 'validate this extension', or /review-claude-extension."
argument-hint: "<path-to-skill-or-agent>"
disable-model-invocation: true
allowed-tools: Read, Glob, Grep, WebFetch, Bash(wc *)
context: fork
---

## Version Check

If `$ARGUMENTS` is `--version`, respond with exactly:

> review-claude-extension v2

Then stop. Do not continue with the rest of the skill.

---

# Review Claude Extension

Review a Claude Code skill or agent against Anthropic's official best practices and structural requirements. Produces a structured report with PASS/WARN/FAIL ratings and actionable recommendations.

## Guards

- **Read-only**: Do NOT modify any files in the reviewed skill or agent
- **No output files**: Print the review report to the console only
- **Fail fast**: If the target path is invalid or has no SKILL.md / agent .md, stop immediately with a clear error

---

## Step 1: Resolve the Target

Use `$ARGUMENTS` as the path to the skill or agent to review.

### If `$ARGUMENTS` is provided:
1. Check if the path points to a directory containing `SKILL.md` → it's a **skill**
2. Check if the path points to a `.md` file → read its frontmatter; if it contains `tools`, `disallowedTools`, or `permissionMode`, it's an **agent**
3. Check if the path points to a directory containing a `.md` file with agent frontmatter → it's an **agent**
4. If none match, print an error and **STOP**:
   ```
   ERROR: No SKILL.md or agent definition found at: <path>
   ```

### If `$ARGUMENTS` is empty:
1. Check if the current directory contains `SKILL.md` → use it
2. Check parent directories up to `.claude/skills/` for `SKILL.md`
3. Check if the current directory is inside `.claude/agents/` and contains a `.md` file
4. If nothing found, print an error and **STOP**:
   ```
   ERROR: No skill or agent found. Provide a path: /review-claude-extension <path>
   ```

Set `TARGET_TYPE` to either `skill` or `agent`.

---

## Step 2: Read All Target Files

1. If **skill**: Read `SKILL.md` and all files in the skill directory recursively (references/, scripts/, examples/)
2. If **agent**: Read the agent `.md` file
3. Parse the YAML frontmatter — extract all fields
4. Count the total lines of the main file (SKILL.md or agent .md)
5. List all supporting files found

Print a brief header:
```
=== REVIEW: <name> ===
Type: <Skill|Agent>
Path: <path>
Files: <count> (<file list>)
Lines: <main file line count>
```

---

## Step 3: Fetch Latest Anthropic Guidance

Fetch these URLs using WebFetch to get the latest official guidance. These supplement the bundled checklist — if any fetch fails, note it and continue with the bundled checklist alone.

1. `https://code.claude.com/docs/en/skills`
2. `https://code.claude.com/docs/en/best-practices`
3. If reviewing an agent: `https://code.claude.com/docs/en/sub-agents`

After fetching, scan for any guidance not already captured in the bundled checklist. If you find new criteria, include them in the review under a "New Guidance" section.

---

## Step 4: Run the Review

Load the review criteria:
- Read `${CLAUDE_SKILL_DIR}/references/review-checklist.md` — the comprehensive checklist
- Read `${CLAUDE_SKILL_DIR}/references/skill-structure-reference.md` (if skill)
- Read `${CLAUDE_SKILL_DIR}/references/agent-structure-reference.md` (if agent)

Evaluate every applicable criterion from the checklist against the target. For each check:

1. Determine the result: **PASS**, **WARN**, **FAIL**, or **N/A**
2. For WARN and FAIL results, write a specific finding explaining what's wrong
3. For WARN and FAIL results, write an actionable recommendation (what to change)
4. For subjective checks (C01 single responsibility, B02 native capabilities), explain your reasoning and prefer WARN over FAIL when uncertain

### Sections to evaluate:
- **Structure & Format** (S01–S12) — always
- **Content Quality** (C01–C10) — always
- **Best Practices** (B01–B12) — always
- **Agent-Specific** (A01–A08) — only if TARGET_TYPE is `agent`

---

## Step 5: Print the Review Report

Print the full report to the console using this format:

```
--- STRUCTURE & FORMAT ---
[PASS] S01: YAML frontmatter present
[FAIL] S06: SKILL.md exceeds 500 lines (currently 627)
       -> Move detailed content to references/ files
[WARN] S10: $ARGUMENTS used but no argument-hint in frontmatter
       -> Add argument-hint: "<expected-input>" to frontmatter
...

--- CONTENT QUALITY ---
[PASS] C01: Single responsibility — clear, focused purpose
[WARN] C04: No error handling instructions found
       -> Add guidance for what to do when <specific scenario> fails
...

--- BEST PRACTICES ---
[PASS] B01: Verification method provided
[N/A]  B04: context: fork (not applicable for this skill type)
...

--- AGENT-SPECIFIC ---  (only if agent)
[PASS] A01: name and description present
[WARN] A06: No maxTurns set — agent could run indefinitely
       -> Add maxTurns: <suggested-value> for bounded execution
...
```

After all sections, print the summary:

```
=== SUMMARY ===
Pass: <n> | Warn: <n> | Fail: <n> | N/A: <n>
```

If there are any WARN or FAIL results, print a prioritized recommendations list:

```
Top recommendations:
1. [FAIL] <most critical issue and fix>
2. [FAIL] <next critical issue and fix>
3. [WARN] <most impactful warning and fix>
...
```

List all FAILs first (sorted by ID), then WARNs (sorted by ID). Limit to the top 10 recommendations.

---

## Step 6: Done

The review is complete. Do not modify any files. The user can now act on the recommendations or ask follow-up questions about specific findings.
