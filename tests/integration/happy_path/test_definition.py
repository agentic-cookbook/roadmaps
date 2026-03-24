"""Happy path integration tests for the atomic-batch-pr workflow."""

from pathlib import Path

import pytest

from tests.integration.helpers import (
    _run_git,
    _run_gh,
    simulate_step,
    TEST_REPO_REMOTE,
)


class TestAllAutoStepsSinglePR:
    """3 auto steps -> single branch, single PR, merged, issues closed."""

    def test_all_auto_steps_single_pr(
        self, test_branch, roadmap_in_repo, coordinator, gh,
    ):
        repo_path = test_branch.repo_path

        # Create GitHub issues
        issues = {}
        for i in range(1, 4):
            issues[i] = gh.create_issue(f"Test step {i}")

        # Load roadmap fixture with real issue numbers
        roadmap_relpath = roadmap_in_repo(
            "happy_path/fixtures/all_auto_3step", issue_map=issues,
        )
        roadmap_abspath = str(repo_path / roadmap_relpath)

        # Create feature branch + worktree (as the skill would)
        suffix = test_branch.name.split("/")[-1]
        feature_branch = f"feature/AllAuto3Step-{suffix}"
        worktree_path = str(
            repo_path.parent / f"cat-herding-tests-wt/all-auto-{suffix}"
        )
        _run_git(
            ["worktree", "add", worktree_path, "-b", feature_branch],
            cwd=repo_path,
        )
        test_branch.track_worktree(worktree_path)
        wt_roadmap = str(Path(worktree_path) / roadmap_relpath)

        # Run coordinator loop
        dispatched_steps = []
        for _ in range(10):  # safety limit
            result = coordinator.next_step(wt_roadmap)
            if result["action"] == "done":
                break
            assert result["action"] == "implement"
            step_num = result["step"]
            dispatched_steps.append(step_num)
            simulate_step(worktree_path, step_num, wt_roadmap)

        assert dispatched_steps == [1, 2, 3]

        # Push and create PR
        _run_git(
            ["push", "-u", "origin", feature_branch], cwd=worktree_path,
        )
        closes_lines = "\n".join(
            f"Closes #{issues[i]}" for i in range(1, 4)
        )
        pr_body = (
            f"## Summary\n\nAll 3 steps.\n\n"
            f"## Linked Issues\n\n{closes_lines}"
        )
        pr_result = _run_gh([
            "pr", "create",
            "--repo", TEST_REPO_REMOTE,
            "--head", feature_branch,
            "--base", test_branch.name,
            "--title", "feat: AllAuto3Step",
            "--body", pr_body,
        ])
        pr_url = pr_result.stdout.strip()
        pr_number = int(pr_url.rstrip("/").split("/")[-1])

        # Merge with --merge (not squash)
        _run_gh([
            "pr", "merge", "--repo", TEST_REPO_REMOTE,
            str(pr_number), "--merge",
        ])

        # Verify: all issues closed
        for issue_num in issues.values():
            issue_data = gh.get_issue(issue_num)
            assert issue_data["state"] == "CLOSED", (
                f"Issue #{issue_num} not closed"
            )

        # Verify: step commits visible in history (not squashed)
        _run_git(["pull"], cwd=repo_path)
        log_result = _run_git(["log", "--oneline", "-10"], cwd=repo_path)
        for step_num in [1, 2, 3]:
            assert f"complete step {step_num}" in log_result.stdout


