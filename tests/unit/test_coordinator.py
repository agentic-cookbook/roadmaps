"""Tests for skills/implement-roadmap/references/coordinator."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# The coordinator script location (no .py extension — it's a directly executable script)
COORDINATOR = Path(__file__).resolve().parent.parent.parent / "skills" / "implement-roadmap" / "references" / "coordinator"

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


# ---------------------------------------------------------------------------
# Helpers shared by new tests
# ---------------------------------------------------------------------------

def _make_roadmap_dir(tmp_path, date_name, steps_text, state="Ready", project=None):
    """Create a minimal roadmap directory with State/ and Roadmap.md."""
    rd = tmp_path / "Roadmaps" / date_name
    rd.mkdir(parents=True)
    state_dir = rd / "State"
    state_dir.mkdir()
    (state_dir / f"2026-03-21-{state}.md").write_text(f"# State: {state}\n")
    if project:
        frontmatter = f"---\nproject: {project}\n---\n\n"
        (rd / "Roadmap.md").write_text(frontmatter + steps_text)
    else:
        (rd / "Roadmap.md").write_text(steps_text)
    return rd


def _make_workdir_roadmap(base, project, date_name, steps_text, state="Ready"):
    """Create a roadmap in ~/.roadmaps/<project>/ style layout."""
    rd = base / project / date_name
    rd.mkdir(parents=True)
    state_dir = rd / "State"
    state_dir.mkdir()
    (state_dir / f"2026-03-21-{state}.md").write_text(f"# State: {state}\n")
    frontmatter = f"---\nproject: {project}\n---\n\n"
    (rd / "Roadmap.md").write_text(frontmatter + steps_text)
    return rd


def _init_git_repo(path, name=None):
    """Initialize a bare git repo at path so git rev-parse works."""
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=str(path), capture_output=True)
    if name:
        # Rename to control basename
        pass  # basename is already correct if path ends with name


# ---------------------------------------------------------------------------
# TestResolve (cmd_resolve — completely untested)
# ---------------------------------------------------------------------------

class TestResolve:
    def test_resolve_single_match(self, tmp_path):
        """Single implementable roadmap, name filter matches — returns path/name/total/complete."""
        _make_roadmap_dir(
            tmp_path, "2026-03-21-AlphaFeature",
            "# Feature Roadmap: AlphaFeature\n\n"
            "### Step 1: Do thing\n\n- **Status**: Complete\n- **Type**: Auto\n\n"
            "### Step 2: Do another\n\n- **Status**: Not Started\n- **Type**: Auto\n",
        )
        result = subprocess.run(
            [sys.executable, str(COORDINATOR), "resolve", "AlphaFeature"],
            capture_output=True, text=True, cwd=str(tmp_path),
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "path" in data
        assert data["name"] == "AlphaFeature"
        assert data["total"] == 2
        assert data["complete"] == 1

    def test_resolve_multiple_matches(self, tmp_path):
        """Two implementable roadmaps, no name filter — returns choose array."""
        _make_roadmap_dir(
            tmp_path, "2026-03-21-AlphaFeature",
            "# Feature Roadmap: AlphaFeature\n\n"
            "### Step 1: Do thing\n\n- **Status**: Not Started\n- **Type**: Auto\n",
        )
        _make_roadmap_dir(
            tmp_path, "2026-03-22-BetaFeature",
            "# Feature Roadmap: BetaFeature\n\n"
            "### Step 1: Do other\n\n- **Status**: Not Started\n- **Type**: Auto\n",
        )
        result = subprocess.run(
            [sys.executable, str(COORDINATOR), "resolve"],
            capture_output=True, text=True, cwd=str(tmp_path),
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "choose" in data
        names = [item["name"] for item in data["choose"]]
        assert "AlphaFeature" in names
        assert "BetaFeature" in names

    def test_resolve_no_match(self, tmp_path):
        """Name filter matches nothing — returns JSON error and nonzero exit."""
        _make_roadmap_dir(
            tmp_path, "2026-03-21-AlphaFeature",
            "# Feature Roadmap: AlphaFeature\n\n"
            "### Step 1: Do thing\n\n- **Status**: Not Started\n- **Type**: Auto\n",
        )
        result = subprocess.run(
            [sys.executable, str(COORDINATOR), "resolve", "NonExistent"],
            capture_output=True, text=True, cwd=str(tmp_path),
        )
        assert result.returncode != 0
        data = json.loads(result.stdout)
        assert "error" in data

    def test_resolve_exact_name_match(self, tmp_path):
        """Two roadmaps but resolve with exact name — returns single match, not choose."""
        _make_roadmap_dir(
            tmp_path, "2026-03-21-AlphaFeature",
            "# Feature Roadmap: AlphaFeature\n\n"
            "### Step 1: Do thing\n\n- **Status**: Not Started\n- **Type**: Auto\n",
        )
        _make_roadmap_dir(
            tmp_path, "2026-03-22-BetaFeature",
            "# Feature Roadmap: BetaFeature\n\n"
            "### Step 1: Do other\n\n- **Status**: Not Started\n- **Type**: Auto\n",
        )
        result = subprocess.run(
            [sys.executable, str(COORDINATOR), "resolve", "AlphaFeature"],
            capture_output=True, text=True, cwd=str(tmp_path),
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "choose" not in data
        assert data["name"] == "AlphaFeature"
        assert "path" in data


# ---------------------------------------------------------------------------
# TestNextStepEdgeCases
# ---------------------------------------------------------------------------

class TestNextStepEdgeCases:
    def test_empty_roadmap_no_steps(self, tmp_path):
        """Roadmap with a header but no step sections — should return done."""
        roadmap_path = tmp_path / "Roadmap.md"
        roadmap_path.write_text(
            "# Feature Roadmap: EmptyFeature\n\n"
            "## Implementation Steps\n\nNo steps here.\n"
        )
        result = subprocess.run(
            [sys.executable, str(COORDINATOR), "next-step", str(roadmap_path)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["action"] == "done"

    def test_all_manual_steps(self, tmp_path):
        """All steps are Manual — should return done with all in manual_skipped."""
        roadmap_path = tmp_path / "Roadmap.md"
        roadmap_path.write_text(
            "# Feature Roadmap: ManualFeature\n\n"
            "### Step 1: Manual task one\n\n"
            "- **Type**: Manual\n- **Status**: Not Started\n\n"
            "### Step 2: Manual task two\n\n"
            "- **Type**: Manual\n- **Status**: Not Started\n"
        )
        result = subprocess.run(
            [sys.executable, str(COORDINATOR), "next-step", str(roadmap_path)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["action"] == "done"
        assert len(data["manual_skipped"]) == 2

    def test_step_with_dependencies_field(self, tmp_path):
        """parse_step_fields should extract a Dependencies field from a step block."""
        roadmap_path = tmp_path / "Roadmap.md"
        roadmap_path.write_text(
            "# Feature Roadmap: DepsFeature\n\n"
            "### Step 1: Step with deps\n\n"
            "- **Type**: Auto\n"
            "- **Status**: Not Started\n"
            "- **Dependencies**: Step 0\n"
        )
        steps = coord.list_all_steps(roadmap_path)
        assert len(steps) == 1
        # parse_step_fields is called internally; verify it extracted correctly
        content = roadmap_path.read_text()
        import re as _re
        block_match = _re.search(r"### Step 1:.*?\n(.*)", content, _re.DOTALL)
        block = block_match.group(1) if block_match else ""
        fields = coord.parse_step_fields(block)
        assert fields.get("Dependencies") == "Step 0"

    def test_next_step_invalid_path(self, tmp_path):
        """Nonexistent roadmap file — should return JSON error and nonzero exit."""
        result = subprocess.run(
            [sys.executable, str(COORDINATOR), "next-step", str(tmp_path / "nonexistent.md")],
            capture_output=True, text=True,
        )
        assert result.returncode != 0
        data = json.loads(result.stdout)
        assert "error" in data


# ---------------------------------------------------------------------------
# TestSummaryEdgeCases
# ---------------------------------------------------------------------------

class TestSummaryEdgeCases:
    def test_summary_all_complete(self, tmp_path):
        """All steps Complete — total and complete counts match."""
        roadmap_path = tmp_path / "Roadmap.md"
        roadmap_path.write_text(
            "# Feature Roadmap: DoneFeature\n\n"
            "### Step 1: First\n\n- **Status**: Complete\n- **Type**: Auto\n\n"
            "### Step 2: Second\n\n- **Status**: Complete\n- **Type**: Auto\n"
        )
        result = subprocess.run(
            [sys.executable, str(COORDINATOR), "summary", str(roadmap_path)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["total"] == 2
        assert data["complete"] == 2

    def test_summary_empty_roadmap(self, tmp_path):
        """No steps — total=0, complete=0."""
        roadmap_path = tmp_path / "Roadmap.md"
        roadmap_path.write_text(
            "# Feature Roadmap: EmptyFeature\n\nNo steps here.\n"
        )
        result = subprocess.run(
            [sys.executable, str(COORDINATOR), "summary", str(roadmap_path)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["total"] == 0
        assert data["complete"] == 0

    def test_summary_invalid_path(self, tmp_path):
        """Nonexistent file — should raise and produce an error (nonzero exit or exception)."""
        result = subprocess.run(
            [sys.executable, str(COORDINATOR), "summary", str(tmp_path / "missing.md")],
            capture_output=True, text=True,
        )
        assert result.returncode != 0


# ---------------------------------------------------------------------------
# TestParseStepFieldsEdgeCases
# ---------------------------------------------------------------------------

class TestParseStepFieldsEdgeCases:
    def test_fields_with_colons_in_value(self):
        """Values containing colons should be captured in full."""
        block = "- **PR**: https://github.com/foo/bar\n"
        fields = coord.parse_step_fields(block)
        assert fields["PR"] == "https://github.com/foo/bar"

    def test_fields_with_special_chars(self):
        """Values with hashes, dashes, and quotes are captured verbatim."""
        block = '- **Description**: Fix #123 \u2014 the "big" bug\n'
        fields = coord.parse_step_fields(block)
        assert fields["Description"] == 'Fix #123 \u2014 the "big" bug'

    def test_fields_with_empty_value(self):
        """A field with no value after the colon should map to an empty string."""
        block = "- **PR**: \n"
        fields = coord.parse_step_fields(block)
        assert "PR" in fields
        assert fields["PR"] == ""


# ---------------------------------------------------------------------------
# TestResolveProjectFiltering
# ---------------------------------------------------------------------------

STEP_TEXT = (
    "# Feature Roadmap: {name}\n\n"
    "### Step 1: Do thing\n\n- **Status**: Not Started\n- **Type**: Auto\n"
)


class TestResolveProjectFiltering:
    """Coordinator resolve filters roadmaps by project frontmatter field."""

    def test_filters_out_wrong_project(self, tmp_path):
        """Roadmap with project=other-repo is excluded when running in my-repo."""
        repo = tmp_path / "my-repo"
        _init_git_repo(repo)
        _make_roadmap_dir(repo, "2026-03-25-Feature",
                          STEP_TEXT.format(name="Feature"), project="other-repo")
        result = subprocess.run(
            [sys.executable, str(COORDINATOR), "resolve"],
            capture_output=True, text=True, cwd=str(repo),
        )
        data = json.loads(result.stdout)
        assert "error" in data

    def test_includes_matching_project(self, tmp_path):
        """Roadmap with project=my-repo is included when running in my-repo."""
        repo = tmp_path / "my-repo"
        _init_git_repo(repo)
        _make_roadmap_dir(repo, "2026-03-25-Feature",
                          STEP_TEXT.format(name="Feature"), project="my-repo")
        result = subprocess.run(
            [sys.executable, str(COORDINATOR), "resolve"],
            capture_output=True, text=True, cwd=str(repo),
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["name"] == "Feature"

    def test_includes_roadmap_without_project_field(self, tmp_path):
        """Roadmap with no project field is included (backward compat)."""
        repo = tmp_path / "my-repo"
        _init_git_repo(repo)
        _make_roadmap_dir(repo, "2026-03-25-Legacy",
                          STEP_TEXT.format(name="Legacy"))  # no project
        result = subprocess.run(
            [sys.executable, str(COORDINATOR), "resolve"],
            capture_output=True, text=True, cwd=str(repo),
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["name"] == "Legacy"

    def test_mixed_projects_only_returns_matching(self, tmp_path):
        """Two roadmaps, one matching project, one not — only matching returned."""
        repo = tmp_path / "my-repo"
        _init_git_repo(repo)
        _make_roadmap_dir(repo, "2026-03-25-Mine",
                          STEP_TEXT.format(name="Mine"), project="my-repo")
        _make_roadmap_dir(repo, "2026-03-25-Theirs",
                          STEP_TEXT.format(name="Theirs"), project="other-repo")
        result = subprocess.run(
            [sys.executable, str(COORDINATOR), "resolve"],
            capture_output=True, text=True, cwd=str(repo),
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        # Should return single match, not choose
        assert "path" in data
        assert data["name"] == "Mine"


class TestResolveWorkDir:
    """Coordinator resolve scans ~/.roadmaps/<project>/ for drafts."""

    def test_finds_roadmap_in_workdir(self, tmp_path, monkeypatch):
        """Roadmap in ~/.roadmaps/<project>/ is found by resolve."""
        repo = tmp_path / "my-repo"
        _init_git_repo(repo)
        work_root = tmp_path / "fake-home" / ".roadmaps"
        _make_workdir_roadmap(work_root, "my-repo", "2026-03-25-Draft",
                              STEP_TEXT.format(name="Draft"))
        monkeypatch.setenv("HOME", str(tmp_path / "fake-home"))
        result = subprocess.run(
            [sys.executable, str(COORDINATOR), "resolve"],
            capture_output=True, text=True, cwd=str(repo),
            env={**dict(__import__("os").environ), "HOME": str(tmp_path / "fake-home")},
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["name"] == "Draft"

    def test_workdir_roadmap_filtered_by_project(self, tmp_path):
        """Roadmap in ~/.roadmaps/other-repo/ is NOT found when in my-repo."""
        repo = tmp_path / "my-repo"
        _init_git_repo(repo)
        work_root = tmp_path / "fake-home" / ".roadmaps"
        # Roadmap is under other-repo directory but has project=other-repo
        _make_workdir_roadmap(work_root, "other-repo", "2026-03-25-Wrong",
                              STEP_TEXT.format(name="Wrong"))
        result = subprocess.run(
            [sys.executable, str(COORDINATOR), "resolve"],
            capture_output=True, text=True, cwd=str(repo),
            env={**dict(__import__("os").environ), "HOME": str(tmp_path / "fake-home")},
        )
        data = json.loads(result.stdout)
        assert "error" in data
