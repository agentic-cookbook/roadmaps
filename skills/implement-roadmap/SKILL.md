---
name: implement-roadmap
version: "6"
description: "Implement a planned feature from its Roadmap autonomously in the background. Use after /plan-roadmap or /plan-bugfix-roadmap has created a Roadmap."
disable-model-invocation: true
---

## Version Check

If `$ARGUMENTS` is `--version`:

1. Print the skill version:
   > implement-roadmap v6

2. Print the agent version by running:
   ```bash
   grep -m1 'version:' ~/.claude/agents/implement-roadmap-agent.md
   ```
   Format the output as:
   > implement-roadmap-agent v{version}

Then stop. Do not continue with the rest of the skill.

---

# Implement Roadmap

Launch the `implement-roadmap-agent` to autonomously implement a feature from its Roadmap. Runs in **foreground** by default. Pass `-b` or `--background` to run in the background.

## Step 0: Parse Arguments

Check if `$ARGUMENTS` contains `-b` or `--background`. If so, set `BACKGROUND=true` and remove the flag from arguments. Otherwise `BACKGROUND=false`. The remaining arguments (after removing the flag) are the feature name, if any.

## Step 1: Resolve Feature

### If remaining arguments name a feature:

Look for a matching `*-FeatureRoadmap.md` in `.claude/Features/Active-Roadmaps/`. If found and `Phase` is `Ready` and `Status` is not `Complete`, use it. Otherwise report the error and **STOP**.

### If remaining arguments are empty:

Scan `.claude/Features/Active-Roadmaps/` for all `*-FeatureRoadmap.md` files. Parse each for feature name, `**Status**:`, and `**Phase**:`.

Categorize:
- **Available**: `Status` is not `Complete` AND `Phase` is `Ready`
- **Not Ready**: `Phase` is `Planning`
- **Complete**: `Status` is `Complete`

If no features are available:
- List any "Not Ready" features and explain they need `/plan-roadmap` completed first
- **STOP**

If exactly **one** feature is available, auto-select it. Print:

```
Auto-selecting: <FeatureName> — <M>/<N> steps complete
```

Then proceed directly to Step 2.

If **multiple** features are available, present a numbered list with a quit option:

```
Available roadmaps:

1. FeatureA — 0/5 steps complete
2. FeatureB — 3/7 steps complete

q. Quit

Which roadmap? (number or q)
```

**STOP. Wait for the user's choice.**

If the user chooses `q`, **STOP** — do not launch anything.

## Step 2: Print Versions

Before launching, print both versions so the user knows what's running:

```
implement-roadmap v5
implement-roadmap-agent v<agent_version>
```

Get the agent version by running:

```bash
grep -m1 'version:' ~/.claude/agents/implement-roadmap-agent.md
```

## Step 3: Launch Agent

Launch the `implement-roadmap-agent` using the Agent tool:

- **subagent_type**: `implement-roadmap-agent`
- **run_in_background**: `BACKGROUND` (true if `-b`/`--background` was passed, false otherwise)
- **prompt**: `Implement the <FeatureName> feature. Roadmap: .claude/Features/Active-Roadmaps/<FeatureName>-FeatureRoadmap.md`

If running in background, print:

```
Launched implement-roadmap-agent for <FeatureName> in the background.
You can continue working. You'll be notified when the agent completes.
```

If running in foreground, print:

```
Launching implement-roadmap-agent for <FeatureName>...
```
