# /plan-feature

Collaborative planning skill for new features. Guides you through discussing an idea, then produces structured planning artifacts — no implementation code.

## What It Does

Takes a feature idea from conversation to a concrete plan:

1. **Discussion** — Talk through the idea naturally. Claude asks questions, clarifies scope, and summarizes.
2. **Planning** — Creates a Feature Definition, Feature Roadmap, and GitHub issues.

The transition from Discussion to Planning requires your explicit permission.

## Usage

```
/plan-feature
```

That's it. The skill walks you through everything interactively.

## Workflow

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

## Examples

**Starting a new feature:**
```
You: /plan-feature
Claude: What feature would you like to plan?
You: I want to add dark mode support to the app
Claude: [asks clarifying questions about scope, platforms, etc.]
...
Claude: Here's my summary: [summary]. Proposed name: DarkModeSupport
You: looks good
Claude: May I transition from Discussion to Planning?
You: yes
Claude: [creates Feature Definition, Roadmap, GitHub issues]
```

**Resuming after interruption:**
If a session is interrupted during planning, the Roadmap will have `Phase: Planning`. Run `/plan-feature` again to continue, or manually update the Phase field.

## Key Rules

- **No implementation code** — ever. This skill only produces Markdown planning files and GitHub issues.
- **Every draft is shown in full** and requires your approval before being written to disk.
- **Checkpoint gates** pause for your acknowledgment between major steps.
- **Phase gate** between Discussion and Planning requires explicit permission.

## Files Created

- `.claude/Features/FeatureDefinitions/<Name>-FeatureDefinition.md`
- `.claude/Features/Active-Roadmaps/<Name>-FeatureRoadmap.md`
- GitHub issues (one per implementation step)

## Changelog

### v2 (2026-03-21)
- Restructured into two phases: Discussion and Planning
- Added explicit phase gate requiring user permission to transition
- Added `Phase: Planning | Ready` field to Roadmap template
- Reinforced no-implementation-code guardrails in both phases and all guards
- Added `version: 2` to SKILL.md frontmatter

### v1 (2026-03-20)
- Initial release
- Single-phase workflow: startup validation → Feature Definition → Feature Roadmap → GitHub issues
- Checkpoint gates between major steps
- No-implementation-code guardrails
