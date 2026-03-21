---
name: implement-roadmap
description: "Implement a planned feature from its Roadmap step by step with worktrees, PRs, and reviews. Use after /plan-roadmap has created a Roadmap."
disable-model-invocation: true
---

# Implement Roadmap

Implementation workflow for features that have been planned with `/plan-roadmap`. Picks up a Roadmap from `Active-Roadmaps/` and works through each step with proper isolation, testing, and review.

## CRITICAL RULES

1. **NEVER implement a feature without a Roadmap.** If no Roadmap exists, tell the user to run `/plan-roadmap` first.
2. **NEVER combine steps.** Each Roadmap step gets its own worktree, its own PR, its own review cycle, and its own merge. No exceptions.
3. **NEVER skip reviews.** Every PR gets at minimum a code review and security review before merge.
4. **NEVER implement a feature that is already being implemented.** If the Roadmap's `Implementing` field is `Yes`, another session is working on it — refuse and tell the user.
5. **At every step completion, print a checkpoint summary** to the user showing what was completed and what comes next. Do not proceed without user acknowledgment.
6. **ALWAYS acquire the lock before writing code and release it when done.** The `Implementing` field is the concurrency lock.

---

## STARTUP: Select a Feature to Implement

### Step 0: Start Progress Dashboard

**This is the very first thing you do.** Before scanning roadmaps or prompting the user, start the dashboard so progress is visible from the beginning.

Locate the `dash` CLI:

```bash
DASH_CLI="$(find -L ~/.claude/skills -path '*/progress-dashboard/references/dash' 2>/dev/null | head -1)"
```

You will initialize the dashboard after the user selects a feature (since you need the feature name and step names). For now, just confirm `DASH_CLI` is available. If not found, log it and continue without the dashboard.

### Step 1: Scan Active Roadmaps

Read all files in `.claude/Features/Active-Roadmaps/`. For each `*-FeatureRoadmap.md` file, parse:

- The feature name (from `# Feature Roadmap: <name>`)
- The `**Status**:` field
- The `**Implementing**:` field
- The `**Phase**:` field (if present — `Planning` or `Ready`)
- The progress table (how many steps complete vs total)

### Step 2: Build Available Features List

Categorize each roadmap:

- **Available**: `Implementing` is `No` AND `Status` is not `Complete` AND `Phase` is `Ready` (or `Phase` field is absent for backward compatibility)
- **Not Ready (Still Planning)**: `Phase` is `Planning` — this feature is still being defined by `/plan-roadmap` and is not available for implementation
- **Locked**: `Implementing` is `Yes` (another session is working on it)
- **Complete**: `Status` is `Complete` (nothing left to do)

If no features are available:
- If there are "Not Ready" features, list them and explain: "The following features are still in the planning phase and not yet available for implementation. Run `/plan-roadmap` to complete their planning."
- If there are locked features, tell the user which features are currently being implemented and suggest waiting or checking on the other session
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

Currently locked (being implemented by another session):
- FeatureC — 2/4 steps complete

Which feature would you like to implement? (enter number)
```

Wait for the user to choose.

### Step 4: Acquire Lock

Once the user selects a feature:

1. **Re-read the roadmap file** to check `Implementing` is still `No` (race condition guard)
2. If it's `Yes`, the feature is locked by another session. Ask the user:

```
Feature <FeatureName> is currently locked (Implementing: Yes).
This usually means another session is working on it, or a previous session crashed without releasing the lock.

  [u] Unlock and continue — release the stale lock and start implementing
  [q] Quit — leave the lock in place and exit

(u/q)
```

**Wait for the user to respond.**

- If `u`: continue to step 3 below (set `Implementing: Yes` is already set, just proceed)
- If `q`: **STOP**

3. If `Implementing` is `No` (or user chose to unlock), update the roadmap:
   - Set `**Implementing**:` to `Yes`
   - Commit and push this change: `chore: acquire implementation lock for <FeatureName>`

The lock is now held. **All code below runs under this lock.**

### Step 5: Initialize Progress Dashboard

If `DASH_CLI` was found in Step 0, initialize the dashboard now that you have the feature name and step names:

```bash
python3 "$DASH_CLI" init "<FeatureName>" "Step 1: <name>" "Step 2: <name>" ...
```

This creates the temp directory, starts the server, and opens the browser. The `dash` CLI manages all state internally — no shell variables to track between calls.

After init, populate the Issues panel from the Roadmap:

```bash
python3 "$DASH_CLI" add-issue <number> "<Step title>" "https://github.com/<owner>/<repo>/issues/<number>"
```

Do this for every step's GitHub issue so the Issues panel is populated from the start.

**Dashboard**: `python3 "$DASH_CLI" event "Implementation lock acquired"`

Use `dash` commands throughout implementation to update the dashboard. Key commands for issues and PRs:

```bash
# When a step starts
python3 "$DASH_CLI" update-issue <issue_number> in_progress

# When a PR is created
python3 "$DASH_CLI" add-pr <pr_number> "<title>" "<pr_url>"

# When a PR is merged
python3 "$DASH_CLI" update-pr <pr_number> merged

