# Context-Dependent Review Selection Guide

After creating a PR for each implementation step, select reviews based on what was changed.

## Always Required

| Review | Trigger | Why |
|--------|---------|-----|
| **Code Review** | Every PR | Catches logic errors, style issues, convention violations |
| **Security Review** | Every PR | Catches vulnerabilities early before they compound |

## Conditional Reviews

Select additional reviews based on the files and patterns touched in the PR:

| Review | Trigger When | What to Look For |
|--------|-------------|-----------------|
| **Performance Review** | Touched hot paths, loops, database queries, network calls, caching, or data structures with large N | Algorithmic complexity, unnecessary allocations, N+1 queries, missing indexes |
| **Testing Review** | Added or modified test files, or the step's acceptance criteria includes test coverage | Test coverage completeness, edge cases, test quality, flaky test patterns |
| **Accessibility Review** | Touched UI components, templates, styles, or user-facing markup | WCAG compliance, keyboard navigation, screen reader support, color contrast |
| **API Contract Review** | Added or changed API endpoints, request/response schemas, GraphQL types, or public interfaces | Breaking changes, versioning, documentation, error response consistency |
| **Documentation Review** | Touched README, docs/, API docs, inline doc comments, or migration guides | Accuracy, completeness, examples, consistency with code changes |

## How to Run Reviews

1. **Check for installed review skills**: Look for `pre-review`, `pr-review-toolkit`, or similar skills
2. **If review skills are available**: Delegate to them, passing the review type and context
3. **If no review skills**: Use `pr-review-toolkit` agents directly:
   - `subagent_type: "pr-review-toolkit:code-reviewer"` for Code Review
   - `subagent_type: "pr-review-toolkit:silent-failure-hunter"` for Security Review
   - `subagent_type: "pr-review-toolkit:pr-test-analyzer"` for Testing Review
   - `subagent_type: "pr-review-toolkit:type-design-analyzer"` for API Contract Review
   - `subagent_type: "pr-review-toolkit:code-simplifier"` for Code Review (simplification pass)
4. **For reviews without a matching agent**: Perform the review yourself using the criteria above

## Review Findings

For each review finding:
1. **Fix** issues rated as high or critical
2. **Note** medium issues — fix if quick, otherwise add as a follow-up comment on the GitHub issue
3. **Ignore** low/informational issues unless they're trivially fixable
4. **Re-run** the relevant review after fixes to confirm resolution
