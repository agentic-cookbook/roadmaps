# Cat Herding
My cat's name is Claude.

Shared repository of reusable Claude Code skills and agents.

Skills live in `skills/`, agents in `agents/`. Run `./install.sh` to install everything, or manually copy/symlink into `~/.claude/skills/` and `~/.claude/agents/`.

## Compatibility

| Platform | Status | Notes |
|----------|--------|-------|
| macOS | Supported | Symlink and copy both work |
| Linux | Supported | Symlink and copy both work |
| Windows (WSL) | Supported | Choose **copy** when prompted. Symlinks can fail across the WSL/Windows filesystem boundary (e.g., repo cloned to `/mnt/c/...`, skills installed to `~/.claude/`). If you keep the repo on the Linux filesystem (`~/...`), symlinks work fine. |

Both scripts require `bash`. The install script auto-detects WSL and uses `apt` for tool installation.

## Skills

### /plan-roadmap

Collaborative planning skill for new features. Guides you through discussing an idea, then produces structured planning artifacts — no implementation code.

**What it does:** Takes a feature idea from conversation to a concrete plan:

1. **Discussion** — Talk through the idea naturally. Claude asks questions, clarifies scope, and summarizes.
2. **Planning** — Creates a Feature Definition, Feature Roadmap, and GitHub issues.

The transition from Discussion to Planning requires your explicit permission.

**Usage:**

```
/plan-roadmap
```

The skill walks you through everything interactively.

**Workflow:**

```
Discussion Phase
  → "What feature would you like to plan?"
  → Conversation about the idea
  → Summary + proposed feature name
  → You approve the name

Phase Gate (requires your permission)
  → "May I transition from Discussion to Planning?"

Planning Phase
  → Feature Definition drafted, reviewed, approved, committed
  → Feature Roadmap drafted, reviewed, approved, committed
  → GitHub issues created and verified
  → Roadmap Phase set to "Ready"

Done → run /implement-roadmap-interactively to build it
```

**Key rules:**

- **No implementation code** — ever. This skill only produces Markdown planning files and GitHub issues.
- **Every draft is shown in full** and requires your approval before being written to disk.
- **Checkpoint gates** pause for your acknowledgment between major steps.
- **Phase gate** between Discussion and Planning requires explicit permission.

**Files created:**

- `Roadmaps/YYYY-MM-DD-<Name>/Definition.md`
- `Roadmaps/YYYY-MM-DD-<Name>/Roadmap.md`
- `Roadmaps/YYYY-MM-DD-<Name>/State/` (lifecycle state files)
- `Roadmaps/YYYY-MM-DD-<Name>/History/` (event log)
- GitHub issues (one per implementation step)

**Changelog:**

| Version | Date | Changes |
|---------|------|---------|
| v4 | 2026-03-23 | Per-directory File Record layout (`Roadmaps/YYYY-MM-DD-Name/`); YAML frontmatter; State/ directory for lifecycle; History/ for event log |
| v2 | 2026-03-21 | Added `version` field to frontmatter; added `--version` argument support; restructured into Discussion + Planning phases; added phase gate requiring user permission; added `Phase: Planning \| Ready` field to Roadmap; reinforced no-implementation-code guardrails; moved Active Guards to references/; added `disable-model-invocation: true`; shortened description for context budget |
| v1 | 2026-03-20 | Initial release — single-phase workflow with checkpoint gates and no-implementation-code guardrails |

---

### /plan-bugfix-roadmap

Lightweight roadmap generator for batches of bugfixes. Takes a list of existing GitHub issue numbers and produces a Feature Definition and Feature Roadmap, ready for `/implement-roadmap-interactively`.

**What it does:** Skips the discussion phase of `/plan-roadmap` — you already know the bugs. Fetches issue details from GitHub, groups and orders them by component, assigns complexity, and generates all planning artifacts with a single approval step.

**Usage:**

```
/plan-bugfix-roadmap 3 4 5 6 7 8 9 10 11 12 13 14
/plan-bugfix-roadmap all
```

Pass issue numbers, or `all` to include every open issue.

**Key differences from /plan-roadmap:**

| | /plan-roadmap | /plan-bugfix-roadmap |
|---|---|---|
| **Discussion** | Full back-and-forth exploration | None — bugs are already defined |
| **Approval gates** | Multiple checkpoints | Single approval of the full plan |
| **GitHub issues** | Creates new issues per step | Uses existing issues (creates only for new bugs) |
| **Use case** | New features, design exploration | Known bugs, batch fixes |

