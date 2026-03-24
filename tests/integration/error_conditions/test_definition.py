"""Error condition integration tests -- failure recovery and edge cases."""

import uuid
from pathlib import Path

import pytest

from tests.integration.helpers import _run_git, simulate_step, simulate_failed_step


class TestWorkerFailureStopsLoop:
    """Failed step stays Not Started -- coordinator returns same step again."""

    def test_worker_failure_stops_loop(
        self, test_branch, roadmap_in_repo, coordinator, gh,
    ):
        repo_path = test_branch.repo_path
        issues = {i: gh.create_issue(f"Fail step {i}") for i in range(1, 4)}
        roadmap_relpath = roadmap_in_repo(
            "error_conditions/fixtures/all_auto_3step", issue_map=issues,
        )

        suffix = test_branch.name.split("/")[-1]
        feature_branch = f"feature/Fail-{suffix}"
        worktree_path = str(
            repo_path.parent / f"cat-herding-tests-wt/fail-{suffix}"
        )
        _run_git(
            ["worktree", "add", worktree_path, "-b", feature_branch],
            cwd=repo_path,
        )
        test_branch.track_worktree(worktree_path)
        wt_roadmap = str(Path(worktree_path) / roadmap_relpath)

        # Step 1 succeeds
        result = coordinator.next_step(wt_roadmap)
        assert result["step"] == 1
        simulate_step(worktree_path, 1, wt_roadmap)

        # Step 2 "fails" -- partial work committed but status not updated
        result = coordinator.next_step(wt_roadmap)
        assert result["step"] == 2
        simulate_failed_step(worktree_path, 2)

        # Coordinator returns step 2 again (still Not Started)
        result = coordinator.next_step(wt_roadmap)
        assert result["action"] == "implement"
        assert result["step"] == 2, (
            "Coordinator should return step 2 again since it wasn't "
            "marked Complete"
        )

        # Worktree still exists for manual recovery
        assert Path(worktree_path).exists()


class TestWorkerFailureDashboardShowsError:
    """step_error marks step as error in dashboard."""

    def test_worker_failure_dashboard_shows_error(self, dashboard_server):
        ds = dashboard_server
        rid = str(uuid.uuid4())

        ds.cli.create_roadmap("ErrorTest", id=rid, status="running")
        ds.cli.set_steps(rid, [
            {
                "number": 1, "description": "Step 1",
                "status": "not_started", "step_type": "Auto",
                "complexity": "S",
            },
            {
                "number": 2, "description": "Step 2",
                "status": "not_started", "step_type": "Auto",
                "complexity": "S",
            },
        ])

        # Step 1 succeeds
        ds.cli.begin_step(rid, 1)
        ds.cli.finish_step(rid, 1)

        # Step 2 fails
        ds.cli.begin_step(rid, 2)
        ds.cli.step_error(rid, 2, "Build failed after 3 attempts")

        data = ds.api_get(f"/api/v1/roadmaps/{rid}")
        step2 = next(s for s in data["steps"] if s["number"] == 2)
        assert step2["status"] == "error"


class TestExistingWorktreeHandled:
    """Worktree already exists -- git worktree add fails cleanly."""

    def test_existing_worktree_handled(self, test_branch):
        repo_path = test_branch.repo_path
        suffix = test_branch.name.split("/")[-1]
        branch1 = f"feature/wt-exist-1-{suffix}"
        branch2 = f"feature/wt-exist-2-{suffix}"
        worktree_path = str(
            repo_path.parent / f"cat-herding-tests-wt/exist-{suffix}"
        )

        # Create first worktree
        _run_git(
            ["worktree", "add", worktree_path, "-b", branch1],
            cwd=repo_path,
        )
        test_branch.track_worktree(worktree_path)
        assert Path(worktree_path).exists()

        # Attempt to create second worktree at same path -- should fail
        result = _run_git(
            ["worktree", "add", worktree_path, "-b", branch2],
            cwd=repo_path, check=False,
        )
        assert result.returncode != 0
        assert "already" in result.stderr.lower()


class TestExistingRemoteBranchHandled:
    """Branch already exists on remote -- recovery uses existing branch."""

    def test_existing_remote_branch_handled(self, test_branch):
        repo_path = test_branch.repo_path
        suffix = test_branch.name.split("/")[-1]
        branch_name = f"feature/branch-exist-{suffix}"

        # Create and push branch
        _run_git(["branch", branch_name], cwd=repo_path)
        _run_git(["push", "origin", branch_name], cwd=repo_path)

        # Attempt worktree with -b for same branch -- should fail
        worktree_path = str(
            repo_path.parent / f"cat-herding-tests-wt/brexist-{suffix}"
        )
        result = _run_git(
            ["worktree", "add", worktree_path, "-b", branch_name],
            cwd=repo_path, check=False,
        )
        assert result.returncode != 0

        # Recovery: use existing branch without -b
        _run_git(
            ["worktree", "add", worktree_path, branch_name],
            cwd=repo_path,
        )
        test_branch.track_worktree(worktree_path)
        assert Path(worktree_path).exists()

        # Cleanup remote branch
        _run_git(
            ["push", "origin", "--delete", branch_name],
            cwd=repo_path, check=False,
        )
