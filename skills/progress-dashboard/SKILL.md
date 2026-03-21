---
name: progress-dashboard
version: "2.0.0"
description: "Start a live progress dashboard in the browser. Use when an agent or skill wants to show real-time step-by-step progress to the user. Triggers on 'show progress', 'start dashboard', or /progress-dashboard."
argument-hint: "<feature-name>"
allowed-tools: Read, Bash(cp *), Bash(mkdir *), Bash(python3 *), Bash(open *), Bash(cat *), Bash(kill *), Bash(lsof *), Bash(chmod *), Write
---

## Version Check

If `$ARGUMENTS` is `--version`, respond with exactly:

> progress-dashboard v2.0.0

Then stop. Do not continue with the rest of the skill.

---

# Progress Dashboard

Reusable live progress dashboard. Starts a tiny local web server serving a progress page that polls a JSON file for updates. Any agent or skill can write to the JSON file to update the dashboard in real time.

## How It Works

1. **Start**: Creates a temp directory, copies in the HTML, starts a Python HTTP server, opens the browser.
2. **Update**: The caller uses the `dash` CLI to update progress — one command per state change.
3. **Stop**: `dash shutdown` kills the server. The temp directory is cleaned up by the OS.

## Quick Start with `dash` CLI

The `dash` CLI at `${CLAUDE_SKILL_DIR}/references/dash` handles all dashboard operations. It persists state internally so you don't need to track shell variables between calls.

```bash
DASH_CLI="${CLAUDE_SKILL_DIR}/references/dash"

# Start — creates temp dir, starts server, opens browser
python3 "$DASH_CLI" init "MyFeature" "Step 1: Setup" "Step 2: Build" "Step 3: Test"

# Update steps
python3 "$DASH_CLI" step-start 1
python3 "$DASH_CLI" step-detail 1 "Installing dependencies"
python3 "$DASH_CLI" step-link 1 "PR #42" "https://github.com/org/repo/pull/42"
python3 "$DASH_CLI" step-complete 1

# Add event log entries
python3 "$DASH_CLI" event "Reviews passed"

# Check user controls (pause/resume/stop buttons)
python3 "$DASH_CLI" check-control    # prints: none, pause, resume, or stop

# Finish
python3 "$DASH_CLI" complete         # mark all done
python3 "$DASH_CLI" shutdown         # kill server

# On error
python3 "$DASH_CLI" step-error 2 "Build failed: missing dependency"
python3 "$DASH_CLI" shutdown
```

If you need lower-level control, the manual steps below still work — but the `dash` CLI is the recommended approach.

---

## Manual Setup (alternative to `dash` CLI)

---

## Step 1: Create the Dashboard Directory

```bash
DASH_DIR=$(mktemp -d "${TMPDIR:-/tmp}/progress-dashboard-XXXXXX")
echo "$DASH_DIR"
```

Save `DASH_DIR` — you will reference it throughout.

## Step 2: Copy the HTML Template

```bash
cp "${CLAUDE_SKILL_DIR}/references/dashboard.html" "$DASH_DIR/index.html"
```

## Step 3: Write the Initial Progress File

Write `$DASH_DIR/progress.json` with the initial state. Use this JSON structure:

```json
{
  "title": "<feature or task name>",
  "status": "running",
  "steps": [
    {
      "name": "<step description>",
      "status": "not_started",
      "detail": null,
      "links": [],
      "updated_at": null
    }
  ],
  "events": [
    {
      "time": "<ISO 8601 timestamp>",
      "message": "Dashboard started"
    }
  ],
  "updated_at": "<ISO 8601 timestamp>"
}
```

### Step status values

| Value | Meaning | Dashboard display |
|-------|---------|-------------------|
| `not_started` | Queued | Empty circle |
| `in_progress` | Currently executing | Animated spinner |
| `complete` | Finished successfully | Green checkmark |
| `error` | Failed | Red X |
| `skipped` | Intentionally skipped | Dash |

### Step links

Each step can have links that render as clickable anchors:

```json
"links": [
  { "label": "PR #42", "url": "https://github.com/org/repo/pull/42" }
]
```

### Events

The `events` array is an append-only log. Add an entry for each meaningful state change (step started, PR created, review complete, error occurred, etc.).

