---
name: implement-roadmap
version: "14"
description: "Implement a planned feature from its Roadmap. Uses a deterministic Python coordinator for step selection and the Agent tool to launch a worker for each step. Use after /plan-roadmap or /plan-bugfix-roadmap has created a Roadmap."
disable-model-invocation: true
---

## Version Check

If `$ARGUMENTS` is `--version`:

1. Print the skill version:
   > implement-roadmap v14

2. Print the worker agent version by running:
   ```bash
   grep -m1 'version:' ~/.claude/agents/implement-step-agent.md
   ```
   Format the output as:
   > implement-step-agent v{version}

Then stop. Do not continue with the rest of the skill.

---

# Implement Roadmap

Uses a deterministic Python script for step selection (no LLM judgment) and the Agent tool to launch a worker agent for each step.

**Do NOT modify the coordinator script, the worker agent, or any skill files.** If something fails, report the error.

## Step 1: Resolve Roadmap

Run the coordinator to find the roadmap:

```bash
python3 "${CLAUDE_SKILL_DIR}/references/coordinator" resolve $ARGUMENTS
```

This outputs JSON. Parse it:
- If it has `"path"` — use that roadmap. Print: `Implementing: <name> (<complete>/<total> steps complete)`
- If it has `"choose"` — present the list to the user and ask them to pick. Then use the chosen path.
- If it has `"error"` — print the error and **STOP**.

## Step 2: Start Dashboard

```bash
DASH_CLI="$HOME/.claude/skills/progress-dashboard/references/dash"
export DASH_FEATURE="<feature_name>"
test -f "$DASH_CLI" && python3 "$DASH_CLI" init "<feature_name>" && python3 "$DASH_CLI" load-roadmap "<roadmap_path>" || echo "Dashboard not available"
```

**IMPORTANT**: Always set `export DASH_FEATURE="<feature_name>"` before ANY `dash` command. This ensures concurrent sessions don't interfere with each other. The `DASH_FEATURE` must be set in the shell so all subsequent `python3 "$DASH_CLI" ...` calls inherit it.

## Step 2b: Create Feature Branch and Worktree

Create a single feature branch and worktree for all steps:

```bash
FEATURE_BRANCH="feature/<feature_name>"
WORKTREE_PATH="../$(basename $(pwd))-wt/<feature_name>"
git worktree add "$WORKTREE_PATH" -b "$FEATURE_BRANCH"
```

Print: `Working on branch: $FEATURE_BRANCH`

All steps will commit to this single branch. One PR will be created at the end.

## Step 3: Implementation Loop

This is a loop. Repeat until done:

### 3a: Get Next Step

Run the coordinator to find the next step:

```bash
python3 "${CLAUDE_SKILL_DIR}/references/coordinator" next-step "<roadmap_path>"
```

This outputs JSON. Parse it:

- If `"action": "implement"` — continue with 3b.
- If there are `"manual_skipped"` entries, print them once: `Skipping manual step N: <description>`
- If `"action": "done"` — all steps are complete. **Run the completion sequence immediately:**

  **1. Write State and History files (inside the worktree):**

  Derive the roadmap directory from `<roadmap_path>` (its parent directory). Then:

  ```bash
  ROADMAP_DIR="$(dirname "<roadmap_path>")"
  TODAY="$(date +%Y-%m-%d)"
  NOW="$(date +%Y-%m-%d-%H%M%S)"
  AUTHOR="$(git config user.name) <$(git config user.email)>"

  # Write Complete state file
  cat > "$ROADMAP_DIR/State/$TODAY-Complete.md" << STATEEOF
  ---
  id: $(python3 -c "import uuid; print(uuid.uuid4())")
  created: $TODAY
  author: $AUTHOR
  definition-id: $(grep '^definition-id:' "$ROADMAP_DIR/Roadmap.md" | head -1 | sed 's/definition-id: //')
  previous-state: Implementing
  ---

  # State: Complete

  All auto steps finished.
  STATEEOF

  # Write History entry
  cat > "$ROADMAP_DIR/History/$NOW-ImplementationComplete.md" << HISTEOF
  ---
  id: $(python3 -c "import uuid; print(uuid.uuid4())")
  created: $TODAY
  author: $AUTHOR
  definition-id: $(grep '^definition-id:' "$ROADMAP_DIR/Roadmap.md" | head -1 | sed 's/definition-id: //')
  ---

  # Event: ImplementationComplete

  All auto steps finished for <feature_name>.
  HISTEOF
  ```

  **2. Commit State/History to the feature branch:**
  ```bash
  git -C "$WORKTREE_PATH" add -A Roadmaps/
  git -C "$WORKTREE_PATH" commit -m "docs: complete feature <feature_name> — all steps done"
  ```

  **3. Push the feature branch and create a PR:**

  Build the PR body dynamically. For each step that had a GitHub issue, include `Closes #<issue_number>`.

  ```bash
  git -C "$WORKTREE_PATH" push -u origin "$FEATURE_BRANCH"
  gh pr create --head "$FEATURE_BRANCH" --title "feat: <feature_name>" --body-file /tmp/gh-pr-body.md
  ```

  The PR body file (`/tmp/gh-pr-body.md`) should contain:
  - A summary line: `Implements the <feature_name> feature.`
  - A section listing all steps: `## Steps` with each step as a checkbox line
  - A blank line, then `Closes #<issue>` for every step that had a GitHub issue (each on its own line)

  **4. Run reviews on the PR:**

  Always run:
  - Code Review (use `/review-pr`)
  - Security Review (use `/security-review`)

  Run conditionally based on what changed:
  - UI Review if HTML/CSS/JS changed
  - API Review if API endpoints changed

  Fix any issues found by reviews, committing fixes to the feature branch.

  **5. Merge the PR:**
  ```bash
  gh pr merge --merge
  ```

  Use `--merge` (NOT `--squash`) to preserve individual step commits.

  **6. Close any issues not auto-closed:**

  If any step issues were not closed by the `Closes #N` lines (e.g., if merge didn't trigger auto-close), close them manually with `gh issue close`.

  **7. Clean up the worktree:**
  ```bash
  git worktree remove "$WORKTREE_PATH"
  ```

  **8. Dashboard complete and shutdown:**
  ```bash
  python3 "$DASH_CLI" complete
  python3 "$DASH_CLI" shutdown
  ```

  Print: `All steps complete for <feature_name>.`
  Then **STOP**.

### 3b: Print Step Info

Print:
```
Step <N>: <description>
  Issue: <issue>  |  Complexity: <complexity>
```

### 3c: Update Dashboard

```bash
python3 "$DASH_CLI" begin-step <N>
```

### 3d: Launch Worker Agent

Use the **Agent tool** (NOT subprocess, NOT `claude --agent`):

- **subagent_type**: `implement-step-agent`
- **prompt**: The exact text below, with values filled in:

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

### 3e: After Worker Returns

Update dashboard:
```bash
python3 "$DASH_CLI" finish-step <N>
```

Print: `Step <N> complete.`

Then **go back to 3a** to get the next step.

