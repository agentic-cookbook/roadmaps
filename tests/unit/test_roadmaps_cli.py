"""Tests for scripts/roadmaps.py — cross-repo roadmap CLI tool."""

import importlib
import json
import os
import sys
import time
from pathlib import Path
from unittest import mock

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

    def test_flat_file_wins_over_implementing_directory_with_same_id(self, tmp_path):
        """Regression: completed flat file must win over stale directory with Implementing state.

        Bug: WindowsDesktopParity showed as 'running' because the directory
        (with Implementing state) was scanned before the flat file (completed).
        Both had the same ID but the directory won the dedup race.
        """
        fm = '---\nid: same-uuid\n---\n\n'
        # Flat file (completed) — should win
        _make_flat_roadmap(tmp_path, "repo", "Feature", STEPS_3, frontmatter=fm)
        # Directory with Implementing state (stale) — should be skipped
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-Feature", STEPS_3,
                          state="Implementing", frontmatter=fm)
        results = roadmaps.find_all_roadmaps(tmp_path)
        # Should only have ONE entry (flat file wins)
        assert len(results) == 1
        assert results[0]["source"] == "repo-flat"
        assert results[0]["is_running"] is False
        assert results[0]["is_complete"] is True


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


# ---------------------------------------------------------------------------
# Steps with more detail (used by --show tests)
# ---------------------------------------------------------------------------

STEPS_DETAILED = (
    "# Feature Roadmap: DetailedFeature\n\n"
    "### Step 1: Setup project\n\n"
    "- **Status**: Complete\n- **Type**: Auto\n- **Complexity**: Low\n\n"
    "### Step 2: Build core\n\n"
    "- **Status**: Not Started\n- **Type**: Manual\n- **Complexity**: High\n\n"
    "### Step 3: Write tests\n\n"
    "- **Status**: Not Started\n- **Type**: Auto\n- **Complexity**: Medium\n"
)

FRONTMATTER_WITH_PR = (
    "---\nid: test-uuid-123\nchange-history:\n"
    "  - pr: https://github.com/org/repo/pull/42\n---\n"
)


# ---------------------------------------------------------------------------
# cmd_show
# ---------------------------------------------------------------------------

class TestCmdShow:
    def test_show_displays_detail(self, tmp_path, capsys):
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-DetailedFeature",
                          STEPS_DETAILED)
        roadmaps.cmd_show(tmp_path, "Detailed")
        out = capsys.readouterr().out
        assert "DetailedFeature" in out
        assert "repo" in out
        assert "Step 1" in out
        assert "Setup project" in out
        assert "Step 2" in out
        assert "Build core" in out
        assert "1/3" in out

    def test_show_not_found(self, tmp_path, capsys):
        roadmaps.cmd_show(tmp_path, "NonExistent")
        out = capsys.readouterr().out
        assert "No roadmap found" in out

    def test_show_multiple_matches(self, tmp_path, capsys):
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-FeatureAlpha",
                          STEPS_3)
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-FeatureBeta",
                          STEPS_3)
        roadmaps.cmd_show(tmp_path, "Feature")
        out = capsys.readouterr().out
        assert "Multiple roadmaps match" in out

    def test_show_pr_link_from_frontmatter(self, tmp_path, capsys):
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-PRFeature",
                          STEPS_DETAILED, frontmatter=FRONTMATTER_WITH_PR)
        roadmaps.cmd_show(tmp_path, "PRFeature")
        out = capsys.readouterr().out
        assert "pull/42" in out

    def test_show_source_field(self, tmp_path, capsys):
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-SourceTest",
                          STEPS_3)
        roadmaps.cmd_show(tmp_path, "SourceTest")
        out = capsys.readouterr().out
        assert "Source:" in out
        assert "repo" in out


# ---------------------------------------------------------------------------
# cmd_logs
# ---------------------------------------------------------------------------

