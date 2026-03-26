---
name: implement-roadmap
version: "25"
description: "Implement a planned feature from its Roadmap. Uses a deterministic Python coordinator for step selection and the Agent tool to launch a worker for each step. Use after /plan-roadmap or /plan-bugfix-roadmap has created a Roadmap."
disable-model-invocation: true
---

## Version Check

If `$ARGUMENTS` is `--version`:

1. Print the skill version:
   > implement-roadmap v25

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

## Preflight: Dashboard Server Check

Verify the dashboard server is running. If not, start it automatically.

```bash
DASH_URL="${DASHBOARD_URL:-http://localhost:8888}"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$DASH_URL/" 2>/dev/null || echo "000")
```

- If `HTTP_STATUS` is `200` — the server is running. Print: `Dashboard server OK ($DASH_URL)` and continue.
- If `HTTP_STATUS` is anything else — start the server:
  ```bash
  bash "$HOME/.claude/services/dashboard/server.sh" start
  ```
  Wait up to 5 seconds for it to accept connections, then re-check:
  ```bash
  HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$DASH_URL/" 2>/dev/null || echo "000")
  ```
  If still not `200`, **STOP** and tell the user: `ERROR: Could not start dashboard server (HTTP $HTTP_STATUS at $DASH_URL/).`

## Step 1: Resolve Roadmap

The coordinator scans both `~/.roadmaps/<project>/` (created by plan-roadmap) and the repo's `Roadmaps/` directory. It filters by the `project` frontmatter field to only show roadmaps belonging to the current repo.

```bash
PROJECT=$(basename $(git rev-parse --show-toplevel))
python3 "${CLAUDE_SKILL_DIR}/references/coordinator" resolve $ARGUMENTS
```

This outputs JSON. Parse it:
- If it has `"path"` — use that roadmap. Print: `Implementing: <name> (<complete>/<total> steps complete)`
- If it has `"choose"` — present the list to the user and ask them to pick. Then use the chosen path.
- If it has `"error"` — print the error and **STOP**.

Note whether the resolved roadmap path is under `~/.roadmaps/` or `Roadmaps/`. Store as `ROADMAP_SOURCE=workdir` or `ROADMAP_SOURCE=repo`. The PR step needs this.

## Step 1a: Initialize Implementation Log

Create the implementation log in the roadmap's working directory:

```bash
ROADMAP_DIR="$(dirname "<roadmap_path>")"
IMPL_LOG="$ROADMAP_DIR/implementation.log"
```

Write the initial entry:
```
[YYYY-MM-DD HH:MM:SS] IMPLEMENTATION_START: <feature_name>
[YYYY-MM-DD HH:MM:SS] PROJECT: $PROJECT
[YYYY-MM-DD HH:MM:SS] ROADMAP: <roadmap_path>
[YYYY-MM-DD HH:MM:SS] SOURCE: $ROADMAP_SOURCE
```

**Throughout this skill, append to `$IMPL_LOG` before every significant action** using the format:
- `[timestamp] DASHBOARD: server at <url>`
- `[timestamp] WORKTREE: created at <path>`
- `[timestamp] ROADMAP_COPIED: from <source> to <dest>`
- `[timestamp] STEP_BEGIN: Step <N> — <description>`
- `[timestamp] STEP_SKIP_MANUAL: Step <N> — <description>`
- `[timestamp] STEP_COMPLETE: Step <N>`
- `[timestamp] STEP_FAILED: Step <N> — <reason>`
- `[timestamp] PR_CREATED: #<number> (draft)`
- `[timestamp] PR_READY: #<number>`
- `[timestamp] PR_MERGED: #<number>`
- `[timestamp] IMPLEMENTATION_COMPLETE: <feature_name>`

## Step 1b: Mark Roadmap as Implementing

Write an Implementing state file so other sessions won't try to start this roadmap:

```bash
ROADMAP_DIR="$(dirname "<roadmap_path>")"
TODAY="$(date +%Y-%m-%d)"
printf -- '---\nevent: implementing\ndate: %s\n---\n' "$TODAY" > "$ROADMAP_DIR/State/$TODAY-Implementing.md"
```

If `ROADMAP_SOURCE=repo`, commit and push the state change:
```bash
git -C "$(dirname "$ROADMAP_DIR")" add -A Roadmaps/ && git -C "$(dirname "$ROADMAP_DIR")" commit -m "state: mark <feature_name> as Implementing" && git -C "$(dirname "$ROADMAP_DIR")" push
```

