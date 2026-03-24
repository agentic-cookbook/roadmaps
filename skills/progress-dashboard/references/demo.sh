#!/bin/bash
# Simulates a complete implement-roadmap run against the progress dashboard.
# Usage: ./demo.sh
#
# Opens the dashboard in a browser and walks through a 3-step feature
# implementation with realistic delays between state changes.
#
# Demonstrates the atomic-batch-pr workflow: all steps commit to a single
# shared branch, one PR is created at the end covering all steps.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DASH_CLI="$SCRIPT_DIR/dash"

if [[ ! -f "$DASH_CLI" ]]; then
    echo "ERROR: dash CLI not found at $DASH_CLI"
    exit 1
fi

dash() {
    python3 "$DASH_CLI" "$@"
}

pause() {
    sleep "$1"
}

# Create a temp roadmap file for load-roadmap
ROADMAP=$(mktemp /tmp/demo-roadmap-XXXXXX.md)
cat > "$ROADMAP" <<'ROADMAP_EOF'
# Feature Roadmap: WidgetSystem

**Status**: Not Started
**Phase**: Ready

## Implementation Steps

### Step 1: Project scaffolding and configuration

- **GitHub Issue**: #50
- **Type**: Auto
- **Status**: Not Started
- **Complexity**: S

---

### Step 2: Core widget engine implementation

- **GitHub Issue**: #51
- **Type**: Auto
- **Status**: Not Started
- **Complexity**: M

---

### Step 3: API endpoints and integration tests

- **GitHub Issue**: #52
- **Type**: Auto
- **Status**: Not Started
- **Complexity**: M
ROADMAP_EOF

echo "=== Progress Dashboard Demo (Atomic Batch PR) ==="
echo ""

# --- STARTUP ---
echo "[startup] Initializing dashboard..."
DASH_DIR=$(dash init "WidgetSystem")
echo "[startup] Dashboard directory: $DASH_DIR"
echo "[startup] Loading roadmap..."
dash load-roadmap "$ROADMAP"
echo "[startup] Dashboard is open in your browser"
echo ""
pause 3

# --- Create shared branch ---
echo "[branch] Creating feature branch and worktree..."
dash log "Creating branch: feature/WidgetSystem"
dash log "Worktree: ../repo-wt/WidgetSystem"
pause 2

echo "[branch] All steps will commit to this single branch"
echo ""
pause 1

# --- Check controls (should be none) ---
echo "[control] Checking for user controls..."
CONTROL=$(dash check-control)
echo "[control] Result: $CONTROL"
echo ""
pause 1

# --- STEP 1 ---
echo "[step 1] Starting: Project scaffolding and configuration"
dash begin-step 1
pause 3

echo "[step 1] Implementing..."
dash step-detail 1 "Writing project config and directory structure"
pause 3

echo "[step 1] Building and testing..."
dash step-detail 1 "Build passed, 12 tests passing"
dash log "Step 1: build clean, all tests pass"
pause 2

echo "[step 1] Committing to shared branch..."
dash step-detail 1 "Committed: feat: complete step 1"
dash log "Step 1 committed to feature/WidgetSystem"
pause 2

echo "[step 1] Updating roadmap — step 1 complete"
dash update-issue 50 open
dash finish-step 1
echo "[step 1] Done"
echo ""
pause 3

# --- Check controls between steps ---
echo "[control] Checking for user controls..."
CONTROL=$(dash check-control)
echo "[control] Result: $CONTROL"
echo ""
pause 1

# --- STEP 2 ---
echo "[step 2] Starting: Core widget engine implementation"
dash begin-step 2
pause 3

echo "[step 2] Planning step (M complexity)..."
dash step-detail 2 "Planning: widget registry, lifecycle hooks, render pipeline"
dash log "Step 2 plan: widget registry + lifecycle + render pipeline"
pause 3

echo "[step 2] Implementing widget registry..."
dash step-detail 2 "Implementing widget registry and type system"
pause 4

echo "[step 2] Implementing lifecycle hooks..."
dash step-detail 2 "Implementing lifecycle hooks: onMount, onUpdate, onDestroy"
pause 3

echo "[step 2] Implementing render pipeline..."
dash step-detail 2 "Implementing render pipeline with diffing"
pause 3

