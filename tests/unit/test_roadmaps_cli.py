"""Tests for scripts/roadmaps.py — cross-repo roadmap CLI tool."""

import importlib
import sys
from pathlib import Path

import pytest

# Ensure the worktree's scripts/ takes precedence
_scripts_dir = str(Path(__file__).resolve().parent.parent.parent / "scripts")
if _scripts_dir not in sys.path[:2]:
    sys.path.insert(0, _scripts_dir)
if "roadmaps" in sys.modules:
    importlib.reload(sys.modules["roadmaps"])

import roadmaps
import roadmap_lib as lib


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_roadmap_dir(projects_dir, repo_name, date_name, steps_text,
                      state="Ready", frontmatter=""):
    """Create a per-directory roadmap in projects/<repo>/Roadmaps/<date_name>/."""
    rd = projects_dir / repo_name / "Roadmaps" / date_name
    rd.mkdir(parents=True)
    (rd / "State").mkdir()
    (rd / "History").mkdir()
    (rd / "State" / f"2026-03-25-{state}.md").write_text(
        f"---\nevent: {state.lower()}\ndate: 2026-03-25\n---\n"
    )
    content = frontmatter + steps_text if frontmatter else steps_text
    (rd / "Roadmap.md").write_text(content)
    return rd


def _make_flat_roadmap(projects_dir, repo_name, feature_name, steps_text,
                       frontmatter=""):
    """Create a flat <Name>-Roadmap.md file in projects/<repo>/Roadmaps/."""
    roadmaps_dir = projects_dir / repo_name / "Roadmaps"
    roadmaps_dir.mkdir(parents=True, exist_ok=True)
    content = frontmatter + steps_text if frontmatter else steps_text
    path = roadmaps_dir / f"{feature_name}-Roadmap.md"
    path.write_text(content)
    return path


def _make_workdir_roadmap(workdir_root, project_name, date_name, steps_text,
                          state="Ready"):
    """Create a roadmap in ~/.roadmaps/<project>/<date_name>/."""
    rd = workdir_root / project_name / date_name
    rd.mkdir(parents=True)
    (rd / "State").mkdir()
    (rd / "History").mkdir()
    (rd / "State" / f"2026-03-25-{state}.md").write_text(
        f"---\nevent: {state.lower()}\ndate: 2026-03-25\n---\n"
    )
    (rd / "Roadmap.md").write_text(steps_text)
    return rd


STEPS_3 = (
    "# Feature Roadmap: TestFeature\n\n"
    "### Step 1: First\n\n- **Status**: Complete\n- **Type**: Auto\n\n"
    "### Step 2: Second\n\n- **Status**: Not Started\n- **Type**: Auto\n\n"
    "### Step 3: Third\n\n- **Status**: Not Started\n- **Type**: Auto\n"
)


# ---------------------------------------------------------------------------
# find_all_roadmaps — per-directory layout
# ---------------------------------------------------------------------------

class TestFindAllRoadmaps:
    def test_finds_roadmap_in_repo(self, tmp_path):
        _make_roadmap_dir(tmp_path, "my-repo", "2026-03-25-Feature", STEPS_3)
        results = roadmaps.find_all_roadmaps(tmp_path)
        assert len(results) == 1
        assert results[0]["name"] == "Feature"
        assert results[0]["repo"] == "my-repo"
        assert results[0]["total"] == 3
        assert results[0]["complete"] == 1

    def test_finds_multiple_repos(self, tmp_path):
        _make_roadmap_dir(tmp_path, "repo-a", "2026-03-25-Alpha", STEPS_3)
        _make_roadmap_dir(tmp_path, "repo-b", "2026-03-25-Beta", STEPS_3)
        results = roadmaps.find_all_roadmaps(tmp_path)
        assert len(results) == 2
        repos = {r["repo"] for r in results}
        assert repos == {"repo-a", "repo-b"}

    def test_state_is_read_correctly(self, tmp_path):
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-Done", STEPS_3, state="Complete")
        results = roadmaps.find_all_roadmaps(tmp_path)
        assert results[0]["state"] == "Complete"
        assert results[0]["is_complete"] is True

    def test_archived_state(self, tmp_path):
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-Old", STEPS_3, state="Archived")
        results = roadmaps.find_all_roadmaps(tmp_path)
        assert results[0]["is_archived"] is True

    def test_implementing_state(self, tmp_path):
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-WIP", STEPS_3, state="Implementing")
        results = roadmaps.find_all_roadmaps(tmp_path)
        assert results[0]["is_running"] is True

    def test_empty_projects_dir(self, tmp_path):
        results = roadmaps.find_all_roadmaps(tmp_path)
        assert results == []

    def test_nonexistent_dir(self, tmp_path):
        results = roadmaps.find_all_roadmaps(tmp_path / "nope")
        assert results == []


# ---------------------------------------------------------------------------
# find_all_roadmaps — flat file layout
# ---------------------------------------------------------------------------

