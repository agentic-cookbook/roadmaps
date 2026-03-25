"""Integration tests for planning functions against cat-herding-tests repo."""

import sys
from pathlib import Path

import pytest

# Ensure worktree scripts/ is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import roadmap_lib as lib

from tests.integration.helpers import _run_git


class TestFullPlanningFlow:
    """End-to-end: create dir, write files, create issues, replace placeholders, validate."""

    def test_complete_planning_lifecycle(self, planning_dir_with_files, gh):
        info = planning_dir_with_files
        rd = info.path

        # Verify directory structure
        assert (rd / "State").is_dir()
        assert (rd / "History").is_dir()
        assert (rd / "Roadmap.md").exists()

        # Verify state files were created correctly
        assert lib.current_state(rd) == "Planning"

        # Create real GitHub issues for each step
        roadmap_content = (rd / "Roadmap.md").read_text()
        step_issue_map = {}
        for step_num in range(1, 4):
            issue_num = gh.create_issue(
                f"Test: [PlanFull] Step {step_num}",
                body=lib.generate_issue_body(
                    feature_name="PlanFull",
                    step_description=f"Step {step_num} description",
                    acceptance_criteria=f"- [ ] Step {step_num} done",
                    complexity="S",
                    dependencies="None" if step_num == 1 else f"Step {step_num - 1}",
                    roadmap_dir=f"Roadmaps/2026-03-24-PlanFull",
                ),
            )
            info.track_issue(issue_num)
            step_issue_map[step_num] = issue_num

        # Replace placeholders
        count = lib.replace_issue_placeholders(rd / "Roadmap.md", step_issue_map)
        assert count == 3

        # Verify no placeholders remain
        content = (rd / "Roadmap.md").read_text()
        assert "{{REPO}}" not in content
        assert "{{ISSUE_NUMBER}}" not in content

        # Verify actual issue numbers are present
        for issue_num in step_issue_map.values():
            assert f"#{issue_num}" in content

        # Create Ready state
        lib.create_state_file(rd, "ready", date="2026-03-24")
        assert lib.current_state(rd) == "Ready"
        assert lib.is_implementable(rd)

        # Validate complete
        ok, errors = lib.validate_planning_complete(rd)
        assert ok is True, f"Validation failed: {errors}"
        assert errors == []

        # Verify issues exist on GitHub
        for issue_num in step_issue_map.values():
            issue = gh.get_issue(issue_num)
            assert issue["state"] == "OPEN"


class TestValidationCatchesIncomplete:
    """Validation correctly identifies missing artifacts."""

    def test_missing_ready_state(self, planning_dir):
        rd = planning_dir
        (rd / "Roadmap.md").write_text("# Roadmap\n\n### Step 1: Foo\n\n- **GitHub Issue**: #1\n")
        lib.create_state_file(rd, "created", date="2026-03-24")
        lib.create_state_file(rd, "planning", date="2026-03-24")
        # No Ready state

        ok, errors = lib.validate_planning_complete(rd)
        assert ok is False
        assert any("Ready" in e for e in errors)

    def test_unresolved_placeholders(self, planning_dir):
        rd = planning_dir
        (rd / "Roadmap.md").write_text(
            "# Roadmap\n\n### Step 1: Foo\n\n- **GitHub Issue**: {{REPO}}#{{ISSUE_NUMBER}}\n"
        )
        lib.create_state_file(rd, "created", date="2026-03-24")
        lib.create_state_file(rd, "planning", date="2026-03-24")
        lib.create_state_file(rd, "ready", date="2026-03-24")

        ok, errors = lib.validate_planning_complete(rd)
        assert ok is False
        assert any("placeholder" in e.lower() for e in errors)


class TestIssuePlaceholderReplacement:
    """Placeholder replacement with real GitHub issues."""

    def test_replace_with_real_issues(self, planning_dir_with_files, gh):
        info = planning_dir_with_files
        rd = info.path

        # Create 3 real issues
        step_issue_map = {}
        for step_num in range(1, 4):
            issue_num = gh.create_issue(f"Test: Placeholder Step {step_num}")
            info.track_issue(issue_num)
            step_issue_map[step_num] = issue_num

        # Replace
        count = lib.replace_issue_placeholders(rd / "Roadmap.md", step_issue_map)
        assert count == 3

        # Verify each step section has the correct issue number
        content = (rd / "Roadmap.md").read_text()
        for step_num, issue_num in step_issue_map.items():
            # Find the step section and verify the issue reference is there
            import re
            pattern = rf"### Step {step_num}:.*?(?=### Step \d+:|\Z)"
            match = re.search(pattern, content, re.DOTALL)
            assert match, f"Step {step_num} section not found"
            assert f"#{issue_num}" in match.group(0), (
                f"Issue #{issue_num} not found in Step {step_num} section"
            )
