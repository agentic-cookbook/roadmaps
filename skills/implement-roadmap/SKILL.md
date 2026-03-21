---
name: implement-roadmap
version: "1.0.0"
description: "Implement a planned feature from its Roadmap autonomously in the background. Use after /plan-roadmap or /plan-bugfix-roadmap has created a Roadmap."
disable-model-invocation: true
---

## Version Check

If `$ARGUMENTS` is `--version`, respond with exactly:

> implement-roadmap v1.0.0

Then stop. Do not continue with the rest of the skill.

---

# Implement Roadmap

Launch the `implement-roadmap-agent` in the background to autonomously implement a feature from its Roadmap.

## Step 1: Scan Available Roadmaps

Read all files in `.claude/Features/Active-Roadmaps/`. For each `*-FeatureRoadmap.md` file, parse:

- The feature name (from `# Feature Roadmap: <name>`)
- The `**Status**:` field
- The `**Phase**:` field

Categorize each roadmap:

- **Available**: `Status` is not `Complete` AND `Phase` is `Ready`
- **Not Ready**: `Phase` is `Planning`
- **Complete**: `Status` is `Complete`

If no features are available:
- List any "Not Ready" features and explain they need `/plan-roadmap` completed first
- **STOP**

## Step 2: Select Feature

If only one feature is available, use it automatically.

If multiple are available, present a numbered list and let the user choose.

## Step 3: Launch Agent

Launch the `implement-roadmap-agent` in the background using the Agent tool:

- **subagent_type**: `implement-roadmap-agent`
- **run_in_background**: `true`
- **prompt**: `Implement the <FeatureName> feature. Roadmap: .claude/Features/Active-Roadmaps/<FeatureName>-FeatureRoadmap.md`

Print:

```
Launched implement-roadmap-agent for <FeatureName> in the background.

The agent will:
  - Work through each roadmap step autonomously
  - Create worktrees, PRs, run reviews, and merge
  - Open the progress dashboard (if installed)

You can continue working in this session. You'll be notified when the agent completes.

For interactive step-by-step control instead, use: /implement-roadmap-interactively
```
