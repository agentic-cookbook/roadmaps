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

Done → run /implement-roadmap to build it
```

**Key rules:**

- **No implementation code** — ever. This skill only produces Markdown planning files and GitHub issues.
- **Every draft is shown in full** and requires your approval before being written to disk.
- **Checkpoint gates** pause for your acknowledgment between major steps.
- **Phase gate** between Discussion and Planning requires explicit permission.

**Files created:**

- `.claude/Features/FeatureDefinitions/<Name>-FeatureDefinition.md`
- `.claude/Features/Active-Roadmaps/<Name>-FeatureRoadmap.md`
- GitHub issues (one per implementation step)

**Changelog:**

| Version | Date | Changes |
|---------|------|---------|
| v2 | 2026-03-21 | Restructured into Discussion + Planning phases; added phase gate requiring user permission; added `Phase: Planning \| Ready` field to Roadmap; reinforced no-implementation-code guardrails; moved Active Guards to references/; added `disable-model-invocation: true`; shortened description for context budget; removed `version` from frontmatter |
| v1 | 2026-03-20 | Initial release — single-phase workflow with checkpoint gates and no-implementation-code guardrails |

---

### /implement-roadmap

Implementation skill for features planned with `/plan-roadmap`. Works through each Roadmap step with proper isolation, testing, and review.

**What it does:** Picks up a Feature Roadmap from `Active-Roadmaps/` and implements it step by step:

1. **Selects** a feature from available roadmaps
2. **Acquires a lock** so no other session works on the same feature
3. **Implements each step** — one worktree, one PR, one review cycle per step
4. **Completes** — archives the roadmap, creates a feature summary, releases the lock

**Usage:**

```
/implement-roadmap
```

Requires a Roadmap created by `/plan-roadmap` with `Phase: Ready`.

**Workflow:**

```
Startup
  → Scans Active-Roadmaps/
  → Shows available features (filters out Planning phase and locked features)
  → You choose a feature
  → Lock acquired

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
  → Archive Roadmap
  → Release lock
```

**Key rules:**

- **One step = one PR** — never combine steps, even if they seem small.
- **Never skip reviews** — every PR gets code review and security review.
- **Concurrency lock** — `Implementing: Yes` prevents other sessions from working on the same feature.
- **Phase guard** — features with `Phase: Planning` are not available for implementation.
- **Checkpoint gates** — pause for your acknowledgment after every step.

**Lock management:**

The `Implementing` field in the Roadmap prevents concurrent work. If a session crashes, the lock stays — manually edit the Roadmap to set `Implementing: No` to release it.

**Changelog:**

| Version | Date | Changes |
|---------|------|---------|
| v1 | 2026-03-21 | Initial release — step-by-step implementation loop with worktrees, PRs, reviews, checkpoint gates; Phase guard for `Planning` features; concurrency lock via `Implementing` field |

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
| v2 | 2026-03-21 | Added `allowed-tools` restriction and `context: fork` for isolated execution |
| v1 | 2026-03-21 | Initial release — comprehensive review checklist (S01–S12, C01–C10, B01–B12, A01–A08); fetches latest Anthropic docs; structured PASS/WARN/FAIL report |

---

## Agents

### implement-roadmap-agent

Autonomous version of `/implement-roadmap`. Runs the same implementation workflow — worktrees, PRs, reviews, merges — without stopping for user input.

**How it differs from the skill:**

| | /implement-roadmap (skill) | implement-roadmap-agent (agent) |
|---|---|---|
| **Interaction** | Interactive — pauses at checkpoints for your acknowledgment | Autonomous — logs summaries and continues |
| **Feature selection** | You choose from a menu | Feature name passed in the task prompt |
| **Permissions** | Inherits session permissions | `bypassPermissions` — no prompts |
| **Isolation** | Runs in your session | Runs in its own git worktree |
| **Use case** | You want to supervise each step | Fire and forget |

**Usage:**

Tell Claude to use the agent:

```
Use the implement-roadmap-agent agent to implement FeatureX
```

Or invoke directly:

```bash
claude --agent implement-roadmap-agent "Implement FeatureX"
```

Requires a Roadmap created by `/plan-roadmap` with `Phase: Ready`.

**Key rules:**

- Same one-step-one-PR discipline as the interactive skill
- Same review requirements — every PR gets code review and security review
- Same concurrency lock — acquires on start, releases on completion or error
- On failure: logs the error, releases the lock, and stops (never retries silently)

**Changelog:**

| Version | Date | Changes |
|---------|------|---------|
| v1 | 2026-03-21 | Initial release — autonomous implementation agent with bypassPermissions, worktree isolation, and error-handling-with-lock-release |
