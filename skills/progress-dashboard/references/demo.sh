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

echo "=== Progress Dashboard Demo ==="
echo ""

# --- STARTUP ---
echo "[startup] Initializing dashboard..."
DASH_DIR=$(dash init "WidgetSystem" \
    "Project scaffolding and configuration" \
    "Core widget engine implementation" \
    "API endpoints and integration tests")
echo "[startup] Dashboard directory: $DASH_DIR"
echo "[startup] Dashboard is open in your browser"
echo ""
pause 3

# --- Add roadmap issues ---
echo "[issues] Adding roadmap issues..."
dash add-issue 50 "Step 1: Project scaffolding and configuration" "https://github.com/example/widget-system/issues/50"
dash add-issue 51 "Step 2: Core widget engine implementation" "https://github.com/example/widget-system/issues/51"
dash add-issue 52 "Step 3: API endpoints and integration tests" "https://github.com/example/widget-system/issues/52"
echo ""
pause 2

# --- Check controls (should be none) ---
echo "[control] Checking for user controls..."
CONTROL=$(dash check-control)
echo "[control] Result: $CONTROL"
echo ""
pause 1

# --- STEP 1 ---
echo "[step 1] Starting: Project scaffolding and configuration"
dash step-start 1
dash update-issue 50 in_progress
pause 3

echo "[step 1] Creating worktree and branch..."
dash step-detail 1 "Creating worktree: feature/widget-system-step-1"
dash event "Worktree created: feature/widget-system-step-1"
pause 2

echo "[step 1] Implementing..."
dash step-detail 1 "Writing project config and directory structure"
pause 3

echo "[step 1] Building and testing..."
dash step-detail 1 "Build passed, 12 tests passing"
dash event "Build clean, all tests pass"
pause 2

echo "[step 1] Creating PR..."
dash add-pr 101 "Project scaffolding and configuration" "https://github.com/example/widget-system/pull/101"
dash step-detail 1 "PR #101 created"
dash step-link 1 "PR #101" "https://github.com/example/widget-system/pull/101"
pause 3

echo "[step 1] Running reviews..."
dash step-detail 1 "Code review: 0 issues. Security review: 0 issues."
dash event "Reviews passed: code review + security review"
pause 2

echo "[step 1] Merging PR and closing issue..."
dash update-pr 101 merged
dash update-issue 50 closed
dash step-link 1 "Issue #50" "https://github.com/example/widget-system/issues/50"
dash step-complete 1
echo "[step 1] Done"
echo ""
pause 3

# --- Check controls between steps ---
echo "[control] Checking for user controls..."
CONTROL=$(dash check-control)
echo "[control] Result: $CONTROL"
if [[ "$CONTROL" == "pause" ]]; then
    echo "[control] Paused by user. Waiting for resume..."
    while true; do
        sleep 2
        CONTROL=$(dash check-control)
        if [[ "$CONTROL" != "pause" ]]; then break; fi
    done
    if [[ "$CONTROL" == "stop" ]]; then
        echo "[control] Stopped by user."
        dash error "Stopped by user"
        dash shutdown
        exit 0
    fi
fi
echo ""
pause 1

# --- STEP 2 ---
echo "[step 2] Starting: Core widget engine implementation"
dash step-start 2
dash update-issue 51 in_progress
pause 3

echo "[step 2] Planning step (M complexity)..."
dash step-detail 2 "Planning: widget registry, lifecycle hooks, render pipeline"
dash event "Step 2 plan: widget registry + lifecycle + render pipeline"
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
dash event "Build clean, 47 tests pass"
pause 2

echo "[step 2] Creating PR..."
dash add-pr 102 "Core widget engine implementation" "https://github.com/example/widget-system/pull/102"
dash step-detail 2 "PR #102 created"
dash step-link 2 "PR #102" "https://github.com/example/widget-system/pull/102"
pause 3

echo "[step 2] Running reviews..."
dash step-detail 2 "Code review: 1 warning (resolved). Security review: 0 issues."
dash event "Reviews passed: 1 warning addressed"
pause 2

echo "[step 2] Merging PR and closing issue..."
dash update-pr 102 merged
dash update-issue 51 closed
dash step-link 2 "Issue #51" "https://github.com/example/widget-system/issues/51"
dash step-complete 2
echo "[step 2] Done"
echo ""
pause 2

# --- PAUSE/RESUME demo ---
echo "[control] Simulating pause..."
dash event "Pause received by agent"
python3 "$DASH_CLI" check-control > /dev/null  # clear any stale control
# Write pause control directly to simulate user clicking Pause
DASH_DIR_PATH=$(python3 "$DASH_CLI" dir)
echo '{"action":"pause","time":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}' > "$DASH_DIR_PATH/control.json"
# Update progress.json with pause state
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
dash event "Resume received by agent"
echo "[control] Resumed"
echo ""
pause 2

# --- STEP 3 ---
echo "[step 3] Starting: API endpoints and integration tests"
dash step-start 3
dash update-issue 52 in_progress
pause 3

echo "[step 3] Implementing REST endpoints..."
dash step-detail 3 "Implementing /api/widgets CRUD endpoints"
dash event "REST endpoints: GET, POST, PUT, DELETE /api/widgets"
pause 4

echo "[step 3] Writing integration tests..."
dash step-detail 3 "Writing integration tests against live database"
pause 3

echo "[step 3] Building and testing..."
dash step-detail 3 "Build passed, 83 tests passing (36 new integration tests)"
dash event "Build clean, 83 tests pass"
pause 2

echo "[step 3] Creating PR..."
dash add-pr 103 "API endpoints and integration tests" "https://github.com/example/widget-system/pull/103"
dash step-detail 3 "PR #103 created"
dash step-link 3 "PR #103" "https://github.com/example/widget-system/pull/103"
pause 3

echo "[step 3] Running reviews..."
dash step-detail 3 "Code review: 0 issues. Security review: 0 issues. API review: 0 issues."
dash event "Reviews passed: code + security + API contract"
pause 2

echo "[step 3] Merging PR and closing issue..."
dash update-pr 103 merged
dash update-issue 52 closed
dash step-link 3 "Issue #52" "https://github.com/example/widget-system/issues/52"
dash step-complete 3
echo "[step 3] Done"
echo ""
pause 2

# --- COMPLETION ---
echo "[complete] All steps done. Marking complete..."
dash complete
pause 3

echo "[shutdown] Shutting down dashboard server..."
dash shutdown

echo ""
echo "=== Demo Complete ==="
echo "The dashboard should show all 3 steps as complete."
echo "You can close the browser tab now."
