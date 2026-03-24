"""Git workflow integration tests -- branch, worktree, PR, merge behavior."""

from pathlib import Path

import pytest

from tests.integration.helpers import (
    _run_git,
    _run_gh,
    simulate_step,
    TEST_REPO_REMOTE,
)


class TestAllCommitsOnSingleBranch:
    """All step commits land on one branch -- no extra branches created."""

    def test_all_commits_on_single_branch(
        self, test_branch, roadmap_in_repo, coordinator, gh,
    ):
        repo_path = test_branch.repo_path
        issues = {
            i: gh.create_issue(f"Branch step {i}") for i in range(1, 4)
        }
        roadmap_relpath = roadmap_in_repo(
            "git_workflow/fixtures/all_auto_3step", issue_map=issues,
        )

        suffix = test_branch.name.split("/")[-1]
        feature_branch = f"feature/BranchTest-{suffix}"
        worktree_path = str(
            repo_path.parent / f"cat-herding-tests-wt/branch-{suffix}"
        )
        _run_git(
            ["worktree", "add", worktree_path, "-b", feature_branch],
            cwd=repo_path,
        )
        test_branch.track_worktree(worktree_path)
        wt_roadmap = str(Path(worktree_path) / roadmap_relpath)

        # Run all 3 steps
        for _ in range(10):
            result = coordinator.next_step(wt_roadmap)
            if result["action"] == "done":
                break
            simulate_step(worktree_path, result["step"], wt_roadmap)

        # All commits on the feature branch
        log_result = _run_git(
            ["log", "--oneline", feature_branch], cwd=worktree_path,
        )
        lines = log_result.stdout.strip().split("\n")
        # 3 step commits + roadmap fixture commit + initial empty commit
        assert len(lines) >= 4

        for step_num in [1, 2, 3]:
            assert f"complete step {step_num}" in log_result.stdout

        # No per-step branches created for THIS test's feature
        branch_result = _run_git(
            ["branch", "--list", f"feature/BranchTest-{suffix}-step-*"],
            cwd=repo_path,
        )
        assert branch_result.stdout.strip() == "", (
            "Per-step branches should not exist for this test"
        )


class TestWorktreeCreatedAtExpectedPath:
    """Worktree created at ../repo-wt/<feature_name>."""

    def test_worktree_created_at_expected_path(self, test_branch):
        repo_path = test_branch.repo_path
        suffix = test_branch.name.split("/")[-1]
        feature_name = f"WtPath-{suffix}"
        feature_branch = f"feature/{feature_name}"

        # Use the skill's formula
        repo_basename = repo_path.name
        worktree_path = str(
            repo_path.parent / f"{repo_basename}-wt" / feature_name
        )

        _run_git(
            ["worktree", "add", worktree_path, "-b", feature_branch],
            cwd=repo_path,
        )
        test_branch.track_worktree(worktree_path)

        # Verify it exists and is a valid worktree
        assert Path(worktree_path).exists()
        assert (Path(worktree_path) / ".git").exists()

        # Verify git worktree list includes it
        list_result = _run_git(["worktree", "list"], cwd=repo_path)
        assert feature_name in list_result.stdout


class TestWorktreeCleanedUpOnSuccess:
    """After git worktree remove, the directory and listing are clean."""

    def test_worktree_cleaned_up_on_success(self, test_branch):
        repo_path = test_branch.repo_path
        suffix = test_branch.name.split("/")[-1]
        feature_branch = f"feature/WtClean-{suffix}"
        worktree_path = str(
            repo_path.parent / f"cat-herding-tests-wt/clean-{suffix}"
        )

        _run_git(
            ["worktree", "add", worktree_path, "-b", feature_branch],
            cwd=repo_path,
        )
        assert Path(worktree_path).exists()

        # Remove the worktree
        _run_git(["worktree", "remove", worktree_path], cwd=repo_path)

        assert not Path(worktree_path).exists()
        list_result = _run_git(["worktree", "list"], cwd=repo_path)
        assert worktree_path not in list_result.stdout


