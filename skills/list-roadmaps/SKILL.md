---
name: list-roadmaps
version: "1"
description: "List active roadmaps with step summaries and execution state. Use when the user wants to see what roadmaps exist, check roadmap progress, or review pending work."
disable-model-invocation: true
---

## Version Check

If `$ARGUMENTS` is `--version`:

1. Print:
   > list-roadmaps v1

Then stop.

---

# List Roadmaps

Run the listing script to show all active roadmaps with their steps and execution state.

```bash
python3 "${CLAUDE_SKILL_DIR}/references/list-roadmaps"
```

Print the output as-is. The legend for the step icons:

- `[+]` Complete
- `[~]` In Progress
- `[!]` Blocked
- `[-]` Not Started

That's it. No other actions needed.
