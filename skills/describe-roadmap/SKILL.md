---
name: describe-roadmap
version: "4"
description: "Show detailed info about an active roadmap — goal, progress, and all steps with status. Use when the user wants to inspect a specific roadmap, see step details, or review what's left before implementation."
disable-model-invocation: true
---

## Version Check

If `$ARGUMENTS` is `--version`:

1. Print:
   > describe-roadmap v4

Then stop.

---

# Describe Roadmap

Run the script to display detailed roadmap info. If there are multiple active roadmaps, the script prompts the user to choose one.

```bash
python3 "${CLAUDE_SKILL_DIR}/references/describe-roadmap" $ARGUMENTS
```

The script output is shown directly. Do not repeat it.

The script ends with "Run /implement-roadmap now? [y/N]". If the user answers yes, run `/implement-roadmap` for that feature. Otherwise, stop.
