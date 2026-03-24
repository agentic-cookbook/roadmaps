# Atomic Batch PR Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Change implement-roadmap so all steps commit to a single shared branch and produce one PR at the end, instead of one PR per step.

**Architecture:** The implement-step-agent stops creating worktrees, branches, and PRs. Instead, the coordinator (SKILL.md) creates a single feature branch + worktree before the loop, passes it to each worker, and creates one PR after all steps complete. The dashboard UI shifts from per-step PRs to a single roadmap-level PR.

**Tech Stack:** Markdown (skill/agent files), HTML/JS (dashboard UI), Python (models/API)

---

### Task 1: Update implement-step-agent to work on a shared branch

**Files:**
- Modify: `agents/implement-step-agent.md`

The agent currently owns the full lifecycle: create worktree → implement → create PR → merge → clean up. We need to strip it down to: implement → commit → return. The worktree and branch are provided by the coordinator.

- [ ] **Step 1: Remove worktree creation from agent**

Replace section "### 1. Create Worktree" with instructions to use the worktree path provided in the prompt. The agent no longer creates branches or worktrees.

In `agents/implement-step-agent.md`, replace the worktree section with:

```markdown
### 1. Use Provided Worktree

Your task prompt includes a `Worktree path`. All implementation work happens there.
Use `git -C <worktree_path>` for all git commands. Do NOT create a new worktree or branch.
```

- [ ] **Step 2: Remove PR creation, merge, and issue close sections**

Remove sections 5 (Create PR), 6 (Run Reviews), 7 (Address Findings), 8 (Merge PR), 10 (Close GitHub Issue), and 11 (Clean Up Worktree).

The agent should end after updating the roadmap (section 9). Renumber remaining sections.

- [ ] **Step 3: Update critical rules**

Change rule 3 from "One step = one worktree, one PR, one review, one merge" to "One step = implement, test, commit. The coordinator manages the branch and PR."

- [ ] **Step 4: Update the return section**

The agent should return a summary like:

```
Step <N> complete:
  Commits: <count> commits on shared branch
  Issue: #<number> — commented (not closed)
```

Remove the PR reference from the return output.

- [ ] **Step 5: Add issue comment without closing**

Replace the "Close GitHub Issue" section with a simpler "Comment on Issue" section that comments on the issue noting the step is implemented but does NOT close it (the PR will close it on merge via `Closes #N` in the PR body).

```markdown
### 7. Comment on Issue

If the step has a GitHub issue:

\```bash
gh issue comment <number> --body "Step <N> implemented on shared branch. Will be included in feature PR."
\```

Do NOT close the issue — it will be closed when the feature PR merges.
```

- [ ] **Step 6: Bump version to 4**

Change `version: "3"` to `version: "4"` in the frontmatter.

- [ ] **Step 7: Commit**

```bash
git -C ../cat-herding-wt/atomic-batch-pr add agents/implement-step-agent.md
git -C ../cat-herding-wt/atomic-batch-pr commit -m "feat: strip implement-step-agent to shared-branch worker (v4)"
```

---

### Task 2: Update implement-roadmap SKILL.md for single branch + PR

**Files:**
- Modify: `skills/implement-roadmap/SKILL.md`

The coordinator now creates a single worktree + branch before the loop, passes it to each worker, and creates one PR after all steps finish.

- [ ] **Step 1: Add new Step 2.5 — Create Feature Branch and Worktree**

After the dashboard init (Step 2) and before the implementation loop (Step 3), add a new section that creates a single feature branch and worktree:

```markdown
## Step 2b: Create Feature Branch and Worktree

Create a single feature branch and worktree for all steps:

\```bash
FEATURE_BRANCH="feature/<feature_name>"
WORKTREE_PATH="../$(basename $(pwd))-wt/<feature_name>"
git worktree add "$WORKTREE_PATH" -b "$FEATURE_BRANCH"
\```

Print: `Working on branch: $FEATURE_BRANCH`

All steps will commit to this single branch. One PR will be created at the end.
```

- [ ] **Step 2: Update worker agent prompt in Step 3d**

Add the worktree path to the prompt template so the worker knows where to work:

```
Implement step <N> of the <feature_name> feature.

Step <N>: <description>
GitHub Issue: <issue>
Complexity: <complexity>
Roadmap file: <roadmap_path>
Feature Definition: <roadmap_dir>/Definition.md
Worktree path: <worktree_path>

Implement ONLY this step. Commit your changes to the existing branch.
When done, update the roadmap to mark this step Complete, then return.
Do not implement any other step.
```

- [ ] **Step 3: Update completion sequence — create PR instead of just committing**

Replace the current completion sequence (which just writes State/History files and commits) with one that:

1. Writes State and History files (same as before)
2. Commits them to the feature branch
3. Pushes the feature branch
4. Creates a single PR with all step descriptions in the body
5. Runs reviews on the PR
6. Merges the PR (with `--merge` not `--squash` to preserve commits)
7. Cleans up the worktree
8. Closes all linked GitHub issues

