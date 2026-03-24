#!/bin/bash
# Simulates a complete implement-roadmap run against the progress dashboard.
# Usage: ./demo.sh
#
# Opens the dashboard in a browser and walks through a 5-step feature
# implementation with realistic delays between state changes.
#
# Demonstrates the atomic-batch-pr workflow: step 1 creates GitHub issues,
# steps 2-4 implement features on a shared branch, step 5 creates and
# merges the feature PR.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DASH_CLI="$SCRIPT_DIR/dash"
# Navigate to project root (4 levels up from skills/progress-dashboard/references/)
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SERVER_SH="$PROJECT_ROOT/services/dashboard/server.sh"

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

# --- Start the Flask dashboard service on a DEMO PORT ---
# Uses port 9888 to avoid conflicting with the production dashboard on 8888.
DEMO_PORT=9888
DEMO_DB="/tmp/demo-dashboard-$$.db"
export DASHBOARD_PORT="$DEMO_PORT"
export DASHBOARD_DB="$DEMO_DB"
export DASHBOARD_URL="http://127.0.0.1:$DEMO_PORT"

STARTED_SERVICE=false
if [[ -f "$SERVER_SH" ]]; then
    echo "[service] Starting demo dashboard on port $DEMO_PORT..."
    cd "$PROJECT_ROOT" && bash "$SERVER_SH" start --port "$DEMO_PORT"
    STARTED_SERVICE=true
    pause 1
else
    echo "WARNING: server.sh not found at $SERVER_SH — falling back to file-based mode"
fi

# Create a temp roadmap file for load-roadmap
ROADMAP=$(mktemp /tmp/demo-roadmap-XXXXXX.md)
cat > "$ROADMAP" <<'ROADMAP_EOF'
---
id: demo-widget-system-001
created: 2026-01-01
modified: 2026-01-01
author: Demo Runner <demo@example.com>
definition-id: demo-widget-def-001
change-history:
  - date: 2026-01-01
    author: Demo Runner <demo@example.com>
    summary: Demo fixture
---

# Feature Roadmap: WidgetSystem

**Status**: Not Started
**Phase**: Ready

## Implementation Steps

### Step 1: Create GitHub Issues

- **Type**: Auto
- **Status**: Not Started
- **Complexity**: S

---

### Step 2: Project scaffolding and configuration

- **GitHub Issue**: #50
- **Type**: Auto
- **Status**: Not Started
- **Complexity**: S

---

### Step 3: Core widget engine implementation

- **GitHub Issue**: #51
- **Type**: Auto
- **Status**: Not Started
- **Complexity**: M

---

### Step 4: API endpoints and integration tests

- **GitHub Issue**: #52
- **Type**: Auto
- **Status**: Not Started
- **Complexity**: M

---

### Step 5: Create & Review Feature PR

- **Type**: Auto
- **Status**: Not Started
- **Complexity**: M
- **Dependencies**: Step 4
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

# --- STEP 1: CREATE GITHUB ISSUES ---
echo "[step 1] Starting: Create GitHub Issues"
dash begin-step 1
pause 2

echo "[step 1] Creating issues for each step..."
dash step-detail 1 "Creating GitHub issue for step 2: Project scaffolding and configuration"
dash log "Created issue #50: Project scaffolding and configuration"
pause 2

dash step-detail 1 "Creating GitHub issue for step 3: Core widget engine implementation"
dash log "Created issue #51: Core widget engine implementation"
pause 2

dash step-detail 1 "Creating GitHub issue for step 4: API endpoints and integration tests"
dash log "Created issue #52: API endpoints and integration tests"
pause 2

dash step-detail 1 "Issue placeholders filled in: #50, #51, #52"
pause 1

echo "[step 1] Updating roadmap — step 1 complete"
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

# --- STEP 2: PROJECT SCAFFOLDING ---
echo "[step 2] Starting: Project scaffolding and configuration"
dash begin-step 2
pause 3

echo "[step 2] Implementing..."
dash step-detail 2 "Writing project config and directory structure"
pause 3

echo "[step 2] Building and testing..."
dash step-detail 2 "Build passed, 12 tests passing"
dash log "Build clean, all tests pass"
pause 2

echo "[step 2] Committing to shared branch..."
dash step-detail 2 "Committed: feat: create project scaffolding"
dash log "git commit: a3f7b21 Demo Runner  2026-03-24  feat: create project scaffolding"
pause 2

echo "[step 2] Updating roadmap — step 2 complete"
dash finish-step 2
echo "[step 2] Done"
echo ""
pause 3

# --- Check controls between steps ---
echo "[control] Checking for user controls..."
CONTROL=$(dash check-control)
echo "[control] Result: $CONTROL"
echo ""
pause 1

# --- STEP 3: CORE WIDGET ENGINE ---
echo "[step 3] Starting: Core widget engine implementation"
dash begin-step 3
pause 3

echo "[step 3] Planning step (M complexity)..."
dash step-detail 3 "Planning: widget registry, lifecycle hooks, render pipeline"
dash log "Planning: widget registry + lifecycle + render pipeline"
pause 3

