---
name: implement-roadmap
version: "11"
description: "Implement a planned feature from its Roadmap. Uses a deterministic Python coordinator for step selection and the Agent tool to launch a worker for each step. Use after /plan-roadmap or /plan-bugfix-roadmap has created a Roadmap."
disable-model-invocation: true
---

## Version Check

If `$ARGUMENTS` is `--version`:

1. Print the skill version:
   > implement-roadmap v11

2. Print the worker agent version by running:
   ```bash
   grep -m1 'version:' ~/.claude/agents/implement-step-agent.md
   ```
   Format the output as:
   > implement-step-agent v{version}

Then stop. Do not continue with the rest of the skill.

---

# Implement Roadmap

Uses a deterministic Python script for step selection (no LLM judgment) and the Agent tool to launch a worker agent for each step.

**Do NOT modify the coordinator script, the worker agent, or any skill files.** If something fails, report the error.

## Step 1: Resolve Roadmap

Run the coordinator to find the roadmap:

```bash
python3 "${CLAUDE_SKILL_DIR}/references/coordinator" resolve $ARGUMENTS
```

This outputs JSON. Parse it:
- If it has `"path"` — use that roadmap. Print: `Implementing: <name> (<complete>/<total> steps complete)`
- If it has `"choose"` — present the list to the user and ask them to pick. Then use the chosen path.
- If it has `"error"` — print the error and **STOP**.

## Step 2: Start Dashboard

```bash
DASH_CLI="$HOME/.claude/skills/progress-dashboard/references/dash"
test -f "$DASH_CLI" && python3 "$DASH_CLI" init "<feature_name>" && python3 "$DASH_CLI" load-roadmap "<roadmap_path>" || echo "Dashboard not available"
```

## Step 3: Implementation Loop

This is a loop. Repeat until done:

### 3a: Get Next Step

Run the coordinator to find the next step:

```bash
python3 "${CLAUDE_SKILL_DIR}/references/coordinator" next-step "<roadmap_path>"
```

This outputs JSON. Parse it:

- If `"action": "implement"` — continue with 3b.
- If there are `"manual_skipped"` entries, print them once: `Skipping manual step N: <description>`
- If `"action": "done"` — all steps are complete. **Immediately run the completion commands:**
  ```bash
  python3 "$DASH_CLI" complete
  python3 "$DASH_CLI" shutdown
  ```
  Print: `All steps complete for <feature_name>.`
  Then **STOP**.

### 3b: Print Step Info

Print:
```
Step <N>: <description>
  Issue: <issue>  |  Complexity: <complexity>
```

### 3c: Update Dashboard

```bash
python3 "$DASH_CLI" begin-step <N>
```

### 3d: Launch Worker Agent

Use the **Agent tool** (NOT subprocess, NOT `claude --agent`):

- **subagent_type**: `implement-step-agent`
- **prompt**: The exact text below, with values filled in:

```
Implement step <N> of the <feature_name> feature.

Step <N>: <description>
GitHub Issue: <issue>
Complexity: <complexity>
Roadmap file: <roadmap_path>
Feature Definition: .claude/Features/FeatureDefinitions/<feature_name>-FeatureDefinition.md

Implement ONLY this step. When done, update the roadmap to mark this step Complete, then return. Do not implement any other step.
```

### 3e: After Worker Returns

Update dashboard:
```bash
python3 "$DASH_CLI" finish-step <N>
```

Print: `Step <N> complete.`

Then **go back to 3a** to get the next step.

## Note

Step 4 (completion) is handled inline in step 3a when the coordinator returns `"action": "done"`. There is no separate completion step.
