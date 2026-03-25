# Roadmaps: Automated Feature Planning & Implementation for Claude Code

You have a feature idea. Turning it into shipped code means planning, breaking it into steps, implementing each one, tracking progress, creating PRs, and keeping things organized across sessions. That's a lot of cat herding.

This system handles the full lifecycle — from a conversation about what you want to build, through structured planning artifacts, to deterministic step-by-step implementation with a live progress dashboard. You discuss the idea, approve the plan, and then watch it execute.

**Why does this exist?** LLMs are capable at individual tasks, but they need structure to stay on track across multi-step work. Left to their own devices, they'll skip steps, repeat work, or wander off course. This system provides guardrails: file-based records as the source of truth, deterministic step selection (a Python script picks the next step — not the LLM), and a real-time dashboard so you can pause, resume, or stop at any point.

---

## How It All Fits Together

```
┌─────────────────────────────────────────────────────────────┐
│                        The Lifecycle                         │
│                                                              │
│   📋 Plan          ⚙️ Implement         📊 Monitor           │
│   ─────────        ──────────────       ──────────           │
│   /plan-roadmap    /implement-roadmap   Dashboard Service    │
│   /plan-bugfix     coordinator script   /progress-dashboard  │
│                    worker agents        /list-roadmaps       │
│                                                              │
│               All phases read and write:                     │
│                                                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │              📁 File Records                         │   │
│   │   Roadmaps/YYYY-MM-DD-FeatureName/                  │   │
│   │   Roadmap.md · State/ · History/                      │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                              │
│   Supported by:                                              │
│   roadmap_lib (Python) · roadmaps CLI · GitHub CLI (gh)      │
└─────────────────────────────────────────────────────────────┘
```

The three phases operate on shared **File Records** — markdown files with YAML frontmatter that live in your repo. The coordinator picks steps deterministically using regex-based parsing (no LLM judgment on what to do next). The dashboard service is intentionally decoupled: it knows nothing about git or files — agents push status updates to it via a REST API.

---

## The Lifecycle: From Idea to Shipped Feature

**1. You have an idea.** Maybe it's a new feature, maybe it's a batch of bugs. You run `/plan-roadmap` (or `/plan-bugfix-roadmap` for existing issues) and have a conversation about what you want to build.

**2. Planning produces artifacts.** The skill creates a Feature Roadmap containing both the feature definition (what and why) and the implementation steps. Drafts are written to `~/.roadmaps/` and moved to the repo by `/implement-roadmap`.

**3. Implementation is automated.** You run `/implement-roadmap`. A coordinator script reads the roadmap, picks the next incomplete step, and launches a worker agent to implement it. The worker implements, tests, commits, and updates the roadmap file. Repeat until done.

**4. You watch it work.** The dashboard service shows real-time progress — which step is running, what's complete, event logs. You can pause, resume, or stop from the dashboard UI.

**5. One PR wraps it up.** All steps are implemented on a shared feature branch in a single worktree. When everything's done, one atomic PR is created with all the changes.

[screenshot: overview dashboard showing roadmaps with progress bars]

[screenshot: detail dashboard showing steps, events, and controls]

---

## Component Reference

### Skills

Skills are Claude Code slash commands — you type `/skill-name` and Claude follows structured instructions. Each skill has a `SKILL.md` file with version-tracked instructions and a `references/` directory with supporting scripts.

---

#### `/plan-roadmap` (v8)

**What it does:** Two-phase collaborative planning for new features.

- **Phase 1 — Discussion:** Conversational exploration of the feature idea. No files created. Claude asks questions, you refine the scope.
- **Phase 2 — Planning:** Creates a single **Feature Roadmap** file containing the feature definition (goal, scope, acceptance criteria, verification strategy) and implementation steps with status, complexity, and dependencies.

Hard rule: this skill produces planning documents only. It will never write implementation code.

When planning is complete, it tells you to run `/implement-roadmap`.

---

#### `/plan-bugfix-roadmap` (v3)

**What it does:** Lightweight roadmap generator for batches of existing bugs.

Takes a list of GitHub issue numbers (or `all`) and produces the same artifacts as `/plan-roadmap` — but skips the discussion phase. You already know what the bugs are.