```markdown
**Create Feature PR:**

Build the PR body listing all steps:

\```bash
cat > /tmp/gh-pr-body.md <<'EOF'
## Summary

Implements the <feature_name> feature — all steps in a single atomic PR.

## Steps Included

<For each completed step, add: - Step N: description (Closes #issue)>

## Changes

<Bulleted list of key changes across all steps>

## Testing

All steps verified against the feature definition's verification strategy.

## Checklist

- [ ] Build passes
- [ ] Tests pass
- [ ] Follows project conventions
EOF
\```

\```bash
git -C "$WORKTREE_PATH" push -u origin "$FEATURE_BRANCH"
gh pr create --repo <repo> --head "$FEATURE_BRANCH" --title "feat: <feature_name>" --body-file /tmp/gh-pr-body.md
\```

**Run Reviews** on the PR (Code Review + Security Review, plus conditional reviews).

**Merge PR:**

\```bash
gh pr merge --merge
\```

This preserves individual step commits in the history.

**Close Issues:**

For each step that had a GitHub issue:
\```bash
gh issue close <number> --comment "Completed in PR #<pr_number>"
\```

**Clean Up Worktree:**

\```bash
git worktree remove "$WORKTREE_PATH"
\```
```

- [ ] **Step 4: Bump version to 14**

Change `version: "13"` to `version: "14"` in the frontmatter.

- [ ] **Step 5: Commit**

```bash
git -C ../cat-herding-wt/atomic-batch-pr add skills/implement-roadmap/SKILL.md
git -C ../cat-herding-wt/atomic-batch-pr commit -m "feat: implement-roadmap creates single branch + PR for all steps (v14)"
```

---

### Task 3: Update dashboard detail page — single PR display

**Files:**
- Modify: `services/dashboard/static/dashboard.html`

The detail page currently shows per-step PR links and a PR panel listing multiple PRs. With the new model, there's one PR for the whole roadmap. Update the UI accordingly.

- [ ] **Step 1: Update step rendering to remove per-step PR links**

In `dashboard.html` around line 831-837, remove the block that renders `step.pr_number` as a link on each step. Steps no longer have individual PRs.

Remove this block:
```javascript
// Always show PR link if present
if (step.pr_number) {
  var prText = 'PR #' + step.pr_number;
  if (step.pr_title) prText += ': ' + step.pr_title;
  var prLink = el('a', { href: step.pr_url || '#', textContent: prText });
  bodyChildren.push(el('div', { className: 'step-detail' }, [prLink]));
}
```

- [ ] **Step 2: Update the PRs panel to show a single "Feature PR"**

The PRs panel (rendered by `renderTickets` at line 1098) will now typically show one PR. No code change needed in `renderTickets` itself — it already handles a list of any size. The label is already "PRs" which is fine.

Verify this works by reading the render function — no changes needed if the panel already handles 0-1 items gracefully. Skip this step if confirmed.

- [ ] **Step 3: Bump dashboard version**

Update the version string in the footer from `v6` to `v7`:

```javascript
footerEl.textContent = 'Dashboard Service v7';
```

Find and update all version references in dashboard.html.

- [ ] **Step 4: Commit**

```bash
git -C ../cat-herding-wt/atomic-batch-pr add services/dashboard/static/dashboard.html
git -C ../cat-herding-wt/atomic-batch-pr commit -m "feat: remove per-step PR links from dashboard detail page (dashboard v7)"
```

---

### Task 4: Update overview page — show single PR on cards

**Files:**
- Modify: `services/dashboard/static/overview.html`

The overview cards don't currently show PR info prominently, but the data model changes. The overview already fetches `prs` in the detail response. No card-level change is needed unless we want to show the feature PR link on the card.

- [ ] **Step 1: Add PR link to card footer when available**

In the `renderRoadmaps` function, after the progress text, add a PR link if the roadmap has exactly one PR:

```javascript
if (r.prs && r.prs.length > 0) {
  var pr = r.prs[0];
  var prLink = el('a', {
    href: pr.url || '#',
    className: 'card-pr-link',
    onclick: function(ev) { ev.stopPropagation(); }
  }, 'PR #' + pr.number);
  footerRightItems.push(prLink);
}
```

Add CSS for `.card-pr-link`:

```css
.card-pr-link {
  font-size: 0.75rem; color: var(--accent); text-decoration: none;
}
.card-pr-link:hover { text-decoration: underline; }
```

- [ ] **Step 2: Bump overview version**

Update `Dashboard Service v16` to `v17` in the footer.

- [ ] **Step 3: Commit**

```bash
git -C ../cat-herding-wt/atomic-batch-pr add services/dashboard/static/overview.html
git -C ../cat-herding-wt/atomic-batch-pr commit -m "feat: show feature PR link on overview cards (overview v17)"
```

---

### Task 5: Verify and test

- [ ] **Step 1: Read all modified files end-to-end**

Read through the final state of all four modified files to verify consistency:
- `agents/implement-step-agent.md`
- `skills/implement-roadmap/SKILL.md`
- `services/dashboard/static/dashboard.html`
- `services/dashboard/static/overview.html`

- [ ] **Step 2: Verify no references to `--squash` remain**

```bash
grep -r "squash" agents/implement-step-agent.md skills/implement-roadmap/SKILL.md
```

Expected: no matches.

- [ ] **Step 3: Verify the agent no longer creates worktrees**

```bash
grep -r "worktree add" agents/implement-step-agent.md
```

Expected: no matches.

- [ ] **Step 4: Verify the skill creates exactly one worktree**

```bash
grep -c "worktree add" skills/implement-roadmap/SKILL.md
```

Expected: 1.

- [ ] **Step 5: Run the dashboard tests if they exist**

```bash
cd ../cat-herding-wt/atomic-batch-pr && python3 -m pytest tests/ -v 2>&1 | tail -20
```

Review output for any failures related to our changes.
