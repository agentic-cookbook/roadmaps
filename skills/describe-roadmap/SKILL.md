---
name: describe-roadmap
version: "5"
description: "Show detailed info about a roadmap — goal, progress, steps. Use when the user wants to inspect a roadmap, see step details, check progress, or review what's left."
---

## Version Check

If `$ARGUMENTS` is `--version`:

1. Print:
   > describe-roadmap v5

Then stop.

---

# Describe Roadmap

Run the script to display detailed roadmap info. If there are multiple active roadmaps, the script prompts the user to choose one.

```bash
python3 "${CLAUDE_SKILL_DIR}/references/describe-roadmap" $ARGUMENTS
```

The script output is shown directly. Do not repeat it.

The script ends with "Run /implement-roadmap now? [y/N]". If the user answers yes, run `/implement-roadmap` for that feature. Otherwise, stop.