**Changelog:**

| Version | Date | Changes |
|---------|------|---------|
| v3 | 2026-03-23 | Per-directory File Record layout; YAML frontmatter; State/ directory for lifecycle |
| v1 | 2026-03-21 | Initial release — fetches issues from GitHub, groups by component, single-approval flow |

---

### /implement-roadmap

Uses a deterministic Python coordinator for step selection and launches `implement-step-agent` for each step. The coordinator reads the roadmap file with regex (no LLM judgment) and passes the exact step number to the worker agent.

**Usage:**

```
/implement-roadmap
/implement-roadmap MyFeature
```

**How it works:**

1. Coordinator (Python, deterministic) reads the roadmap, finds first non-Complete step
2. Launches `claude --agent implement-step-agent "Implement step N..."`
3. Worker agent implements ONE step, creates PR, merges, updates roadmap
4. Coordinator verifies completion, moves to next step
5. Repeats until all steps done

For interactive step-by-step control with checkpoints, use `/implement-roadmap-interactively` instead.

**Changelog:**

| Version | Date | Changes |
|---------|------|---------|
| v13 | 2026-03-23 | Per-directory File Record layout; completion writes State/Complete.md instead of git mv; History/ event logging; shared roadmap_lib |
| v9 | 2026-03-22 | Per-feature dashboard URL lookup by slug |
| v8 | 2026-03-22 | Show dashboard URL on startup |
| v7 | 2026-03-22 | Python coordinator + single-step worker agent — deterministic step selection, no LLM skipping |
| v6 | 2026-03-22 | Run agent in foreground by default; `-b`/`--background` flag for background mode |
| v5 | 2026-03-21 | Auto-select when only one roadmap available; print both skill and agent version when launching |
| v1 | 2026-03-21 | Initial release |

---

### /implement-roadmap-interactively

Implementation skill for features planned with `/plan-roadmap`. Works through each Roadmap step with proper isolation, testing, and review.

**What it does:** Picks up an implementable Feature Roadmap and works through it step by step:

1. **Selects** a feature from available roadmaps
2. **Acquires a lock** so no other session works on the same feature
3. **Implements each step** — one worktree, one PR, one review cycle per step
4. **Completes** — archives the roadmap, creates a feature summary, releases the lock

**Usage:**

```
/implement-roadmap-interactively
```

Requires a Roadmap created by `/plan-roadmap` with State: Ready.

**Workflow:**

```
Startup
  → Scans Roadmaps/ directories
  → Shows available features (filters by State: Ready)
  → You choose a feature

Per Step (repeats for each Roadmap step)
  → Plan the step
  → Create worktree + branch
  → Implement
  → Build + test
  → Create PR
  → Run reviews
  → Address findings
  → Merge PR
  → Update Roadmap + close issue
  → Checkpoint (wait for your acknowledgment)

Completion
  → Verify all steps done
  → Clean up worktrees
  → Update Feature Definition
  → Create Feature Summary
  → Write State/Complete.md
```

**Key rules:**

- **One step = one PR** — never combine steps, even if they seem small.
- **Never skip reviews** — every PR gets code review and security review.
- **State guard** — only features with State: Ready are available for implementation.
- **Checkpoint gates** — pause for your acknowledgment after every step.

**Changelog:**

| Version | Date | Changes |
|---------|------|---------|
| v10 | 2026-03-23 | Per-directory File Record layout; State/ replaces inline Status/Phase; completion writes State/Complete.md instead of git mv |
| v9 | 2026-03-22 | Inline bash grep/awk for step selection — self-enclosed, no external scripts |
| v8 | 2026-03-22 | Use standalone `next-step` script for step selection — no dashboard dependency |
| v7 | 2026-03-21 | Use `dash next-step` command for step selection — removes LLM judgment entirely |
| v6 | 2026-03-21 | Mechanical step selection: only use Status field, never skip steps based on description content |
| v5 | 2026-03-21 | Fix step selection: pick first non-complete step, so interrupted steps resume correctly |
| v4 | 2026-03-21 | Responsive stop/pause — control check at every sub-step boundary (12 per step, not 1) |
| v3 | 2026-03-21 | Strengthen sequential step enforcement — never work on two steps at once |
| v2 | 2026-03-21 | Enforce sequential step ordering — always pick lowest-numbered Not Started step |
| v1 | 2026-03-21 | Initial release — step-by-step implementation loop with worktrees, PRs, reviews, checkpoint gates; Phase guard for `Planning` features; concurrency lock via `Implementing` field |

