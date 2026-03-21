# Feature Roadmap: DashboardBugfixes

**Feature Definition**: `.claude/Features/FeatureDefinitions/DashboardBugfixes-FeatureDefinition.md`
**Created**: 2026-03-21
**Status**: Not Started
**Phase**: Ready

## Progress

| Total Steps | Complete | In Progress | Blocked | Not Started |
|-------------|----------|-------------|---------|-------------|
| 12          | 0        | 0           | 0       | 12          |

## Implementation Steps

### Step 1: Fix step ordering display

- **GitHub Issue**: #17
- **Type**: Auto
- **Status**: Not Started
- **Complexity**: M
- **Dependencies**: None
- **Acceptance Criteria**:
  - [ ] Steps display in correct numerical order in the dashboard
- **Testing / Verification**:
  - [ ] Load a roadmap with 5+ steps, verify order matches roadmap
- **PR**: _TBD_
- **Notes**: Either the execution order or the display order is wrong per the screenshot in the issue

---

### Step 2: Fix issues not showing in issues box

- **GitHub Issue**: #15
- **Type**: Auto
- **Status**: Not Started
- **Complexity**: M
- **Dependencies**: None
- **Acceptance Criteria**:
  - [ ] Issues loaded from roadmap appear in the issues panel
- **Testing / Verification**:
  - [ ] Load a roadmap with GitHub issues, verify they appear in the issues box
- **PR**: _TBD_
- **Notes**:

---

### Step 3: Fix completion state not showing green checkmark

- **GitHub Issue**: #16
- **Type**: Auto
- **Status**: Not Started
- **Complexity**: S
- **Dependencies**: None
- **Acceptance Criteria**:
  - [ ] When all steps complete, the dashboard shows a big green checkmark
- **Testing / Verification**:
  - [ ] Complete all steps in a test roadmap, verify checkmark appears
- **PR**: _TBD_
- **Notes**:

---

### Step 4: Fix dashboard spawning second instance

- **GitHub Issue**: #12
- **Type**: Auto
- **Status**: Not Started
- **Complexity**: M
- **Dependencies**: None
- **Acceptance Criteria**:
  - [ ] Only one dashboard instance runs at a time
  - [ ] Re-init reuses the existing instance instead of spawning a new one
- **Testing / Verification**:
  - [ ] Run init twice, verify only one browser tab opens
- **PR**: _TBD_
- **Notes**: Agent needed approval which paused things; when resumed, it respawned the dashboard

---

### Step 5: Show issue name with number and link in step

- **GitHub Issue**: #3
- **Type**: Auto
- **Status**: Not Started
- **Complexity**: S
- **Dependencies**: None
- **Acceptance Criteria**:
  - [ ] Each step shows the issue title, number, and a clickable link
- **Testing / Verification**:
  - [ ] Load roadmap, verify issue info appears in each step card
- **PR**: _TBD_
- **Notes**:

---

### Step 6: Show PR name in step

- **GitHub Issue**: #4
- **Type**: Auto
- **Status**: Not Started
- **Complexity**: S
- **Dependencies**: None
- **Acceptance Criteria**:
  - [ ] When a PR is created for a step, the PR title/number appears in the step card
- **Testing / Verification**:
  - [ ] Create a PR for a step, verify PR name shows in the step
- **PR**: _TBD_
- **Notes**:

---

### Step 7: Add review/merge info under pull requests

- **GitHub Issue**: #7
- **Type**: Auto
- **Status**: Not Started
- **Complexity**: M
- **Dependencies**: Step 6
- **Acceptance Criteria**:
  - [ ] PR panel shows status info (reviewed, fixed, submitted, merged)
- **Testing / Verification**:
  - [ ] Walk through PR lifecycle, verify status updates appear
- **PR**: _TBD_
- **Notes**:

---

### Step 8: Add per-step running timer

- **GitHub Issue**: #5
- **Type**: Auto
- **Status**: Not Started
- **Complexity**: M
- **Dependencies**: None
- **Acceptance Criteria**:
  - [ ] Each in-progress step shows elapsed time in the lower right
  - [ ] Timer stops when step completes
- **Testing / Verification**:
  - [ ] Start a step, verify timer counts up, verify it stops on completion
- **PR**: _TBD_
- **Notes**:

---

### Step 9: Add total roadmap running timer with badge

- **GitHub Issue**: #6
- **Type**: Auto
- **Status**: Not Started
- **Complexity**: S
- **Dependencies**: None
- **Acceptance Criteria**:
  - [ ] Upper right shows total elapsed time with a "running" badge
  - [ ] Timer stops when roadmap completes
- **Testing / Verification**:
  - [ ] Start dashboard, verify timer and badge appear and count up
- **PR**: _TBD_
- **Notes**:

---

### Step 10: Make event log smaller in height

- **GitHub Issue**: #8
- **Type**: Auto
- **Status**: Not Started
- **Complexity**: S
- **Dependencies**: None
- **Acceptance Criteria**:
  - [ ] Event log takes up roughly 1/3 of available height
  - [ ] Pinned to lower right with a max height
  - [ ] User can scroll it
- **Testing / Verification**:
  - [ ] Verify log height is reduced and scrollable
- **PR**: _TBD_
- **Notes**:

---

### Step 11: Auto-scroll to changed content in scrollers

- **GitHub Issue**: #10
- **Type**: Auto
- **Status**: Not Started
- **Complexity**: S
- **Dependencies**: None
- **Acceptance Criteria**:
  - [ ] When a new log entry appears, the log scrolls to show it
  - [ ] When the current step changes, it scrolls into view
- **Testing / Verification**:
  - [ ] Add log entries, verify auto-scroll behavior
- **PR**: _TBD_
- **Notes**:

---

### Step 12: Close #1 (plan-roadmap warning — already fixed)

- **GitHub Issue**: #1
- **Type**: Auto
- **Status**: Not Started
- **Complexity**: S
- **Dependencies**: None
- **Acceptance Criteria**:
  - [ ] Issue #1 is closed with a comment noting the fix
- **Testing / Verification**:
  - [ ] Verify issue is closed on GitHub
- **PR**: _TBD_
- **Notes**: Already fixed — just needs the issue closed

---

## Completion Checklist

- [ ] All steps marked Complete
- [ ] All GitHub issues closed
- [ ] All PRs merged
- [ ] Feature Definition updated with completion date and deviations
- [ ] Feature Summary written
- [ ] Roadmap moved to Completed-Roadmaps/
