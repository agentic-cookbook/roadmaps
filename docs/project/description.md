# Roadmaps

A feature planning and implementation system for Claude Code that transforms ideas into shipped code through structured planning, automated step execution, and live progress dashboards.

## Purpose

Roadmaps handles the full lifecycle from conversational planning through deterministic step-by-step implementation with real-time progress monitoring. It provides Claude Code skills for planning, agent workers for execution, and a Flask-based dashboard for tracking progress across active roadmaps.

## Key Features

- Structured planning artifacts (roadmap YAML files with steps, dependencies, acceptance criteria)
- Automated step-by-step implementation via Claude Code agent workers
- Real-time Flask dashboard with SQLite backend for live progress tracking
- GitHub issue and PR automation via `gh` CLI
- Git worktree management for parallel feature development
- 250+ unit tests plus integration test suite

## Tech Stack

- **Language:** Python 3
- **Dashboard:** Flask + SQLite (WAL mode) + HTML/CSS/JavaScript
- **Testing:** pytest (250+ tests)
- **Integration:** Claude Code CLI, GitHub CLI (`gh`), git worktrees
- **Design:** No heavy external dependencies — core libraries use Python stdlib only

## Status

Active development.

## Related Projects

- [Cookbook](../../cookbook/docs/project/description.md) — knowledge base for the agentic ecosystem
- [Dev Team](../../dev-team/docs/project/description.md) — multi-agent platform for product discovery
- [Tools](../../tools/docs/project/description.md) — companion skills and rules
