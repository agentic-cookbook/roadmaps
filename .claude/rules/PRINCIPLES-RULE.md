# Principles Rule

This rule enforces the agentic cookbook engineering principles during planning and implementation. It applies to every task regardless of size. The principles are the foundation of all design and coding decisions.

---

## Planning

### Read All 18 Principles

Before making any design decision, you MUST read ALL of the following files. These paths assume the cookbook is cloned at `../agentic-cookbook/` relative to your project root.

```
../agentic-cookbook/cookbook/principles/simplicity.md
../agentic-cookbook/cookbook/principles/make-it-work-make-it-right-make-it-fast.md
../agentic-cookbook/cookbook/principles/yagni.md
../agentic-cookbook/cookbook/principles/fail-fast.md
../agentic-cookbook/cookbook/principles/dependency-injection.md
../agentic-cookbook/cookbook/principles/immutability-by-default.md
../agentic-cookbook/cookbook/principles/composition-over-inheritance.md
../agentic-cookbook/cookbook/principles/separation-of-concerns.md
../agentic-cookbook/cookbook/principles/design-for-deletion.md
../agentic-cookbook/cookbook/principles/explicit-over-implicit.md
../agentic-cookbook/cookbook/principles/small-reversible-decisions.md
../agentic-cookbook/cookbook/principles/tight-feedback-loops.md
../agentic-cookbook/cookbook/principles/manage-complexity-through-boundaries.md
../agentic-cookbook/cookbook/principles/principle-of-least-astonishment.md
../agentic-cookbook/cookbook/principles/idempotency.md
../agentic-cookbook/cookbook/principles/native-controls.md
../agentic-cookbook/cookbook/principles/open-source-preference.md
../agentic-cookbook/cookbook/principles/meta-principle-optimize-for-change.md
```

If any principle file is not found at the expected path, stop and inform the user. Do not proceed with missing principles.

You MUST NOT produce a plan without reading these files first.

### Trace Decisions to Principles

Every design decision in the plan MUST be traceable to one or more principles. In the plan, include a "Principles applied" section listing which principles actively influenced the design and how. Do not list all 18 — list only the ones that shaped specific decisions.

Before presenting the plan, verify it includes a "Principles applied" section listing specific principles. If it does not, add one before proceeding.

### Follow the Three-Phase Discipline

Plan for all three phases of Work, Right, Fast:

1. **Phase 1 scope** — what constitutes "it works" (happy path, core functionality).
2. **Phase 2 scope** — what edge cases, error handling, and refactoring are required.
3. **Phase 3 criteria** — under what evidence would optimization be warranted. If none is expected, state "Phase 3 not anticipated."

---

## Implementing

### Apply Principles During Coding

You MUST keep these principles active throughout implementation. You do not need to re-read the files if you read them during planning, but you MUST apply them:

| Principle | Key Rule |
|-----------|----------|
| Simplicity | No interleaving of concerns. Simple beats easy. |
| YAGNI | Build for today's requirements only. |
| Fail Fast | Detect invalid state at the point of origin. |
| Dependency Injection | Receive dependencies from outside. |
| Immutability | Default to immutable values; mutate only when necessary. |
| Composition | Compose small pieces over deep hierarchies. |
| Separation of Concerns | One reason to change per module. |
| Explicit over Implicit | Visible dependencies, clear intent, no hidden behavior. |
| Design for Deletion | Easy to remove. Disposable over reusable. |
| Least Astonishment | Behavior matches what the name promises. |

### Follow the Three-Phase Discipline

Execute phases in order. Do not skip phases.

**Phase 1: Make It Work**
- Implement the happy path that makes the feature work for the common case.
- Write tests alongside code — not after. Every function MUST have a test, written before or immediately after the implementation.
- You MUST build and run tests after each completed unit (one function with its test, one completed file, or one discrete feature boundary from the plan). Do not accumulate broken state.
- You MUST commit after completing each unit (one function with its test, one completed file, or one discrete feature boundary from the plan).
- Defer edge cases, error handling refinements, and optimizations to Phase 2.

**Checkpoint before Phase 2:** Confirm: all Phase 1 functions have tests, all tests pass, code is committed.

**Phase 2: Make It Right**
- You MUST NOT skip this phase. Do not go directly from "it works" to "ship it."
- Handle edge cases identified in the plan and any discovered during Phase 1.
- Add error handling appropriate to each boundary.
- Refactor for clarity — apply separation of concerns, clean up naming, ensure readability.
- You MUST add tests for every edge case and error path added in this phase.

**Checkpoint before Phase 3:** Confirm: edge cases handled, error paths tested, code refactored, all tests pass.

**Phase 3: Make It Fast (Conditional)**
- You MUST NOT enter this phase without evidence of a performance problem.
- Evidence means: a test with measurable latency, a user report of slowness, or a known algorithmic concern.
- Measure before and after. State the metric, baseline, and target.
- If no evidence exists, skip this phase entirely.

### Tests Alongside Code

You MUST write tests as you write code. Every function MUST have a test. Every edge case MUST have a test. Do not accumulate untested code and add tests at the end.

### Commit After Each Completed Unit

You MUST commit after completing each unit: one function with its test, one completed file, or one discrete feature boundary from the plan. Do not accumulate large uncommitted changes.

---

## MUST NOT

- Do not skip reading the principles because the task seems small. Every task gets the full read.
- Do not skip Phase 2 (Make It Right). Ever.
- Do not skip writing tests. Tests are a deliverable, not an afterthought.
- Do not add scope beyond the approved plan. No "bonus" features, no unrelated refactoring.
- Do not optimize without evidence. Phase 3 requires measured proof of a problem before entry.
- Do not treat any principle as optional. If a principle conflicts with the plan, stop and raise the conflict with the user.