class TestCmdLogs:
    def test_logs_shows_log_contents(self, tmp_path, capsys):
        rd = _make_roadmap_dir(tmp_path, "repo", "2026-03-25-LogFeature",
                               STEPS_3)
        (rd / "planning.log").write_text("Planning started at 10:00\nStep 1 done\n")
        (rd / "implementation.log").write_text("Building step 1\n")
        roadmaps.cmd_logs(tmp_path, "LogFeature")
        out = capsys.readouterr().out
        assert "planning.log" in out
        assert "Planning started at 10:00" in out
        assert "implementation.log" in out
        assert "Building step 1" in out

    def test_logs_no_log_files(self, tmp_path, capsys):
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-NoLogs", STEPS_3)
        roadmaps.cmd_logs(tmp_path, "NoLogs")
        out = capsys.readouterr().out
        assert "No log files" in out

    def test_logs_not_found(self, tmp_path, capsys):
        roadmaps.cmd_logs(tmp_path, "Nonexistent")
        out = capsys.readouterr().out
        assert "No roadmap found" in out

    def test_logs_flat_layout_no_dir(self, tmp_path, capsys):
        _make_flat_roadmap(tmp_path, "repo", "FlatOnly", STEPS_3)
        roadmaps.cmd_logs(tmp_path, "TestFeature")  # heading name
        out = capsys.readouterr().out
        assert "No roadmap directory" in out or "flat layout" in out


# ---------------------------------------------------------------------------
# cmd_cancel
# ---------------------------------------------------------------------------

class TestCmdCancel:
    def test_cancel_removes_implementing_state(self, tmp_path, capsys):
        rd = _make_roadmap_dir(tmp_path, "repo", "2026-03-25-StuckFeature",
                               STEPS_3, state="Implementing")
        # Verify implementing state file exists
        state_files = list((rd / "State").glob("*-Implementing.md"))
        assert len(state_files) == 1

        # Mock subprocess calls so git/gh don't actually run
        with mock.patch("roadmaps.subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=1)  # all fail (not found)
            roadmaps.cmd_cancel(tmp_path, "StuckFeature",
                                confirm_fn=lambda _: True)

        out = capsys.readouterr().out
        assert "Removed state file" in out

        # Verify state file was removed
        state_files = list((rd / "State").glob("*-Implementing.md"))
        assert len(state_files) == 0

    def test_cancel_declined(self, tmp_path, capsys):
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-CancelMe",
                          STEPS_3, state="Implementing")
        roadmaps.cmd_cancel(tmp_path, "CancelMe",
                            confirm_fn=lambda _: False)
        out = capsys.readouterr().out
        assert "Cancelled" in out

    def test_cancel_not_found(self, tmp_path, capsys):
        roadmaps.cmd_cancel(tmp_path, "Ghost",
                            confirm_fn=lambda _: True)
        out = capsys.readouterr().out
        assert "No roadmap found" in out

    def test_cancel_calls_git_worktree_and_branch(self, tmp_path, capsys):
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-GitCleanup",
                          STEPS_3, state="Implementing")

        calls = []
        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            return mock.Mock(returncode=0)

        with mock.patch("roadmaps.subprocess.run", side_effect=fake_run):
            roadmaps.cmd_cancel(tmp_path, "GitCleanup",
                                confirm_fn=lambda _: True)

        out = capsys.readouterr().out
        # Should have called git worktree remove, git branch -D, git push --delete, gh pr close
        cmd_strs = [" ".join(c) for c in calls]
        assert any("worktree" in s for s in cmd_strs)
        assert any("branch -D" in s for s in cmd_strs)
        assert any("push origin --delete" in s for s in cmd_strs)
        assert any("gh pr close" in s for s in cmd_strs)
        assert "Removed worktree" in out
        assert "Deleted local branch" in out


# ---------------------------------------------------------------------------
# cmd_json_list (--json)
# ---------------------------------------------------------------------------