## Step 4: Start the HTTP Server

Copy the server script and find a free port:

```bash
cp "${CLAUDE_SKILL_DIR}/references/server.py" "$DASH_DIR/server.py"
DASH_PORT=$(python3 -c "import socket; s=socket.socket(); s.bind(('',0)); print(s.getsockname()[1]); s.close()")
python3 "$DASH_DIR/server.py" "$DASH_PORT" "$DASH_DIR" &
DASH_PID=$!
echo "Dashboard server PID: $DASH_PID, port: $DASH_PORT"
```

This uses a custom server (not `python3 -m http.server`) because it also accepts PUT requests for `control.json`, which is how the dashboard's Pause/Resume/Stop buttons communicate back to the agent.

Verify the server started:

```bash
sleep 1 && kill -0 "$DASH_PID" 2>/dev/null && echo "Server running" || echo "Server failed to start"
```

If the server failed, **STOP** and tell the user. Common causes: Python not found, port conflict.

## Step 5: Open the Browser

```bash
open "http://127.0.0.1:$DASH_PORT"
```

On Linux, use `xdg-open` instead of `open`.

## Step 6: Report to Caller

Print the dashboard details so the calling agent/skill can use them:

```
=== PROGRESS DASHBOARD ===
URL: http://127.0.0.1:<port>
Directory: <DASH_DIR>
Progress file: <DASH_DIR>/progress.json
Server PID: <DASH_PID>
```

The caller is now responsible for:
- Writing updated `progress.json` whenever state changes
- Calling the shutdown procedure when done

---

## Updating Progress

To update the dashboard, overwrite `$DASH_DIR/progress.json` with the new state. The HTML page polls every 3 seconds.

When updating:
- Change the relevant step's `status` and `detail`
- Set `updated_at` on the step and the root object to the current ISO 8601 timestamp
- Append to the `events` array

Example — marking step 2 as in progress:

```json
{
  "title": "MyFeature",
  "status": "running",
  "steps": [
    { "name": "Setup", "status": "complete", "detail": "Done", "links": [], "updated_at": "2026-03-21T10:01:00Z" },
    { "name": "Core logic", "status": "in_progress", "detail": "Writing implementation", "links": [], "updated_at": "2026-03-21T10:05:00Z" },
    { "name": "Tests", "status": "not_started", "detail": null, "links": [], "updated_at": null }
  ],
  "events": [
    { "time": "2026-03-21T10:00:00Z", "message": "Dashboard started" },
    { "time": "2026-03-21T10:01:00Z", "message": "Step 1: Setup complete" },
    { "time": "2026-03-21T10:05:00Z", "message": "Step 2: Core logic started" }
  ],
  "updated_at": "2026-03-21T10:05:00Z"
}
```

---

## Checking for User Controls

The dashboard has **Pause**, **Resume**, and **Stop** buttons. When the user clicks one, the dashboard writes `$DASH_DIR/control.json`:

```json
{ "action": "pause", "time": "2026-03-21T10:05:00Z" }
```

Possible `action` values:

| Action | Meaning | What the agent should do |
|--------|---------|--------------------------|
| `pause` | User wants to pause | Finish the current atomic operation (e.g., commit), then wait. Check `control.json` in a loop until it changes to `resume` or `stop`. |
| `resume` | User wants to continue | Delete `control.json` and continue where you left off. |
| `stop` | User wants to abort | Finish the current atomic operation, release the lock, update the dashboard to `"status": "error"` with detail "Stopped by user", and shut down. |

### How to check

Before starting each new step (or at any natural pause point), check for the control file:

```bash
cat "$DASH_DIR/control.json" 2>/dev/null
```

If the file exists and contains an action, handle it as described above. If the file does not exist or is empty, continue normally.

After handling `resume`, delete the control file:

```bash
rm -f "$DASH_DIR/control.json"
```

---

## Shutting Down

When the task is complete or has failed:

1. Write a final `progress.json` with `"status": "complete"` (or `"error"`)
2. Kill the server:

```bash
kill "$DASH_PID" 2>/dev/null
```

The temp directory in `$TMPDIR` will be cleaned up by the OS on reboot. No manual cleanup is needed.