class TestFindAllRoadmapsFlatFiles:
    def test_finds_flat_roadmap_files(self, tmp_path):
        _make_flat_roadmap(tmp_path, "repo", "MyFeature", STEPS_3)
        results = roadmaps.find_all_roadmaps(tmp_path)
        assert len(results) == 1
        assert results[0]["name"] == "TestFeature"  # from heading
        assert results[0]["repo"] == "repo"

    def test_finds_both_dir_and_flat(self, tmp_path):
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-DirFeature", STEPS_3)
        _make_flat_roadmap(tmp_path, "repo", "FlatFeature", STEPS_3)
        results = roadmaps.find_all_roadmaps(tmp_path)
        assert len(results) == 2


# ---------------------------------------------------------------------------
# find_all_roadmaps — workdir (~/.roadmaps/) scanning
# ---------------------------------------------------------------------------

class TestFindAllRoadmapsWorkdir:
    def test_finds_workdir_roadmaps(self, tmp_path):
        workdir = tmp_path / "fake-home" / ".roadmaps"
        _make_workdir_roadmap(workdir, "my-repo", "2026-03-25-Draft", STEPS_3)
        # Also need the repo dir to exist (even empty) for the scan
        (tmp_path / "my-repo").mkdir()
        results = roadmaps.find_all_roadmaps(tmp_path, workdir_root=workdir)
        assert len(results) == 1
        assert results[0]["name"] == "Draft"
        assert results[0]["repo"] == "my-repo"
        assert "workdir" in results[0].get("source", "workdir")


# ---------------------------------------------------------------------------
# cmd_list — filtering
# ---------------------------------------------------------------------------

class TestCmdListFiltering:
    def test_default_shows_running_and_active(self, tmp_path, capsys):
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-Active", STEPS_3, state="Ready")
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-Done", STEPS_3, state="Complete")
        roadmaps.cmd_list(tmp_path, show_running=True, show_active=True,
                          show_complete=False, show_archived=False)
        out = capsys.readouterr().out
        assert "Active" in out
        assert "Done" not in out

    def test_all_flag_shows_everything(self, tmp_path, capsys):
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-Active", STEPS_3, state="Ready")
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-Done", STEPS_3, state="Complete")
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-Old", STEPS_3, state="Archived")
        roadmaps.cmd_list(tmp_path, show_running=True, show_active=True,
                          show_complete=True, show_archived=True)
        out = capsys.readouterr().out
        assert "Active" in out
        assert "Done" in out
        assert "Old" in out

    def test_search_filter(self, tmp_path, capsys):
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-AuthFeature", STEPS_3)
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-UIFeature", STEPS_3)
        roadmaps.cmd_list(tmp_path, search="auth")
        out = capsys.readouterr().out
        assert "Auth" in out
        assert "UI" not in out

    def test_project_filter(self, tmp_path, capsys):
        _make_roadmap_dir(tmp_path, "repo-a", "2026-03-25-Alpha", STEPS_3)
        _make_roadmap_dir(tmp_path, "repo-b", "2026-03-25-Beta", STEPS_3)
        roadmaps.cmd_list(tmp_path, project="repo-a")
        out = capsys.readouterr().out
        assert "Alpha" in out
        assert "Beta" not in out

    def test_no_matches(self, tmp_path, capsys):
        roadmaps.cmd_list(tmp_path)
        out = capsys.readouterr().out
        assert "No roadmaps" in out


# ---------------------------------------------------------------------------
# progress_bar
# ---------------------------------------------------------------------------

class TestProgressBar:
    def test_zero_progress(self):
        bar = roadmaps.progress_bar(0, 5)
        assert "\u2588" not in bar

    def test_full_progress(self):
        bar = roadmaps.progress_bar(5, 5)
        assert "\u2591" not in bar

    def test_partial_progress(self):
        bar = roadmaps.progress_bar(2, 4)
        assert "\u2588" in bar
        assert "\u2591" in bar

    def test_zero_total(self):
        bar = roadmaps.progress_bar(0, 0)
        assert len(bar) == 16


# ---------------------------------------------------------------------------
# detect_project
# ---------------------------------------------------------------------------

class TestDetectProject:
    def test_returns_none_outside_projects(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert roadmaps.detect_project(str(tmp_path / "projects")) is None

    def test_detects_project_from_cwd(self, tmp_path, monkeypatch):
        project_dir = tmp_path / "projects" / "my-repo"
        project_dir.mkdir(parents=True)
        monkeypatch.chdir(project_dir)
        assert roadmaps.detect_project(str(tmp_path / "projects")) == "my-repo"

    def test_detects_from_subdirectory(self, tmp_path, monkeypatch):
        subdir = tmp_path / "projects" / "my-repo" / "src" / "lib"
        subdir.mkdir(parents=True)
        monkeypatch.chdir(subdir)
        assert roadmaps.detect_project(str(tmp_path / "projects")) == "my-repo"