class TestCmdJsonList:
    def test_json_output_is_valid(self, tmp_path, capsys):
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-JsonTest", STEPS_3)
        roadmaps.cmd_json_list(tmp_path)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == "JsonTest"

    def test_json_output_empty_list(self, tmp_path, capsys):
        roadmaps.cmd_json_list(tmp_path)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data == []

    def test_json_with_search_filter(self, tmp_path, capsys):
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-Alpha", STEPS_3)
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-Beta", STEPS_3)
        roadmaps.cmd_json_list(tmp_path, search="alpha")
        out = capsys.readouterr().out
        data = json.loads(out)
        assert len(data) == 1
        assert data[0]["name"] == "Alpha"

    def test_json_respects_filters(self, tmp_path, capsys):
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-Active", STEPS_3, state="Ready")
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-Done", STEPS_3, state="Complete")
        # Default: show_running + show_active only
        roadmaps.cmd_json_list(tmp_path, show_running=True, show_active=True,
                               show_complete=False, show_archived=False)
        out = capsys.readouterr().out
        data = json.loads(out)
        names = [r["name"] for r in data]
        assert "Active" in names
        assert "Done" not in names

    def test_json_fields_present(self, tmp_path, capsys):
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-FieldCheck", STEPS_3)
        roadmaps.cmd_json_list(tmp_path)
        out = capsys.readouterr().out
        data = json.loads(out)
        entry = data[0]
        for key in ("name", "repo", "path", "state", "total", "complete",
                     "is_running", "is_active", "is_complete", "is_archived", "source"):
            assert key in entry, f"Missing key: {key}"


# ---------------------------------------------------------------------------
# cmd_stale
# ---------------------------------------------------------------------------

class TestCmdStale:
    def test_stale_finds_old_implementing(self, tmp_path, capsys):
        rd = _make_roadmap_dir(tmp_path, "repo", "2026-03-25-OldImpl",
                               STEPS_3, state="Implementing")
        # Set the state file mtime to 48 hours ago
        state_file = list((rd / "State").glob("*-Implementing.md"))[0]
        old_time = time.time() - (48 * 3600)
        os.utime(state_file, (old_time, old_time))

        roadmaps.cmd_stale(tmp_path, hours=24)
        out = capsys.readouterr().out
        assert "OldImpl" in out
        assert "1 stale" in out

    def test_stale_skips_recent_implementing(self, tmp_path, capsys):
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-FreshImpl",
                          STEPS_3, state="Implementing")
        # State file was just created — it's recent
        roadmaps.cmd_stale(tmp_path, hours=24)
        out = capsys.readouterr().out
        assert "No stale roadmaps" in out

    def test_stale_skips_non_implementing(self, tmp_path, capsys):
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-ReadyOne",
                          STEPS_3, state="Ready")
        roadmaps.cmd_stale(tmp_path, hours=1)
        out = capsys.readouterr().out
        assert "No stale roadmaps" in out

    def test_stale_custom_hours(self, tmp_path, capsys):
        rd = _make_roadmap_dir(tmp_path, "repo", "2026-03-25-HourTest",
                               STEPS_3, state="Implementing")
        state_file = list((rd / "State").glob("*-Implementing.md"))[0]
        # Set to 3 hours ago
        old_time = time.time() - (3 * 3600)
        os.utime(state_file, (old_time, old_time))

        # 24h threshold — should not be stale
        roadmaps.cmd_stale(tmp_path, hours=24)
        out = capsys.readouterr().out
        assert "No stale roadmaps" in out

        # 2h threshold — should be stale
        roadmaps.cmd_stale(tmp_path, hours=2)
        out = capsys.readouterr().out
        assert "HourTest" in out


# ---------------------------------------------------------------------------
# cmd_dashboard_status
# ---------------------------------------------------------------------------