---

### /generate-test-roadmap

Generates a complete test roadmap for exercising `/implement-roadmap-interactively` and `implement-roadmap-agent`. Creates all planning artifacts (Feature Definition, Feature Roadmap, 20 GitHub issues) in one shot with no user interaction.

**What it does:** Creates a silly cat-herding themed feature with 20 trivial steps that each append a line to `roadmap-test.md`. The output is structurally identical to what `/plan-roadmap` produces, so the implementation agent can pick it up.

**Usage:**

```
/generate-test-roadmap
```

No arguments, no prompts, no approvals. Just run it and it creates everything.

**Changelog:**

| Version | Date | Changes |
|---------|------|---------|
| v1 | 2026-03-21 | Initial release — 20-step cat-herding test roadmap generator |

---

### /list-roadmaps

Lists all active roadmaps with progress bar, step counts, and a one-line description from the Feature Definition.

**Usage:**

```
/list-roadmaps
```

No arguments needed.

**Changelog:**

| Version | Date | Changes |
|---------|------|---------|
| v5 | 2026-03-22 | Per-feature dashboard URL lookup by slug; clickable OSC 8 links |
| v4 | 2026-03-22 | Print version on invocation; dashboard URL inline per roadmap |
| v3 | 2026-03-22 | Show dashboard URL when dashboard is running |
| v2 | 2026-03-22 | Concise output — progress bar, counts, goal summary from Feature Definition |
| v1 | 2026-03-22 | Initial release — scans active roadmaps, prints step summaries with status icons |

---

### /describe-roadmap

Shows detailed info about a single active roadmap — goal, progress, and all steps with status, complexity, issues, PRs, and dependencies. If multiple roadmaps exist, prompts to choose one. Offers to run `/implement-roadmap` at the end.

**Usage:**

```
/describe-roadmap
/describe-roadmap DashboardBugfixes
```

**Changelog:**

| Version | Date | Changes |
|---------|------|---------|
| v4 | 2026-03-22 | Per-feature dashboard URL lookup by slug; clickable OSC 8 links |
| v3 | 2026-03-22 | Print version on invocation; dashboard URL inline in header |
| v2 | 2026-03-22 | Show dashboard URL when dashboard is running |
| v1 | 2026-03-22 | Initial release — detailed roadmap view with selection and implement prompt |

---

### /progress-dashboard

Reusable live progress dashboard that any agent or skill can use to show real-time step-by-step progress in the browser. Opens a local web page that polls a JSON file for updates.

**What it does:**

1. Creates a temp directory with an HTML dashboard and a tiny Python HTTP server
2. Starts the server on a random port and opens the browser
3. The calling agent/skill writes `progress.json` to update the dashboard in real time
4. Dashboard auto-polls every 3 seconds and renders steps with status icons, progress bar, links, and event log

**Usage:**

```
/progress-dashboard MyFeature
```

Or invoke programmatically from another skill/agent — the skill returns the `DASH_DIR`, `DASH_PID`, and `DASH_PORT` for the caller to use.

**User controls:**

The dashboard has **Pause**, **Resume**, and **Stop** buttons. When clicked, they write a `control.json` file that the agent checks between steps:

- **Pause** — agent finishes current operation and waits
- **Resume** — agent continues where it left off
- **Stop** — agent finishes current operation, releases locks, and shuts down gracefully

**Integration:**

Both `/implement-roadmap-interactively` and `implement-roadmap-agent` automatically start the dashboard if the skill is available.

**Changelog:**

