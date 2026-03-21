# /implement-feature

Implementation skill for features planned with `/plan-feature`. Works through each Roadmap step with proper isolation, testing, and review.

## What It Does

Picks up a Feature Roadmap from `Active-Roadmaps/` and implements it step by step:

1. **Selects** a feature from available roadmaps
2. **Acquires a lock** so no other session works on the same feature
3. **Implements each step** — one worktree, one PR, one review cycle per step
4. **Completes** — archives the roadmap, creates a feature summary, releases the lock

## Usage

```
/implement-feature
```

Requires a Roadmap created by `/plan-feature` with `Phase: Ready`.

## Workflow

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

## Examples

**Implementing a planned feature:**
```
You: /implement-feature
Claude: Available features to implement:
        1. DarkModeSupport — 0/4 steps complete (Not Started)
        Which feature would you like to implement?
You: 1
Claude: [acquires lock, starts Step 1]
...
Claude: Step 1 complete:
          - PR: #42 — merged
          - Issue: #15 — closed
        Next: Step 2 — Add theme toggle component
You: continue
```

**Feature still in planning:**
```
You: /implement-feature
Claude: Still in planning phase (not yet available):
        - NewAuth — planning in progress, run /plan-feature to complete
        No features available for implementation.
```

## Key Rules

- **One step = one PR** — never combine steps, even if they seem small.
- **Never skip reviews** — every PR gets code review and security review.
- **Concurrency lock** — `Implementing: Yes` prevents other sessions from working on the same feature.
- **Phase guard** — features with `Phase: Planning` are not available for implementation.
- **Checkpoint gates** — pause for your acknowledgment after every step.

## Lock Management

The `Implementing` field in the Roadmap prevents concurrent work:

| State | Meaning |
|-------|---------|
| `No`  | Available for implementation |
| `Yes` | Another session is actively implementing |

If a session crashes, the lock stays. Manually edit the Roadmap to set `Implementing: No` to release it.

## Changelog

### v1 (2026-03-21)
- Added `version: 1` to SKILL.md frontmatter
- Added Phase guard: features with `Phase: Planning` are excluded from available features
- Added "Not Ready (Still Planning)" category to startup scan
- Baseline implementation: step-by-step loop with worktrees, PRs, reviews, and checkpoint gates
