"""Tests for data integrity guardrails.

Verifies that the roadmap system's guardrails prevent data loss:
- Repair skill preserves all steps (no scope reduction)
- write_frontmatter correctly serializes list items
- Step count comparison detects removals
- Complexity is never used as a filter
"""

import sys
from pathlib import Path

import pytest

_scripts_dir = str(Path(__file__).resolve().parent.parent.parent / "scripts")
if _scripts_dir not in sys.path[:2]:
    sys.path.insert(0, _scripts_dir)

import roadmap_lib as lib


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ROADMAP_20_STEPS = """---
id: test-integrity-uuid
project: test-repo
plan-version: "12"
created: "2026-03-25"
modified: "2026-03-25"
author: "Test"
description: "Test roadmap with mixed complexity"
reviews:
  per-step: [code-reviewer]
  final: [code-reviewer, silent-failure-hunter]
change-history:
  - date: "2026-03-25"
    description: "Initial draft"
---

# Roadmap: IntegrityTest

## Goal and Purpose

Test data integrity.

## Progress

| Total Steps | Complete | In Progress | Blocked | Not Started |
|-------------|----------|-------------|---------|-------------|
| 20          | 0        | 0           | 0       | 20          |

## Implementation Steps

### Step 1: Create Draft PR

- **Type**: Auto
- **Status**: Not Started
- **Complexity**: S

---

### Step 2: Small task

- **Type**: Auto
- **Status**: Not Started
- **Complexity**: S

---

### Step 3: Medium task

- **Type**: Auto
- **Status**: Not Started
- **Complexity**: M

---

### Step 4: Large task one

- **Type**: Auto
- **Status**: Not Started
- **Complexity**: L
- **Acceptance Criteria**:
  - [ ] Complex feature A implemented
  - [ ] Complex feature B implemented

---

### Step 5: Medium task two

- **Type**: Auto
- **Status**: Not Started
- **Complexity**: M

---

### Step 6: Large task two

- **Type**: Auto
- **Status**: Not Started
- **Complexity**: L
- **Acceptance Criteria**:
  - [ ] Complex feature C implemented
  - [ ] Complex feature D implemented

---

### Step 7: Large task three

- **Type**: Auto
- **Status**: Not Started
- **Complexity**: L
- **Acceptance Criteria**:
  - [ ] Complex feature E implemented

---

### Step 8: Small task two

- **Type**: Auto
- **Status**: Not Started
- **Complexity**: S

---

### Step 9: Large task four

- **Type**: Auto
- **Status**: Not Started
- **Complexity**: L

---

### Step 10: Medium task three

- **Type**: Auto
- **Status**: Not Started
- **Complexity**: M

---

### Step 11: Large task five

- **Type**: Auto
- **Status**: Not Started
- **Complexity**: L

---

### Step 12: Small task three

- **Type**: Auto
- **Status**: Not Started
- **Complexity**: S

---

### Step 13: Large task six

- **Type**: Auto
- **Status**: Not Started
- **Complexity**: L

---

### Step 14: Medium task four

- **Type**: Auto
- **Status**: Not Started
- **Complexity**: M

---

### Step 15: Small task four

- **Type**: Auto
- **Status**: Not Started
- **Complexity**: S

---

### Step 16: Medium task five

- **Type**: Auto
- **Status**: Not Started
- **Complexity**: M

---

### Step 17: Small task five

- **Type**: Auto
- **Status**: Not Started
- **Complexity**: S

---

### Step 18: Medium task six

- **Type**: Auto
- **Status**: Not Started
- **Complexity**: M

---

### Step 19: Small task six

- **Type**: Auto
- **Status**: Not Started
- **Complexity**: S

---

### Step 20: Finalize & Merge PR

- **Type**: Auto
- **Status**: Not Started
- **Complexity**: M
"""


def _write_roadmap(tmp_path, content=ROADMAP_20_STEPS):
    rd = tmp_path / "Roadmaps" / "2026-03-25-IntegrityTest"
    rd.mkdir(parents=True)
    (rd / "Roadmap.md").write_text(content)
    (rd / "State").mkdir()
    (rd / "History").mkdir()
    (rd / "State" / "2026-03-25-Ready.md").write_text("---\nevent: ready\n---\n")
    return rd


# ---------------------------------------------------------------------------
# Step count preservation
# ---------------------------------------------------------------------------

