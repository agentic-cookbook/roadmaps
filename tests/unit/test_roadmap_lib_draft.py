"""Tests for roadmap working directory functions in scripts/roadmap_lib.py."""

import importlib
import sys
from pathlib import Path

import pytest

# Ensure the worktree's scripts/ takes precedence over installed versions.
_scripts_dir = str(Path(__file__).resolve().parent.parent.parent / "scripts")
if _scripts_dir not in sys.path[:2]:
    sys.path.insert(0, _scripts_dir)
if "roadmap_lib" in sys.modules:
    importlib.reload(sys.modules["roadmap_lib"])

import roadmap_lib as lib


# ---------------------------------------------------------------------------
# roadmap_work_dir
# ---------------------------------------------------------------------------

class TestRoadmapWorkDir:
    def test_returns_path_under_default_base(self):
        result = lib.roadmap_work_dir("my-project")
        expected = Path.home() / ".roadmaps" / "my-project"
        assert result == expected

    def test_returns_path_under_custom_base(self, tmp_path):
        result = lib.roadmap_work_dir("my-project", base=tmp_path)
        assert result == tmp_path / "my-project"

    def test_does_not_create_directory(self, tmp_path):
        result = lib.roadmap_work_dir("phantom", base=tmp_path)
        assert not result.exists()

    def test_project_name_is_last_component(self, tmp_path):
        result = lib.roadmap_work_dir("some-feature", base=tmp_path)
        assert result.name == "some-feature"

    def test_no_drafts_intermediate_dir(self, tmp_path):
        result = lib.roadmap_work_dir("feat", base=tmp_path)
        assert result.parent == tmp_path


# ---------------------------------------------------------------------------
# copy_roadmap_to_branch
# ---------------------------------------------------------------------------

class TestCopyRoadmapToBranch:
    def _make_roadmap(self, base, name="2026-03-24-MyFeature"):
        """Create a minimal roadmap directory with files."""
        rd = base / name
        rd.mkdir(parents=True)
        (rd / "Roadmap.md").write_text("# Roadmap\n")
        (rd / "State").mkdir()
        (rd / "State" / "2026-03-24-Ready.md").write_text("ready\n")
        return rd

    def test_copies_to_target(self, tmp_path):
        rd = self._make_roadmap(tmp_path / "work")
        target = tmp_path / "worktree" / "Roadmaps"
        target.mkdir(parents=True)
        result = lib.copy_roadmap_to_branch(rd, target)
        assert result == target / "2026-03-24-MyFeature"
        assert result.is_dir()

    def test_source_still_exists(self, tmp_path):
        rd = self._make_roadmap(tmp_path / "work")
        target = tmp_path / "worktree" / "Roadmaps"
        target.mkdir(parents=True)
        lib.copy_roadmap_to_branch(rd, target)
        assert rd.exists()  # copy, not move

    def test_contents_are_preserved(self, tmp_path):
        rd = self._make_roadmap(tmp_path / "work")
        target = tmp_path / "worktree" / "Roadmaps"
        target.mkdir(parents=True)
        result = lib.copy_roadmap_to_branch(rd, target)
        assert (result / "Roadmap.md").read_text() == "# Roadmap\n"
        assert (result / "State" / "2026-03-24-Ready.md").exists()

    def test_creates_parent_dirs(self, tmp_path):
        rd = self._make_roadmap(tmp_path / "work")
        target = tmp_path / "worktree" / "Roadmaps"
        assert not target.exists()
        lib.copy_roadmap_to_branch(rd, target)
        assert target.is_dir()

    def test_raises_if_target_exists(self, tmp_path):
        rd = self._make_roadmap(tmp_path / "work")
        target = tmp_path / "worktree" / "Roadmaps"
        (target / "2026-03-24-MyFeature").mkdir(parents=True)
        with pytest.raises(FileExistsError):
            lib.copy_roadmap_to_branch(rd, target)

    def test_dirname_preserved(self, tmp_path):
        rd = self._make_roadmap(tmp_path / "work", name="2026-01-01-Special")
        target = tmp_path / "worktree" / "Roadmaps"
        target.mkdir(parents=True)
        result = lib.copy_roadmap_to_branch(rd, target)
        assert result.name == "2026-01-01-Special"


# ---------------------------------------------------------------------------
# cleanup_roadmap
# ---------------------------------------------------------------------------

class TestCleanupRoadmap:
    def test_removes_directory(self, tmp_path):
        rd = tmp_path / "2026-03-24-Feature"
        rd.mkdir()
        (rd / "Roadmap.md").write_text("# test\n")
        assert lib.cleanup_roadmap(rd) is True
        assert not rd.exists()

    def test_returns_false_if_not_exists(self, tmp_path):
        rd = tmp_path / "nonexistent"
        assert lib.cleanup_roadmap(rd) is False

    def test_removes_nested_contents(self, tmp_path):
        rd = tmp_path / "2026-03-24-Feature"
        rd.mkdir()
        (rd / "State").mkdir()
        (rd / "State" / "file.md").write_text("x")
        (rd / "History").mkdir()
        lib.cleanup_roadmap(rd)
        assert not rd.exists()


# ---------------------------------------------------------------------------
# validate_planning_complete — allow_placeholders
# ---------------------------------------------------------------------------