If `ROADMAP_SOURCE=workdir`, the state file is already in `~/.roadmaps/` — no git commit needed.

## Step 2: Start Dashboard

```bash
DASH_CLI="$HOME/.claude/skills/progress-dashboard/references/dash"
export DASH_FEATURE="<feature_name>"
test -f "$DASH_CLI" && python3 "$DASH_CLI" init "<feature_name>" && python3 "$DASH_CLI" load-roadmap "<roadmap_path>" || echo "Dashboard not available"
```

**IMPORTANT**: Always set `export DASH_FEATURE="<feature_name>"` before ANY `dash` command. This ensures concurrent sessions don't interfere with each other. The `DASH_FEATURE` must be set in the shell so all subsequent `python3 "$DASH_CLI" ...` calls inherit it.

## Step 2a: Check for Previous Implementation Artifacts

Before creating a new branch, check if a previous implementation left behind artifacts:

```bash
FEATURE_BRANCH="feature/<feature_name>"
WORKTREE_PATH="../$(basename $(pwd))-wt/<feature_name>"
```

**Check for existing worktree:**
```bash
git worktree list | grep "$WORKTREE_PATH" && echo "WORKTREE_EXISTS" || echo "NO_WORKTREE"
```

**Check for existing local branch:**
```bash
git branch --list "$FEATURE_BRANCH" | grep -q . && echo "LOCAL_BRANCH" || echo "NO_LOCAL_BRANCH"
```

**Check for existing remote branch:**
```bash
git ls-remote --heads origin "$FEATURE_BRANCH" | grep -q . && echo "REMOTE_BRANCH" || echo "NO_REMOTE_BRANCH"
```

**Check for existing PR:**
```bash
gh pr list --head "$FEATURE_BRANCH" --state all --json number,title,state,url --jq '.[0]' 2>/dev/null || echo "NO_PR"
```

If ANY of these exist, present the findings and ask:

```
Found artifacts from a previous implementation of <feature_name>:
  - Worktree: <path> (if exists)
  - Local branch: <branch> (if exists)
  - Remote branch: <branch> (if exists)
  - PR: #<number> <title> (<state>) (if exists)

This roadmap will start fresh. Clean up and continue?

[x] yes — remove all artifacts and start fresh
[ ] no — stop so I can investigate
```

**STOP. Wait for the user's response.**

If yes, clean up:
```bash
git worktree remove "$WORKTREE_PATH" --force 2>/dev/null || true
git branch -D "$FEATURE_BRANCH" 2>/dev/null || true
git push origin --delete "$FEATURE_BRANCH" 2>/dev/null || true
```
If there's an open PR, close it:
```bash
gh pr close <number> -c "Superseded by fresh implementation run" 2>/dev/null || true
```

If no artifacts exist, continue silently.

## Step 2b: Create Feature Branch and Worktree

Create a single feature branch and worktree for all steps:

```bash
git worktree add "$WORKTREE_PATH" -b "$FEATURE_BRANCH"
```

Print: `Working on branch: $FEATURE_BRANCH`

All steps will commit to this single branch. One PR will be created at the end.

## Step 2c: Copy Roadmap to Worktree

The roadmap must be inside the worktree so the coordinator and worker agent can read and update it.

**If `ROADMAP_SOURCE=workdir`** (roadmap is in `~/.roadmaps/`):

```bash
ROADMAP_DIR_NAME="$(basename "$(dirname "<roadmap_path>")")"
mkdir -p "$WORKTREE_PATH/Roadmaps/$ROADMAP_DIR_NAME/State" "$WORKTREE_PATH/Roadmaps/$ROADMAP_DIR_NAME/History"
cp "$ROADMAP_DIR/Roadmap.md" "$WORKTREE_PATH/Roadmaps/$ROADMAP_DIR_NAME/Roadmap.md"
cp "$ROADMAP_DIR"/State/*.md "$WORKTREE_PATH/Roadmaps/$ROADMAP_DIR_NAME/State/" 2>/dev/null || true
git -C "$WORKTREE_PATH" add Roadmaps/
git -C "$WORKTREE_PATH" commit -m "docs: add roadmap for <feature_name>"
```