- Fetches issue details from GitHub
- Groups and orders by component automatically
- Requires only one approval — shows the full plan, then writes everything
- No new issues created (reuses existing ones)

```
/plan-bugfix-roadmap 17 18 19 20
/plan-bugfix-roadmap all
```

---

#### `/implement-roadmap` (v19)

**What it does:** Deterministic coordinator for automated feature implementation.

This is the main implementation engine. It:

1. Resolves which roadmap to implement (or asks you to choose)
2. Creates a feature branch and shared git worktree
3. Writes an `Implementing` state file to mark the roadmap as in-progress
4. Loops: a Python coordinator script picks the next incomplete step → launches a worker agent via the `Agent` tool → worker implements, tests, and commits → coordinator picks the next step
5. Creates a single atomic PR when all steps are complete

**Key design decision:** Step selection is handled by a deterministic Python script (`references/coordinator`) that parses the roadmap with regex. The LLM never decides which step to do next — it just follows orders.

The coordinator also syncs progress to the dashboard service, so you get real-time updates.

[screenshot: terminal output showing coordinator picking steps]

---

#### `/implement-roadmap-interactively` (v10)

**What it does:** Interactive step-by-step implementation with human review checkpoints.

The slower, more deliberate alternative to `/implement-roadmap`. Each step gets:

- Its own git worktree
- Its own PR
- A code review and security review
- A checkpoint summary requiring your acknowledgment before proceeding

Use this when you want to review each step individually rather than letting the system run autonomously.

---

#### `/list-roadmaps` (v5)

**What it does:** Quick scan of all active roadmaps with progress bars.

Runs a script that finds all roadmaps in the current repo and displays them with status, step counts, and a visual progress bar. One line per roadmap.

```
/list-roadmaps
```

---

#### `/describe-roadmap` (v4)

**What it does:** Detailed view of a single roadmap.

Shows the goal, progress summary, and every step with its status, complexity, GitHub issue, PR, and dependencies. If multiple roadmaps exist, prompts you to choose one. Offers to launch `/implement-roadmap` when you're done reviewing.

```
/describe-roadmap
/describe-roadmap DashboardBugfixes
```

---

#### `/progress-dashboard` (v17)

**What it does:** Reusable live progress dashboard for any agent or skill.

A lightweight, self-contained progress display that works independently of the main dashboard service. Starts a tiny Python HTTP server, opens a browser, and polls a JSON file for updates every 3 seconds.

- The `dash` CLI tool manages the server and state
- Any skill or agent can update progress with simple commands
- Supports pause/resume/stop controls via `control.json`
- Feature-scoped via `DASH_FEATURE` env var for concurrent session isolation

```bash
# Initialize with steps
python3 "$DASH_CLI" init "MyFeature" "Step 1" "Step 2" "Step 3"

# Update progress
python3 "$DASH_CLI" step-start 1
python3 "$DASH_CLI" step-complete 1

# Check for user controls (pause/stop)
python3 "$DASH_CLI" check-control
```

---

#### `/generate-test-roadmap` (v2)

**What it does:** Creates a complete test roadmap for exercising the implementation workflow.

Generates all planning artifacts (Roadmap, GitHub issues) in one shot with no user interaction. The test feature is deliberately trivial — 20 steps that each append a line to `roadmap-test.md`. The content is cat-herding themed, because of course it is.

Useful for integration testing and demos.

---

#### `/review-claude-extension` (v2)

**What it does:** Validates skills and agents against best practices.

Takes a path to a skill or agent directory and produces a structured report with PASS/WARN/FAIL ratings. Checks structure, content quality, and adherence to the Claude Code skills specification.

Read-only — it never modifies the files it's reviewing.

```
/review-claude-extension skills/plan-roadmap
/review-claude-extension agents/implement-step-agent.md
```

---

### Agents

Agents are autonomous workers launched by the `Agent` tool. Unlike skills (which run in your conversation), agents run as subprocesses with their own context.

---

#### `implement-step-agent` (v4)

**What it does:** Implements exactly one roadmap step.

The worker bee of the system. Launched by `/implement-roadmap`'s coordinator, it receives a step number and details, then:

