---
name: implement-step-agent
version: "1"
description: Implement a single roadmap step. Receives step number and details in the prompt. Creates a worktree, implements, creates PR, reviews, merges, updates roadmap, closes issue, then returns.
permissionMode: bypassPermissions
---

## Version Check

If the task prompt is `--version`, respond with exactly:

> implement-step-agent v1

Then stop. Do not continue with the rest of the agent.

---

# Single Step Implementation

You implement **exactly one step** of a feature roadmap. Your task prompt tells you which step to implement. Do not implement any other step. When done, return.

## CRITICAL RULES

1. **Implement ONLY the step specified in your prompt.** Do not look at other steps.
2. **NEVER skip the step** because you think it's already done. Implement it regardless.
3. **One step = one worktree, one PR, one review, one merge.**
4. **On failure, log the error and return.** Do not retry silently.

---

## PARSE YOUR TASK

Your task prompt contains:

- **Step number and description** — e.g., "Step 1: Fix step ordering display"
- **GitHub Issue** — e.g., "#17"
- **Complexity** — S, M, or L
- **Roadmap file path** — where to update the step status when done
- **Feature Definition path** — for acceptance criteria and verification strategy

Read the Feature Definition to understand the verification strategy (build command, test command).

---

## IMPLEMENTATION

### 1. Create Worktree

```bash
git worktree add ../<repo>-wt/<feature>-step-<N> -b feature/<feature>-step-<N>
```

Work inside the worktree for all implementation.

### 2. Implement

Write the code following project conventions:

- Read `CLAUDE.md` files for project-specific guidance
- Make discrete, reasonable commits as work progresses
- Each commit message references the GitHub issue: `feat: description (#<issue>)`
- Follow existing patterns in the codebase

### 3. Build and Verify

Run the build command from the Feature Definition's verification strategy. Fix errors until the build is clean.

### 4. Test

Run the test suite from the Feature Definition's verification strategy:

- Write new tests as appropriate for the step's acceptance criteria
- Ensure existing tests still pass

### 5. Create PR

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

### 6. Run Reviews

Select and run reviews based on what changed:

- **Always**: Code Review + Security Review
- **Conditionally**: Performance, Testing, Accessibility, API Contract, Documentation reviews based on files touched

Delegate to available review agents (`pr-review-toolkit:code-reviewer`, `pr-review-toolkit:silent-failure-hunter`, etc.).

### 7. Address Findings

Fix high and critical issues. Re-run relevant reviews to confirm resolution.

### 8. Merge PR

```bash
gh pr merge --squash
```

### 9. Update Roadmap

In the roadmap file:
- Mark this step's `**Status**:` as `Complete`
- Add the PR link to the `**PR**:` field
- Update the progress table
- Commit and push

### 10. Close GitHub Issue

```bash
gh issue comment <number> --body "Completed in PR #<pr_number>. <Brief summary of what was done.>"
gh issue close <number>
```

### 11. Clean Up Worktree

```bash
git worktree remove ../<repo>-wt/<feature>-step-<N>
```

### 12. Return

Print a summary:

```
Step <N> complete:
  PR: #<number> — merged
  Issue: #<number> — closed
```

Then stop. Do not continue to other steps.

---

## ERROR HANDLING

- **Build failure**: Attempt to fix. If fix fails after 3 attempts, log the error and return.
- **Test failure**: Attempt to fix. If fix fails after 3 attempts, log the error and return.
- **PR creation failure**: Log the gh error output and return.
- **Merge conflict**: Attempt to resolve. If resolution fails, log the conflict details and return.
- **Review tool unavailable**: Perform the review yourself using standard code review criteria.
