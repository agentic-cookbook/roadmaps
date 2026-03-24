"""Tests for draft helper functions in scripts/roadmap_lib.py."""

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
# draft_dir_for
# ---------------------------------------------------------------------------

class TestDraftDirFor:
    def test_returns_path_under_default_base(self):
        result = lib.draft_dir_for("my-project")
        expected = Path.home() / ".roadmaps" / "drafts" / "my-project"
        assert result == expected

    def test_returns_path_under_custom_base(self, tmp_path):
        result = lib.draft_dir_for("my-project", base=tmp_path)
        assert result == tmp_path / "drafts" / "my-project"

    def test_does_not_create_directory(self, tmp_path):
        result = lib.draft_dir_for("phantom", base=tmp_path)
        assert not result.exists()

    def test_project_name_is_last_component(self, tmp_path):
        result = lib.draft_dir_for("some-feature", base=tmp_path)
        assert result.name == "some-feature"

    def test_drafts_is_intermediate_component(self, tmp_path):
        result = lib.draft_dir_for("feat", base=tmp_path)
        assert result.parent.name == "drafts"


# ---------------------------------------------------------------------------
# move_draft_to_repo
# ---------------------------------------------------------------------------

class TestMoveDraftToRepo:
    def _make_draft(self, base, name="2026-03-24-MyFeature"):
        """Create a minimal draft directory with a file inside."""
        draft = base / name
        draft.mkdir(parents=True)
        (draft / "Definition.md").write_text("# Draft\n")
        return draft

    def test_moves_directory_to_roadmaps(self, tmp_path):
        draft = self._make_draft(tmp_path / "drafts")
        repo = tmp_path / "repo"
        repo.mkdir()
        result = lib.move_draft_to_repo(draft, repo)
        assert result == repo / "Roadmaps" / "2026-03-24-MyFeature"
        assert result.is_dir()

    def test_source_no_longer_exists(self, tmp_path):
        draft = self._make_draft(tmp_path / "drafts")
        repo = tmp_path / "repo"
        repo.mkdir()
        lib.move_draft_to_repo(draft, repo)
        assert not draft.exists()

    def test_contents_are_preserved(self, tmp_path):
        draft = self._make_draft(tmp_path / "drafts")
        repo = tmp_path / "repo"
        repo.mkdir()
        result = lib.move_draft_to_repo(draft, repo)
        assert (result / "Definition.md").read_text() == "# Draft\n"

    def test_creates_roadmaps_dir_if_missing(self, tmp_path):
        draft = self._make_draft(tmp_path / "drafts")
        repo = tmp_path / "repo"
        repo.mkdir()
        assert not (repo / "Roadmaps").exists()
        lib.move_draft_to_repo(draft, repo)
        assert (repo / "Roadmaps").is_dir()

    def test_raises_if_target_already_exists(self, tmp_path):
        draft = self._make_draft(tmp_path / "drafts")
        repo = tmp_path / "repo"
        repo.mkdir()
        # Pre-create the target
        (repo / "Roadmaps" / "2026-03-24-MyFeature").mkdir(parents=True)
        with pytest.raises(FileExistsError):
            lib.move_draft_to_repo(draft, repo)

    def test_returns_new_path(self, tmp_path):
        draft = self._make_draft(tmp_path / "drafts")
        repo = tmp_path / "repo"
        repo.mkdir()
        result = lib.move_draft_to_repo(draft, repo)
        assert isinstance(result, Path)
        assert result.is_dir()

    def test_dirname_is_preserved(self, tmp_path):
        draft = self._make_draft(tmp_path / "drafts", name="2026-01-15-SpecialFeature")
        repo = tmp_path / "repo"
        repo.mkdir()
        result = lib.move_draft_to_repo(draft, repo)
        assert result.name == "2026-01-15-SpecialFeature"


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
        (rd / "Definition.md").write_text("# Feature Definition: Draft\n\nGoal: test\n")
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
        (rd / "Definition.md").unlink()
        ok, errors = lib.validate_planning_complete(rd, allow_placeholders=True)
        assert ok is False
        assert any("Definition.md" in e for e in errors)
