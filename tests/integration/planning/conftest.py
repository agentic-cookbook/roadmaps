"""Fixtures for planning integration tests."""

import shutil
import sys
from pathlib import Path

import pytest

# Ensure worktree scripts/ is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import roadmap_lib as lib

from tests.integration.helpers import _run_git


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def planning_dir(test_branch):
    """Create a planning directory in the test repo, yield it, clean up."""
    rd = lib.create_planning_dir(test_branch.repo_path, "PlanTest", date="2026-03-24")

    yield rd

    # Teardown
    if rd.exists():
        shutil.rmtree(rd)


@pytest.fixture
def planning_dir_with_files(test_branch):
    """Create a full planning directory with Definition.md, Roadmap.md, and state files."""
    rd = lib.create_planning_dir(test_branch.repo_path, "PlanFull", date="2026-03-24")

    # Copy fixture files
    fixture = FIXTURES_DIR / "planning_3step"
    shutil.copy(fixture / "Definition.md", rd / "Definition.md")
    shutil.copy(fixture / "Roadmap.md", rd / "Roadmap.md")

    # Create state files
    lib.create_state_file(rd, "created", date="2026-03-24")
    lib.create_state_file(rd, "planning", date="2026-03-24")

    # Commit
    _run_git(["add", "-A"], cwd=test_branch.repo_path)
    _run_git(
        ["commit", "-m", "test: add PlanFull planning directory"],
        cwd=test_branch.repo_path,
    )
    _run_git(["push"], cwd=test_branch.repo_path)

    created_issues = []

    class PlanningDirInfo:
        path = rd
        repo_path = test_branch.repo_path
        issues = created_issues

        def track_issue(self, number):
            created_issues.append(number)

    yield PlanningDirInfo()

    # Teardown: close issues, remove directory
    for issue_num in created_issues:
        try:
            from tests.integration.helpers import _run_gh
            _run_gh(["issue", "close", "--repo", "mikefullerton/cat-herding-tests", str(issue_num)], check=False)
        except Exception:
            pass
    if rd.exists():
        shutil.rmtree(rd)
