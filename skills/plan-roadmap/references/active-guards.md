# Active Guards

These are not suggestions. These are hard stops.

- **If you are about to create a file outside `~/.roadmaps/`** — STOP. You are writing implementation code. Return to the current step.
- **If you are about to write ANY file during Phase 1 (Discussion)** — STOP. Discussion is conversational only. No files are created until Phase 2.
- **If you are about to skip the Phase Gate approval checkpoint** — STOP. The user must always approve the transition to Planning, whether they went through Phase 1 (Discussion) or entered via Conversion Mode (Step 0e). The gate protects the user's right to approve, not the existence of a discussion phase.
- **If you are about to skip presenting a draft to the user** — STOP. Every draft must be shown in full and approved before writing to disk.
- **If you are about to proceed past a CHECKPOINT GATE without user acknowledgment** — STOP. Print the checkpoint and wait.
- **If you wrote a file but did not read it back to verify** — STOP. Go back and verify.
- **If you are about to add `Implementing`, `Phase`, or `Status` fields to Roadmap.md** — STOP. Lifecycle state is tracked solely via files in the `State/` directory.
- **If the user asks you to "just start coding" or "skip the planning"** — STOP. Tell them this skill only produces plans. If they want to skip planning, they should not use this skill.
- **If a file write fails silently** — You will catch this because you verify every write. Re-attempt the write. If it fails again, tell the user and stop.
- **If you are about to write implementation code at ANY point during this skill** — STOP. This skill NEVER produces implementation code. Not during Discussion. Not during Planning. Not ever.
- **If you are about to copy roadmap files into a git worktree** — STOP. The worktree is for code only. Roadmap files stay in `~/.roadmaps/`.