class TestMixedAutoManualSkipsManual:
    """Auto + manual steps -> only auto steps dispatched, manual skipped."""

    def test_mixed_auto_manual_skips_manual(
        self, test_branch, roadmap_in_repo, coordinator, gh,
    ):
        repo_path = test_branch.repo_path

        issues = {}
        for i in range(1, 5):
            issues[i] = gh.create_issue(f"Mixed step {i}")

        roadmap_relpath = roadmap_in_repo(
            "happy_path/fixtures/mixed_auto_manual", issue_map=issues,
        )

        suffix = test_branch.name.split("/")[-1]
        feature_branch = f"feature/MixedAutoManual-{suffix}"
        worktree_path = str(
            repo_path.parent / f"cat-herding-tests-wt/mixed-{suffix}"
        )
        _run_git(
            ["worktree", "add", worktree_path, "-b", feature_branch],
            cwd=repo_path,
        )
        test_branch.track_worktree(worktree_path)
        wt_roadmap = str(Path(worktree_path) / roadmap_relpath)

        dispatched_steps = []
        skipped_manual = []
        for _ in range(10):
            result = coordinator.next_step(wt_roadmap)
            if result["action"] == "done":
                skipped_manual = result.get("manual_skipped", [])
                break
            step_num = result["step"]
            dispatched_steps.append(step_num)
            if result.get("manual_skipped"):
                skipped_manual.extend(result["manual_skipped"])
            simulate_step(worktree_path, step_num, wt_roadmap)

        # Only auto steps dispatched
        assert dispatched_steps == [1, 2, 4]
        # Step 3 was skipped as manual
        assert any(s["step"] == 3 for s in skipped_manual)

        # Create PR -- only auto step issues in Closes lines
        _run_git(
            ["push", "-u", "origin", feature_branch], cwd=worktree_path,
        )
        auto_closes = "\n".join(
            f"Closes #{issues[i]}" for i in [1, 2, 4]
        )
        pr_body = (
            f"## Summary\n\nMixed auto/manual.\n\n"
            f"## Linked Issues\n\n{auto_closes}"
        )
        pr_result = _run_gh([
            "pr", "create", "--repo", TEST_REPO_REMOTE,
            "--head", feature_branch, "--base", test_branch.name,
            "--title", "feat: MixedAutoManual", "--body", pr_body,
        ])
        pr_number = int(
            pr_result.stdout.strip().rstrip("/").split("/")[-1]
        )
        _run_gh([
            "pr", "merge", "--repo", TEST_REPO_REMOTE,
            str(pr_number), "--merge",
        ])

        # Auto issues closed, manual issue still open
        for i in [1, 2, 4]:
            assert gh.get_issue(issues[i])["state"] == "CLOSED"
        assert gh.get_issue(issues[3])["state"] == "OPEN"

        # Cleanup: close the manual issue so it doesn't linger
        gh.close_issue(issues[3])


class TestSingleStepRoadmap:
    """1 step -> still creates branch, worktree, PR."""

    def test_single_step_roadmap(
        self, test_branch, roadmap_in_repo, coordinator, gh,
    ):
        repo_path = test_branch.repo_path

        issues = {1: gh.create_issue("Single step")}
        roadmap_relpath = roadmap_in_repo(
            "happy_path/fixtures/single_step", issue_map=issues,
        )

        suffix = test_branch.name.split("/")[-1]
        feature_branch = f"feature/SingleStep-{suffix}"
        worktree_path = str(
            repo_path.parent / f"cat-herding-tests-wt/single-{suffix}"
        )
        _run_git(
            ["worktree", "add", worktree_path, "-b", feature_branch],
            cwd=repo_path,
        )
        test_branch.track_worktree(worktree_path)
        wt_roadmap = str(Path(worktree_path) / roadmap_relpath)

        # Single step
        result = coordinator.next_step(wt_roadmap)
        assert result["action"] == "implement"
        assert result["step"] == 1
        simulate_step(worktree_path, 1, wt_roadmap)

        # Should be done
        result = coordinator.next_step(wt_roadmap)
        assert result["action"] == "done"

        # Create and merge PR
        _run_git(
            ["push", "-u", "origin", feature_branch], cwd=worktree_path,
        )
        pr_result = _run_gh([
            "pr", "create", "--repo", TEST_REPO_REMOTE,
            "--head", feature_branch, "--base", test_branch.name,
            "--title", "feat: SingleStep",
            "--body", f"Closes #{issues[1]}",
        ])
        pr_number = int(
            pr_result.stdout.strip().rstrip("/").split("/")[-1]
        )
        _run_gh([
            "pr", "merge", "--repo", TEST_REPO_REMOTE,
            str(pr_number), "--merge",
        ])

        assert gh.get_issue(issues[1])["state"] == "CLOSED"
