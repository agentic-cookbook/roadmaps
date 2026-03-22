---
name: list-roadmaps
version: "3"
description: "List active roadmaps with progress and description. Use when the user wants to see what roadmaps exist, check roadmap progress, or review pending work."
disable-model-invocation: true
---

## Version Check

If `$ARGUMENTS` is `--version`:

1. Print:
   > list-roadmaps v3

Then stop.

---

# List Roadmaps

Run the listing script to show all active roadmaps with progress and description.

```bash
python3 "${CLAUDE_SKILL_DIR}/references/list-roadmaps"
```

Print the output as-is. No other actions needed.