Set the relative roadmap path for all subsequent steps:
```bash
ROADMAP_PATH="Roadmaps/$ROADMAP_DIR_NAME/Roadmap.md"
```

**If `ROADMAP_SOURCE=repo`**: The roadmap is already in the repo. Set `ROADMAP_PATH` to the relative path from Step 1. No copy needed.

## Step 3: Implementation Loop

Derive the worktree roadmap path from the **relative** `ROADMAP_PATH` set in Step 2c:

```bash
WT_ROADMAP_PATH="$WORKTREE_PATH/$ROADMAP_PATH"
```

This is a loop. Repeat until done:

### 3a: Get Next Step

Run the coordinator against the **worktree copy** of the roadmap so it sees status updates from previous steps:

```bash
python3 "${CLAUDE_SKILL_DIR}/references/coordinator" next-step "$WT_ROADMAP_PATH"
```

This outputs JSON. Parse it:

- If `"action": "implement"` — continue with 3b.
- If there are `"manual_skipped"` entries, for each one:
  1. **Create a GitHub issue** assigned to the roadmap creator:
     ```bash
     GITHUB_USER=$(python3 -c "
     import sys; sys.path.insert(0, '$(dirname ${CLAUDE_SKILL_DIR})/../../scripts')
     import roadmap_lib as lib
     meta, _ = lib.parse_frontmatter('$WT_ROADMAP_PATH')
     print(meta.get('github-user', ''))
     ")
     gh issue create --title "[<feature_name>] Step <N>: <description>" --body "<acceptance criteria from step>" --assignee "$GITHUB_USER"
     ```
  2. Print: `Skipping manual step N: <description> — created issue #<number> assigned to $GITHUB_USER`
  3. Update the dashboard:
     ```bash
     python3 "$DASH_CLI" finish-step <N>
     python3 "$DASH_CLI" log "Manual step <N>: created issue #<number> for $GITHUB_USER"
     ```
  If `gh issue create` fails (e.g., not a GitHub repo), just skip the step without creating an issue.
- If `"action": "done"` — all implementation steps are complete. Exit the loop and do the following:

  1. **Dashboard: complete and shutdown:**

     ```bash
     python3 "$DASH_CLI" complete
     python3 "$DASH_CLI" shutdown
     ```

  2. Print: `All steps complete for <feature_name>.` Then **STOP**.

  Note: The final "Create & Review Feature PR" step (handled by the worker agent) populates the Change History, copies the roadmap to the repo, creates the PR, and cleans up.

### 3b: Print Step Info

Print:
```
Step <N>: <description>
  Issue: <issue>  |  Complexity: <complexity>
```

### 3c: Update Dashboard

```bash
python3 "$DASH_CLI" begin-step <N>
python3 "$DASH_CLI" log "Starting step <N>: <description>"
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
Roadmap file: <wt_roadmap_path>
Worktree path: <worktree_path>
Dashboard CLI: <$DASH_CLI>
Dashboard URL: <$DASH_URL>
Roadmap ID: <roadmap_id>
Implementation log: <$IMPL_LOG>

Implement ONLY this step. Commit your changes to the existing branch.
When done, update the roadmap to mark this step Complete, then return.
Do not implement any other step.
```

### 3e: After Worker Returns

**Check if the step was actually completed.** Read the roadmap file and verify the step's `**Status**:` is now `Complete`. If it is NOT:

1. The worker failed. Print: `Step <N> FAILED — worker did not mark it Complete.`
2. Update dashboard:
   ```bash
   python3 "$DASH_CLI" fail-step <N>
   ```
3. **Do NOT retry.** Stop the loop and report the failure:
   ```
   Implementation stopped at step <N>.
   Worktree preserved at: $WORKTREE_PATH
   Branch: $FEATURE_BRANCH
   Completed steps: <list of completed step numbers>
   ```
4. Shut down the dashboard and **STOP**:
   ```bash
   python3 "$DASH_CLI" shutdown
   ```

If the step IS marked Complete:

Log the commit to the dashboard:
```bash
COMMIT_INFO=$(git -C "$WORKTREE_PATH" log -1 --format="%h %an  %ad  %s" --date=short)
python3 "$DASH_CLI" log "git commit: $COMMIT_INFO"
```

Update dashboard:
```bash
python3 "$DASH_CLI" finish-step <N>
```

Print: `Step <N> complete.`

Then **go back to 3a** to get the next step.

