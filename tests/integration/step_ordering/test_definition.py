"""Step ordering integration tests -- verify coordinator dispatches steps correctly."""

from pathlib import Path

import pytest

from tests.integration.helpers import _run_git, simulate_step, WORKTREE_DIR


class TestStepsExecuteInNumericalOrder:
    """Coordinator returns steps 1, 2, 3 in order."""

    def test_steps_execute_in_numerical_order(
        self, test_branch, roadmap_in_repo, coordinator, gh,
    ):
        repo_path = test_branch.repo_path
        issues = {i: gh.create_issue(f"Order step {i}") for i in range(1, 4)}
        roadmap_relpath = roadmap_in_repo(
            "step_ordering/fixtures/all_auto_3step", issue_map=issues,
        )

        suffix = test_branch.name.split("/")[-1]
        feature_branch = f"feature/Order-{suffix}"
        worktree_path = str(
            WORKTREE_DIR / f"order-{suffix}"
        )
        _run_git(
            ["worktree", "add", worktree_path, "-b", feature_branch],
            cwd=repo_path,
        )
        test_branch.track_worktree(worktree_path)
        wt_roadmap = str(Path(worktree_path) / roadmap_relpath)

        step_sequence = []
        for _ in range(10):
            result = coordinator.next_step(wt_roadmap)
            if result["action"] == "done":
                break
            step_sequence.append(result["step"])
            simulate_step(worktree_path, result["step"], wt_roadmap)

        assert step_sequence == [1, 2, 3]


class TestSkipsAlreadyCompleteSteps:
    """Step 1 already complete -> starts at step 2."""

    def test_skips_already_complete_steps(
        self, test_branch, roadmap_in_repo, coordinator, gh,
    ):
        repo_path = test_branch.repo_path
        issues = {i: gh.create_issue(f"Partial step {i}") for i in range(1, 4)}
        roadmap_relpath = roadmap_in_repo(
            "step_ordering/fixtures/partial_complete", issue_map=issues,
        )

        suffix = test_branch.name.split("/")[-1]
        feature_branch = f"feature/Partial-{suffix}"
        worktree_path = str(
            WORKTREE_DIR / f"partial-{suffix}"
        )
        _run_git(
            ["worktree", "add", worktree_path, "-b", feature_branch],
            cwd=repo_path,
        )
        test_branch.track_worktree(worktree_path)
        wt_roadmap = str(Path(worktree_path) / roadmap_relpath)

        result = coordinator.next_step(wt_roadmap)
        assert result["action"] == "implement"
        assert result["step"] == 2  # Step 1 already complete


class TestDependenciesRespected:
    """Step 2 depends on step 1 -- coordinator dispatches step 1 first."""

    def test_dependencies_respected(
        self, test_branch, roadmap_in_repo, coordinator, gh,
    ):
        repo_path = test_branch.repo_path
        issues = {i: gh.create_issue(f"Dep step {i}") for i in range(1, 4)}
        roadmap_relpath = roadmap_in_repo(
            "step_ordering/fixtures/with_dependencies", issue_map=issues,
        )

        suffix = test_branch.name.split("/")[-1]
        feature_branch = f"feature/Deps-{suffix}"
        worktree_path = str(
            WORKTREE_DIR / f"deps-{suffix}"
        )
        _run_git(
            ["worktree", "add", worktree_path, "-b", feature_branch],
            cwd=repo_path,
        )
        test_branch.track_worktree(worktree_path)
        wt_roadmap = str(Path(worktree_path) / roadmap_relpath)

        # First call -- step 2 depends on step 1, so step 2 cannot be first
        result = coordinator.next_step(wt_roadmap)
        assert result["action"] == "implement"
        first_step = result["step"]
        assert first_step != 2, (
            "Step 2 dispatched before its dependency (step 1)"
        )
