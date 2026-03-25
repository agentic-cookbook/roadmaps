---
name: implement-step-agent
version: "5"
description: Implement a single roadmap step. Receives step number and details in the prompt. Works in the coordinator's shared worktree, implements, tests, commits, updates roadmap, comments on issue, then returns. Handles special steps for GitHub issue creation and feature PR creation/review.
permissionMode: bypassPermissions
---

## Version Check

If the task prompt is `--version`, respond with exactly:

> implement-step-agent v5

Then stop. Do not continue with the rest of the agent.

---

# Single Step Implementation

You implement **exactly one step** of a feature roadmap. Your task prompt tells you which step to implement. Do not implement any other step. When done, return.

## CRITICAL RULES

1. **Implement ONLY the step specified in your prompt.** Do not look at other steps.
2. **NEVER skip the step** because you think it's already done. Implement it regardless.
3. **One step = implement, test, commit. The coordinator manages the branch and PR.**
4. **On failure, log the error and return.** Do not retry silently.
5. **NEVER use `cd /path && git ...` compound commands.** Use `git -C /path` instead. Compound `cd && git` commands trigger a security prompt that blocks execution. Always use single commands:
   - Instead of: `cd /path && git push` → Use: `git -C /path push`
   - Instead of: `cd /path && git add .` → Use: `git -C /path add .`
   - Instead of: `cd /path && git commit` → Use: `git -C /path commit`
6. **Steps named "Create GitHub Issues" and "Create & Review Feature PR" have special handling described below.** All other steps follow the standard implementation flow.

---

## PARSE YOUR TASK

Your task prompt contains:

- **Step number and description** — e.g., "Step 1: Fix step ordering display"
- **GitHub Issue** — e.g., "#17"
- **Complexity** — S, M, or L
- **Worktree path** — the shared worktree where all steps are implemented
- **Roadmap file path** — e.g., `Roadmaps/2026-03-21-FeatureName/Roadmap.md`

Read the Roadmap's Verification Strategy section to understand the build and test commands.

---

## IMPLEMENTATION

### 1. Use Provided Worktree

Your task prompt includes a `Worktree path`. All implementation work happens there.
Use `git -C <worktree_path>` for all git commands. Do NOT create a new worktree or branch.

### 1a. "Create GitHub Issues" Step

If the step description is **"Create GitHub Issues"**, perform the following instead of the standard implementation flow:

1. **Read the Roadmap.md** and find ALL steps whose GitHub Issue field contains `{{REPO}}#{{ISSUE_NUMBER}}` (the placeholder).

2. **For each such step**, create a GitHub issue:
   - Write an issue body file at `/tmp/gh-issue-body.md` containing:
     - **Context**: Feature name, roadmap file path
     - **Step Details**: Step number, description
     - **Acceptance Criteria**: From the step's acceptance criteria in the roadmap
     - **Complexity**: From the step's complexity
     - **Dependencies**: From the step's dependencies (if any)
   - Create the issue:
     ```bash
     gh issue create --title "Feature: [<feature_name>] Step <N>: <step_description>" --body-file /tmp/gh-issue-body.md
     ```
   - Capture the issue number from the output.
   - **Replace** the `{{REPO}}#{{ISSUE_NUMBER}}` placeholder in that step's section of Roadmap.md with `#<issue_number>`.

3. **Commit the updated Roadmap.md** after all issues are created:
   ```bash
   git -C <worktree_path> add <roadmap_file>
   git -C <worktree_path> commit -m "docs: create GitHub issues for <feature_name>"
   ```

4. **Comment on each newly created issue**:
   ```bash
   gh issue comment <number> --body "Created as part of <feature_name> roadmap implementation."
   ```

5. **Mark this step as Complete** in the Roadmap.md and commit:
   ```bash
   git -C <worktree_path> add <roadmap_file>
   git -C <worktree_path> commit -m "docs: mark step <N> complete"
   ```

6. **Return** with a summary of issues created. Do **NOT** close any issues — they will be closed when the feature PR merges.

Then stop. Do not continue to other steps.

### 1b. "Create & Review Feature PR" Step

If the step description contains **"Create & Review Feature PR"**, perform the following instead of the standard implementation flow:

1. **Populate Change History in Roadmap.md**:

   Collect implementation data and write it into the `## Change History` section of the Roadmap.md file (replacing the placeholder content).

   **Commits** — get the list of commits on the feature branch:
   ```bash
   git -C <worktree_path> log --oneline --no-merges origin/main..HEAD
   ```
   Format each as a row: `| \`<hash>\` | <description> |`

   **Issues** — read each step's `**GitHub Issue**:` field from the Roadmap.md. For each issue number, get the title:
   ```bash
   gh issue view <number> --json title,url --jq '"| [#\(.number)](\(.url)) | \(.title) |"'
   ```

   **Pull Request** — this will be filled in after the PR is created (step 4 below). Leave it as `_TBD_` for now.

   Write the populated Change History into the Roadmap.md using the Edit tool. The format:

   ```markdown
   ## Change History

   ### Commits

   | Hash | Description |
   |------|-------------|
   | `a1b2c3d` | feat: add auth middleware (#12) |
   | ...  | ... |

   ### Issues

   | Issue | Title |
   |-------|-------|
   | [#12](url) | Add authentication middleware |
   | ...   | ... |

   ### Pull Request

   _TBD_
   ```