class TestCmdDashboardStatus:
    def test_dashboard_not_running(self, tmp_path, capsys, monkeypatch):
        monkeypatch.setenv("DASHBOARD_URL", "http://localhost:19999")
        roadmaps.cmd_dashboard_status()
        out = capsys.readouterr().out
        assert "not running" in out

    def test_dashboard_running(self, capsys, monkeypatch):
        monkeypatch.setenv("DASHBOARD_URL", "http://localhost:19999")

        health_resp = json.dumps({"status": "ok"}).encode()
        roadmaps_resp = json.dumps([
            {"name": "Feature1", "state": "Implementing", "status": "running"},
        ]).encode()

        call_count = [0]
        def fake_urlopen(req, timeout=None):
            resp = mock.Mock()
            if call_count[0] == 0:
                resp.read.return_value = health_resp
            else:
                resp.read.return_value = roadmaps_resp
            call_count[0] += 1
            return resp

        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
            roadmaps.cmd_dashboard_status()

        out = capsys.readouterr().out
        assert "running" in out
        assert "Roadmaps: 1" in out
        assert "Feature1" in out

    def test_dashboard_shows_url(self, capsys, monkeypatch):
        monkeypatch.setenv("DASHBOARD_URL", "http://my-server:9000")
        roadmaps.cmd_dashboard_status()
        out = capsys.readouterr().out
        assert "http://my-server:9000" in out


# ---------------------------------------------------------------------------
# cmd_dashboard_sync
# ---------------------------------------------------------------------------

class TestCmdDashboardSync:
    def test_sync_no_active_roadmaps(self, tmp_path, capsys):
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-Done",
                          STEPS_3, state="Complete")
        roadmaps.cmd_dashboard_sync(tmp_path)
        out = capsys.readouterr().out
        assert "No active roadmaps" in out

    def test_sync_skips_no_id(self, tmp_path, capsys, monkeypatch):
        monkeypatch.setenv("DASHBOARD_URL", "http://localhost:19999")
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-NoId", STEPS_3)
        roadmaps.cmd_dashboard_sync(tmp_path)
        out = capsys.readouterr().out
        assert "Skipped" in out
        assert "no ID" in out

    def test_sync_posts_to_dashboard(self, tmp_path, capsys, monkeypatch):
        monkeypatch.setenv("DASHBOARD_URL", "http://localhost:19999")
        fm = "---\nid: sync-uuid-1\n---\n"
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-SyncMe",
                          STEPS_3, frontmatter=fm)

        with mock.patch("roadmaps._dashboard_request") as mock_req:
            mock_req.return_value = ({"ok": True}, None)
            roadmaps.cmd_dashboard_sync(tmp_path)

        out = capsys.readouterr().out
        assert "SyncMe" in out
        assert "Synced 1" in out
        mock_req.assert_called_once()
        call_args = mock_req.call_args
        assert call_args[0][0] == "POST"
        assert "sync-uuid-1" in call_args[0][1]

    def test_sync_reports_errors(self, tmp_path, capsys, monkeypatch):
        monkeypatch.setenv("DASHBOARD_URL", "http://localhost:19999")
        fm = "---\nid: err-uuid-1\n---\n"
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-ErrSync",
                          STEPS_3, frontmatter=fm)

        with mock.patch("roadmaps._dashboard_request") as mock_req:
            mock_req.return_value = (None, "connection refused")
            roadmaps.cmd_dashboard_sync(tmp_path)

        out = capsys.readouterr().out
        assert "Error" in out
        assert "connection refused" in out


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

class TestFindRoadmapByName:
    def test_finds_by_substring(self, tmp_path):
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-AuthFeature", STEPS_3)
        result, err = roadmaps._find_roadmap_by_name(tmp_path, "Auth")
        assert err is None
        assert result["name"] == "AuthFeature"

    def test_case_insensitive(self, tmp_path):
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-AuthFeature", STEPS_3)
        result, err = roadmaps._find_roadmap_by_name(tmp_path, "auth")
        assert err is None
        assert result["name"] == "AuthFeature"

    def test_not_found(self, tmp_path):
        result, err = roadmaps._find_roadmap_by_name(tmp_path, "Nope")
        assert result is None
        assert "No roadmap found" in err

    def test_multiple_matches(self, tmp_path):
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-FeatureA", STEPS_3)
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-FeatureB", STEPS_3)
        result, err = roadmaps._find_roadmap_by_name(tmp_path, "Feature")
        assert result is None
        assert "Multiple" in err


