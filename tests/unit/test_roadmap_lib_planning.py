"""Tests for planning functions in scripts/roadmap_lib.py."""

import importlib
import sys
from datetime import date
from pathlib import Path

import pytest

# Ensure the worktree's scripts/ takes precedence over installed versions.
# test_coordinator.py loads the coordinator via SourceFileLoader, which inserts
# ~/.claude/scripts/ into sys.path, potentially shadowing the worktree version.
_scripts_dir = str(Path(__file__).resolve().parent.parent.parent / "scripts")
if _scripts_dir not in sys.path[:2]:
    sys.path.insert(0, _scripts_dir)
if "roadmap_lib" in sys.modules:
    # Reload from the correct path if already cached from installed location
    importlib.reload(sys.modules["roadmap_lib"])

import roadmap_lib as lib


# ---------------------------------------------------------------------------
# create_planning_dir
# ---------------------------------------------------------------------------

class TestCreatePlanningDir:
    def test_creates_directory_structure(self, tmp_path):
        rd = lib.create_planning_dir(tmp_path, "MyFeature", date="2026-03-24")
        assert rd.exists()
        assert (rd / "State").is_dir()
        assert (rd / "History").is_dir()
        assert rd.name == "2026-03-24-MyFeature"
        assert rd.parent.name == "Roadmaps"

    def test_uses_today_when_no_date(self, tmp_path):
        rd = lib.create_planning_dir(tmp_path, "AutoDate")
        today = date.today().isoformat()
        assert rd.name == f"{today}-AutoDate"

    def test_raises_on_empty_feature_name(self, tmp_path):
        with pytest.raises(ValueError, match="feature_name"):
            lib.create_planning_dir(tmp_path, "")

    def test_raises_on_existing_directory(self, tmp_path):
        lib.create_planning_dir(tmp_path, "Duplicate", date="2026-03-24")
        with pytest.raises(FileExistsError):
            lib.create_planning_dir(tmp_path, "Duplicate", date="2026-03-24")

    def test_creates_roadmaps_parent_if_missing(self, tmp_path):
        rd = lib.create_planning_dir(tmp_path, "Fresh", date="2026-03-24")
        assert (tmp_path / "Roadmaps").is_dir()
        assert rd.exists()


# ---------------------------------------------------------------------------
# create_state_file
# ---------------------------------------------------------------------------

class TestCreateStateFile:
    def test_creates_state_file_with_frontmatter(self, tmp_path):
        state_dir = tmp_path / "State"
        state_dir.mkdir()
        path = lib.create_state_file(tmp_path, "created", date="2026-03-24")
        assert path.exists()
        content = path.read_text()
        assert "event: created" in content
        assert "date: 2026-03-24" in content

    def test_capitalizes_event_in_filename(self, tmp_path):
        state_dir = tmp_path / "State"
        state_dir.mkdir()
        path = lib.create_state_file(tmp_path, "planning", date="2026-03-24")
        assert path.name == "2026-03-24-Planning.md"

    def test_uses_today_when_no_date(self, tmp_path):
        state_dir = tmp_path / "State"
        state_dir.mkdir()
        path = lib.create_state_file(tmp_path, "ready")
        today = date.today().isoformat()
        assert path.name == f"{today}-Ready.md"

    def test_works_with_current_state(self, tmp_path):
        """State files created by this function should be readable by current_state()."""
        state_dir = tmp_path / "State"
        state_dir.mkdir()
        lib.create_state_file(tmp_path, "created", date="2026-03-24")
        lib.create_state_file(tmp_path, "planning", date="2026-03-24")
        lib.create_state_file(tmp_path, "ready", date="2026-03-24")
        assert lib.current_state(tmp_path) == "Ready"

    def test_raises_if_state_dir_missing(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="State"):
            lib.create_state_file(tmp_path, "created")


# ---------------------------------------------------------------------------
# generate_issue_body
# ---------------------------------------------------------------------------

class TestGenerateIssueBody:
    def test_returns_correct_markdown(self):
        body = lib.generate_issue_body(
            feature_name="MyFeature",
            step_description="Build the widget",
            acceptance_criteria="- [ ] Widget works",
            complexity="M",
            dependencies="Step 1",
            roadmap_dir="Roadmaps/2026-03-24-MyFeature",
        )
        assert "## Context" in body
        assert "Part of the MyFeature feature." in body

        assert "Roadmaps/2026-03-24-MyFeature/Roadmap.md" in body
        assert "## Step Details" in body
        assert "Build the widget" in body
        assert "## Acceptance Criteria" in body
        assert "Widget works" in body
        assert "## Complexity" in body
        assert "M" in body
        assert "## Dependencies" in body
        assert "Step 1" in body

    def test_raises_on_empty_feature_name(self):
        with pytest.raises(ValueError, match="feature_name"):
            lib.generate_issue_body("", "desc", "ac", "S", "none", "dir")

    def test_raises_on_empty_step_description(self):
        with pytest.raises(ValueError, match="step_description"):
            lib.generate_issue_body("Feat", "", "ac", "S", "none", "dir")


# ---------------------------------------------------------------------------
# replace_issue_placeholders
# ---------------------------------------------------------------------------