class TestValidatePlanningCompleteAllowPlaceholders:
    def _make_dir_with_placeholders(self, tmp_path):
        """Create a planning directory that has placeholder issue refs."""
        rd = tmp_path / "2026-03-24-Draft"
        rd.mkdir()
        (rd / "State").mkdir()
        (rd / "History").mkdir()
        (rd / "Roadmap.md").write_text(
            "# Feature Roadmap: Draft\n\n"
            "### Step 1: First\n\n"
            "- **GitHub Issue**: {{REPO}}#{{ISSUE_NUMBER}}\n"
            "- **Status**: Not Started\n"
        )
        (rd / "State" / "2026-03-24-Created.md").write_text("---\nevent: created\ndate: 2026-03-24\n---\n")
        (rd / "State" / "2026-03-24-Planning.md").write_text("---\nevent: planning\ndate: 2026-03-24\n---\n")
        (rd / "State" / "2026-03-24-Ready.md").write_text("---\nevent: ready\ndate: 2026-03-24\n---\n")
        return rd

    def test_default_rejects_placeholders(self, tmp_path):
        rd = self._make_dir_with_placeholders(tmp_path)
        ok, errors = lib.validate_planning_complete(rd)
        assert ok is False
        assert any("placeholder" in e.lower() for e in errors)

    def test_allow_placeholders_skips_check(self, tmp_path):
        rd = self._make_dir_with_placeholders(tmp_path)
        ok, errors = lib.validate_planning_complete(rd, allow_placeholders=True)
        assert ok is True
        assert errors == []

    def test_allow_placeholders_false_still_rejects(self, tmp_path):
        rd = self._make_dir_with_placeholders(tmp_path)
        ok, errors = lib.validate_planning_complete(rd, allow_placeholders=False)
        assert ok is False
        assert any("placeholder" in e.lower() for e in errors)

    def test_allow_placeholders_does_not_skip_other_errors(self, tmp_path):
        rd = self._make_dir_with_placeholders(tmp_path)
        (rd / "Roadmap.md").unlink()
        ok, errors = lib.validate_planning_complete(rd, allow_placeholders=True)
        assert ok is False
        assert any("Roadmap.md" in e for e in errors)


# ---------------------------------------------------------------------------
# find_roadmap_files (flat *-Roadmap.md files)
# ---------------------------------------------------------------------------

class TestFindRoadmapFiles:
    def test_finds_flat_roadmap_files(self, tmp_path):
        roadmaps = tmp_path / "Roadmaps"
        roadmaps.mkdir()
        (roadmaps / "MyFeature-Roadmap.md").write_text("# Roadmap\n")
        (roadmaps / "Other-Roadmap.md").write_text("# Roadmap\n")
        result = lib.find_roadmap_files(tmp_path)
        assert len(result) == 2
        names = [f.name for f in result]
        assert "MyFeature-Roadmap.md" in names
        assert "Other-Roadmap.md" in names

    def test_ignores_non_roadmap_files(self, tmp_path):
        roadmaps = tmp_path / "Roadmaps"
        roadmaps.mkdir()
        (roadmaps / "MyFeature-Roadmap.md").write_text("# Roadmap\n")
        (roadmaps / "README.md").write_text("# Readme\n")
        (roadmaps / "notes.txt").write_text("notes\n")
        result = lib.find_roadmap_files(tmp_path)
        assert len(result) == 1
        assert result[0].name == "MyFeature-Roadmap.md"

    def test_empty_when_no_roadmaps_dir(self, tmp_path):
        assert lib.find_roadmap_files(tmp_path) == []

    def test_empty_when_no_matching_files(self, tmp_path):
        roadmaps = tmp_path / "Roadmaps"
        roadmaps.mkdir()
        (roadmaps / "README.md").write_text("# Readme\n")
        assert lib.find_roadmap_files(tmp_path) == []


# ---------------------------------------------------------------------------
# copy_roadmap_file (single file copy with rename)
# ---------------------------------------------------------------------------

class TestCopyRoadmapFile:
    def _make_roadmap(self, base):
        rd = base / "2026-03-25-Feature"
        rd.mkdir(parents=True)
        (rd / "Roadmap.md").write_text("# Feature Roadmap: Feature\n")
        (rd / "State").mkdir()
        (rd / "History").mkdir()
        return rd

    def test_copies_as_renamed_file(self, tmp_path):
        rd = self._make_roadmap(tmp_path / "work")
        target = tmp_path / "repo" / "Roadmaps"
        result = lib.copy_roadmap_file(rd, target, "Feature")
        assert result == target / "Feature-Roadmap.md"
        assert result.exists()
        assert "Feature Roadmap" in result.read_text()

    def test_only_copies_roadmap_not_state(self, tmp_path):
        rd = self._make_roadmap(tmp_path / "work")
        target = tmp_path / "repo" / "Roadmaps"
        lib.copy_roadmap_file(rd, target, "Feature")
        # Only the single file, no subdirectories
        contents = list(target.iterdir())
        assert len(contents) == 1
        assert contents[0].name == "Feature-Roadmap.md"

    def test_creates_parent_dirs(self, tmp_path):
        rd = self._make_roadmap(tmp_path / "work")
        target = tmp_path / "repo" / "Roadmaps"
        assert not target.exists()
        lib.copy_roadmap_file(rd, target, "Feature")
        assert target.is_dir()

    def test_raises_if_target_exists(self, tmp_path):
        rd = self._make_roadmap(tmp_path / "work")
        target = tmp_path / "repo" / "Roadmaps"
        target.mkdir(parents=True)
        (target / "Feature-Roadmap.md").write_text("existing\n")
        with pytest.raises(FileExistsError):
            lib.copy_roadmap_file(rd, target, "Feature")

    def test_raises_if_source_missing(self, tmp_path):
        rd = tmp_path / "empty"
        rd.mkdir()
        target = tmp_path / "repo" / "Roadmaps"
        with pytest.raises(FileNotFoundError):
            lib.copy_roadmap_file(rd, target, "Feature")
