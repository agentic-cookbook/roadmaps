"""Cleanup and idempotency integration tests."""

from pathlib import Path

import pytest

from conftest import _run_git, simulate_step


class TestAlreadyCompleteRoadmapReturnsDone:
    """Coordinator returns done immediately for a fully complete roadmap."""

    def test_already_complete_roadmap_returns_done(
        self, test_branch, roadmap_in_repo, coordinator, gh,
    ):
        repo_path = test_branch.repo_path
        issues = {
            i: gh.create_issue(f"Done step {i}") for i in range(1, 4)
        }
        roadmap_relpath = roadmap_in_repo(
            "cleanup/fixtures/already_complete", issue_map=issues,
        )

        suffix = test_branch.name.split("/")[-1]
        feature_branch = f"feature/Done-{suffix}"
        worktree_path = str(
            repo_path.parent / f"cat-herding-tests-wt/done-{suffix}"
        )
        _run_git(
            ["worktree", "add", worktree_path, "-b", feature_branch],
            cwd=repo_path,
        )
        test_branch.track_worktree(worktree_path)
        wt_roadmap = str(Path(worktree_path) / roadmap_relpath)

        result = coordinator.next_step(wt_roadmap)
        assert result["action"] == "done"
        assert result["complete"] == 3


class TestPartialCompletionResumes:
    """Step 1 complete -> picks up at step 2, then step 3."""

    def test_partial_completion_resumes(
        self, test_branch, roadmap_in_repo, coordinator, gh,
    ):
        repo_path = test_branch.repo_path
        issues = {
            i: gh.create_issue(f"Resume step {i}") for i in range(1, 4)
        }
        roadmap_relpath = roadmap_in_repo(
            "cleanup/fixtures/partial_complete", issue_map=issues,
        )

        suffix = test_branch.name.split("/")[-1]
        feature_branch = f"feature/Resume-{suffix}"
        worktree_path = str(
            repo_path.parent / f"cat-herding-tests-wt/resume-{suffix}"
        )
        _run_git(
            ["worktree", "add", worktree_path, "-b", feature_branch],
            cwd=repo_path,
        )
        test_branch.track_worktree(worktree_path)
        wt_roadmap = str(Path(worktree_path) / roadmap_relpath)

        # Should start at step 2
        result = coordinator.next_step(wt_roadmap)
        assert result["action"] == "implement"
        assert result["step"] == 2

        simulate_step(worktree_path, 2, wt_roadmap)

        # Should continue to step 3
        result = coordinator.next_step(wt_roadmap)
        assert result["action"] == "implement"
        assert result["step"] == 3

        simulate_step(worktree_path, 3, wt_roadmap)

        # Should be done
        result = coordinator.next_step(wt_roadmap)
        assert result["action"] == "done"