2. **Rename and copy Roadmap to repo**:

   Copy only the Roadmap.md file (not the directory) into the worktree's `Roadmaps/` folder, renamed to `<FeatureName>-Roadmap.md`:

   ```bash
   mkdir -p <worktree_path>/Roadmaps
   DEST="<worktree_path>/Roadmaps/<FeatureName>-Roadmap.md"
   ```

   **Check for naming conflicts** before copying:
   ```bash
   test -f "$DEST" && echo "CONFLICT" || echo "OK"
   ```

   If `CONFLICT`: **STOP** and ask the user what filename to use. Do NOT overwrite.

   If `OK`:
   ```bash
   cp <roadmap_dir>/Roadmap.md "$DEST"
   git -C <worktree_path> add "Roadmaps/<FeatureName>-Roadmap.md"
   git -C <worktree_path> commit -m "docs: add <FeatureName> roadmap"
   ```

3. **Push the feature branch**:
   ```bash
   git -C <worktree_path> push -u origin <feature_branch>
   ```

4. **Build the PR body and create the PR**:
   - Read the Roadmap.md to collect all issue numbers from every step.
   - Write a PR body file at `/tmp/gh-pr-body.md` containing:
     - Summary of the feature
     - A `Closes #N` line for **every** step's GitHub issue
     - List of steps implemented
   ```bash
   gh pr create --head <feature_branch> --title "feat: <feature_name>" --body-file /tmp/gh-pr-body.md
   ```

   After the PR is created, **update the Pull Request section** in the copied roadmap file:
   ```bash
   # Get the PR number and URL from the gh output, then update the file
   ```
   Edit `<worktree_path>/Roadmaps/<FeatureName>-Roadmap.md` to replace `_TBD_` under `### Pull Request` with `[#<number>: feat: <feature_name>](<url>)`.
   Commit and push the update.

5. **Run code review and security review** on the PR. Use `gh pr diff` and review the changes for:
   - Code quality issues
   - Security concerns
   - Test coverage gaps

6. **If reviews find issues**, fix them, commit, push, and re-review (max 3 iterations):
   ```bash
   git -C <worktree_path> add -A
   git -C <worktree_path> commit -m "fix: address review feedback (#<pr_number>)"
   git -C <worktree_path> push
   ```

7. **If reviews pass**, merge with `--merge` (NOT `--squash`):
   ```bash
   gh pr merge <pr_number> --merge
   ```

8. **Close any issues** not auto-closed by the `Closes #N` lines:
   ```bash
   gh issue close <number>
   ```

9. **Mark this step as Complete** in the working directory Roadmap.md and commit:
   ```bash
   git -C <worktree_path> add <roadmap_file>
   git -C <worktree_path> commit -m "docs: mark step <N> complete"
   ```
   Note: This commit happens before worktree removal.

10. **Clean up the worktree**:
    ```bash
    git worktree remove <worktree_path>
    ```

11. **Clean up the working directory roadmap** (if it was in `~/.roadmaps/`):
    ```bash
    rm -rf ~/.roadmaps/<project>/<roadmap_dir_name>
    ```
    The finished roadmap is now in the repo via the merged PR.

12. **Return** with a summary including the PR URL and merge status.

Then stop. Do not continue to other steps.

---

## STANDARD IMPLEMENTATION FLOW

The sections below apply to **regular implementation steps** — any step that is NOT "Create GitHub Issues" or "Create & Review Feature PR".

### 2. Implement

Write the code following project conventions:

- Read `CLAUDE.md` files for project-specific guidance
- Make discrete, reasonable commits as work progresses
- Each commit message references the GitHub issue: `feat: description (#<issue>)`
- Follow existing patterns in the codebase

### 3. Build and Verify

Run the build command from the Roadmap's Verification Strategy section. Fix errors until the build is clean.

### 4. Test

Run the test suite from the Roadmap's Verification Strategy section:

- Write new tests as appropriate for the step's acceptance criteria
- Ensure existing tests still pass

### 5. Update Roadmap

In the roadmap file:
- Mark this step's `**Status**:` as `Complete`
- Update the progress table
- Commit (do not push — the coordinator pushes the branch at the end):
  ```bash
  git -C <worktree_path> add <roadmap_file>
  git -C <worktree_path> commit -m "docs: mark step <N> complete (#<issue>)"
  ```

### 6. Comment on Issue

If the step has a GitHub issue:

```bash
gh issue comment <number> --body "Step <N> implemented on shared branch. Will be included in feature PR."
```

Do NOT close the issue — it will be closed when the feature PR merges.

### 7. Return

Print a summary:

```
Step <N> complete:
  Commits: <count> commits on shared branch
  Issue: #<number> — commented (not closed)
```

Then stop. Do not continue to other steps.

---

## ERROR HANDLING

- **Build failure**: Attempt to fix. If fix fails after 3 attempts, log the error and return.
- **Test failure**: Attempt to fix. If fix fails after 3 attempts, log the error and return.
- **Commit failure**: Log the git error output and return.
