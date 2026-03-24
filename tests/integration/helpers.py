"""Shared helper functions and constants for integration tests."""

import os
import re
import subprocess
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
COORDINATOR = PROJECT_ROOT / "skills" / "implement-roadmap" / "references" / "coordinator"
TEST_REPO_REMOTE = "mikefullerton/cat-herding-tests"


def _find_test_repo():
    """Find cat-herding-tests repo, handling worktree paths.

    When running from a worktree (e.g., cat-herding-wt/atomic-batch-pr),
    PROJECT_ROOT.parent is cat-herding-wt/, not the projects directory.
    Use git to find the main worktree and look for cat-herding-tests next to it.
    """
    # 1. Explicit override
    env = os.environ.get("CAT_HERDING_TEST_REPO")
    if env:
        return Path(env)

    # 2. Direct sibling (works from main checkout)
    candidate = PROJECT_ROOT.parent / "cat-herding-tests"
    if candidate.exists():
        return candidate

    # 3. Find main worktree via git, look for test repo next to it
    try:
        result = subprocess.run(
            ["git", "-C", str(PROJECT_ROOT), "worktree", "list"],
            capture_output=True, text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            # First line is always the main worktree
            main_repo = Path(result.stdout.splitlines()[0].split()[0])
            candidate = main_repo.parent / "cat-herding-tests"
            if candidate.exists():
                return candidate
    except Exception:
        pass

    # 4. Fallback
    return PROJECT_ROOT.parent / "cat-herding-tests"


TEST_REPO_PATH = _find_test_repo()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_git(args, cwd=None, check=True):
    """Run a git command and return the result."""
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr}")
    return result


def _run_gh(args, check=True):
    """Run a gh CLI command and return the result."""
    result = subprocess.run(
        ["gh"] + args,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)} failed: {result.stderr}")
    return result


def simulate_step(worktree_path, step_number, roadmap_path):
    """Simulate what the implement-step-agent does for one step.

    1. Creates step_<N>_output.txt in the worktree
    2. Updates roadmap: marks step N as Complete
    3. Commits both changes
    Returns the commit SHA.
    """
    wt = Path(worktree_path)

    # Create output file
    (wt / f"step_{step_number}_output.txt").write_text(
        f"Step {step_number} completed.\n"
    )

    # Update roadmap status
    rm_path = Path(roadmap_path)
    content = rm_path.read_text()
    pattern = rf"(### Step {step_number}:.*?\n(?:.*?\n)*?- \*\*Status\*\*: )Not Started"
    content = re.sub(pattern, rf"\g<1>Complete", content)
    rm_path.write_text(content)

    # Commit
    _run_git(["add", "-A"], cwd=worktree_path)
    _run_git(
        ["commit", "-m", f"feat: complete step {step_number}"],
        cwd=worktree_path,
    )

    result = _run_git(["rev-parse", "HEAD"], cwd=worktree_path)
    return result.stdout.strip()


def simulate_failed_step(worktree_path, step_number):
    """Simulate a worker that fails -- creates partial work but does NOT mark step Complete.

    Returns the commit SHA.
    """
    wt = Path(worktree_path)

    # Create partial file
    (wt / f"step_{step_number}_partial.txt").write_text(
        f"Step {step_number} started but failed.\n"
    )

    # Commit partial work (roadmap NOT updated)
    _run_git(["add", "-A"], cwd=worktree_path)
    _run_git(
        ["commit", "-m", f"wip: partial step {step_number} (failed)"],
        cwd=worktree_path,
    )

    result = _run_git(["rev-parse", "HEAD"], cwd=worktree_path)
    return result.stdout.strip()
