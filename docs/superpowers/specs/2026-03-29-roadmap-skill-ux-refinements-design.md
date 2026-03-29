# Roadmap Skill UX Refinements — Design Spec

**Date:** 2026-03-29
**Status:** Approved

## Problem

Three UX issues with the roadmap skill system:

1. **Rigid invocation** — Users must type `/plan-roadmap` explicitly. Saying "make this into a roadmap" or "convert this plan" does nothing. No proactive offering after normal planning sessions.
2. **Slow launch feel** — Step 0 runs four sequential validation checks before the user sees anything. The skill feels heavyweight to start.
3. **Non-deterministic output** — The same skill shows different text in different sessions. Prompts, gates, and status messages get paraphrased by the model.

## Design

### 1. Auto-invoke — Frontmatter and Description Changes

Remove `disable-model-invocation: true` from skills where auto-invoke is appropriate. Enrich descriptions with trigger phrases for semantic matching.

**Skills that get auto-invoke enabled:**

| Skill | New Description |
|-------|----------------|
| plan-roadmap | "Plan a new feature as a structured Roadmap with steps and PRs. Use when the user wants to plan a feature, create a roadmap, convert a plan to a roadmap, make a plan into a roadmap, organize work into steps, or save a plan as a roadmap." |
| plan-bugfix-roadmap | "Create a bugfix roadmap from GitHub issues. Use when the user wants to plan bug fixes, organize issues into a roadmap, or batch fix multiple bugs." |
| list-roadmaps | "List active roadmaps with progress. Use when the user asks what roadmaps exist, wants to see roadmap status, or asks about pending work." |
| describe-roadmap | "Show detailed info about a roadmap — goal, progress, steps. Use when the user wants to inspect a roadmap, see step details, check progress, or review what's left." |
| repair-roadmap | "Repair a broken or stuck roadmap by re-planning incomplete steps. Use when a roadmap has stuck steps, needs re-planning, or the user says a roadmap is broken." |

**Skills that keep `disable-model-invocation: true`:**

| Skill | Reason |
|-------|--------|
| implement-roadmap | Heavy side effects — creates worktrees, PRs, pushes code |
| implement-roadmap-interactively | Same side effects |
| generate-test-roadmap | Testing tool, not user-facing |

**progress-dashboard** also has `disable-model-invocation: true`. It stays disabled — it has restricted `allowed-tools` and is designed to be explicitly invoked during implementation, not auto-triggered.

### 2. Conversion Mode — New Entry Path for plan-roadmap

When plan-roadmap is invoked and a plan or feature discussion already exists in the conversation context, it enters **conversion mode** instead of starting Phase 1 from scratch.

**New Step 0e: Context Detection** (inserted after validation, before Step 1):

1. Claude examines the conversation history for a pre-existing plan. A plan is detected if ANY of these are true:
   - The conversation contains output from plan mode (ExitPlanMode was called)
   - The conversation contains a numbered or bulleted list of implementation steps (3+ steps)
   - The conversation contains a brainstorming spec or design document
   - The user explicitly said "convert this" / "make this into a roadmap" (i.e., referencing existing context)
2. If a plan is detected → enter conversion mode:
   - Skip Phase 1 (Discussion) entirely
   - Synthesize a discussion summary from what's already in context
   - Propose a feature name
   - Go straight to the Phase Gate prompt (Step 3)
   - Proceed to Phase 2 as normal
3. If no plan exists → proceed to Phase 1 (Discussion) as normal

The Phase Gate is still mandatory in conversion mode. The user must approve the summary and name before any files are created.

**Note:** `references/active-guards.md` must be updated to clarify that the "Discussion → Planning" guard refers to the Phase Gate approval checkpoint, not to requiring Phase 1 to have occurred. The guard protects the user's right to approve the transition, not the existence of a discussion phase.

### 3. Instant Feel — Batched Validation

Replace the four sequential validation steps with a single bash call that runs while the user sees the greeting.

**New flow:**
```
plan-roadmap v13

What feature would you like to plan?
[single bash call validates in background]
```

**The single bash call:**
```bash
git rev-parse --is-inside-work-tree && \
PROJECT=$(basename $(git rev-parse --show-toplevel)) && \
mkdir -p "$HOME/.roadmaps/$PROJECT" && \
touch "$HOME/.roadmaps/$PROJECT/.verify" && \
rm "$HOME/.roadmaps/$PROJECT/.verify" && \
echo "OK:$PROJECT"
```

If output is `OK:<project>`, validation passed silently. If it fails, Claude interrupts with the specific error.

Planning log setup is deferred to Step 5f when the roadmap directory is created. No early accumulation of log entries.

### 4. Deterministic UX — Verbatim Convention

A convention at the top of plan-roadmap (and eventually all roadmap skills) that declares certain text blocks as literal output.

**Output Rules section added to the top of the skill:**

```
Text inside VERBATIM blocks MUST be printed exactly as written —
character for character. No paraphrasing, no rewording, no additions,
no omissions. Do not add greetings, commentary, or transitions
around verbatim output.
```

**All fixed user-facing messages become VERBATIM blocks:**
- Version announcement
- Opening question ("What feature would you like to plan?")
- Phase Gate prompt (Step 3)
- Alignment failure warning (Step 5c)
- Draft approval prompt (Step 5d)
- Planning complete summary (Step 6c)
- All error messages

