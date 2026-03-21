# Cat Herding

Shared repository of reusable Claude Code skills and agents.

Skills in this repo are developed in the top-level `skills/` directory. To use them, copy or symlink the skill directory into `.claude/skills/` (project-level) or `~/.claude/skills/` (personal).

## Skills

### /plan-feature

Collaborative planning skill for new features. Guides you through discussing an idea, then produces structured planning artifacts — no implementation code.

**What it does:** Takes a feature idea from conversation to a concrete plan:

1. **Discussion** — Talk through the idea naturally. Claude asks questions, clarifies scope, and summarizes.
2. **Planning** — Creates a Feature Definition, Feature Roadmap, and GitHub issues.

The transition from Discussion to Planning requires your explicit permission.

**Usage:**

```
/plan-feature
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

Done → run /implement-feature to build it
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

### /implement-feature

Implementation skill for features planned with `/plan-feature`. Works through each Roadmap step with proper isolation, testing, and review.

**What it does:** Picks up a Feature Roadmap from `Active-Roadmaps/` and implements it step by step:

1. **Selects** a feature from available roadmaps
2. **Acquires a lock** so no other session works on the same feature
3. **Implements each step** — one worktree, one PR, one review cycle per step
4. **Completes** — archives the roadmap, creates a feature summary, releases the lock

**Usage:**

```
/implement-feature
```

Requires a Roadmap created by `/plan-feature` with `Phase: Ready`.

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