1. Parses the step specification from its task prompt
2. Implements the change in the shared worktree
3. Runs tests
4. Commits with a descriptive message
5. Updates the roadmap file to mark the step as complete
6. Comments on the GitHub issue

Runs with `bypassPermissions` for unattended execution. Uses `git -C <worktree>` commands (never `cd && git`) to avoid security prompts.

---

### Services

#### Dashboard Service

**What it does:** Flask-based REST API and web UI for real-time roadmap progress tracking.

A generic progress tracking service — it knows nothing about git, files, or Claude Code. Skills and agents push data to it via REST endpoints. This separation means the dashboard can display progress from any source.

**Components:**

| File | Purpose |
|------|---------|
| `services/dashboard/app.py` | Flask app factory, health check, static serving |
| `services/dashboard/db.py` | SQLite schema with WAL mode, migrations, foreign keys |
| `services/dashboard/models.py` | Data access layer (CRUD operations) |
| `services/dashboard/server.sh` | Lifecycle script (start/stop/status/restart) |
| `services/dashboard/api/` | Route handlers for roadmaps, steps, state, history, controls, SSE, sync |
| `services/dashboard/static/overview.html` | Homepage — all roadmaps with progress bars and project filter |
| `services/dashboard/static/dashboard.html` | Detail view — steps, issues, PRs, event log, pause/resume/stop |

**Database (SQLite):** Stores roadmaps, definitions, steps, GitHub issues, PRs, runtime events, and user preferences. Uses WAL mode for concurrent reads.

**API highlights:**
- CRUD for roadmaps and steps
- State transitions (Ready → Implementing → Complete)
- Server-Sent Events (SSE) for real-time UI updates
- Sync endpoints for agents to push bulk data
- Control endpoints for pause/resume/stop

```bash
# Start the service
bash services/dashboard/server.sh start

# Check status
bash services/dashboard/server.sh status
```

Default port: `8888` (configurable via `DASHBOARD_PORT`).

[screenshot: overview dashboard with project filter dropdown]

[screenshot: detail dashboard with step progress and event log]

---

### Libraries & CLI Tools

#### `roadmap_lib.py`

**What it does:** Shared Python library for roadmap discovery, parsing, and state management.

The foundation that everything else builds on. No external dependencies — uses a custom YAML frontmatter parser (no PyYAML needed).

**Key functions:**
- `find_roadmap_dirs()` — Scan for roadmap directories
- `parse_frontmatter()` — Extract YAML metadata from markdown files
- `current_state()` — Determine lifecycle state from State/ directory
- `count_steps()` — Parse step status from roadmap files
- `is_active()`, `is_implementable()`, `is_running()` — State predicates
- `create_planning_dir()`, `create_state_file()` — Planning utilities

---

#### `dashboard_client.py`

**What it does:** REST client library for the dashboard service.

No external dependencies (uses stdlib `urllib`). Configurable via `DASHBOARD_URL` env var, `~/.claude/dashboard.conf`, or falls back to `http://localhost:8888`.

```python
from dashboard_client import DashboardClient
client = DashboardClient()
client.create_roadmap(roadmap_id, name, steps)
client.begin_step(roadmap_id, step_number)
client.finish_step(roadmap_id, step_number)
```

---

#### `roadmaps` CLI

**What it does:** Cross-repo roadmap scanner and management tool.

Scans all repos in `~/projects/` (configurable) for roadmaps and provides a unified view.

```bash
roadmaps --list                    # Active roadmaps (running + ready)
roadmaps --list --running          # Only running roadmaps
roadmaps --list --all              # Everything including completed/archived
roadmaps --list --search "dash"    # Filter by name
roadmaps --list-dashboards         # Show all dashboard URLs
roadmaps --monitor                 # Live monitor (refreshes every 30s)
roadmaps --archive-completed       # Archive all completed roadmaps
roadmaps --decline                 # Interactively decline roadmaps
```

[screenshot: terminal output of roadmaps --list showing multiple repos]

---

## File Records

During planning and implementation, roadmaps live in their own directory under `~/.roadmaps/<project>/` with State/ and History/ subdirectories for lifecycle tracking.

When implementation is complete, only the **Roadmap.md** file is copied to the repo as a flat file:

