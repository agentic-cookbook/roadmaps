---
id: def-test-deps
created: 2026-01-01
modified: 2026-01-01
author: Test Runner <test@test.com>
change-history:
  - date: 2026-01-01
    author: Test Runner <test@test.com>
    summary: Initial creation
---

# Definition: WithDependencies

## Purpose

Fixture with step dependencies — step 2 depends on step 1, step 3 has no dependency.

## Verification

- Steps execute in correct dependency order
- Step 2 does not start until step 1 is complete
