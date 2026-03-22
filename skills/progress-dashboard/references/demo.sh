#!/bin/bash
# Simulates a complete implement-roadmap-agent run against the progress dashboard.
# Usage: ./demo.sh
#
# Opens the dashboard in a browser and walks through a 3-step feature
# implementation with realistic delays between state changes.

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
- **PR**: _TBD_

---

### Step 2: Core widget engine implementation

- **GitHub Issue**: #51
- **Type**: Auto
- **Status**: Not Started
- **Complexity**: M
- **PR**: _TBD_

---

### Step 3: API endpoints and integration tests

- **GitHub Issue**: #52
- **Type**: Auto
- **Status**: Not Started
- **Complexity**: M
- **PR**: _TBD_
ROADMAP_EOF

echo "=== Progress Dashboard Demo ==="
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

echo "[step 1] Creating worktree and branch..."
dash step-detail 1 "Creating worktree: feature/widget-system-step-1"
dash log "Worktree created: feature/widget-system-step-1"
pause 2

echo "[step 1] Implementing..."
dash step-detail 1 "Writing project config and directory structure"
pause 3

echo "[step 1] Building and testing..."
dash step-detail 1 "Build passed, 12 tests passing"
dash log "Build clean, all tests pass"
pause 2

echo "[step 1] Creating PR..."
dash pr-created 1 101 "https://github.com/example/widget-system/pull/101"
dash step-detail 1 "PR #101 created — running reviews"
pause 3

echo "[step 1] Running reviews..."
dash step-detail 1 "Code review: 0 issues. Security review: 0 issues."
dash log "Reviews passed: code review + security review"
pause 2

echo "[step 1] Merging PR and closing issue..."
dash update-pr 101 merged
dash update-issue 50 closed
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
dash log "Build clean, 47 tests pass"
pause 2

echo "[step 2] Creating PR..."
dash pr-created 2 102 "https://github.com/example/widget-system/pull/102"
dash step-detail 2 "PR #102 created — running reviews"
pause 3

echo "[step 2] Running reviews..."
dash step-detail 2 "Code review: 1 warning (resolved). Security review: 0 issues."
dash log "Reviews passed: 1 warning addressed"
pause 2

echo "[step 2] Merging PR and closing issue..."
dash update-pr 102 merged
dash update-issue 51 closed
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
dash log "Build clean, 83 tests pass"
pause 2

echo "[step 3] Creating PR..."
dash pr-created 3 103 "https://github.com/example/widget-system/pull/103"
dash step-detail 3 "PR #103 created — running reviews"
pause 3

echo "[step 3] Running reviews..."
dash step-detail 3 "Code review: 0 issues. Security review: 0 issues. API review: 0 issues."
dash log "Reviews passed: code + security + API contract"
pause 2

echo "[step 3] Merging PR and closing issue..."
dash update-pr 103 merged
dash update-issue 52 closed
dash finish-step 3
echo "[step 3] Done"
echo ""
pause 2

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
echo "The dashboard should show all 3 steps as complete."
echo "You can close the browser tab now."
