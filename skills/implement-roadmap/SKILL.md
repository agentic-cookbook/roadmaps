---
name: implement-roadmap
version: "29"
description: "Implement a feature from its Roadmap using a deterministic coordinator and worker agents. Use after /plan-roadmap or /plan-bugfix-roadmap."
argument-hint: "[feature-name | --version]"
disable-model-invocation: true
---

## Version Check

If `$ARGUMENTS` is `--version`:

1. Print the skill version:
   > implement-roadmap v29

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

## CRITICAL INVARIANT

The worktree is for CODE ONLY. Roadmap files (Roadmap.md, State/, History/)
stay in `~/.roadmaps/<project>/` throughout implementation. NEVER copy roadmap
files into the worktree. The only roadmap artifact that enters the repo is
the final `<Name>-Roadmap.md` flat file copy during the Finalize PR step.

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

Store the resolved path as `ROADMAP_PATH` (this is an absolute path when source is `~/.roadmaps/`).
Store `ROADMAP_DIR` as the parent directory of `ROADMAP_PATH`.

**Read review configuration:**

1. Check the Roadmap.md frontmatter for a `reviews` field
2. If not present, check the project's `CLAUDE.md` for a `reviews:` section
3. If neither exists, use defaults: `per-step: [code-reviewer]`, `final: [code-reviewer, silent-failure-hunter]`

Store as `REVIEW_PER_STEP` and `REVIEW_FINAL`.

**Detect platform** for guideline selection: check the project's primary language from file extensions or CLAUDE.md. Map to the agentic-cookbook guideline directory: `../agentic-cookbook/cookbook/guidelines/language/<platform>/`. Store as `GUIDELINE_PLATFORM`.

## Step 1a: Check for Previous Implementation Artifacts

**This must happen immediately after resolve — before anything else.**

```bash
FEATURE_BRANCH="feature/<feature_name>"
WORKTREE_PATH="../$(basename $(pwd))-wt/<feature_name>"
```

**Check for stale Implementing state** (from a previous failed run):
```bash
ls "$ROADMAP_DIR/State/"*-Implementing.md 2>/dev/null && echo "STALE_IMPLEMENTING" || echo "NO_STALE"
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
  - Implementing state file (if exists)
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
rm -f "$ROADMAP_DIR/State/"*-Implementing.md
git worktree remove "$WORKTREE_PATH" --force 2>/dev/null || true
git branch -D "$FEATURE_BRANCH" 2>/dev/null || true
git push origin --delete "$FEATURE_BRANCH" 2>/dev/null || true
```
If there's an open PR, close it:
```bash
gh pr close <number> -c "Superseded by fresh implementation run" 2>/dev/null || true
```

If no artifacts exist, continue silently.

## Step 1a2: Auto-Merge Preference

Ask the user:

```
Auto-merge PR when implementation is complete?
[x] yes — merge automatically after reviews pass (default)
[ ] no — leave PR ready for manual review before merging
```

**STOP. Wait for the user's response.**

Store the result as `AUTO_MERGE` (`true` if yes, `false` if no). Default is `true`.

## Step 1b: Initialize Implementation Log

Create the implementation log in the roadmap directory:

```bash
IMPL_LOG="$ROADMAP_DIR/implementation.log"
```

Write the initial entry:
```
[YYYY-MM-DD HH:MM:SS] IMPLEMENTATION_START: <feature_name>
[YYYY-MM-DD HH:MM:SS] PROJECT: $PROJECT
[YYYY-MM-DD HH:MM:SS] ROADMAP: $ROADMAP_PATH
```

**Throughout this skill, append to `$IMPL_LOG` before every significant action.**

## Step 1c: Mark as Implementing

Write the Implementing state file (after cleanup, so it won't conflict):

```bash
TODAY="$(date +%Y-%m-%d)"
printf -- '---\nevent: implementing\ndate: %s\n---\n' "$TODAY" > "$ROADMAP_DIR/State/$TODAY-Implementing.md"
```

## Step 2: Start Dashboard

```bash
DASH_CLI="$HOME/.claude/skills/progress-dashboard/references/dash"
export DASH_FEATURE="<feature_name>"
test -f "$DASH_CLI" && python3 "$DASH_CLI" init "<feature_name>" && python3 "$DASH_CLI" load-roadmap "$ROADMAP_PATH" || echo "Dashboard not available"
```

**IMPORTANT**: Always set `export DASH_FEATURE="<feature_name>"` before ANY `dash` command. This ensures concurrent sessions don't interfere with each other.

## Step 2b: Create Feature Branch and Worktree

Create a single feature branch and worktree for CODE ONLY:

```bash
git worktree add "$WORKTREE_PATH" -b "$FEATURE_BRANCH"
```

Print: `Working on branch: $FEATURE_BRANCH`

All steps will commit to this single branch. One PR will be created at the end.

**Do NOT copy roadmap files into the worktree.** The roadmap stays at `$ROADMAP_PATH`.

## Step 3: Implementation Loop

This is a loop. Repeat until done:

### 3a: Get Next Step

Run the coordinator against the roadmap at its original location:

```bash
python3 "${CLAUDE_SKILL_DIR}/references/coordinator" next-step "$ROADMAP_PATH"
```

This outputs JSON. Parse it:

- If `"action": "implement"` — continue with 3b.
- If there are `"manual_skipped"` entries, for each one:
  1. **Create a GitHub issue** assigned to the roadmap creator:
     ```bash
     GITHUB_USER=$(python3 -c "
     import sys; sys.path.insert(0, '$(dirname ${CLAUDE_SKILL_DIR})/../../scripts')
     import roadmap_lib as lib
     meta, _ = lib.parse_frontmatter('$ROADMAP_PATH')
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

  Note: The final "Finalize & Merge PR" step (handled by the worker agent) populates the Change History, copies the roadmap to the repo, creates the PR, and cleans up.

### 3b: Print Step Info

Print:
```
Step <N>: <description>
  Complexity: <complexity>
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
Complexity: <complexity>
Roadmap file: <ROADMAP_PATH>
Worktree path: <WORKTREE_PATH>
Feature branch: <FEATURE_BRANCH>
Dashboard CLI: <$DASH_CLI>
Dashboard URL: <$DASH_URL>
Roadmap ID: <roadmap_id>
Implementation log: <$IMPL_LOG>
Review config (per-step): <$REVIEW_PER_STEP>
Review config (final): <$REVIEW_FINAL>
Guidelines platform: <$GUIDELINE_PLATFORM> (agentic-cookbook path)
Auto-merge: <$AUTO_MERGE>

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