class TestParseStepsDetail:
    def test_parses_steps(self, tmp_path):
        rd = _make_roadmap_dir(tmp_path, "repo", "2026-03-25-Detail",
                               STEPS_DETAILED)
        steps = roadmaps._parse_steps_detail(rd / "Roadmap.md")
        assert len(steps) == 3
        assert steps[0]["number"] == 1
        assert steps[0]["title"] == "Setup project"
        assert steps[0]["status"] == "Complete"
        assert steps[0]["type"] == "Auto"
        assert steps[0]["complexity"] == "Low"
        assert steps[1]["status"] == "Not Started"
        assert steps[1]["complexity"] == "High"

    def test_parses_basic_steps(self, tmp_path):
        rd = _make_roadmap_dir(tmp_path, "repo", "2026-03-25-Basic", STEPS_3)
        steps = roadmaps._parse_steps_detail(rd / "Roadmap.md")
        assert len(steps) == 3
        assert steps[0]["status"] == "Complete"
        assert steps[0]["complexity"] == "Unknown"  # not in STEPS_3


class TestExtractPrLink:
    def test_from_frontmatter(self, tmp_path):
        rd = _make_roadmap_dir(tmp_path, "repo", "2026-03-25-PR",
                               STEPS_3, frontmatter=FRONTMATTER_WITH_PR)
        link = roadmaps._extract_pr_link(rd / "Roadmap.md")
        assert link == "https://github.com/org/repo/pull/42"

    def test_from_body(self, tmp_path):
        body_with_pr = STEPS_3 + "\n## Change History\n\nhttps://github.com/org/repo/pull/99\n"
        rd = _make_roadmap_dir(tmp_path, "repo", "2026-03-25-BodyPR", body_with_pr)
        link = roadmaps._extract_pr_link(rd / "Roadmap.md")
        assert link == "https://github.com/org/repo/pull/99"

    def test_no_pr(self, tmp_path):
        rd = _make_roadmap_dir(tmp_path, "repo", "2026-03-25-NoPR", STEPS_3)
        link = roadmaps._extract_pr_link(rd / "Roadmap.md")
        assert link is None


# ---------------------------------------------------------------------------
# cmd_status
# ---------------------------------------------------------------------------

