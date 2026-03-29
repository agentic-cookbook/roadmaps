# Roadmap Permissions Rule

This rule governs permission handling during roadmap skill sessions (`/plan-roadmap`, `/implement-roadmap`, etc.).

---

## Single Permission Prompt

At the start of any roadmap session, before any file access or terminal commands, you MUST present **one** consolidated permission request:

```
This roadmap session will:
- Read and write files in ~/.roadmaps/
- Execute terminal commands (git, build tools, test runners)
- Read and modify project files

Proceed?
```

Wait for confirmation. After the user confirms, you MUST NOT ask for additional permissions during the session. If no permission confirmation is needed (e.g., auto-accept or YOLO mode is active), skip the initial prompt and proceed directly.

## MUST NOT

- You MUST NOT ask "may I read this file?" or "may I run this command?" after the initial prompt.
- You MUST NOT ask for permission before individual git, read, write, or bash operations.
- You MUST NOT re-prompt when switching between planning phases (brainstorm, draft, finalize).
- The initial prompt MUST be the **only** permission interaction for the entire session.

## Verification

At session end, confirm that no mid-session permission prompts were issued beyond the initial consolidated prompt.
