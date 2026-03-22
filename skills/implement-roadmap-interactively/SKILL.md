---
name: implement-roadmap-interactively
version: "6"
description: "Implement a planned feature from its Roadmap step by step with worktrees, PRs, and reviews. Use after /plan-roadmap has created a Roadmap."
disable-model-invocation: true
---

## Version Check

If `$ARGUMENTS` is `--version`, respond with exactly:

> implement-roadmap-interactively v6

Then stop. Do not continue with the rest of the skill.

---

# Implement Roadmap

Implementation workflow for features that have been planned with `/plan-roadmap`. Picks up a Roadmap from `Active-Roadmaps/` and works through each step with proper isolation, testing, and review.

## CRITICAL RULES

1. **NEVER implement a feature without a Roadmap.** If no Roadmap exists, tell the user to run `/plan-roadmap` first.
2. **NEVER combine steps.** Each Roadmap step gets its own worktree, its own PR, its own review cycle, and its own merge. No exceptions.
3. **NEVER skip reviews.** Every PR gets at minimum a code review and security review before merge.
4. **At every step completion, print a checkpoint summary** to the user showing what was completed and what comes next. Do not proceed without user acknowledgment.
5. **CHECK CONTROL FREQUENTLY.** Run the control check at every sub-step boundary — not just between major steps. See Control Check Protocol below.

---

## CONTROL CHECK PROTOCOL

**When the dashboard is running**, run a control check before every significant operation. This makes stop/pause responsive — the user should never have to wait more than one sub-step for the agent to react.

**How to check:**

```bash
python3 "$DASH_CLI" check-control
```

**How to respond:**

- `none` or `resume` — continue normally.
- `pause` — tell the user the dashboard pause button was pressed and wait for them to say to continue (or re-run `check-control` until it returns `resume` or `stop`).
- `stop` — immediately stop. Run `python3 "$DASH_CLI" error "Stopped by user"` then `python3 "$DASH_CLI" shutdown`, and **STOP**.

**When to check** — run a control check before ALL of the following:

- Before starting a new roadmap step (before `begin-step`)
- Before planning the step
- Before creating the worktree
- Before starting implementation
- Before running the build
- Before running tests
- Before creating the PR
- Before starting reviews
- Before addressing review findings
- Before merging the PR
- Before updating the roadmap
- Before closing the GitHub issue

This means **12 control checks per step**, not just 1.

---

## STARTUP: Select a Feature to Implement

### Step 0: Start Progress Dashboard

**This is the very first thing you do.** Before scanning roadmaps or prompting the user, start the dashboard so progress is visible from the beginning.

Locate the `dash` CLI:

```bash
DASH_CLI="$HOME/.claude/skills/progress-dashboard/references/dash"
test -f "$DASH_CLI" && echo "Dashboard available" || echo "NO_DASH"
```

You will initialize the dashboard after the user selects a feature (since you need the feature name). For now, just confirm `DASH_CLI` exists. If not found, continue without the dashboard.

### Step 1: Scan Active Roadmaps

Read all files in `.claude/Features/Active-Roadmaps/`. For each `*-FeatureRoadmap.md` file, parse:

- The feature name (from `# Feature Roadmap: <name>`)
- The `**Status**:` field
- The `**Phase**:` field (if present — `Planning` or `Ready`)
- The progress table (how many steps complete vs total)

### Step 2: Build Available Features List

Categorize each roadmap:

- **Available**: `Status` is not `Complete` AND `Phase` is `Ready` (or `Phase` field is absent for backward compatibility)
- **Not Ready (Still Planning)**: `Phase` is `Planning` — this feature is still being defined by `/plan-roadmap` and is not available for implementation
- **Complete**: `Status` is `Complete` (nothing left to do)

If no features are available:
- If there are "Not Ready" features, list them and explain: "The following features are still in the planning phase and not yet available for implementation. Run `/plan-roadmap` to complete their planning."
- If there are no roadmaps at all, tell the user to run `/plan-roadmap` first
- **STOP** — do not proceed

### Step 3: Present Choices

Present a numbered list of available features to the user:

```
Available features to implement:

1. FeatureA — 0/5 steps complete (Not Started)
2. FeatureB — 3/7 steps complete (In Progress)

Still in planning phase (not yet available):
- FeatureD — planning in progress, run /plan-roadmap to complete

Which feature would you like to implement? (enter number)
```

Wait for the user to choose.

### Step 5: Initialize Progress Dashboard

If `DASH_CLI` was found in Step 0, initialize and load the roadmap:

