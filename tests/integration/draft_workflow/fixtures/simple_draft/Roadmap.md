---
id: rm-test-draft
created: 2026-01-01
modified: 2026-01-01
author: Test Runner <test@test.com>
change-history:
  - date: 2026-01-01
    author: Test Runner <test@test.com>
    summary: Initial creation
---

# Feature Roadmap: SimpleDraft

## Purpose

Minimal 4-step fixture for draft workflow integration tests. Tests the
plan-without-issues -> move-to-repo -> implement flow.

## Verification

- Steps 1 and 4 have no issue placeholders (Create Issues and Final PR steps)
- Steps 2 and 3 have issue placeholders to be replaced
- All steps are Auto type

## Progress

| Total Steps | Complete | In Progress | Blocked | Not Started |
|-------------|----------|-------------|---------|-------------|
| 4           | 0        | 0           | 0       | 4           |

## Implementation Steps

### Step 1: Create GitHub Issues

- **GitHub Issue**: N/A
- **Type**: Auto
- **Status**: Not Started
- **Complexity**: S
- **Dependencies**: None
- **Acceptance Criteria**:
  - [ ] GitHub issues created for Steps 2 and 3

### Step 2: Create test file

- **GitHub Issue**: {{REPO}}#{{ISSUE_NUMBER}}
- **Type**: Auto
- **Status**: Not Started
- **Complexity**: S
- **Dependencies**: Step 1
- **Acceptance Criteria**:
  - [ ] Test file created successfully

### Step 3: Append to test file

- **GitHub Issue**: {{REPO}}#{{ISSUE_NUMBER}}
- **Type**: Auto
- **Status**: Not Started
- **Complexity**: S
- **Dependencies**: Step 2
- **Acceptance Criteria**:
  - [ ] Content appended to test file

### Step 4: Create & Review Feature PR

- **GitHub Issue**: N/A
- **Type**: Auto
- **Status**: Not Started
- **Complexity**: M
- **Dependencies**: Step 3
- **Acceptance Criteria**:
  - [ ] Feature PR created and reviewed