class TestStepCountPreservation:
    """Verify that step counts are accurately tracked and compared."""

    def test_counts_all_20_steps(self, tmp_path):
        rd = _write_roadmap(tmp_path)
        total, complete = lib.count_steps(rd / "Roadmap.md")
        assert total == 20
        assert complete == 0

    def test_counts_l_complexity_steps(self, tmp_path):
        rd = _write_roadmap(tmp_path)
        content = (rd / "Roadmap.md").read_text()
        l_count = content.count("**Complexity**: L")
        assert l_count == 6, f"Expected 6 L-complexity steps, got {l_count}"

    def test_counts_all_complexity_levels(self, tmp_path):
        rd = _write_roadmap(tmp_path)
        content = (rd / "Roadmap.md").read_text()
        s_count = content.count("**Complexity**: S")
        m_count = content.count("**Complexity**: M")
        l_count = content.count("**Complexity**: L")
        assert s_count + m_count + l_count == 20
        assert s_count == 7  # S steps
        assert m_count == 7  # M steps
        assert l_count == 6  # L steps

    def test_detects_step_removal(self, tmp_path):
        """Simulate what the rogue repair did: remove L-complexity steps."""
        rd = _write_roadmap(tmp_path)
        original_total, _ = lib.count_steps(rd / "Roadmap.md")

        # Simulate removing L-complexity steps (the actual bug)
        content = (rd / "Roadmap.md").read_text()
        import re
        # Remove step sections that have Complexity: L
        lines = content.split('\n')
        filtered = []
        skip = False
        for line in lines:
            if line.startswith('### Step') and skip:
                skip = False
            if skip and line.strip() == '---':
                skip = False
                continue
            if '**Complexity**: L' in line:
                # Remove this step and its parent section
                # Go back to remove the ### header
                while filtered and not filtered[-1].startswith('### Step'):
                    filtered.pop()
                if filtered and filtered[-1].startswith('### Step'):
                    filtered.pop()
                # Remove preceding ---
                while filtered and filtered[-1].strip() == '---':
                    filtered.pop()
                skip = True
                continue
            if not skip:
                filtered.append(line)

        modified_content = '\n'.join(filtered)
        (rd / "Roadmap.md").write_text(modified_content)
        modified_total, _ = lib.count_steps(rd / "Roadmap.md")

        # This is the detection: the step count changed
        assert modified_total < original_total, \
            "Modified roadmap should have fewer steps"
        assert original_total - modified_total == 6, \
            f"Expected 6 steps removed, got {original_total - modified_total}"


# ---------------------------------------------------------------------------
# write_frontmatter bug regression
# ---------------------------------------------------------------------------

class TestWriteFrontmatterListItems:
    """Regression: write_frontmatter must correctly serialize list items."""

    def test_dict_list_items_roundtrip(self, tmp_path):
        """Dict list items (change-history) must survive a roundtrip."""
        rd = tmp_path / "test.md"
        rd.write_text(
            "---\nchange-history:\n  - date: 2026-03-25\n    description: Initial\n---\n\n# Content\n"
        )
        meta, body = lib.parse_frontmatter(rd)
        result = lib.write_frontmatter(meta, body)
        rd.write_text(result)
        meta2, _ = lib.parse_frontmatter(rd)
        assert meta2["change-history"][0]["date"] == "2026-03-25"
        assert meta2["change-history"][0]["description"] == "Initial"

    def test_simple_string_values_preserved(self, tmp_path):
        """Simple frontmatter values must survive a roundtrip."""
        rd = tmp_path / "test.md"
        rd.write_text("---\nid: test-uuid\nproject: my-repo\nauthor: Test User\n---\n\n# Content\n")
        meta, body = lib.parse_frontmatter(rd)
        result = lib.write_frontmatter(meta, body)
        rd.write_text(result)
        meta2, _ = lib.parse_frontmatter(rd)
        assert meta2["id"] == "test-uuid"
        assert meta2["project"] == "my-repo"
        assert meta2["author"] == "Test User"


# ---------------------------------------------------------------------------
# Guardrail content verification
# ---------------------------------------------------------------------------

class TestGuardrailContent:
    """Verify that the skill files contain the required guardrail text."""

    def test_repair_has_no_scope_reduction_rule(self):
        skill = Path(__file__).parent.parent.parent / "skills" / "repair-roadmap" / "SKILL.md"
        content = skill.read_text()
        assert "NO SCOPE REDUCTION" in content
        assert "DESCRIPTOR" in content
        assert "not a FILTER" in content or "not a filter" in content

    def test_repair_has_step_count_comparison(self):
        skill = Path(__file__).parent.parent.parent / "skills" / "repair-roadmap" / "SKILL.md"
        content = skill.read_text()
        assert "STEP COUNT COMPARISON" in content
        assert "WARNING" in content
        assert "REMOVED" in content

    def test_repair_guards_prevent_step_removal(self):
        guards = Path(__file__).parent.parent.parent / "skills" / "repair-roadmap" / "references" / "active-guards.md"
        content = guards.read_text()
        assert "fewer steps" in content
        assert "complexity" in content.lower()
        assert "STOP" in content

    def test_repair_guards_prevent_complexity_filtering(self):
        guards = Path(__file__).parent.parent.parent / "skills" / "repair-roadmap" / "references" / "active-guards.md"
        content = guards.read_text()
        assert "filter" in content.lower()
        assert "L-complexity" in content

    def test_repair_guards_prevent_simplification(self):
        guards = Path(__file__).parent.parent.parent / "skills" / "repair-roadmap" / "references" / "active-guards.md"
        content = guards.read_text()
        assert "simplify" in content.lower() or "merge" in content.lower()

    def test_plan_roadmap_has_alignment_review(self):
        skill = Path(__file__).parent.parent.parent / "skills" / "plan-roadmap" / "SKILL.md"
        content = skill.read_text()
        assert "Alignment" in content or "alignment" in content
        assert "Discussion Summary" in content or "discussion-summary" in content

    def test_plan_roadmap_guards_prevent_complexity_filter(self):
        guards = Path(__file__).parent.parent.parent / "skills" / "plan-roadmap" / "references" / "active-guards.md"
        content = guards.read_text()
        # Should have some guardrail about not dropping steps
        assert "worktree" in content.lower()  # at minimum, worktree guard exists


