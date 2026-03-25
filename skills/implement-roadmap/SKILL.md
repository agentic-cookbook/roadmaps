---
name: implement-roadmap
version: "20"
description: "Implement a planned feature from its Roadmap. Uses a deterministic Python coordinator for step selection and the Agent tool to launch a worker for each step. Use after /plan-roadmap or /plan-bugfix-roadmap has created a Roadmap."
disable-model-invocation: true
---

## Version Check

If `$ARGUMENTS` is `--version`:

1. Print the skill version:
   > implement-roadmap v20

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

Verify the dashboard server is running and serving pages:

```bash
DASH_URL="${DASHBOARD_URL:-http://localhost:8888}"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$DASH_URL/" 2>/dev/null || echo "000")
```

- If `HTTP_STATUS` is `200` — the server is running. Print: `Dashboard server OK ($DASH_URL)` and continue.
- If `HTTP_STATUS` is anything else (including `000` for connection refused) — print the error and **STOP**:
  ```
  ERROR: Dashboard server is not running or not serving pages (HTTP $HTTP_STATUS at $DASH_URL/).
  Start it with: bash <project_root>/services/dashboard/server.sh start
  ```
  Do NOT continue with the rest of the skill.

## Step 1: Resolve Roadmap

Roadmaps may be in `~/.roadmaps/<project>/` (created by plan-roadmap) or in `Roadmaps/` in the repo (legacy). Check both locations.

First determine the project name:
```bash
PROJECT=$(basename $(git rev-parse --show-toplevel))
ROADMAPS_WORK_DIR="$HOME/.roadmaps/$PROJECT"
```

If `$ROADMAPS_WORK_DIR` exists, run the coordinator from there first. If it finds a roadmap, use it. Otherwise fall back to the repo's `Roadmaps/`.

Note whether the resolved roadmap is under `~/.roadmaps/` or `Roadmaps/`. Store as `ROADMAP_SOURCE=workdir` or `ROADMAP_SOURCE=repo`. The PR step needs this.

Run the coordinator to find the roadmap:

```bash
python3 "${CLAUDE_SKILL_DIR}/references/coordinator" resolve $ARGUMENTS
```

This outputs JSON. Parse it:
- If it has `"path"` — use that roadmap. Print: `Implementing: <name> (<complete>/<total> steps complete)`
- If it has `"choose"` — present the list to the user and ask them to pick. Then use the chosen path.
- If it has `"error"` — print the error and **STOP**.

## Step 1b: Mark Roadmap as Implementing

Write an Implementing state file so other sessions won't try to start this roadmap:

```bash
ROADMAP_DIR="$(dirname "<roadmap_path>")"
TODAY="$(date +%Y-%m-%d)"
printf -- '---\nevent: implementing\ndate: %s\n---\n' "$TODAY" > "$ROADMAP_DIR/State/$TODAY-Implementing.md"
git -C "$(dirname "$ROADMAP_DIR")" add -A Roadmaps/ && git -C "$(dirname "$ROADMAP_DIR")" commit -m "state: mark <feature_name> as Implementing" && git -C "$(dirname "$ROADMAP_DIR")" push
```

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

**IMPORTANT**: All roadmap paths from this point forward must reference the **worktree copy**. Derive the worktree roadmap path:

```bash
WT_ROADMAP_PATH="$WORKTREE_PATH/<roadmap_path>"
```

Where `<roadmap_path>` is the **relative** path from Step 1 (e.g., `Roadmaps/2026-03-21-FeatureName/Roadmap.md`). It must be relative to the repo root — do not use an absolute path here, or the concatenation will break.

This is a loop. Repeat until done:

### 3a: Get Next Step

Run the coordinator against the **worktree copy** of the roadmap so it sees status updates from previous steps:

```bash
python3 "${CLAUDE_SKILL_DIR}/references/coordinator" next-step "$WT_ROADMAP_PATH"
```

This outputs JSON. Parse it:

- If `"action": "implement"` — continue with 3b.
- If there are `"manual_skipped"` entries, print them once: `Skipping manual step N: <description>`
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

