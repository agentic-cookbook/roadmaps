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