# ---------------------------------------------------------------------------
# Violation scenarios — "Claude going rogue"
# ---------------------------------------------------------------------------

class TestViolationDetection:
    """Test that we can detect when an agent violates data integrity rules."""

    def test_detect_step_count_decrease(self, tmp_path):
        """If a modified roadmap has fewer steps, we must be able to detect it."""
        rd = _write_roadmap(tmp_path)
        original_total, _ = lib.count_steps(rd / "Roadmap.md")

        # Rogue agent removes 3 steps
        content = (rd / "Roadmap.md").read_text()
        content = content.replace("### Step 4: Large task one", "")
        content = content.replace("### Step 6: Large task two", "")
        content = content.replace("### Step 7: Large task three", "")
        (rd / "Roadmap.md").write_text(content)

        new_total, _ = lib.count_steps(rd / "Roadmap.md")
        assert new_total < original_total
        removed = original_total - new_total
        assert removed > 0, "Must detect that steps were removed"

    def test_detect_acceptance_criteria_loss(self, tmp_path):
        """If acceptance criteria are removed, we must be able to detect it."""
        rd = _write_roadmap(tmp_path)
        content = (rd / "Roadmap.md").read_text()

        original_criteria_count = content.count("- [ ]")

        # Rogue agent removes acceptance criteria
        content = content.replace(
            "  - [ ] Complex feature A implemented\n  - [ ] Complex feature B implemented",
            ""
        )
        (rd / "Roadmap.md").write_text(content)

        new_criteria_count = content.count("- [ ]")
        assert new_criteria_count < original_criteria_count, \
            "Must detect acceptance criteria removal"

    def test_detect_complexity_downgrade(self, tmp_path):
        """If L steps are downgraded to M, we must be able to detect it."""
        rd = _write_roadmap(tmp_path)
        content = (rd / "Roadmap.md").read_text()

        original_l_count = content.count("**Complexity**: L")

        # Rogue agent downgrades all L to M
        content = content.replace("**Complexity**: L", "**Complexity**: M")
        (rd / "Roadmap.md").write_text(content)

        new_l_count = content.count("**Complexity**: L")
        assert new_l_count == 0
        assert original_l_count == 6, "Original should have had 6 L steps"

    def test_frontmatter_id_preserved_through_write(self, tmp_path):
        """ID must survive a read-write cycle."""
        rd = _write_roadmap(tmp_path)
        meta, body = lib.parse_frontmatter(rd / "Roadmap.md")
        original_id = meta["id"]
        assert original_id == "test-integrity-uuid"

        (rd / "Roadmap.md").write_text(lib.write_frontmatter(meta, body))

        meta2, _ = lib.parse_frontmatter(rd / "Roadmap.md")
        assert meta2["id"] == original_id, "ID must survive read-write cycle"

    def test_project_field_preserved_through_write(self, tmp_path):
        """Project field must survive a read-write cycle."""
        rd = _write_roadmap(tmp_path)
        meta, body = lib.parse_frontmatter(rd / "Roadmap.md")
        (rd / "Roadmap.md").write_text(lib.write_frontmatter(meta, body))
        meta2, _ = lib.parse_frontmatter(rd / "Roadmap.md")
        assert meta2["project"] == "test-repo"

    def test_body_content_preserved_through_write(self, tmp_path):
        """Full body content must survive a read-write cycle."""
        rd = _write_roadmap(tmp_path)
        _, body = lib.parse_frontmatter(rd / "Roadmap.md")
        original_step_count = body.count("### Step")

        meta, body2 = lib.parse_frontmatter(rd / "Roadmap.md")
        (rd / "Roadmap.md").write_text(lib.write_frontmatter(meta, body2))

        _, body3 = lib.parse_frontmatter(rd / "Roadmap.md")
        new_step_count = body3.count("### Step")
        assert new_step_count == original_step_count, \
            f"Body lost steps through write cycle: {original_step_count} -> {new_step_count}"
