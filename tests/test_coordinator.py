"""Tests for skills/implement-roadmap/references/coordinator."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

# The coordinator script location (no .py extension — it's a directly executable script)
COORDINATOR = Path(__file__).resolve().parent.parent / "skills" / "implement-roadmap" / "references" / "coordinator"

# Import coordinator functions directly by loading it with an explicit SourceFileLoader
import importlib.util
import importlib.machinery
loader = importlib.machinery.SourceFileLoader("coordinator", str(COORDINATOR))
spec = importlib.util.spec_from_loader("coordinator", loader, origin=str(COORDINATOR))
coord = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coord)


# ---------------------------------------------------------------------------
# parse_step_fields
# ---------------------------------------------------------------------------

class TestParseStepFields:
    def test_extracts_fields(self):
        block = (
            "\n"
            "- **GitHub Issue**: #10\n"
            "- **Type**: Auto\n"
            "- **Status**: Not Started\n"
            "- **Complexity**: M\n"
        )
        fields = coord.parse_step_fields(block)
        assert fields["GitHub Issue"] == "#10"
        assert fields["Type"] == "Auto"
        assert fields["Status"] == "Not Started"
        assert fields["Complexity"] == "M"

    def test_empty_block(self):
        fields = coord.parse_step_fields("")
        assert fields == {}

    def test_no_matching_lines(self):
        fields = coord.parse_step_fields("Just some text\nNo fields here\n")
        assert fields == {}


# ---------------------------------------------------------------------------
# list_all_steps
# ---------------------------------------------------------------------------

class TestListAllSteps:
    def test_parses_all_steps(self, coordinator_roadmap):
        roadmap = coordinator_roadmap / "Roadmaps" / "2026-03-21-TestFeature" / "Roadmap.md"
        steps = coord.list_all_steps(roadmap)
        assert len(steps) == 4

    def test_step_numbers(self, coordinator_roadmap):
        roadmap = coordinator_roadmap / "Roadmaps" / "2026-03-21-TestFeature" / "Roadmap.md"
        steps = coord.list_all_steps(roadmap)
        assert [s["step"] for s in steps] == [1, 2, 3, 4]

    def test_step_descriptions(self, coordinator_roadmap):
        roadmap = coordinator_roadmap / "Roadmaps" / "2026-03-21-TestFeature" / "Roadmap.md"
        steps = coord.list_all_steps(roadmap)
        assert steps[0]["description"] == "First step"
        assert steps[1]["description"] == "Second step"
        assert steps[2]["description"] == "Manual step"
        assert steps[3]["description"] == "Last step"

    def test_step_statuses(self, coordinator_roadmap):
        roadmap = coordinator_roadmap / "Roadmaps" / "2026-03-21-TestFeature" / "Roadmap.md"
        steps = coord.list_all_steps(roadmap)
        assert steps[0]["status"] == "Complete"
        assert steps[1]["status"] == "Not Started"
        assert steps[2]["status"] == "Not Started"
        assert steps[3]["status"] == "Not Started"

    def test_step_types(self, coordinator_roadmap):
        roadmap = coordinator_roadmap / "Roadmaps" / "2026-03-21-TestFeature" / "Roadmap.md"
        steps = coord.list_all_steps(roadmap)
        assert steps[0]["type"] == "Auto"
        assert steps[1]["type"] == "Auto"
        assert steps[2]["type"] == "Manual"
        assert steps[3]["type"] == "Auto"


# ---------------------------------------------------------------------------
# next-step command
# ---------------------------------------------------------------------------

class TestNextStep:
    def test_finds_first_non_complete_auto_step(self, coordinator_roadmap):
        roadmap = str(coordinator_roadmap / "Roadmaps" / "2026-03-21-TestFeature" / "Roadmap.md")
        result = subprocess.run(
            [sys.executable, str(COORDINATOR), "next-step", roadmap],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["action"] == "implement"
        assert data["step"] == 2
        assert data["description"] == "Second step"

    def test_skips_manual_and_reports(self, coordinator_roadmap):
        """Mark steps 1 and 2 complete so it hits manual step 3, skips it, goes to step 4."""
        roadmap_path = coordinator_roadmap / "Roadmaps" / "2026-03-21-TestFeature" / "Roadmap.md"
        content = roadmap_path.read_text()
        # Mark step 2 as complete
        content = content.replace(
            "### Step 2: Second step\n\n"
            "- **GitHub Issue**: #11\n- **Type**: Auto\n- **Status**: Not Started\n- **Complexity**: M",
            "### Step 2: Second step\n\n"
            "- **GitHub Issue**: #11\n- **Type**: Auto\n- **Status**: Complete\n- **Complexity**: M",
        )
        roadmap_path.write_text(content)

        result = subprocess.run(
            [sys.executable, str(COORDINATOR), "next-step", str(roadmap_path)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        # Step 3 is manual, so it should skip to step 4
        assert data["action"] == "implement"
        assert data["step"] == 4
        assert len(data["manual_skipped"]) == 1
        assert data["manual_skipped"][0]["step"] == 3

    def test_returns_done_when_all_auto_complete(self, coordinator_roadmap):
        """Mark all auto steps complete, leave manual step."""
        roadmap_path = coordinator_roadmap / "Roadmaps" / "2026-03-21-TestFeature" / "Roadmap.md"
        content = roadmap_path.read_text()
        content = content.replace(
            "### Step 2: Second step\n\n"
            "- **GitHub Issue**: #11\n- **Type**: Auto\n- **Status**: Not Started\n- **Complexity**: M",
            "### Step 2: Second step\n\n"
            "- **GitHub Issue**: #11\n- **Type**: Auto\n- **Status**: Complete\n- **Complexity**: M",
        )
        content = content.replace(
            "### Step 4: Last step\n\n"
            "- **GitHub Issue**: #13\n- **Type**: Auto\n- **Status**: Not Started\n- **Complexity**: L",
            "### Step 4: Last step\n\n"
            "- **GitHub Issue**: #13\n- **Type**: Auto\n- **Status**: Complete\n- **Complexity**: L",
        )
        roadmap_path.write_text(content)

        result = subprocess.run(
            [sys.executable, str(COORDINATOR), "next-step", str(roadmap_path)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["action"] == "done"
        assert len(data["manual_skipped"]) == 1


# ---------------------------------------------------------------------------
# summary command
# ---------------------------------------------------------------------------

class TestSummary:
    def test_returns_correct_summary(self, coordinator_roadmap):
        roadmap = str(coordinator_roadmap / "Roadmaps" / "2026-03-21-TestFeature" / "Roadmap.md")
        result = subprocess.run(
            [sys.executable, str(COORDINATOR), "summary", roadmap],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["feature"] == "TestFeature"
        assert data["total"] == 4
        assert data["complete"] == 1
        assert len(data["steps"]) == 4
