---
id: def-test-draft
created: 2026-01-01
modified: 2026-01-01
author: Test Runner <test@test.com>
change-history:
  - date: 2026-01-01
    author: Test Runner <test@test.com>
    summary: Initial creation
---

# Definition: SimpleDraft

## Purpose

Minimal 4-step fixture for draft workflow integration tests. Tests the
plan-without-issues → move-to-repo → implement flow.

## Verification

- Steps 1 and 4 have no issue placeholders (Create Issues and Final PR steps)
- Steps 2 and 3 have {{REPO}}#{{ISSUE_NUMBER}} placeholders to be replaced
- All steps are Auto type
