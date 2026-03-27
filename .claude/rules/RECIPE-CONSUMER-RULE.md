# Recipe Consumer Rule

Tier 3 rule — additive on top of `rules/PRINCIPLES-RULE.md` and `rules/GUIDELINE-CONSUMER-RULE.md`. This rule enforces recipe search and conformance during planning and implementation. All paths assume the cookbook is cloned at `../agentic-cookbook/` relative to your project root. If any referenced file is not found, stop and inform the user.

---

## Planning

### Search for Matching Recipes

Search `../agentic-cookbook/cookbook/recipes/` recursively for any recipe that matches or partially matches the feature being planned. Check all subdirectories:

- `../agentic-cookbook/cookbook/recipes/ui/component/` — UI building blocks
- `../agentic-cookbook/cookbook/recipes/ui/panel/` — content panes
- `../agentic-cookbook/cookbook/recipes/ui/window/` — top-level layouts
- `../agentic-cookbook/cookbook/recipes/infrastructure/` — non-visual patterns
- `../agentic-cookbook/cookbook/recipes/app/` — application lifecycle patterns

**If a matching recipe exists**: the plan MUST incorporate it. List the recipe file and summarize which requirements it imposes.

**If a partial match exists** (the recipe covers the same component type or shares behavioral requirements but does not fully specify the feature): note what the recipe covers and what is missing. You MUST ask the user whether to extend the existing recipe or proceed without it.

**If no match exists**: record explicitly — "No existing recipe found for this feature."

### Evaluate Recipe Opportunities

You MUST answer both questions in the plan:

1. **Can this feature become a new cookbook recipe?** If the feature implements a reusable pattern that other projects could use, propose creating a recipe.
2. **Can this feature enhance an existing cookbook recipe?** If an existing recipe is close but missing something this feature adds, propose updating it.

Record answers under a "Recipe Opportunities" section. If neither applies, write: "No recipe opportunities identified."

---

## Implementing

### Recipe Conformance

If implementing from a recipe, the implementation MUST match:

- **Behavioral requirements** (REQ-NNN) — every MUST is mandatory, every SHOULD is expected unless documented otherwise.
- **States table** — every state in the table must be implemented.
- **Appearance values** — exact dimensions, colors, fonts, and spacing as specified.
- **Conformance test vectors** — write tests corresponding to each row.
- **Logging messages** — exactly as specified, character for character.
- **Edge cases** — every edge case addressed.
- **Accessibility requirements** — every accessibility item implemented.

Do not improvise. Do not skip sections. Do not substitute your judgment for the recipe's specifications. If you believe the recipe is wrong, stop and tell the user.

### Verify Conformance

Before marking implementation complete, produce a conformance checklist that maps each recipe REQ-NNN to the implementing code location and test. Present this checklist to the user:

| REQ | Status | Code Location | Test |
|-----|--------|---------------|------|
| REQ-001 | PASS/FAIL | file:line | test name |

All items MUST pass before proceeding.

### Flag Reusable Patterns

After implementation, evaluate whether any new patterns emerged that are not currently in the cookbook. If so, note them for potential contribution.

---

## MUST NOT

- Do not skip the recipe search because "it's probably not there." Search every time.
- Do not deviate from a recipe without user approval. If the recipe specifies a value, use that value.
- Do not improvise dimensions, colors, fonts, spacing, or logging messages that the recipe specifies.
- Do not skip any section of a recipe during implementation — requirements, states, appearance, test vectors, logging, edge cases, accessibility.
- Do not mark implementation complete without verifying conformance against every recipe requirement.
