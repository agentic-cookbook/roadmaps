---
name: generate-test-roadmap
description: "Generate a test roadmap with silly cat-herding steps for testing the implement-roadmap workflow. No prompts, no approvals — just creates everything and exits."
disable-model-invocation: true
---

# Generate Test Roadmap

Creates a complete test roadmap for exercising the `/implement-roadmap-interactively` skill and `implement-roadmap-agent`. Generates all planning artifacts (Feature Definition, Feature Roadmap, GitHub issues) in one shot with no user interaction.

The test feature is deliberately trivial — 20 steps that each append a line to `roadmap-test.md`. The content is silly cat-herding themed.

## RULES

- **No prompting the user.** Do everything autonomously. No checkpoint gates, no approval steps, no "is this OK?" questions.
- **No implementation code.** Only planning artifacts and GitHub issues, same as `/plan-roadmap`.
- **Produce real artifacts.** The output must be structurally identical to what `/plan-roadmap` creates — the implement-roadmap agent must be able to pick it up and run.

---

## Step 0: Validate Environment

```bash
git rev-parse --is-inside-work-tree
```
If this fails, **STOP** with an error.

```bash
gh auth status
```
If this fails, **STOP** — tell the user to run `gh auth login`.

Create directories:
```bash
mkdir -p .claude/Features/FeatureDefinitions
mkdir -p .claude/Features/Active-Roadmaps
mkdir -p .claude/Features/Completed-Roadmaps
mkdir -p .claude/Features/Completed-Features
```

Ensure `.claude/Features/` is tracked by git:
```bash
git check-ignore -q .claude/Features/FeatureDefinitions/test 2>/dev/null && echo "IGNORED" || echo "TRACKED"
```
If `IGNORED`, append negation rules to `.gitignore`:
```bash
printf '\n!.claude/Features/\n!.claude/Features/**\n' >> .gitignore
```

```bash
git add .gitignore && git commit -m "chore: allow .claude/Features/ in git" && git push
```

---

## Step 1: Generate a Feature Name

Pick a random silly cat-herding feature name in PascalCase. Examples:
- `OperationCatNap`
- `ProjectWhiskerWrangler`
- `MissionFurballFormation`
- `TaskforceLaserPointer`
- `InitiativeYarnBallLogistics`

Use a different name each time. Store as `FEATURE_NAME`.

---

## Step 2: Define the 20 Steps

Each step appends one line to `roadmap-test.md` in the repo root. Each line should be a silly cat-herding status report. Examples:

1. "Deployed laser pointer decoy at coordinates (3, 7)"
2. "Catnip airdrop completed over sector B"
3. "Whisker formation alpha now in V-pattern"
4. "Recruited tabby lieutenant for flank operations"
5. "Yarn ball perimeter defense established"
...and so on for 20 steps.

Each step:
- **Complexity**: S
- **Dependencies**: Previous step (Step N depends on Step N-1), except Step 1 which has no dependencies
- **Acceptance Criteria**: `roadmap-test.md` contains the expected line (grep for it)
- **Testing**: `grep -q "<the line>" roadmap-test.md`
- **Description**: `Append line N to roadmap-test.md: "<the line>"`

---

## Step 3: Write Feature Definition

Write `.claude/Features/FeatureDefinitions/${FEATURE_NAME}-FeatureDefinition.md`:

```markdown
# Feature Definition: ${FEATURE_NAME}

**Created**: <today's date>
**Status**: In Progress

## Goal and Purpose

A test feature for validating the implement-roadmap-agent workflow and progress dashboard. Each step appends a silly cat-herding status report to roadmap-test.md.

## Platform / Component

Any git repository with bash available.

## Tools and Technologies

- bash (echo/append to file)
- grep (verification)

## Extended Description

This is a generated test feature. It has 20 trivial steps that each append one line to roadmap-test.md. The content is intentionally silly — the point is testing the tooling, not the output.

## Acceptance Criteria

- roadmap-test.md exists with exactly 20 lines
- Each line matches the expected cat-herding status report

## Dependencies / Prerequisites

None.

## Risks and Unknowns

None — this is a test fixture.

## Verification Strategy

| Check | Command / Approach |
|-------|-------------------|
| Build | `true` (no build needed) |
| Test | `wc -l roadmap-test.md` should show 20 |
| Local verification | `cat roadmap-test.md` and confirm 20 silly lines |
```

Commit and push:
```bash
git add ".claude/Features/FeatureDefinitions/${FEATURE_NAME}-FeatureDefinition.md"
git commit -m "docs: add Feature Definition for ${FEATURE_NAME}"
git push
```

---

## Step 4: Write Feature Roadmap

Write `.claude/Features/Active-Roadmaps/${FEATURE_NAME}-FeatureRoadmap.md` using the roadmap template structure.

Set:
- `**Status**: Not Started`
- `**Implementing**: No`
- `**Phase**: Planning` (will be updated to Ready after issues are created)

Include all 20 steps using the step template structure from the plan-roadmap skill. Each step should have:
- GitHub Issue: `REPO#TBD` (placeholder — will be filled in Step 5)
- Status: Not Started
- Complexity: S
- Dependencies: as defined in Step 2
- Acceptance Criteria: grep for the expected line
- Testing: the grep command
- PR: _TBD_

Commit and push:
```bash
git add ".claude/Features/Active-Roadmaps/${FEATURE_NAME}-FeatureRoadmap.md"
git commit -m "docs: add Feature Roadmap for ${FEATURE_NAME}"
git push
```

---

## Step 5: Create GitHub Issues

For each of the 20 steps, create a GitHub issue:

```bash
gh issue create --title "Feature: [${FEATURE_NAME}] Step N: <description>" --body "<body with context, acceptance criteria, complexity>"
```

After each issue, verify with `gh issue view <number> --json number,title,state`.

After all 20 issues are created:
1. Update the Roadmap file — replace each `REPO#TBD` with the actual issue reference
2. Set `**Phase**: Ready`
3. Commit and push:
```bash
git add ".claude/Features/Active-Roadmaps/${FEATURE_NAME}-FeatureRoadmap.md"
git commit -m "docs: add GitHub issue numbers to ${FEATURE_NAME} Roadmap, set Phase to Ready"
git push
```

---

## Step 6: Print Summary and Exit

Print:

```
=== TEST ROADMAP GENERATED: ${FEATURE_NAME} ===

Feature Definition: .claude/Features/FeatureDefinitions/${FEATURE_NAME}-FeatureDefinition.md
Roadmap: .claude/Features/Active-Roadmaps/${FEATURE_NAME}-FeatureRoadmap.md
Steps: 20
GitHub Issues: #<first> through #<last>
Phase: Ready

To implement, run:
  /implement-roadmap-interactively
  or: claude --agent implement-roadmap-agent "Implement ${FEATURE_NAME}"
```

Done. No further action needed.
