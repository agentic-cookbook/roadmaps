# Active Guards

These are not suggestions. These are hard stops.

- **If you are about to create a file outside `~/.roadmaps/`** — STOP. You are writing implementation code. Return to the current step.
- **If you are about to skip presenting a draft to the user** — STOP. Every draft must be shown in full and approved before writing to disk.
- **If you are about to proceed past a CHECKPOINT GATE without user acknowledgment** — STOP. Print the checkpoint and wait.
- **If you wrote a file but did not read it back to verify** — STOP. Go back and verify.
- **If you are about to add `Implementing`, `Phase`, or `Status` fields to Roadmap.md** — STOP. Lifecycle state is tracked solely via files in the `State/` directory.
- **If the user asks you to "just start coding" or "skip the planning"** — STOP. Tell them this skill only produces plans. If they want to skip planning, they should not use this skill.
- **If a file write fails silently** — You will catch this because you verify every write. Re-attempt the write. If it fails again, tell the user and stop.
- **If you are about to write implementation code at ANY point during this skill** — STOP. This skill NEVER produces implementation code.
- **If you are about to delete the original Roadmap.md instead of renaming it** — STOP. The original must be preserved for comparison.
- **If you are about to remove a step that wasn't explicitly broken or requested for removal** — STOP. Steps are fixed in place, never removed. Every original step must appear in the revised roadmap.
- **If you are about to filter or drop steps based on complexity** — STOP. L-complexity steps are valid and expected. Complexity is a descriptor, not a filter.
- **If the revised roadmap has fewer steps than the original** — STOP. Print the step-count comparison and get explicit per-step confirmation for each removal.
- **If you are about to "simplify" the roadmap by merging or consolidating steps** — STOP. Only merge steps if the user explicitly asked to merge those specific steps.