echo "[step 2] Building and testing..."
dash step-detail 2 "Build passed, 47 tests passing (35 new)"
dash log "Step 2: build clean, 47 tests pass"
pause 2

echo "[step 2] Committing to shared branch..."
dash step-detail 2 "Committed: feat: complete step 2"
dash log "Step 2 committed to feature/WidgetSystem"
pause 2

echo "[step 2] Updating roadmap — step 2 complete"
dash update-issue 51 open
dash finish-step 2
echo "[step 2] Done"
echo ""
pause 2

# --- PAUSE/RESUME demo ---
echo "[control] Simulating pause..."
dash log "Pause received by agent"
DASH_DIR_PATH=$(dash dir)
echo '{"action":"pause","time":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}' > "$DASH_DIR_PATH/control.json"
python3 -c "
import json, pathlib
p = pathlib.Path('$DASH_DIR_PATH/progress.json')
d = json.loads(p.read_text())
d['control_state'] = 'pause'
p.write_text(json.dumps(d, indent=2))
"
echo "[control] Paused for 5 seconds..."
pause 5

echo "[control] Resuming..."
python3 -c "
import json, pathlib
p = pathlib.Path('$DASH_DIR_PATH/progress.json')
d = json.loads(p.read_text())
d.pop('control_state', None)
p.write_text(json.dumps(d, indent=2))
"
rm -f "$DASH_DIR_PATH/control.json"
dash log "Resume received by agent"
echo "[control] Resumed"
echo ""
pause 2

# --- STEP 3 ---
echo "[step 3] Starting: API endpoints and integration tests"
dash begin-step 3
pause 3

echo "[step 3] Implementing REST endpoints..."
dash step-detail 3 "Implementing /api/widgets CRUD endpoints"
dash log "REST endpoints: GET, POST, PUT, DELETE /api/widgets"
pause 4

echo "[step 3] Writing integration tests..."
dash step-detail 3 "Writing integration tests against live database"
pause 3

echo "[step 3] Building and testing..."
dash step-detail 3 "Build passed, 83 tests passing (36 new integration tests)"
dash log "Step 3: build clean, 83 tests pass"
pause 2

echo "[step 3] Committing to shared branch..."
dash step-detail 3 "Committed: feat: complete step 3"
dash log "Step 3 committed to feature/WidgetSystem"
pause 2

echo "[step 3] Updating roadmap — step 3 complete"
dash update-issue 52 open
dash finish-step 3
echo "[step 3] Done"
echo ""
pause 2

# --- ALL STEPS DONE — CREATE SINGLE PR ---
echo "[pr] All steps complete. Pushing branch and creating feature PR..."
dash log "Pushing feature/WidgetSystem to origin"
pause 2

echo "[pr] Creating PR: feat: WidgetSystem"
dash pr-created 0 200 "https://github.com/example/widget-system/pull/200"
dash log "PR #200 created — feat: WidgetSystem (Closes #50, Closes #51, Closes #52)"
pause 3

echo "[pr] Running reviews on feature PR..."
dash step-detail 3 "PR #200: running code review + security review"
dash log "Code review: 1 warning (addressed). Security review: 0 issues."
pause 3

echo "[pr] Reviews passed. Merging PR #200 with --merge..."
dash update-pr 200 merged
dash log "PR #200 merged (--merge, preserving step commits)"
pause 2

echo "[pr] Closing issues..."
dash update-issue 50 closed
dash update-issue 51 closed
dash update-issue 52 closed
dash log "Issues #50, #51, #52 closed"
pause 2

echo "[cleanup] Removing worktree..."
dash log "Worktree removed: ../repo-wt/WidgetSystem"
pause 1

# --- COMPLETION ---
echo "[complete] All steps done. Marking complete..."
dash complete
pause 3

echo "[shutdown] Shutting down dashboard server..."
dash shutdown

# Cleanup
rm -f "$ROADMAP"

echo ""
echo "=== Demo Complete ==="
echo "The dashboard showed the atomic-batch-pr workflow:"
echo "  - 3 steps committed to a single shared branch"
echo "  - 1 feature PR created after all steps finished"
echo "  - PR merged with --merge (preserving individual step commits)"
echo "  - All issues closed after PR merge"
echo "You can close the browser tab now."
