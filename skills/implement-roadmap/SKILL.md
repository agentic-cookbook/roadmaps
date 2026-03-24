---
name: implement-roadmap
version: "17"
description: "Implement a planned feature from its Roadmap. Uses a deterministic Python coordinator for step selection and the Agent tool to launch a worker for each step. Use after /plan-roadmap or /plan-bugfix-roadmap has created a Roadmap."
disable-model-invocation: true
---

## Version Check

If `$ARGUMENTS` is `--version`:

1. Print the skill version:
   > implement-roadmap v17

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

## Step 2c: Add PR Step to Dashboard

Get the total step count from the coordinator's resolve output, then add the PR step as step N+1:

```bash
PR_STEP=$((total + 1))
python3 "$DASH_CLI" log "Adding PR step as step $PR_STEP"
```

Use the dashboard client to add the PR step. Get the current steps from the API, append the PR step, and set them all:

```python
python3 -c "
import os, sys, json, urllib.request
base = os.environ.get('DASHBOARD_URL', 'http://localhost:8888')
rid = '<roadmap_id>'
# Get current steps
resp = urllib.request.urlopen(f'{base}/api/v1/roadmaps/{rid}/steps')
steps = json.loads(resp.read())
# Add PR step
steps.append({'number': $PR_STEP, 'description': 'Create & Review Feature PR', 'status': 'not_started', 'step_type': 'Auto', 'complexity': 'S'})
# Set all steps
data = json.dumps(steps).encode()
req = urllib.request.Request(f'{base}/api/v1/roadmaps/{rid}/steps', data=data, headers={'Content-Type': 'application/json'}, method='POST')
urllib.request.urlopen(req)
"
```

If the above is too complex, simply add the step via the `dash` CLI's `set-steps` command — but note this replaces ALL steps, so only use it if you can reconstruct the full list.

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
- If `"action": "done"` — all implementation steps are complete. **Exit the loop and proceed to Step 4.**

## Step 4: Create & Review Feature PR

This is an explicit final step visible in the dashboard. The `done` response includes `"total"` — use `total + 1` as the PR step number.

```bash
PR_STEP=$((total + 1))
```

**Register and start the PR step in the dashboard:**
```bash
python3 -c "
import os, sys
sys.path.insert(0, '$(echo $PROJECT_ROOT)/scripts')
from dashboard_client import DashboardClient
c = DashboardClient(base_url=os.environ.get('DASHBOARD_URL', 'http://localhost:8888'))
rid = open(os.path.expanduser('~/.claude/dashboard/.active_roadmap')).read().strip() if not os.environ.get('DASH_FEATURE') else None
# Use the service's set_steps to append — get existing steps, add PR step
import urllib.request, json
url = c.base_url + '/api/v1/roadmaps/' + (os.environ.get('DASH_ROADMAP_ID') or rid) + '/steps'
"
python3 "$DASH_CLI" begin-step "$PR_STEP"
```

If the above is too complex, simply call:
```bash
python3 "$DASH_CLI" log "Starting: Create & Review Feature PR"
python3 "$DASH_CLI" begin-step "$PR_STEP"
```

If `begin-step` fails because the step doesn't exist, that's OK — the event log still shows progress. Continue regardless.

### 4a: Write State and History files

Derive the roadmap directory from the worktree roadmap path:

```bash
ROADMAP_DIR="$(dirname "$WT_ROADMAP_PATH")"
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

### 4b: Commit and push

```bash
git -C "$WORKTREE_PATH" add -A Roadmaps/
git -C "$WORKTREE_PATH" commit -m "docs: complete feature <feature_name> — all steps done"
git -C "$WORKTREE_PATH" push -u origin "$FEATURE_BRANCH"
```

### 4c: Create the PR

Build the PR body file. **You must substitute all `<...>` placeholders with actual values before writing the file** — do not pass placeholder text through literally. The `Closes #N` lines are critical for auto-closing issues on merge.

```bash
cat > /tmp/gh-pr-body.md <<'PRBODYEOF'
## Summary

Implements the <feature_name> feature.

## Steps

- [x] Step 1: <actual step 1 description>
- [x] Step 2: <actual step 2 description>
...etc for each completed step...

## Linked Issues

Closes #<actual_issue_number_for_step_1>
Closes #<actual_issue_number_for_step_2>
...etc for each step with a GitHub issue...

## Testing

All steps verified against the feature definition's verification strategy.

## Checklist

- [ ] Build passes
- [ ] Tests pass
- [ ] Follows project conventions
PRBODYEOF
```

```bash
gh pr create --head "$FEATURE_BRANCH" --title "feat: <feature_name>" --body-file /tmp/gh-pr-body.md
```

### 4d: Review loop (max 3 iterations)

Run reviews on the PR. **Maximum 3 iterations** — if issues persist after 3 rounds, stop and report.

For each iteration:

1. **Run reviews:**
   - Always: Code Review (use `/review-pr`) + Security Review
   - Conditionally: UI Review (if HTML/CSS/JS changed), API Review (if endpoints changed)

2. **If reviews pass with no issues** — break out of the loop, proceed to 4e.

3. **If reviews find issues** — fix them, commit to the feature branch, push:
   ```bash
   git -C "$WORKTREE_PATH" add -A
   git -C "$WORKTREE_PATH" commit -m "fix: address review feedback (iteration N)"
   git -C "$WORKTREE_PATH" push
   ```
   Then re-run reviews (next iteration).

4. **If 3 iterations exhausted and issues remain:**
   ```bash
   python3 "$DASH_CLI" step-error "$PR_STEP" "Review issues unresolved after 3 iterations"
   python3 "$DASH_CLI" log "PR review failed after 3 iterations — manual intervention needed"
   python3 "$DASH_CLI" shutdown
   ```
   Print:
   ```
   PR review failed after 3 iterations.
   PR is open at: <pr_url>
   Worktree preserved at: $WORKTREE_PATH
   Branch: $FEATURE_BRANCH
   ```
   Then **STOP**.

### 4e: Merge the PR

```bash
gh pr merge --merge
```

Use `--merge` (NOT `--squash`) to preserve individual step commits.

### 4f: Close issues and clean up

Close any issues not auto-closed by the `Closes #N` lines:
```bash
gh issue close <number> --comment "Completed in PR #<pr_number>"
```

Clean up the worktree:
```bash
git worktree remove "$WORKTREE_PATH"
```

### 4g: Dashboard complete

```bash
python3 "$DASH_CLI" finish-step "$PR_STEP"
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
Roadmap file: <wt_roadmap_path>
Feature Definition: <wt_roadmap_dir>/Definition.md
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

Log the commit to the dashboard with SHA, author, date, and message:
```bash
COMMIT_INFO=$(git -C "$WORKTREE_PATH" log -1 --format="%h %an  %ad  %s" --date=short)
python3 "$DASH_CLI" log "Step <N>: $COMMIT_INFO"
```

Update dashboard:
```bash
python3 "$DASH_CLI" finish-step <N>
```

Print: `Step <N> complete.`

Then **go back to 3a** to get the next step.

