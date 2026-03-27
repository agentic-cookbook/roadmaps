# Contributor Rule

Tier 4 rule — additive on top of `rules/PRINCIPLES-RULE.md`, `rules/GUIDELINE-CONSUMER-RULE.md`, and `rules/RECIPE-CONSUMER-RULE.md`. This rule is for users who want to contribute new recipes and improvements back to the agentic cookbook.

All paths assume the cookbook is cloned at `../agentic-cookbook/` relative to your project root. If any referenced file is not found, stop and inform the user.

---

## Identifying Contribution Opportunities

After completing implementation, you MUST evaluate whether any new reusable pattern was created that is not covered by an existing recipe in `../agentic-cookbook/cookbook/recipes/`. Specifically check:

- Did you create a UI component, panel, or window that other projects could reuse?
- Did you implement an infrastructure pattern (networking, storage, auth) that is generic enough to extract?
- Did you discover a workflow improvement worth documenting?

If any answer is yes, record it under the "Recipe Opportunities" section from RECIPE-CONSUMER-RULE.md. You MUST propose the contribution — do not silently skip it.

If no opportunities exist, record: "No contribution opportunities identified."

---

## Creating New Recipes

When a contribution is approved by the user, follow these steps in order:

1. Read `../agentic-cookbook/cookbook/conventions.md` for the full format reference.
2. Read `../agentic-cookbook/contributing/AUTHORING.md` for contribution guidelines.
3. Use `/plan-agentic-cookbook-recipe` to design the recipe interactively. The skill will guide you through every section.

If analyzing an existing codebase for extractable patterns, use `/import-agentic-cookbook` to perform a deep analysis first.

### Recipe Completeness Checklist

Every recipe MUST include all of the following before submission. Start from `../agentic-cookbook/cookbook/recipes/_template.md`:

- [ ] YAML frontmatter with UUID, domain matching file path, title, version, all required fields
- [ ] Behavioral requirements (REQ-NNN) with RFC 2119 keywords
- [ ] States table — every visual/behavioral state
- [ ] Appearance values — exact dimensions, colors, fonts, spacing
- [ ] Conformance test vectors — linked to REQ-NNN
- [ ] Logging messages — exact message strings
- [ ] Edge cases
- [ ] Accessibility requirements
- [ ] Change History section

You MUST verify every item is present and non-empty before proceeding to submission.

---

## Submitting Contributions

1. Create a branch in the cookbook repo: `feature/<description>` for new content, `revise/<description>` for revisions.
2. Make changes in a worktree: `git worktree add ../agentic-cookbook-wt/<branch-name> -b <branch>`.
3. You MUST update `../agentic-cookbook/cookbook/index.md` when adding new content.
4. Commit, push, and create a PR via `gh pr create`.
5. Squash merge after approval: `gh pr merge --squash`.
6. Clean up the worktree after merge.

---

## Before Submitting — Verify

You MUST check all of the following before creating a PR:

- [ ] No duplicate recipe exists — searched `../agentic-cookbook/cookbook/recipes/` recursively
- [ ] Recipe completeness checklist above passes — all items checked
- [ ] `conventions.md` was followed — frontmatter validates, domain matches path
- [ ] `cookbook/index.md` is updated with the new entry
- [ ] All tests pass for any code changes
- [ ] Commit messages are clear and atomic

Do not create a PR until every item passes.

---

## MUST NOT

- You MUST NOT submit recipes that duplicate existing ones. Search `../agentic-cookbook/cookbook/recipes/` first.
- You MUST NOT submit incomplete recipes — no missing sections, no TODOs, no placeholders.
- You MUST NOT modify cookbook content without a branch and PR. Direct commits to main are for the cookbook owner only.
- You MUST NOT submit recipes without proper frontmatter, UUID, and domain identifier.
- You MUST NOT skip reading `conventions.md` and `AUTHORING.md` before contributing.