class TestPRUsesMergeNotSquash:
    """--merge preserves individual step commits in target branch history."""

    def test_pr_uses_merge_not_squash(
        self, test_branch, roadmap_in_repo, coordinator, gh,
    ):
        repo_path = test_branch.repo_path
        issues = {
            i: gh.create_issue(f"Merge step {i}") for i in range(1, 4)
        }
        roadmap_relpath = roadmap_in_repo(
            "git_workflow/fixtures/all_auto_3step", issue_map=issues,
        )

        suffix = test_branch.name.split("/")[-1]
        feature_branch = f"feature/MergeTest-{suffix}"
        worktree_path = str(
            repo_path.parent / f"cat-herding-tests-wt/merge-{suffix}"
        )
        _run_git(
            ["worktree", "add", worktree_path, "-b", feature_branch],
            cwd=repo_path,
        )
        test_branch.track_worktree(worktree_path)
        wt_roadmap = str(Path(worktree_path) / roadmap_relpath)

        for _ in range(10):
            result = coordinator.next_step(wt_roadmap)
            if result["action"] == "done":
                break
            simulate_step(worktree_path, result["step"], wt_roadmap)

        _run_git(
            ["push", "-u", "origin", feature_branch], cwd=worktree_path,
        )
        pr_result = _run_gh([
            "pr", "create", "--repo", TEST_REPO_REMOTE,
            "--head", feature_branch, "--base", test_branch.name,
            "--title", "feat: MergeTest",
            "--body", "Test merge commit preservation",
        ])
        pr_number = int(
            pr_result.stdout.strip().rstrip("/").split("/")[-1]
        )

        # Merge with --merge (not --squash)
        _run_gh([
            "pr", "merge", "--repo", TEST_REPO_REMOTE,
            str(pr_number), "--merge",
        ])

        # Pull and check: individual step commits visible
        _run_git(["pull"], cwd=repo_path)
        log_result = _run_git(["log", "--oneline", "-10"], cwd=repo_path)
        for step_num in [1, 2, 3]:
            assert f"complete step {step_num}" in log_result.stdout, (
                f"Step {step_num} commit not visible -- "
                "was the PR squash-merged?"
            )


class TestPRBodyContainsClosesLines:
    """PR body contains Closes #N for each step's issue."""

    def test_pr_body_contains_closes_lines(
        self, test_branch, roadmap_in_repo, coordinator, gh,
    ):
        repo_path = test_branch.repo_path
        issues = {
            i: gh.create_issue(f"Closes step {i}") for i in range(1, 4)
        }
        roadmap_relpath = roadmap_in_repo(
            "git_workflow/fixtures/all_auto_3step", issue_map=issues,
        )

        suffix = test_branch.name.split("/")[-1]
        feature_branch = f"feature/ClosesTest-{suffix}"
        worktree_path = str(
            repo_path.parent / f"cat-herding-tests-wt/closes-{suffix}"
        )
        _run_git(
            ["worktree", "add", worktree_path, "-b", feature_branch],
            cwd=repo_path,
        )
        test_branch.track_worktree(worktree_path)
        wt_roadmap = str(Path(worktree_path) / roadmap_relpath)

        for _ in range(10):
            result = coordinator.next_step(wt_roadmap)
            if result["action"] == "done":
                break
            simulate_step(worktree_path, result["step"], wt_roadmap)

        # Build PR body with Closes lines
        closes_lines = "\n".join(
            f"Closes #{issues[i]}" for i in range(1, 4)
        )
        pr_body = (
            f"## Steps\n\n- Step 1\n- Step 2\n- Step 3\n\n"
            f"## Issues\n\n{closes_lines}"
        )

        _run_git(
            ["push", "-u", "origin", feature_branch], cwd=worktree_path,
        )
        pr_result = _run_gh([
            "pr", "create", "--repo", TEST_REPO_REMOTE,
            "--head", feature_branch, "--base", test_branch.name,
            "--title", "feat: ClosesTest", "--body", pr_body,
        ])
        pr_number = int(
            pr_result.stdout.strip().rstrip("/").split("/")[-1]
        )

        # Verify PR body
        pr_data = gh.get_pr(pr_number)
        for issue_num in issues.values():
            assert f"Closes #{issue_num}" in pr_data["body"], (
                f"PR body missing 'Closes #{issue_num}'"
            )

        # Cleanup: close PR without merging
        gh.close_pr(pr_number)
