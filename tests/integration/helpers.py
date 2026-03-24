"""Shared helper functions and constants for integration tests."""

import re
import subprocess
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TEST_REPO_PATH = PROJECT_ROOT.parent / "cat-herding-tests"
COORDINATOR = PROJECT_ROOT / "skills" / "implement-roadmap" / "references" / "coordinator"
TEST_REPO_REMOTE = "mikefullerton/cat-herding-tests"


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