```
Roadmaps/
├── DashboardBugfixes-Roadmap.md
├── AuthMiddleware-Roadmap.md
└── UserSettings-Roadmap.md
```

**`<FeatureName>-Roadmap.md`** has YAML frontmatter with a UUID, author, description, and change history. The body contains the feature definition sections (goal, platform, acceptance criteria, verification strategy), followed by implementation steps, a Deviations from Plan section, and a Change History section with commits, linked issues, and the PR.

The working directory (`~/.roadmaps/<project>/YYYY-MM-DD-<FeatureName>/`) retains State/ and History/ during the lifecycle but is cleaned up after the PR merges.

---

## Technology Stack

| Technology | Role |
|-----------|------|
| **Python 3** | Core language — roadmap_lib, coordinator, dashboard service, CLI tools, test suite |
| **Flask** | Dashboard REST API |
| **SQLite** | Dashboard database (WAL mode for concurrent reads) |
| **Bash** | Skill scripts, server lifecycle, install/uninstall |
| **HTML/CSS/JavaScript** | Dashboard web UI |
| **GitHub CLI (`gh`)** | Issue and PR automation |
| **Claude Code CLI (`claude`)** | Agent launching and skill execution |
| **Git** | Worktree management, branching, commits |
| **pytest** | Test suite (251+ unit tests plus integration tests) |

**No heavy dependencies.** The core libraries (`roadmap_lib`, `dashboard_client`) use only Python's standard library. The dashboard service needs Flask. That's about it.

---

## Testing

The test suite covers the full stack:

- **Unit tests** (`tests/unit/`): roadmap_lib parsing and discovery, coordinator step selection, dashboard client, all API endpoints, database operations, data models
- **Integration tests** (`tests/integration/`): end-to-end happy path, planning workflows, step ordering, error conditions, dashboard sync, cleanup

```bash
# Run all tests
pytest

# Run just unit tests
pytest tests/unit/

# Run a specific test file
pytest tests/unit/test_roadmap_lib.py
```

---

## Installation

```bash
# Install all skills and agents
bash install.sh

# Remove everything
bash uninstall.sh
```

Skills install to `~/.claude/skills/`, agents to `~/.claude/agents/`.

---

## Examples

_Coming soon — this section will include walkthroughs of common workflows:_

- [ ] Planning a new feature from scratch with `/plan-roadmap`
- [ ] Creating a bugfix roadmap from GitHub issues
- [ ] Running automated implementation with `/implement-roadmap`
- [ ] Using the interactive workflow for careful review
- [ ] Monitoring progress across multiple repos
- [ ] Using the dashboard service

---

## Project Structure

```
cat-herding/
├── skills/                          # Claude Code skills (slash commands)
│   ├── plan-roadmap/                # Feature planning
│   ├── plan-bugfix-roadmap/         # Bugfix planning
│   ├── implement-roadmap/           # Automated implementation
│   ├── implement-roadmap-interactively/  # Interactive implementation
│   ├── list-roadmaps/              # Quick roadmap listing
│   ├── describe-roadmap/           # Detailed roadmap view
│   ├── progress-dashboard/         # Live progress display
│   ├── generate-test-roadmap/      # Test roadmap generator
│   └── review-claude-extension/    # Skill/agent validator
├── agents/                          # Claude Code agents
│   └── implement-step-agent.md     # Worker agent for single steps
├── services/
│   └── dashboard/                   # Flask dashboard service
│       ├── app.py                   # App factory
│       ├── db.py                    # SQLite schema
│       ├── models.py                # Data access
│       ├── server.sh                # Lifecycle management
│       ├── api/                     # REST route handlers
│       └── static/                  # HTML/CSS/JS UI
├── scripts/                         # Shared libraries and CLI tools
│   ├── roadmap_lib.py              # Core roadmap library
│   ├── roadmaps.py                 # Cross-repo CLI
│   └── dashboard_client.py         # REST client
├── tests/                           # Test suite
│   ├── unit/                        # Unit tests
│   └── integration/                 # Integration tests
├── Roadmaps/                        # Roadmap file records (per-repo)
├── install.sh                       # Install skills and agents
└── uninstall.sh                     # Remove skills and agents
```