class TestCmdStatus:
    def test_status_shows_all_sections(self, tmp_path, capsys):
        fm = '---\nid: status-uuid\nproject: repo\ngithub-user: testuser\nplan-version: 11\ncreated: 2026-03-25\nmodified: 2026-03-25\n---\n\n'
        rd = _make_roadmap_dir(tmp_path, "repo", "2026-03-25-StatusFeature",
                               STEPS_DETAILED, frontmatter=fm)
        (rd / "planning.log").write_text("log entry\n")

        with mock.patch("roadmaps.subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=1, stdout="", stderr="")
            with mock.patch("roadmaps._dashboard_request") as mock_dash:
                mock_dash.return_value = (None, "not found")
                roadmaps.cmd_status(tmp_path, "StatusFeature")

        out = capsys.readouterr().out
        assert "StatusFeature" in out
        assert "Frontmatter:" in out
        assert "status-uuid" in out
        assert "testuser" in out
        assert "State files:" in out
        assert "Log files:" in out
        assert "planning.log" in out
        assert "Git artifacts:" in out

    def test_status_not_found(self, tmp_path, capsys):
        roadmaps.cmd_status(tmp_path, "Ghost")
        out = capsys.readouterr().out
        assert "No roadmap found" in out

    def test_status_shows_workdir(self, tmp_path, capsys):
        fm = '---\nid: wd-uuid\n---\n\n'
        workdir = tmp_path / "fake-home" / ".roadmaps"
        _make_workdir_roadmap(workdir, "repo", "2026-03-25-WorkdirTest", STEPS_3)
        (tmp_path / "repo").mkdir()

        with mock.patch("roadmaps.subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=1, stdout="", stderr="")
            with mock.patch("roadmaps._dashboard_request") as mock_dash:
                mock_dash.return_value = (None, "not found")
                roadmaps.cmd_status(tmp_path, "WorkdirTest",)

        # Should not crash on workdir roadmaps
        out = capsys.readouterr().out
        assert "WorkdirTest" in out


# ---------------------------------------------------------------------------
# cmd_diagnose
# ---------------------------------------------------------------------------

class TestCmdDiagnose:
    def test_clean_system(self, tmp_path, capsys):
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-Clean", STEPS_3,
                          frontmatter='---\nid: clean-id\nproject: repo\n---\n\n')
        with mock.patch("roadmaps.subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            roadmaps.cmd_diagnose(tmp_path)
        out = capsys.readouterr().out
        assert "No issues found" in out

    def test_detects_orphaned_directory(self, tmp_path, capsys):
        fm = '---\nid: orphan-id\nproject: repo\n---\n\n'
        _make_flat_roadmap(tmp_path, "repo", "Feature", STEPS_3, frontmatter=fm)
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-Feature", STEPS_3,
                          state="Implementing", frontmatter=fm)
        with mock.patch("roadmaps.subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            roadmaps.cmd_diagnose(tmp_path)
        out = capsys.readouterr().out
        assert "orphaned_directory" in out
        assert "1 warning" in out

    def test_detects_stale_implementing(self, tmp_path, capsys):
        fm = '---\nid: stale-id\nproject: repo\n---\n\n'
        rd = _make_roadmap_dir(tmp_path, "repo", "2026-03-25-Stale", STEPS_3,
                               state="Implementing", frontmatter=fm)
        state_file = list((rd / "State").glob("*-Implementing.md"))[0]
        old_time = time.time() - (48 * 3600)
        os.utime(state_file, (old_time, old_time))
        with mock.patch("roadmaps.subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            roadmaps.cmd_diagnose(tmp_path)
        out = capsys.readouterr().out
        assert "stale_implementing" in out
        assert "48" in out

    def test_detects_missing_project_field(self, tmp_path, capsys):
        fm = '---\nid: noproj-id\n---\n\n'
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-NoProj", STEPS_3,
                          frontmatter=fm)
        with mock.patch("roadmaps.subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            roadmaps.cmd_diagnose(tmp_path)
        out = capsys.readouterr().out
        assert "missing_project_field" in out

    def test_detects_missing_id(self, tmp_path, capsys):
        _make_roadmap_dir(tmp_path, "repo", "2026-03-25-NoId", STEPS_3)
        with mock.patch("roadmaps.subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            roadmaps.cmd_diagnose(tmp_path)
        out = capsys.readouterr().out
        assert "missing_id" in out

    def test_project_filter(self, tmp_path, capsys):
        fm_a = '---\nid: a-id\nproject: repo-a\n---\n\n'
        fm_b = '---\nid: b-id\n---\n\n'  # missing project
        _make_roadmap_dir(tmp_path, "repo-a", "2026-03-25-A", STEPS_3, frontmatter=fm_a)
        _make_roadmap_dir(tmp_path, "repo-b", "2026-03-25-B", STEPS_3, frontmatter=fm_b)
        with mock.patch("roadmaps.subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            roadmaps.cmd_diagnose(tmp_path, project="repo-a")
        out = capsys.readouterr().out
        # repo-a has project field, so no missing_project_field for it
        # repo-b is filtered out
        assert "repo-b" not in out
