# Guideline Consumer Rule

This rule enforces agentic cookbook guidelines during planning and implementation. It is additive — use alongside PRINCIPLES-RULE.md.

All paths are relative from the consuming project. These paths assume the cookbook is cloned at `../agentic-cookbook/` relative to your project root.

---

## Planning: Run the Guideline Checklist

Before producing a plan, read these files in order:

```
../agentic-cookbook/cookbook/guidelines/general.md
../agentic-cookbook/cookbook/guidelines/INDEX.md
../agentic-cookbook/cookbook/workflow/guideline-checklist.md
```

If any referenced file does not exist at the expected path, stop and inform the user. Do not proceed with assumptions about the file's content.

You MUST walk through every item in the checklist with the user:

1. **"Always" items**: You MUST note them as applicable. Do not ask. These are non-negotiable.
2. **"Opt-in" items**: Opt-in items: Present as included by default. The user may opt out; do not require explicit confirmation unless the user raises a concern.
3. **"Opt-out" items**: You MUST ask the user if they want to opt in.
4. **"Ask" items**: You MUST ask the prompt template question from the checklist.

Present ALL items in a single consolidated table. Do not ask one at a time.

| Guideline | Category | Default | Decision | Reason |
|-----------|----------|---------|----------|--------|
| Native controls | Always | -- | Included | -- |
| Instrumented logging | Opt-in | Included | ? | -- |
| Deep linking | Ask | -- | ? | -- |
| Scriptable/automatable | Opt-out | Excluded | ? | -- |
| ... | ... | ... | ... | ... |

Wait for the user to fill in every "?" before proceeding. Record all decisions in the plan.

---

## Implementing: Apply Every Applicable Guideline

### Always guidelines

Apply ALL "Always" guidelines to every relevant file. No exceptions. No deferral.

### Opted-in guidelines

Apply ALL opted-in guidelines to every relevant file during the same pass as core functionality. Do not defer them to a later phase.

- If logging was opted in, every component gets logging.
- If accessibility was opted in, every view gets accessibility attributes.
- If localizability was opted in, every user-facing string is localizable.
- If feature flags were opted in, the feature is gated from the first commit.

### Opted-out guidelines

Do not apply opted-out items. If a new concern surfaces during implementation that was not in the checklist, present the new concern to the user using the same table format. Do not proceed until the user decides to opt in or opt out.

---

## Verification: Confirm Compliance

After implementation is complete, read:

```
../agentic-cookbook/cookbook/workflow/code-verification.md
```

Run the full verification checklist:

1. **Build** passes with no errors.
2. **Tests** pass — unit, integration, and any E2E tests written for this feature.
3. **Lint** is clean — no warnings, no added suppressions.
4. **Logging** matches the opted-in logging specification — verify structured log output.
5. **Accessibility** verified — screen reader labels present, keyboard navigation works, display options respected.
6. **Guideline compliance** — review every "Always" guideline and every opted-in guideline against the implementation. Confirm each is fully addressed, not partially.

Do not mark the work as complete until every verification check passes. If a check fails, fix the issue and re-run the failing check. If the fix requires design changes, present the failure and proposed fix to the user before proceeding.

---

## What You MUST NOT Do

- Do not skip the checklist because "we did it last time." Every session starts fresh. Re-read the checklist. Re-ask the user.
- Do not skip verification. Build, test, lint, and guideline compliance are mandatory exit criteria.
- Do not apply guidelines partially. "I added some accessibility labels" is not compliance. Every applicable view gets every applicable attribute.
- Do not suppress linter warnings. Fix the underlying issue.
- Do not defer opted-in concerns to a later phase. If it was opted in, it ships with the feature.
- Do not invent guidelines not in the checklist. Apply what was agreed upon, nothing more.

---

## Reference

| Resource | Path |
|----------|------|
| Core guidelines | `../agentic-cookbook/cookbook/guidelines/general.md` |
| Full guideline index | `../agentic-cookbook/cookbook/guidelines/INDEX.md` |
| Guideline checklist | `../agentic-cookbook/cookbook/workflow/guideline-checklist.md` |
| Verification workflow | `../agentic-cookbook/cookbook/workflow/code-verification.md` |
| Planning workflow | `../agentic-cookbook/cookbook/workflow/code-planning.md` |
| Implementation workflow | `../agentic-cookbook/cookbook/workflow/code-implementation.md` |