class TestReplaceIssuePlaceholders:
    def _write_roadmap(self, tmp_path, n_steps=3):
        """Helper: write a Roadmap.md with N steps and placeholders."""
        lines = ["# Feature Roadmap: Test\n\n## Implementation Steps\n"]
        for i in range(1, n_steps + 1):
            lines.append(f"\n### Step {i}: Step {i} description\n")
            lines.append(f"\n- **GitHub Issue**: {{{{REPO}}}}#{{{{ISSUE_NUMBER}}}}")
            lines.append(f"\n- **Type**: Auto")
            lines.append(f"\n- **Status**: Not Started\n")
        rm = tmp_path / "Roadmap.md"
        rm.write_text("\n".join(lines))
        return rm

    def test_replaces_placeholders_in_correct_sections(self, tmp_path):
        rm = self._write_roadmap(tmp_path, n_steps=3)
        count = lib.replace_issue_placeholders(rm, {1: 42, 2: 43, 3: 44})
        assert count == 3
        content = rm.read_text()
        assert "#42" in content
        assert "#43" in content
        assert "#44" in content
        assert "{{REPO}}" not in content

    def test_replaces_only_specified_steps(self, tmp_path):
        rm = self._write_roadmap(tmp_path, n_steps=3)
        count = lib.replace_issue_placeholders(rm, {1: 42})
        assert count == 1
        content = rm.read_text()
        assert "#42" in content
        # Steps 2 and 3 still have placeholders
        assert "{{REPO}}#{{ISSUE_NUMBER}}" in content

    def test_returns_zero_when_no_placeholders(self, tmp_path):
        rm = tmp_path / "Roadmap.md"
        rm.write_text("### Step 1: Foo\n\n- **GitHub Issue**: #42\n")
        count = lib.replace_issue_placeholders(rm, {1: 99})
        assert count == 0

    def test_raises_on_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            lib.replace_issue_placeholders(tmp_path / "nope.md", {1: 42})

    def test_raises_on_empty_map(self, tmp_path):
        rm = self._write_roadmap(tmp_path)
        with pytest.raises(ValueError, match="step_issue_map"):
            lib.replace_issue_placeholders(rm, {})

    def test_preserves_surrounding_content(self, tmp_path):
        rm = self._write_roadmap(tmp_path, n_steps=1)
        original = rm.read_text()
        lib.replace_issue_placeholders(rm, {1: 42})
        content = rm.read_text()
        # The heading and other fields should be preserved
        assert "# Feature Roadmap: Test" in content
        assert "### Step 1: Step 1 description" in content
        assert "- **Type**: Auto" in content


# ---------------------------------------------------------------------------
# validate_planning_complete
# ---------------------------------------------------------------------------

class TestValidatePlanningComplete:
    def _make_complete_dir(self, tmp_path):
        """Helper: create a fully valid planning directory."""
        rd = tmp_path / "2026-03-24-TestFeature"
        rd.mkdir()
        (rd / "State").mkdir()
        (rd / "History").mkdir()
        (rd / "Roadmap.md").write_text(
            "# Feature Roadmap: TestFeature\n\n"
            "### Step 1: First\n\n- **GitHub Issue**: #42\n- **Status**: Not Started\n"
        )
        (rd / "State" / "2026-03-24-Created.md").write_text("---\nevent: created\ndate: 2026-03-24\n---\n")
        (rd / "State" / "2026-03-24-Planning.md").write_text("---\nevent: planning\ndate: 2026-03-24\n---\n")
        (rd / "State" / "2026-03-24-Ready.md").write_text("---\nevent: ready\ndate: 2026-03-24\n---\n")
        return rd

    def test_passes_for_complete_directory(self, tmp_path):
        rd = self._make_complete_dir(tmp_path)
        ok, errors = lib.validate_planning_complete(rd)
        assert ok is True
        assert errors == []

    def test_catches_missing_roadmap(self, tmp_path):
        rd = self._make_complete_dir(tmp_path)
        (rd / "Roadmap.md").unlink()
        ok, errors = lib.validate_planning_complete(rd)
        assert ok is False
        assert any("Roadmap.md" in e for e in errors)

    def test_catches_missing_state_files(self, tmp_path):
        rd = self._make_complete_dir(tmp_path)
        (rd / "State" / "2026-03-24-Ready.md").unlink()
        ok, errors = lib.validate_planning_complete(rd)
        assert ok is False
        assert any("Ready" in e for e in errors)

    def test_catches_remaining_placeholders(self, tmp_path):
        rd = self._make_complete_dir(tmp_path)
        (rd / "Roadmap.md").write_text(
            "### Step 1: First\n\n- **GitHub Issue**: {{REPO}}#{{ISSUE_NUMBER}}\n"
        )
        ok, errors = lib.validate_planning_complete(rd)
        assert ok is False
        assert any("placeholder" in e.lower() for e in errors)

    def test_handles_missing_state_dir(self, tmp_path):
        rd = self._make_complete_dir(tmp_path)
        import shutil
        shutil.rmtree(rd / "State")
        ok, errors = lib.validate_planning_complete(rd)
        assert ok is False
        assert any("Created" in e for e in errors)

    def test_reports_all_errors(self, tmp_path):
        """When multiple things are wrong, all are reported."""
        rd = tmp_path / "2026-03-24-Broken"
        rd.mkdir()
        # No State/, no files at all
        ok, errors = lib.validate_planning_complete(rd)
        assert ok is False
        assert len(errors) >= 2  # At least Roadmap.md missing + state files