```bash
python3 "$DASH_CLI" init "<FeatureName>"
python3 "$DASH_CLI" load-roadmap ".claude/Features/Active-Roadmaps/<FeatureName>-FeatureRoadmap.md"
```

The `init` command opens the browser immediately. The `load-roadmap` command reads the roadmap markdown file and automatically populates all step names, GitHub issues, PRs, and completion status. You do NOT manually add steps, issues, or PRs — `load-roadmap` does it all.

Use these commands during implementation — each is a single atomic call:

| Moment | Command |
|--------|---------|
| Before each step | `python3 "$DASH_CLI" check-control` |
| Step starts | `python3 "$DASH_CLI" begin-step <N>` |
| PR created | `python3 "$DASH_CLI" pr-created <N> <pr_number> <pr_url>` |
| Step done | `python3 "$DASH_CLI" finish-step <N>` |
| Log a message | `python3 "$DASH_CLI" log "<message>"` |
| Error | `python3 "$DASH_CLI" step-error <N> "<message>"` then `shutdown` |
| All done | `python3 "$DASH_CLI" complete` then `shutdown` |

If init fails, skip the dashboard and continue without it — it is not required for implementation.

---

## IMPLEMENTATION LOOP

Loop for each step in the Roadmap. **Run a control check before every sub-step** (see Control Check Protocol).

### Step 1: Pick Next Step

**Control check.** Then select the next step using this **MECHANICAL RULE** — no judgment, no exceptions:

1. Read the roadmap file
2. Find every `### Step N:` header
3. For each step, read its `- **Status**:` field — this is the ONLY field that determines step selection
4. Select the step with the **LOWEST number** whose `**Status**:` is NOT `Complete`
5. Implement THAT step

**DO NOT** skip steps because you think the work was already done outside the roadmap. **DO NOT** look at the description to decide whether it needs work. The `**Status**:` field is the **SOLE source of truth**. If it says `Not Started`, you implement it — period.

**CRITICAL: Always execute steps strictly in order — complete Step N fully (PR merged, issue closed, `finish-step` called) before beginning Step N+1. Never work on two steps at once.** If all steps are complete, proceed to the Completion phase.

**If the step's Type is `Manual`**: Skip it — print a message telling the user that step N is a manual step assigned to them, and move to the next non-complete step. Do not attempt to implement manual steps.

### Step 2: Update Status

**Control check.** Update the step's status to "In Progress" in the Roadmap file. Commit and push this change.

**Dashboard**: `python3 "$DASH_CLI" begin-step <N>`

### Step 3: Plan the Step

**Control check.** Brief implementation plan for this specific step. Use plan mode if the step is complex (M or L complexity).

### Step 4: Create Worktree

**Control check.** Then:

**If `superpowers:using-git-worktrees` skill is available**: Invoke it to create the worktree.

**Otherwise**: Create manually:
```bash
git worktree add ../<repo>-wt/<feature>-step-<N> -b feature/<feature>-step-<N>
```

Work inside the worktree for all implementation.

### Step 5: Implement

**Control check.** Write the code following project conventions:

- Read `CLAUDE.md` files for project-specific guidance
- Make discrete, reasonable commits as work progresses
- Each commit message references the GitHub issue number: `feat: description (#<issue>)`
- Follow existing patterns in the codebase

### Step 6: Build and Verify

**Control check.** Run the build command from the Feature Definition's verification strategy. Fix errors until the build is clean.

### Step 7: Test

**Control check.** Run the test suite from the Feature Definition's verification strategy:

- Write new tests as appropriate for the step's acceptance criteria
- Ensure existing tests still pass
- If the Feature Definition flags this step for manual verification, **pause and ask the user to verify** before proceeding

### Step 8: Create PR

**Control check.** Create a PR with a comprehensive description:

Write the PR body to a temp file, then create the PR:

```bash
cat > /tmp/gh-pr-body.md <<'EOF'
## Summary

<What this PR does>

## Linked Issue

Closes #<issue_number>

## Changes

<Bulleted list of changes>

## Testing

<How this was tested>

## Checklist

- [ ] Build passes
- [ ] Tests pass
- [ ] Follows project conventions
EOF
```

```bash
gh pr create --title "<Step description>" --body-file /tmp/gh-pr-body.md
```

### Step 9: Run Reviews

**Control check.** Read the review guide at `${CLAUDE_SKILL_DIR}/references/review-guide.md`.

Select and run reviews based on what changed in this step:

- **Always**: Code Review + Security Review
- **Conditionally**: Performance, Testing, Accessibility, API Contract, Documentation reviews based on files touched

Delegate to available review skills (`pre-review`, `pr-review-toolkit`, `code-review:code-review`).