echo "[step 3] Implementing widget registry..."
dash step-detail 3 "Implementing widget registry and type system"
pause 4

echo "[step 3] Implementing lifecycle hooks..."
dash step-detail 3 "Implementing lifecycle hooks: onMount, onUpdate, onDestroy"
pause 3

echo "[step 3] Implementing render pipeline..."
dash step-detail 3 "Implementing render pipeline with diffing"
pause 3

echo "[step 3] Building and testing..."
dash step-detail 3 "Build passed, 47 tests passing (35 new)"
dash log "Build clean, 47 tests pass"
pause 2

echo "[step 3] Committing to shared branch..."
dash step-detail 3 "Committed: feat: implement core widget engine"
dash log "git commit: e8c4d09 Demo Runner  2026-03-24  feat: implement core widget engine"
pause 2

echo "[step 3] Updating roadmap — step 3 complete"
dash finish-step 3
echo "[step 3] Done"
echo ""
pause 3

# --- Check controls between steps ---
echo "[control] Checking for user controls..."
CONTROL=$(dash check-control)
echo "[control] Result: $CONTROL"
echo ""
pause 1

# --- STEP 4: API ENDPOINTS ---
echo "[step 4] Starting: API endpoints and integration tests"
dash begin-step 4
pause 3

echo "[step 4] Implementing REST endpoints..."
dash step-detail 4 "Implementing /api/widgets CRUD endpoints"
dash log "REST endpoints: GET, POST, PUT, DELETE /api/widgets"
pause 4

echo "[step 4] Writing integration tests..."
dash step-detail 4 "Writing integration tests against live database"
pause 3

echo "[step 4] Building and testing..."
dash step-detail 4 "Build passed, 83 tests passing (36 new integration tests)"
dash log "Build clean, 83 tests pass"
pause 2

echo "[step 4] Committing to shared branch..."
dash step-detail 4 "Committed: feat: add API endpoints and integration tests"
dash log "git commit: 1b5f6e3 Demo Runner  2026-03-24  feat: add API endpoints and integration tests"
pause 2

echo "[step 4] Updating roadmap — step 4 complete"
dash finish-step 4
echo "[step 4] Done"
echo ""
pause 2

# --- STEP 5: CREATE & REVIEW FEATURE PR ---
echo "[step 5] Starting: Create & Review Feature PR"
dash begin-step 5
pause 2

echo "[step 5] Writing state and history files..."
dash step-detail 5 "Writing Complete state and ImplementationComplete history"
dash log "State: Complete, History: ImplementationComplete"
pause 2

echo "[step 5] Pushing branch..."
dash step-detail 5 "Pushing feature/WidgetSystem to origin"
dash log "Pushing feature/WidgetSystem to origin"
pause 2

echo "[step 5] Creating PR: feat: WidgetSystem"
dash step-detail 5 "PR #200 created — Closes #50, #51, #52"
dash log "PR #200 created — feat: WidgetSystem (Closes #50, Closes #51, Closes #52)"
pause 3

echo "[step 5] Review iteration 1: running code review + security review..."
dash step-detail 5 "Review iteration 1/3: code review + security review"
dash log "Code review: 1 warning found"
pause 3

echo "[step 5] Fixing review feedback..."
dash step-detail 5 "Fixing: addressed code review warning"
dash log "git commit: 7d2a4c8 Demo Runner  2026-03-24  fix: address review feedback (iteration 1)"
pause 2

echo "[step 5] Review iteration 2: re-reviewing..."
dash step-detail 5 "Review iteration 2/3: re-running reviews"
dash log "Code review: 0 issues. Security review: 0 issues."
pause 3

echo "[step 5] Reviews passed. Merging PR #200 with --merge..."
dash step-detail 5 "PR #200 merged (--merge, preserving step commits)"
dash log "PR #200 merged (--merge, preserving step commits)"
pause 2

echo "[step 5] Closing issues..."
dash log "Issues #50, #51, #52 closed via gh issue close"
pause 2

echo "[step 5] Cleaning up worktree..."
dash log "Worktree removed: ../repo-wt/WidgetSystem"
dash finish-step 5
echo "[step 5] Done"
echo ""
pause 2

# --- COMPLETION ---
echo "[complete] All steps done. Marking complete..."
dash complete
pause 3

echo "[shutdown] Shutting down..."
dash shutdown

# Cleanup
rm -f "$ROADMAP"
rm -f "$DEMO_DB"

# Stop the demo dashboard service
if [[ "$STARTED_SERVICE" == "true" ]]; then
    cd "$PROJECT_ROOT" && DASHBOARD_PORT="$DEMO_PORT" bash "$SERVER_SH" stop 2>/dev/null
fi

echo ""
echo "=== Demo Complete ==="
echo "The dashboard showed the atomic-batch-pr workflow:"
echo "  - Step 1 created GitHub issues for all implementation steps"
echo "  - Steps 2-4 committed to a single shared branch"
echo "  - Step 5 created 1 feature PR covering all steps"
echo "  - PR merged with --merge (preserving individual step commits)"
echo "  - All issues closed after PR merge"
