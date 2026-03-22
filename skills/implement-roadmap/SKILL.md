---
name: implement-roadmap
version: "10"
description: "Implement a planned feature from its Roadmap. Uses a deterministic Python coordinator for step selection and launches a worker agent for each step. Use after /plan-roadmap or /plan-bugfix-roadmap has created a Roadmap."
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(python3 *), Bash(ls *), Bash(grep *), Bash(cat *), Bash(mkdir *), Bash(gh *), Bash(git *), Bash(claude *)
---

## Version Check

If `$ARGUMENTS` is `--version`:

1. Print the skill version:
   > implement-roadmap v10

2. Print the worker agent version by running:
   ```bash
   grep -m1 'version:' ~/.claude/agents/implement-step-agent.md
   ```
   Format the output as:
   > implement-step-agent v{version}

Then stop. Do not continue with the rest of the skill.

---

# Implement Roadmap

Run the deterministic coordinator script to implement a feature roadmap. The coordinator selects steps via regex (no LLM judgment) and launches a worker agent for each step.

## Step 1: Resolve and Launch

If `$ARGUMENTS` names a feature, find the matching roadmap and pass its path to the coordinator. If `$ARGUMENTS` is empty, let the coordinator auto-scan.

Run:

```bash
python3 "${CLAUDE_SKILL_DIR}/references/coordinator" $ARGUMENTS
```

If `$ARGUMENTS` contains a feature name, find the roadmap path first:

```bash
ROADMAP=$(ls .claude/Features/Active-Roadmaps/*$ARGUMENTS*-FeatureRoadmap.md 2>/dev/null | head -1)
if [ -n "$ROADMAP" ]; then
    python3 "${CLAUDE_SKILL_DIR}/references/coordinator" "$ROADMAP"
else
    python3 "${CLAUDE_SKILL_DIR}/references/coordinator" --scan
fi
```

The coordinator handles everything:
- Roadmap selection (auto-selects if only one available)
- Dashboard lifecycle (init, load-roadmap, begin-step, finish-step)
- Step selection (deterministic regex, not LLM)
- Launching `claude --agent implement-step-agent` for each step
- Completion summary

You do not need to do anything else. The coordinator runs to completion.

**Do NOT modify the coordinator script, the worker agent, or any skill files.** Your only job is to run the coordinator. If it fails, report the error — do not attempt to fix the coordinator code.