| Version | Date | Changes |
|---------|------|---------|
| v16 | 2026-03-22 | Fix inline status display; always show issue/PR names in steps; resizable event log pinned to bottom; debug info at end of step; named debug download; demo pause/resume |
| v15 | 2026-03-22 | Stop polling on complete; smart autoscroll (only if at bottom); resizable debug panel via drag |
| v14 | 2026-03-22 | Debug mode checkbox with copyable log panel; overlays scoped to steps pane only |
| v13 | 2026-03-21 | Add `next-step` command — mechanically returns lowest non-Complete step number from roadmap file |
| v12 | 2026-03-21 | Reset in-progress steps to not_started on error/stop — no stale spinners |
| v11 | 2026-03-21 | Clear stale steps/issues/PRs on restart — `load-roadmap` repopulates from roadmap file |
| v10 | 2026-03-21 | Fix overlay + port: clear `control_state` and events on restart; resolve macOS `/var` vs `/private/var` symlink; clear all overlays when no active control |
| v9 | 2026-03-21 | Fix port stability: wait for old server to die before reusing port; remove bind test |
| v8 | 2026-03-21 | Stop polling on complete/error, but keep heartbeat that triggers full page reload on restart |
| v7 | 2026-03-21 | Fix: poll forever with simple setInterval — previous arguments.callee approach was broken |
| v6 | 2026-03-21 | Never stop polling — slow down when done so overlays clear when dashboard restarts |
| v5 | 2026-03-21 | Clear stale stop/completion overlays when dashboard restarts in running state |
| v4 | 2026-03-21 | Persist port in dashboard directory for reliable reuse across restarts; `begin-step` auto-closes any other in-progress step to enforce single-active-step |
| v3 | 2026-03-21 | Deterministic dashboard directory per feature name; reuse existing state on restart; reuse previous port; clear stale control state |
| v2 | 2026-03-21 | Added `dash` CLI helper script — single-command interface for init, step updates, control checks, and shutdown |
| v1 | 2026-03-21 | Initial release — live HTML dashboard with progress polling, Pause/Resume/Stop controls, custom Python server for bidirectional communication |

---

### /review-claude-extension

Review skill for validating Claude Code skills and agents against Anthropic's official best practices. Produces a structured report with PASS/WARN/FAIL ratings and actionable recommendations.

**What it does:** Takes a skill or agent path and runs a comprehensive review:

1. **Resolves** the target — detects whether it's a skill (has `SKILL.md`) or an agent (`.md` with agent frontmatter)
2. **Reads** all target files and parses frontmatter
3. **Fetches** the latest Anthropic guidance from official docs
4. **Reviews** against a bundled checklist covering structure, content quality, best practices, and agent-specific criteria
5. **Prints** a console report with per-check ratings and a prioritized recommendations list

**Usage:**

```
/review-claude-extension path/to/skill-or-agent
```

If no path is given, the skill looks for a skill or agent in the current directory.

**Review categories:**

- **Structure & Format** (S01–S12) — frontmatter fields, file layout, naming conventions
- **Content Quality** (C01–C10) — single responsibility, step-by-step instructions, error handling
- **Best Practices** (B01–B12) — verification methods, anti-patterns, context budget
- **Agent-Specific** (A01–A08) — tool access, permission modes, turn limits (only for agents)

**Key rules:**

- **Read-only** — never modifies the reviewed skill or agent.
- **Console output only** — no files are created.
- **Fetches latest docs** — supplements the bundled checklist with current Anthropic guidance (continues with bundled checklist alone if fetch fails).

**Changelog:**

| Version | Date | Changes |
|---------|------|---------|
| v2 | 2026-03-21 | Added `allowed-tools` restriction, `context: fork` for isolated execution, `version` field, and `--version` support |
| v1 | 2026-03-21 | Initial release — comprehensive review checklist (S01–S12, C01–C10, B01–B12, A01–A08); fetches latest Anthropic docs; structured PASS/WARN/FAIL report |

---

## Agents

### implement-step-agent

Single-step worker agent. Receives one step number and its details in the prompt, implements it (worktree, PR, review, merge), updates the roadmap, and returns. Used by the `/implement-roadmap` coordinator.

**Usage:**

Called by the coordinator script — not typically invoked directly. But can be:

```bash
claude --agent implement-step-agent "Implement step 1 of MyFeature. Step 1: Description. Issue: #17. Roadmap: path/to/roadmap.md"
```

**Key rules:**

- Implements ONLY the step in its prompt — cannot skip or see other steps
- One step = one worktree, one PR, one review, one merge
- Updates the roadmap status to Complete when done
- On failure: logs the error and returns

**Changelog:**

| Version | Date | Changes |
|---------|------|---------|
| v1 | 2026-03-22 | Initial release — single-step worker, replaces the multi-step implement-roadmap-agent |
| v1 | 2026-03-21 | Initial release — autonomous implementation agent with bypassPermissions, worktree isolation, and error-handling-with-lock-release |