**Messages that stay flexible (not verbatim):**
- Conversational discussion in Phase 1 (Step 2) — meant to be natural
- Discussion summary content — generated, not scripted
- Clarifying questions during exploration — contextual

Structure: fixed scaffolding, flexible conversation.

**Limitation:** This is a convention enforced by instruction, not by runtime. The model may still occasionally paraphrase, especially in long conversations where the instruction scrolls out of active attention. This is a mitigation that significantly improves consistency, not a guarantee of byte-identical output.

### 5. The Hook — Intelligent Roadmap Offering

A `PostToolUse` hook on `ExitPlanMode` that triggers Claude to evaluate whether the just-completed plan warrants a Roadmap.

**Hook configuration — added to the `PostToolUse` array in `~/.claude/settings.json` (global, so it applies to all projects that have roadmap skills installed):**

```json
{
  "matcher": "ExitPlanMode",
  "hooks": [
    {
      "type": "command",
      "command": "echo '{\"systemMessage\":\"ROADMAP-EVAL: Consider the plan just discussed. Would it benefit from being tracked as a multi-step Roadmap with individual PRs per step? If yes, offer to convert it with one line. If no, say nothing.\"}'"
    }
  ]
}
```

**Mechanism:** PostToolUse hook stdout is parsed as JSON. The `systemMessage` field is included in Claude's context. Claude then acts on the instruction.

**Claude's behavior after receiving the additionalContext:**
- Evaluates plan complexity against conversation context
- Simple changes (rename, config, one-file fix) → says nothing
- Multi-step, multi-PR work → offers one line: "This looks like it could benefit from a structured Roadmap. Want me to convert it? (/plan-roadmap)"
- If the user ignores or declines, Claude moves on. No follow-up.
- If plan-roadmap is already active, the hook stays silent.

**Installation:** `install.sh` merges this entry into the existing `PostToolUse` array in `~/.claude/settings.json`. It must not overwrite existing PostToolUse hooks. `uninstall.sh` removes the `ExitPlanMode` matcher entry from the array.

### 6. The Rule File — ROADMAP-PLANNING-RULE.md

A lightweight rule in `.claude/rules/` that teaches Claude to recognize roadmap conversion intent during normal conversation.

**Content:**
```markdown
# Roadmap Planning Rule

## When to invoke /plan-roadmap automatically

If the user says any of the following (or similar), invoke the plan-roadmap
skill immediately:

- "make this into a roadmap"
- "convert this plan to a roadmap"
- "save this as a roadmap"
- "create a roadmap from this"
- "turn this into a roadmap"
- "roadmap this"

Do not ask for confirmation — the user's intent is clear. Invoke the skill.

## When NOT to invoke

- Do not offer a roadmap unprompted during normal conversation.
  The PostToolUse hook on ExitPlanMode handles that.
- Do not invoke if plan-roadmap is already active.
- Do not invoke for /implement-roadmap — that requires explicit invocation.
```

**Location:** This rule ships as part of the cat-herding repo in `.claude/rules/ROADMAP-PLANNING-RULE.md`. It is version-controlled like the other rules (PRINCIPLES-RULE.md, etc.). For users who install skills to `~/.claude/skills/` via `install.sh`, the rule file is symlinked to the consuming project's `.claude/rules/` — the same way skills are symlinked to `~/.claude/skills/`. `uninstall.sh` removes the symlink.

## Files Changed

| File | Change |
|------|--------|
| `skills/plan-roadmap/SKILL.md` | Remove `disable-model-invocation`, new description, Output Rules + VERBATIM convention, Context Detection step (conversion mode), batch validation, verbatim blocks on all fixed prompts, version bump to 13 |
| `skills/plan-bugfix-roadmap/SKILL.md` | Remove `disable-model-invocation`, new description, version bump |
| `skills/list-roadmaps/SKILL.md` | Remove `disable-model-invocation`, new description, version bump |
| `skills/describe-roadmap/SKILL.md` | Remove `disable-model-invocation`, new description, version bump |
| `skills/repair-roadmap/SKILL.md` | Remove `disable-model-invocation`, new description, version bump |
| `skills/plan-roadmap/references/active-guards.md` | Clarify Phase Gate guard to allow conversion mode |
| `install.sh` | Symlink ROADMAP-PLANNING-RULE.md to consuming project's `.claude/rules/`, merge ExitPlanMode hook into `~/.claude/settings.json` PostToolUse array |
| `uninstall.sh` | Remove rule symlink, remove ExitPlanMode hook entry from PostToolUse array |

## Files Created

| File | Purpose |
|------|---------|
| `.claude/rules/ROADMAP-PLANNING-RULE.md` | Trigger phrase recognition + conversion intent |

## Files Not Changed

| File | Reason |
|------|--------|
| `skills/implement-roadmap/SKILL.md` | Keeps `disable-model-invocation` — heavy side effects |
| `skills/implement-roadmap-interactively/SKILL.md` | Same |
| `skills/generate-test-roadmap/SKILL.md` | Testing tool |
| `skills/progress-dashboard/SKILL.md` | Keeps `disable-model-invocation` — restricted tools, explicit invocation only |

## No New Dependencies

No new packages, services, or external tools required.