# When an issue is closed
python3 "$DASH_CLI" update-issue <issue_number> closed
```

If init fails, skip the dashboard and continue without it — it is not required for implementation.

---

## IMPLEMENTATION LOOP

Loop for each step in the Roadmap.

**Before each step**, if the dashboard is running, check for user controls:

```bash
python3 "$DASH_CLI" check-control
```

- If output is `pause` — tell the user the dashboard pause button was pressed and wait for them to say to continue (or re-run `check-control` until it returns `resume` or `stop`).
- If output is `stop` — finish the current atomic operation, release the lock, run `python3 "$DASH_CLI" error "Stopped by user"` then `python3 "$DASH_CLI" shutdown`, and **STOP**.
- If output is `none` or `resume` — continue normally.

### Step 1: Pick Next Step

Read the Roadmap file. Find the next step with status "Not Started". If all steps are complete, proceed to the Completion phase.

### Step 2: Update Status

Update the step's status to "In Progress" in the Roadmap file. Commit and push this change.

**Dashboard**: `python3 "$DASH_CLI" step-start <N>`

### Step 3: Plan the Step

Brief implementation plan for this specific step. Use plan mode if the step is complex (M or L complexity).

### Step 4: Create Worktree

**If `superpowers:using-git-worktrees` skill is available**: Invoke it to create the worktree.

**Otherwise**: Create manually:
```bash
git worktree add ../<repo>-wt/<feature>-step-<N> -b feature/<feature>-step-<N>
```

Work inside the worktree for all implementation.

### Step 5: Implement

Write the code following project conventions:

- Read `CLAUDE.md` files for project-specific guidance
- Make discrete, reasonable commits as work progresses
- Each commit message references the GitHub issue number: `feat: description (#<issue>)`
- Follow existing patterns in the codebase

### Step 6: Build and Verify

Run the build command from the Feature Definition's verification strategy. Fix errors until the build is clean.

### Step 7: Test

Run the test suite from the Feature Definition's verification strategy:

- Write new tests as appropriate for the step's acceptance criteria
- Ensure existing tests still pass
- If the Feature Definition flags this step for manual verification, **pause and ask the user to verify** before proceeding

### Step 8: Create PR

Create a PR with a comprehensive description:

```bash
gh pr create --title "<Step description>" --body "$(cat <<'EOF'
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
)"
```

### Step 9: Run Reviews

Read the review guide at `${CLAUDE_SKILL_DIR}/references/review-guide.md`.

Select and run reviews based on what changed in this step:

- **Always**: Code Review + Security Review
- **Conditionally**: Performance, Testing, Accessibility, API Contract, Documentation reviews based on files touched

Delegate to available review skills (`pre-review`, `pr-review-toolkit`, `code-review:code-review`).

### Step 10: Address Review Findings

Fix high and critical issues found by reviews. Re-run relevant reviews to confirm resolution.

### Step 11: Merge PR

**If `superpowers:finishing-a-development-branch` skill is available**: Invoke it to handle the merge.

**Otherwise**: Merge manually:
```bash
gh pr merge --squash
```

### Step 12: Update Roadmap

In the Roadmap file:
- Mark the step as "Complete"
- Add the PR link
- Update the progress table
- Commit and push the Roadmap update

### Step 13: Close GitHub Issue

Add a summary comment to the GitHub issue and close it:

```bash
gh issue comment <number> --body "Completed in PR #<pr_number>. <Brief summary of what was done.>"
gh issue close <number>
```

### CHECKPOINT GATE — Step Complete

**Dashboard**:
```bash
python3 "$DASH_CLI" step-link <N> "PR #<number>" "<pr_url>"
python3 "$DASH_CLI" step-link <N> "Issue #<number>" "<issue_url>"
python3 "$DASH_CLI" step-complete <N>
```

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

### Step 6: Release Lock and Archive Roadmap

Update the Roadmap:
- Set `**Implementing**:` to `No`
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

## LOCK MANAGEMENT

The `**Implementing**:` field in the Roadmap serves as a concurrency lock:

| State | Meaning |
|-------|---------|
| `No` | Available for implementation |
| `Yes` | Another session is actively implementing this feature |

### Lock Rules

- **Acquire** at startup (Step 4) after user selects a feature
- **Release** at completion (Step 6) or if the user aborts (`/implement-roadmap abort`)
- **Never break** another session's lock without explicit user confirmation
- If a lock appears stale (e.g., user says the other session crashed), the user can manually edit the Roadmap to set `Implementing` to `No`, then re-run `/implement-roadmap`

### Abnormal Termination

If the session ends without reaching Completion (crash, user closes terminal, etc.):
- The lock remains in the Roadmap (`Implementing: Yes`)
- The next session that runs `/implement-roadmap` will see the feature as locked
- The user can manually release the lock by editing the Roadmap file
- Partially completed steps should be visible from the Roadmap's step statuses

---

## Anti-Patterns

- **Batching steps into one PR** — even if steps seem small or related
- **Skipping reviews** — every PR gets reviewed, every finding gets addressed
- **Implementing without a Roadmap** — always run `/plan-roadmap` first
- **Ignoring the lock** — if `Implementing` is `Yes`, do not proceed
- **Proceeding past a CHECKPOINT GATE without user acknowledgment**
- **Forgetting to release the lock** — always update `Implementing` to `No` on completion
