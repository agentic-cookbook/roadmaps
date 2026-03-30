# Should Roadmaps Be a Claude Code Plugin?

**Date:** 2026-03-30
**Decision:** Keep install.sh for now. Revisit when distribution becomes a priority.

## Context

Cat-herding currently installs via `install.sh` which symlinks skills, agents, rules, and scripts into `~/.claude/`. The question is whether converting to a Claude Code plugin would be better for distribution, versioning, and user experience.

## What a Plugin Can Contain

| Component | Supported? | Notes |
|-----------|-----------|-------|
| Skills (SKILL.md) | Yes | Core plugin capability |
| Agents (.md) | Yes | Core plugin capability |
| Hooks (hooks.json) | Yes | Newer capability — PostToolUse, SessionStart, etc. |
| MCP servers | Yes | Could potentially replace the Flask dashboard |
| Rules | No direct support | No `rules/` directory in plugin spec |
| Settings defaults | Yes | Plugin can ship a `settings.json` |
| Python scripts in references/ | Yes | Referenced by skills, NOT installed to PATH |
| Backend services (Flask) | Not directly | Could be wrapped as MCP server or started via hook |
| CLI tools on PATH | No | Plugins don't install binaries |
| Persistent storage | Yes | `${CLAUDE_PLUGIN_DATA}` survives updates |

## What Cat-Herding Has vs What Fits

| Component | Fits in plugin? | Notes |
|-----------|----------------|-------|
| 10 skills | Yes | Direct fit |
| 1 agent | Yes | Direct fit |
| 4 rules | Partial | Need hook to copy to `.claude/rules/` |
| ExitPlanMode hook | Yes | Via `hooks/hooks.json` |
| `dash` CLI | Yes | Already in skill references/ |
| `coordinator` script | Yes | Already in skill references/ |
| `roadmap_lib.py` | Yes | Move to references/ |
| `dashboard_client.py` | Yes | Move to references/ |
| Flask dashboard service | No | Biggest blocker |
| `roadmaps.py` CLI | No | Needs PATH installation |

## Pros of Converting to Plugin

- **Distribution**: `claude plugin install cat-herding@marketplace` vs "clone repo, run ./install.sh"
- **Auto-updates**: Marketplace-driven, no manual git pull
- **Version management**: Semantic versioning, per-project pinning, rollback
- **Discovery**: Other Claude Code users can find it
- **Scope control**: User-level vs project-level enabling
- **No symlink fragility**: Claude Code manages the cache

## Cons of Converting to Plugin

- **Namespacing**: Skills become `/cat-herding:plan-roadmap` instead of `/plan-roadmap`
- **Still need install.sh**: For dashboard service, CLI tools, rules — not a clean single-step install
- **Dashboard is the core UX**: The most visible part (browser dashboard) can't be in the plugin
- **Complexity**: Maintaining both a plugin and an install script is more work
- **Rules gap**: Rules need a workaround (SessionStart hook to copy files)
- **Iteration friction**: Plugin packaging adds overhead while the project is still changing rapidly

## The Dashboard Problem

The Flask dashboard is the biggest obstacle. Three options if converting:

**A. MCP server** — Convert to MCP server managed by plugin. Gains: plugin-native. Loses: browser UI needs separate serving.

**B. SessionStart hook** — Start Flask server on session start if not running. Gains: automatic. Loses: lifecycle management is messy.

**C. Keep install.sh for dashboard** — Plugin handles skills/agents/hooks. install.sh handles just the dashboard. Gains: clean separation. Loses: still need manual step.

## Bottom Line

**Net positive for distribution, net negative for iteration speed.** If the goal is sharing with others — convert skills/agents/hooks to a plugin, keep a slim install.sh for the dashboard. If it's just personal/team use, the current install.sh approach is simpler and more flexible while the project is still changing rapidly.

Decision: keep as-is for now.