### Step 10: Address Review Findings

**Control check.** Fix high and critical issues found by reviews. Re-run relevant reviews to confirm resolution.

### Step 11: Merge PR

**Control check.** Then:

**If `superpowers:finishing-a-development-branch` skill is available**: Invoke it to handle the merge.

**Otherwise**: Merge manually:
```bash
gh pr merge --squash
```

### Step 12: Update Roadmap

**Control check.** In the Roadmap file:
- Mark the step as "Complete"
- Add the PR link
- Update the progress table
- Commit and push the Roadmap update

### Step 13: Close GitHub Issue

**Control check.** Add a summary comment to the GitHub issue and close it:

```bash
gh issue comment <number> --body "Completed in PR #<pr_number>. <Brief summary of what was done.>"
gh issue close <number>
```

### CHECKPOINT GATE — Step Complete

**Dashboard**: `python3 "$DASH_CLI" finish-step <N>` — atomically marks step complete, PR merged, issue closed.

Print the following to the user before starting the next step:

```
Step N complete:
  - PR: #<number> (<url>) — merged
  - Issue: #<number> — closed
  - Roadmap: updated to "Complete"
  - Reviews: <list reviews run and findings>
  Next: Step N+1 — <description>
```

**STOP. Do NOT start the next step until this checkpoint is printed and the user acknowledges.**

### Step 14: Continue or Complete

If more steps remain, return to Step 1. If all steps are complete, proceed to the Completion phase.

### CHECKPOINT GATE — All Steps Done

Before proceeding to completion, verify and report:

- [ ] All Roadmap steps marked "Complete"
- [ ] All GitHub issues closed (list each)
- [ ] All PRs merged (list each)
- [ ] Roadmap progress table shows 100%

Print this checklist to the user. **STOP until acknowledged.**

---

## COMPLETION

> **Goal**: Verify everything is done, document the work, release the lock, and clean up.

### Step 1: Verify All Steps Complete

Read the Roadmap. Confirm:
- All steps are marked "Complete"
- All GitHub issues are closed
- All PRs are merged

### Step 2: Clean Up Worktrees

Remove any remaining worktrees:
```bash
git worktree list
git worktree remove <path>
```

### Step 3: Update Feature Definition

Edit the Feature Definition file:
- Set status to "Complete"
- Add the completion date
- Fill in "Deviations from Plan" — what changed from the original plan and why

### Step 4: Update Project Docs

Update relevant project documentation:
- **README** — if the feature adds user-facing functionality
- **CHANGELOG** — add an entry for this feature
- **API docs** — if new endpoints or interfaces were added
- **Migration guides** — if breaking changes were introduced

Only update docs that are relevant. Don't create docs that don't already exist in the project.

### Step 5: Create Feature Summary

Create `.claude/Features/Completed-Features/<FeatureName>-Summary.md`:

```markdown
# Feature Summary: <FeatureName>

**Completed**: <date>
**Feature Definition**: `.claude/Features/FeatureDefinitions/<FeatureName>-FeatureDefinition.md`

## Architecture Decisions

<Key design choices made during implementation and their rationale>

## Lessons Learned

<What went well, what was harder than expected, what would you do differently>

## Pull Requests

| Step | PR | Description |
|------|-----|-------------|
| 1    | #N  | Description |

## GitHub Issues

| Step | Issue | Description |
|------|-------|-------------|
| 1    | #N    | Description |

## Final State vs. Original Plan

<What changed from the original Feature Definition and why>
```

### Step 6: Archive Roadmap

Update the Roadmap:
- Set `**Status**:` to `Complete`

Move the Roadmap from `Active-Roadmaps/` to `Completed-Roadmaps/`:

```bash
git mv ".claude/Features/Active-Roadmaps/<FeatureName>-FeatureRoadmap.md" ".claude/Features/Completed-Roadmaps/<FeatureName>-FeatureRoadmap.md"
```

### Step 7: Stop Dashboard

```bash
python3 "$DASH_CLI" complete
python3 "$DASH_CLI" shutdown
```

### Step 8: Final Commit and Push

Commit and push all documentation updates:

```
docs: complete feature <FeatureName> — add summary and archive roadmap
```

Report the final status to the user with links to all PRs, issues, and the Feature Summary.

---

## Anti-Patterns

- **Batching steps into one PR** — even if steps seem small or related
- **Skipping reviews** — every PR gets reviewed, every finding gets addressed
- **Implementing without a Roadmap** — always run `/plan-roadmap` first
- **Proceeding past a CHECKPOINT GATE without user acknowledgment**
