---
name: list-roadmaps
version: "6"
description: "List active roadmaps with progress. Use when the user asks what roadmaps exist, wants to see roadmap status, or asks about pending work."
---

## Version Check

If `$ARGUMENTS` is `--version`:

1. Print:
   > list-roadmaps v6

Then stop.

---

# List Roadmaps

Run the listing script to show all active roadmaps with progress and description.

```bash
python3 "${CLAUDE_SKILL_DIR}/references/list-roadmaps"
```

The script output is shown directly. Do not repeat it.
