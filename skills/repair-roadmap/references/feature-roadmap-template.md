---
id: "{{ROADMAP_ID}}"
project: "{{PROJECT}}"
github-user: "{{GITHUB_USER}}"
plan-version: "{{PLAN_VERSION}}"
created: "{{DATE}}"
modified: "{{DATE}}"
author: "{{AUTHOR}}"
description: "{{DESCRIPTION}}"
reviews:
  per-step: [code-reviewer]
  final: [code-reviewer, silent-failure-hunter, pr-test-analyzer]
concerns:
  always: [native-controls, surface-design-decisions, no-blocking-main-thread, small-atomic-commits, post-generation-verification, linting-from-day-one, simplicity, work-right-fast, dependency-injection, immutability, fail-fast, design-for-deletion, yagni, explicit-over-implicit, separation-of-concerns, comprehensive-unit-testing, test-pyramid, good-test-properties, unit-test-patterns, flaky-test-prevention, test-data, testing-workflow]
  opted-in: []
  opted-out: []
change-history:
  - date: "{{DATE}}"
    description: "Initial draft"
---

# Feature Roadmap: {{FEATURE_NAME}}

## Goal and Purpose

_What does this feature do and why does it matter?_

## Platform / Component

_Which part of the system does this feature live in?_

## Tools and Technologies

_What languages, frameworks, libraries, or services are needed? Confirm these are already in use or approved for the project._

- [ ] Tool/tech 1
- [ ] Tool/tech 2

## External Resources

_Links to documentation, specs, APIs, or references that will be needed during implementation._

## Extended Description

_Detailed description of what the feature does, how it works, and how users interact with it._

## Acceptance Criteria

_How do we know this feature is done? List specific, testable criteria._

- [ ] Criterion 1
- [ ] Criterion 2

## Dependencies / Prerequisites

_What must exist or be true before this feature can be built?_

## Risks and Unknowns

_What could go wrong? What don't we know yet?_

## Architecture Decisions

_Key design choices and their rationale._

| Decision | Choice | Rationale |
|----------|--------|-----------|
| | | |

## Related Features / Issues

_Links to related GitHub issues, features, or prior work._

## Verification Strategy

| Check | Command / Approach |
|-------|-------------------|
| Build | `{{BUILD_COMMAND}}` |
| Test | `{{TEST_COMMAND}}` |
| Lint | `{{LINT_COMMAND}}` |
| Local verification | _Describe how to manually verify_ |
| Manual verification flags | _List steps that require human verification_ |

## Progress

| Total Steps | Complete | In Progress | Blocked | Not Started |
|-------------|----------|-------------|---------|-------------|
| {{N}}       | 0        | 0           | 0       | {{N}}       |

## Implementation Steps

### Step 1: {{DESCRIPTION}}

- **Type**: Auto | Manual
- **Status**: Not Started | In Progress | Complete | Blocked
- **Complexity**: S | M | L
- **Dependencies**: None | Step N
- **Expected Files**:
  - Create: `exact/path/to/new/file.ext`
  - Modify: `exact/path/to/existing/file.ext`
  - Test: `tests/path/to/test_file.ext`
- **Acceptance Criteria**:
  - [ ] _Specific, verifiable criterion with file path and expected behavior_
  - [ ] _Test: `test_function_name` — verifies specific behavior_
- **Testing / Verification**:
  - [ ] Build passes
  - [ ] Existing tests pass
  - [ ] New tests written and passing: `test_name_1`, `test_name_2`
- **PR**: _TBD_
- **Notes**: _Any implementation notes or blockers_

---

### Step 2: {{DESCRIPTION}}

- **Type**: Auto | Manual
- **Status**: Not Started
- **Complexity**: S | M | L
- **Dependencies**: None | Step N
- **Expected Files**:
  - Create: `exact/path/to/file.ext`
  - Modify: `exact/path/to/file.ext`
  - Test: `tests/path/to/test_file.ext`
- **Acceptance Criteria**:
  - [ ] _Specific criterion with file path and behavior_
- **Testing / Verification**:
  - [ ] Build passes
  - [ ] Existing tests pass
  - [ ] New tests: `test_name`
- **PR**: _TBD_
- **Notes**:

---

_Repeat for each step..._

## Conformance Vectors (Optional)

_Map acceptance criteria to specific test scenarios. Use when traceability between requirements and tests is important. Omit for simple features._

| ID | Criterion | Test Function | Expected Outcome |
|----|-----------|---------------|------------------|
| AC-1 | _Acceptance criterion from step_ | `test_function_name` | _Expected result_ |

## Deviations from Plan

_Filled in at completion — what changed from the original plan and why._

## Change History

_Populated automatically by /implement-roadmap when the feature is complete._

### Commits

| Hash | Description |
|------|-------------|

### Pull Request

_TBD_
