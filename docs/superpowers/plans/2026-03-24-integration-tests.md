# Integration Test Suite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a comprehensive integration test suite that verifies the atomic-batch-pr workflow end-to-end against real git and real GitHub.

**Architecture:** pytest tests in `tests/integration/` exercise the coordinator, dashboard, and git/GitHub workflow by simulating agent work (create files, commit, update roadmap) against the `cat-herding-tests` sandbox repo. Each test gets an isolated orphan branch. A Flask dashboard runs in a daemon thread on a random port.

**Tech Stack:** Python 3.10+, pytest, Flask, subprocess (git, gh CLI)

**Spec:** `docs/superpowers/specs/2026-03-24-atomic-batch-integration-tests-design.md`

---

### Task 1: Restructure test directories

Move existing unit tests from `tests/` to `tests/unit/`, create `tests/integration/` skeleton.

**Files:**
- Move: `tests/*.py` -> `tests/unit/*.py`
- Create: `tests/integration/__init__.py`
- Create: `tests/integration/conftest.py` (placeholder)

- [ ] **Step 1: Create new directory structure**

```bash
mkdir -p tests/unit tests/integration
```

- [ ] **Step 2: Move existing test files to tests/unit/**

```bash
git mv tests/conftest.py tests/unit/conftest.py
git mv tests/test_coordinator.py tests/unit/test_coordinator.py
git mv tests/test_api_roadmaps.py tests/unit/test_api_roadmaps.py
git mv tests/test_api_steps.py tests/unit/test_api_steps.py
git mv tests/test_api_sync.py tests/unit/test_api_sync.py
git mv tests/test_api_state.py tests/unit/test_api_state.py
git mv tests/test_api_controls.py tests/unit/test_api_controls.py
git mv tests/test_dashboard_client.py tests/unit/test_dashboard_client.py
git mv tests/test_db.py tests/unit/test_db.py
git mv tests/test_models.py tests/unit/test_models.py
git mv tests/test_roadmap_lib.py tests/unit/test_roadmap_lib.py
```

- [ ] **Step 3: Fix PROJECT_ROOT in unit conftest.py**

The path in `tests/unit/conftest.py` line 12 currently computes PROJECT_ROOT as `parent.parent` (2 levels up from `tests/`). After the move to `tests/unit/`, it needs to go 3 levels up:

```python
# In tests/unit/conftest.py, change:
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# To:
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
```

- [ ] **Step 4: Fix COORDINATOR path in unit test_coordinator.py**

The path in `tests/unit/test_coordinator.py` line 11 also uses `parent.parent`. Update:

```python
# Change:
COORDINATOR = Path(__file__).resolve().parent.parent / "skills" / "implement-roadmap" / "references" / "coordinator"
# To:
COORDINATOR = Path(__file__).resolve().parent.parent.parent / "skills" / "implement-roadmap" / "references" / "coordinator"
```

Also update the `_scripts_dir` path if present in the file (look for similar parent.parent patterns).

- [ ] **Step 5: Run unit tests to verify the move didn't break anything**

```bash
pytest tests/unit/ -v
```

Expected: all 134 tests pass.

- [ ] **Step 6: Create integration placeholder files**

Create `tests/integration/__init__.py` (empty) and each test group directory:

```bash
mkdir -p tests/integration/happy_path/fixtures
mkdir -p tests/integration/step_ordering/fixtures
mkdir -p tests/integration/dashboard_sync/fixtures
mkdir -p tests/integration/error_conditions/fixtures
mkdir -p tests/integration/git_workflow/fixtures
mkdir -p tests/integration/cleanup/fixtures
```

- [ ] **Step 7: Commit**

```bash
git add -A tests/
git commit -m "refactor: move unit tests to tests/unit/, create tests/integration/ skeleton"
```

---

### Task 2: Create fixture roadmap files

Create pre-built roadmap File Record directories for each test group. Roadmap.md files use `__ISSUE_N__` placeholders for issue numbers, which the conftest's `roadmap_in_repo` fixture factory patches at runtime.

**Files:**
- Create: `tests/integration/happy_path/fixtures/all_auto_3step/` (4 files)
- Create: `tests/integration/happy_path/fixtures/mixed_auto_manual/` (4 files)
- Create: `tests/integration/happy_path/fixtures/single_step/` (4 files)
- Create: `tests/integration/step_ordering/fixtures/all_auto_3step/` (4 files)
- Create: `tests/integration/step_ordering/fixtures/with_dependencies/` (4 files)
- Create: `tests/integration/step_ordering/fixtures/partial_complete/` (4 files)
- Create: `tests/integration/dashboard_sync/fixtures/all_auto_3step/` (4 files)
- Create: `tests/integration/error_conditions/fixtures/all_auto_3step/` (4 files)
- Create: `tests/integration/git_workflow/fixtures/all_auto_3step/` (4 files)
- Create: `tests/integration/cleanup/fixtures/already_complete/` (4 files)
- Create: `tests/integration/cleanup/fixtures/partial_complete/` (4 files)

Each fixture directory has this structure:
```
<fixture_name>/
  Definition.md
  Roadmap.md
  State/
    2026-01-01-Ready.md
  History/
    .gitkeep
```

- [ ] **Step 1: Create all_auto_3step fixture**

This fixture is used by happy_path, step_ordering, dashboard_sync, error_conditions, and git_workflow. Create it once under `happy_path/fixtures/` first, then duplicate.

`tests/integration/happy_path/fixtures/all_auto_3step/Definition.md`:
```markdown
---
id: def-test-all-auto
created: 2026-01-01
modified: 2026-01-01
author: Test Runner <test@test.com>
change-history:
  - date: 2026-01-01
    author: Test Runner <test@test.com>
    summary: Test fixture
---

# Feature Definition: AllAuto3Step

## Goal and Purpose

Test fixture: 3 auto steps that each create a file.

## Acceptance Criteria

- step_1_output.txt, step_2_output.txt, step_3_output.txt exist

## Verification Strategy

- **Build command**: echo "no build needed"
- **Test command**: test -f step_1_output.txt && test -f step_2_output.txt && test -f step_3_output.txt
```

`tests/integration/happy_path/fixtures/all_auto_3step/Roadmap.md`:
```markdown
---
id: rm-test-all-auto
created: 2026-01-01
modified: 2026-01-01
author: Test Runner <test@test.com>
definition-id: def-test-all-auto
change-history:
  - date: 2026-01-01
    author: Test Runner <test@test.com>
    summary: Test fixture
---

# Feature Roadmap: AllAuto3Step

## Progress

| Total Steps | Complete | In Progress | Blocked | Not Started |
|-------------|----------|-------------|---------|-------------|
| 3           | 0        | 0           | 0       | 3           |

## Implementation Steps

### Step 1: Create step 1 output file

- **GitHub Issue**: __ISSUE_1__
- **Type**: Auto
- **Status**: Not Started
- **Complexity**: S
- **Dependencies**: None
- **Acceptance Criteria**:
  - [ ] step_1_output.txt exists

---

### Step 2: Create step 2 output file

- **GitHub Issue**: __ISSUE_2__
- **Type**: Auto
- **Status**: Not Started
- **Complexity**: S
- **Dependencies**: None
- **Acceptance Criteria**:
  - [ ] step_2_output.txt exists

---

### Step 3: Create step 3 output file

- **GitHub Issue**: __ISSUE_3__
- **Type**: Auto
- **Status**: Not Started
- **Complexity**: S
- **Dependencies**: None
- **Acceptance Criteria**:
  - [ ] step_3_output.txt exists
```

`tests/integration/happy_path/fixtures/all_auto_3step/State/2026-01-01-Ready.md`:
```markdown
---
id: state-test-ready
created: 2026-01-01
author: Test Runner <test@test.com>
definition-id: def-test-all-auto
previous-state: Created
---

# State: Ready

Test fixture ready.
```

`tests/integration/happy_path/fixtures/all_auto_3step/History/.gitkeep`:
(empty file)

- [ ] **Step 2: Create mixed_auto_manual fixture**

`tests/integration/happy_path/fixtures/mixed_auto_manual/Definition.md` — same pattern, `id: def-test-mixed`, name `MixedAutoManual`.

`tests/integration/happy_path/fixtures/mixed_auto_manual/Roadmap.md`:

Same frontmatter pattern with `id: rm-test-mixed` and `definition-id: def-test-mixed`. 4 steps:

- Step 1: Auto, Not Started, `__ISSUE_1__`
- Step 2: Auto, Not Started, `__ISSUE_2__`
- Step 3: Manual, Not Started, `__ISSUE_3__`
- Step 4: Auto, Not Started, `__ISSUE_4__`

Progress table: `| 4 | 0 | 0 | 0 | 4 |`

Create matching `State/2026-01-01-Ready.md` and `History/.gitkeep`.

- [ ] **Step 3: Create single_step fixture**

`tests/integration/happy_path/fixtures/single_step/` — `id: def-test-single` / `rm-test-single`, name `SingleStep`. One step: Auto, Not Started, `__ISSUE_1__`.

- [ ] **Step 4: Create with_dependencies fixture**

`tests/integration/step_ordering/fixtures/with_dependencies/` — `id: def-test-deps` / `rm-test-deps`, name `WithDependencies`. 3 steps:

- Step 1: Auto, Not Started, `__ISSUE_1__`, Dependencies: None
- Step 2: Auto, Not Started, `__ISSUE_2__`, Dependencies: Step 1
- Step 3: Auto, Not Started, `__ISSUE_3__`, Dependencies: None

- [ ] **Step 5: Create already_complete fixture**

`tests/integration/cleanup/fixtures/already_complete/` — `id: def-test-complete` / `rm-test-complete`, name `AlreadyComplete`. 3 steps, all `- **Status**: Complete`. Progress: `| 3 | 3 | 0 | 0 | 0 |`.

State directory has both `2026-01-01-Ready.md` and `2026-01-01-Complete.md`.

- [ ] **Step 6: Create partial_complete fixture**

`tests/integration/cleanup/fixtures/partial_complete/` and duplicate to `tests/integration/step_ordering/fixtures/partial_complete/`. `id: def-test-partial` / `rm-test-partial`, name `PartialComplete`. 3 steps: step 1 Complete, steps 2-3 Not Started. Progress: `| 3 | 1 | 0 | 0 | 2 |`.

- [ ] **Step 7: Duplicate shared fixtures to other test groups**

```bash
cp -r tests/integration/happy_path/fixtures/all_auto_3step tests/integration/step_ordering/fixtures/
cp -r tests/integration/happy_path/fixtures/all_auto_3step tests/integration/dashboard_sync/fixtures/
cp -r tests/integration/happy_path/fixtures/all_auto_3step tests/integration/error_conditions/fixtures/
cp -r tests/integration/happy_path/fixtures/all_auto_3step tests/integration/git_workflow/fixtures/
```

- [ ] **Step 8: Commit**

```bash
git add tests/integration/
git commit -m "test: add fixture roadmap files for integration tests"
```

---

### Task 3: Create integration conftest.py

All shared fixtures and helper functions for integration tests.

**Files:**
- Create: `tests/integration/conftest.py`

- [ ] **Step 1: Write the conftest with all fixtures and helpers**

`tests/integration/conftest.py`:

```python
"""Shared fixtures for integration tests against cat-herding-tests repo."""

import json
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TEST_REPO_PATH = PROJECT_ROOT.parent / "cat-herding-tests"
COORDINATOR = PROJECT_ROOT / "skills" / "implement-roadmap" / "references" / "coordinator"
TEST_REPO_REMOTE = "mikefullerton/cat-herding-tests"

# Add project paths
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from services.dashboard import db
from services.dashboard.app import create_app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_free_port():
    """Find an available TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


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
    # Replace the status for this specific step
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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def test_repo():
    """Session-scoped. Verifies the test repo exists and returns its path."""
    if not TEST_REPO_PATH.exists():
        pytest.skip(f"Test repo not found at {TEST_REPO_PATH}")
    if not (TEST_REPO_PATH / ".git").exists():
        pytest.skip(f"{TEST_REPO_PATH} is not a git repository")

    # Verify remote
    result = _run_git(["remote", "get-url", "origin"], cwd=TEST_REPO_PATH)
    remote = result.stdout.strip()
    if "cat-herding-tests" not in remote:
        pytest.skip(f"Test repo remote is {remote}, expected cat-herding-tests")

    return TEST_REPO_PATH


@pytest.fixture
def test_branch(test_repo, request):
    """Function-scoped. Creates a fresh orphan branch, yields its name, cleans up."""
    short_id = uuid.uuid4().hex[:8]
    branch_name = f"test/{request.node.name}-{short_id}"
    worktrees_created = []

    # Fetch latest from origin
    _run_git(["fetch", "origin"], cwd=test_repo)

    # Create orphan branch
    _run_git(["checkout", "--orphan", branch_name], cwd=test_repo)
    _run_git(["reset", "--hard"], cwd=test_repo)
    _run_git(
        ["commit", "--allow-empty", "-m", "Initial empty commit for test"],
        cwd=test_repo,
    )
    _run_git(["push", "-u", "origin", branch_name], cwd=test_repo)

    class BranchInfo:
        name = branch_name
        repo_path = test_repo

        def track_worktree(self, path):
            worktrees_created.append(path)

    yield BranchInfo()

    # Teardown: clean up worktrees, delete branch locally and remotely
    for wt_path in worktrees_created:
        if Path(wt_path).exists():
            _run_git(
                ["worktree", "remove", "--force", wt_path],
                cwd=test_repo, check=False,
            )

    _run_git(["checkout", "main"], cwd=test_repo, check=False)
    _run_git(["branch", "-D", branch_name], cwd=test_repo, check=False)
    _run_git(
        ["push", "origin", "--delete", branch_name],
        cwd=test_repo, check=False,
    )


@pytest.fixture
def roadmap_in_repo(test_branch):
    """Fixture factory. Returns a callable that copies a fixture roadmap into the test repo.

    Usage:
        roadmap_path = roadmap_in_repo(
            "happy_path/fixtures/all_auto_3step", issue_map={1: 42, 2: 43, 3: 44}
        )
    """
    def _copy(fixture_relpath, issue_map=None):
        """Copy fixture roadmap into test repo, patch issue placeholders, commit, push.

        Args:
            fixture_relpath: path relative to tests/integration/
                (e.g., "happy_path/fixtures/all_auto_3step")
            issue_map: dict of step_number -> github_issue_number (optional)

        Returns:
            Relative roadmap path (e.g., "Roadmaps/AllAuto3Step/Roadmap.md")
        """
        fixture_path = Path(__file__).parent / fixture_relpath
        if not fixture_path.exists():
            raise FileNotFoundError(f"Fixture not found: {fixture_path}")

        # Determine feature name from the fixture directory's Roadmap.md
        roadmap_md = fixture_path / "Roadmap.md"
        content = roadmap_md.read_text()
        match = re.search(r"# Feature Roadmap: (\w+)", content)
        feature_name = match.group(1) if match else fixture_path.name

        # Copy into test repo
        dest = test_branch.repo_path / "Roadmaps" / feature_name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(fixture_path, dest)

        # Patch issue placeholders
        if issue_map:
            rm_file = dest / "Roadmap.md"
            text = rm_file.read_text()
            for step_num, issue_num in issue_map.items():
                text = text.replace(f"__ISSUE_{step_num}__", f"#{issue_num}")
            rm_file.write_text(text)

        # Commit and push
        _run_git(["add", "-A"], cwd=test_branch.repo_path)
        _run_git(
            ["commit", "-m", f"test: add {feature_name} roadmap fixture"],
            cwd=test_branch.repo_path,
        )
        _run_git(["push"], cwd=test_branch.repo_path)

        return f"Roadmaps/{feature_name}/Roadmap.md"

    return _copy


@pytest.fixture
def dashboard_server(tmp_path):
    """Function-scoped. Starts Flask dashboard in a daemon thread, yields DashboardHelper."""
    db_path = str(tmp_path / "test.db")
    os.environ["DASHBOARD_DB"] = db_path
    port = _find_free_port()

    application = create_app()
    application.config["TESTING"] = True

    # Initialize DB
    conn = db.connect(db_path)
    db.init_db(conn)
    conn.close()

    server_thread = threading.Thread(
        target=lambda: application.run(
            host="127.0.0.1", port=port, threaded=True, use_reloader=False,
        ),
    )
    server_thread.daemon = True
    server_thread.start()

    # Wait for server to accept connections
    base_url = f"http://127.0.0.1:{port}"
    for _ in range(20):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                break
        except OSError:
            time.sleep(0.1)

    # Configure dashboard client
    os.environ["DASHBOARD_URL"] = base_url
    from scripts.dashboard_client import DashboardClient
    client = DashboardClient(base_url=base_url)

    class DashboardHelper:
        url = base_url
        cli = client

        def api_get(self, path):
            """GET request to API, returns parsed JSON."""
            import urllib.request
            req = urllib.request.Request(f"{base_url}{path}")
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read())

    yield DashboardHelper()

    os.environ.pop("DASHBOARD_DB", None)
    os.environ.pop("DASHBOARD_URL", None)


class CoordinatorHelper:
    """Wraps coordinator subprocess calls."""

    def next_step(self, roadmap_path):
        """Call coordinator next-step, return parsed JSON."""
        cwd = str(Path(roadmap_path).resolve().parent.parent.parent)
        result = subprocess.run(
            [sys.executable, str(COORDINATOR), "next-step", roadmap_path],
            capture_output=True, text=True, cwd=cwd,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"coordinator next-step failed: {result.stderr}"
            )
        return json.loads(result.stdout)

    def resolve(self, feature_name, cwd):
        """Call coordinator resolve, return parsed JSON."""
        result = subprocess.run(
            [sys.executable, str(COORDINATOR), "resolve", feature_name],
            capture_output=True, text=True, cwd=str(cwd),
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"coordinator resolve failed: {result.stderr}"
            )
        return json.loads(result.stdout)

    def summary(self, roadmap_path):
        """Call coordinator summary, return parsed JSON."""
        cwd = str(Path(roadmap_path).resolve().parent.parent.parent)
        result = subprocess.run(
            [sys.executable, str(COORDINATOR), "summary", roadmap_path],
            capture_output=True, text=True, cwd=cwd,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"coordinator summary failed: {result.stderr}"
            )
        return json.loads(result.stdout)


@pytest.fixture(scope="session")
def coordinator():
    """Session-scoped. Returns a CoordinatorHelper."""
    if not COORDINATOR.exists():
        pytest.skip(f"Coordinator not found at {COORDINATOR}")
    return CoordinatorHelper()


class GHHelper:
    """Wraps gh CLI commands for test setup/teardown."""

    def __init__(self, repo):
        self.repo = repo

    def create_issue(self, title, body="Test issue"):
        result = _run_gh([
            "issue", "create", "--repo", self.repo,
            "--title", title, "--body", body,
        ])
        # gh outputs the issue URL, extract number from it
        url = result.stdout.strip()
        return int(url.rstrip("/").split("/")[-1])

    def close_issue(self, number):
        _run_gh(["issue", "close", "--repo", self.repo, str(number)])

    def get_issue(self, number):
        result = _run_gh([
            "issue", "view", "--repo", self.repo, str(number),
            "--json", "number,title,state,url",
        ])
        return json.loads(result.stdout)

    def list_prs(self, head=None):
        args = [
            "pr", "list", "--repo", self.repo,
            "--json", "number,title,state,url,headRefName",
        ]
        if head:
            args.extend(["--head", head])
        result = _run_gh(args)
        return json.loads(result.stdout)

    def get_pr(self, number):
        result = _run_gh([
            "pr", "view", "--repo", self.repo, str(number),
            "--json", "number,title,state,body,url,mergedAt,commits",
        ])
        return json.loads(result.stdout)

    def close_pr(self, number):
        _run_gh(["pr", "close", "--repo", self.repo, str(number)])

    def delete_branch(self, branch):
        _run_gh([
            "api", "--method", "DELETE",
            f"repos/{self.repo}/git/refs/heads/{branch}",
        ], check=False)


@pytest.fixture(scope="session")
def gh():
    """Session-scoped. Returns a GHHelper for the test repo."""
    result = subprocess.run(
        ["gh", "auth", "status"], capture_output=True, text=True,
    )
    if result.returncode != 0:
        pytest.skip("gh CLI not authenticated")
    return GHHelper(TEST_REPO_REMOTE)
```

- [ ] **Step 2: Verify conftest loads without import errors**

```bash
python3 -c "import sys; sys.path.insert(0, '.'); exec(open('tests/integration/conftest.py').read())"
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add tests/integration/conftest.py
git commit -m "test: add integration test conftest with shared fixtures and helpers"
```

---

### Task 4: happy_path tests

**Files:**
- Create: `tests/integration/happy_path/test_definition.py`

**Depends on:** Task 1, 2, 3

- [ ] **Step 1: Write the test file**

`tests/integration/happy_path/test_definition.py`:

```python
"""Happy path integration tests for the atomic-batch-pr workflow."""

from pathlib import Path

import pytest

from conftest import (
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
```

- [ ] **Step 2: Run the happy_path tests**

```bash
pytest tests/integration/happy_path/test_definition.py -v
```

Expected: all 3 tests pass.

- [ ] **Step 3: Commit**

```bash
git add tests/integration/happy_path/test_definition.py
git commit -m "test: add happy_path integration tests (3 tests)"
```

---

### Task 5: step_ordering tests

**Files:**
- Create: `tests/integration/step_ordering/test_definition.py`

**Depends on:** Task 1, 2, 3

- [ ] **Step 1: Write the test file**

`tests/integration/step_ordering/test_definition.py`:

```python
"""Step ordering integration tests -- verify coordinator dispatches steps correctly."""

from pathlib import Path

import pytest

from conftest import _run_git, simulate_step


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
            repo_path.parent / f"cat-herding-tests-wt/order-{suffix}"
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
            repo_path.parent / f"cat-herding-tests-wt/partial-{suffix}"
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
            repo_path.parent / f"cat-herding-tests-wt/deps-{suffix}"
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
```

- [ ] **Step 2: Run the step_ordering tests**

```bash
pytest tests/integration/step_ordering/test_definition.py -v
```

Expected: all 3 tests pass.

- [ ] **Step 3: Commit**

```bash
git add tests/integration/step_ordering/test_definition.py
git commit -m "test: add step_ordering integration tests (3 tests)"
```

---

### Task 6: dashboard_sync tests

**Files:**
- Create: `tests/integration/dashboard_sync/test_definition.py`

**Depends on:** Task 1, 2, 3

- [ ] **Step 1: Write the test file**

`tests/integration/dashboard_sync/test_definition.py`:

```python
"""Dashboard synchronization integration tests."""

import uuid

import pytest


class TestStepStatusTransitions:
    """begin_step -> in_progress, finish_step -> complete."""

    def test_step_status_transitions(self, dashboard_server):
        ds = dashboard_server
        rid = str(uuid.uuid4())

        ds.cli.create_roadmap("SyncTest", id=rid)
        ds.cli.set_steps(rid, [
            {
                "number": 1, "description": "Step 1",
                "status": "not_started", "step_type": "Auto",
                "complexity": "S",
            },
        ])

        # Begin
        ds.cli.begin_step(rid, 1)
        data = ds.api_get(f"/api/v1/roadmaps/{rid}")
        assert data["steps"][0]["status"] == "in_progress"

        # Finish
        ds.cli.finish_step(rid, 1)
        data = ds.api_get(f"/api/v1/roadmaps/{rid}")
        assert data["steps"][0]["status"] == "complete"


class TestRoadmapStatusLifecycle:
    """idle -> running -> complete."""

    def test_roadmap_status_lifecycle(self, dashboard_server):
        ds = dashboard_server
        rid = str(uuid.uuid4())

        ds.cli.create_roadmap("StatusTest", id=rid, status="idle")
        data = ds.api_get(f"/api/v1/roadmaps/{rid}")
        assert data["status"] == "idle"

        ds.cli.update_roadmap(rid, status="running")
        data = ds.api_get(f"/api/v1/roadmaps/{rid}")
        assert data["status"] == "running"

        ds.cli.complete(rid)
        data = ds.api_get(f"/api/v1/roadmaps/{rid}")
        assert data["status"] == "complete"


class TestRoadmapStateLifecycle:
    """Ready -> Implementing -> Complete with state history."""

    def test_roadmap_state_lifecycle(self, dashboard_server):
        ds = dashboard_server
        rid = str(uuid.uuid4())

        ds.cli.create_roadmap("StateTest", id=rid, state="Ready")
        ds.cli.transition_state(rid, "Implementing")
        ds.cli.transition_state(rid, "Complete")

        data = ds.api_get(f"/api/v1/roadmaps/{rid}")
        assert data["state"] == "Complete"


class TestDashboardReflectsCurrentState:
    """After each simulated step, dashboard shows correct completion count."""

    def test_dashboard_reflects_current_state(self, dashboard_server):
        ds = dashboard_server
        rid = str(uuid.uuid4())

        ds.cli.create_roadmap("ReflectTest", id=rid, status="running")
        ds.cli.set_steps(rid, [
            {
                "number": i, "description": f"Step {i}",
                "status": "not_started", "step_type": "Auto",
                "complexity": "S",
            }
            for i in range(1, 4)
        ])

        for step_num in range(1, 4):
            ds.cli.begin_step(rid, step_num)
            ds.cli.finish_step(rid, step_num)
            data = ds.api_get(f"/api/v1/roadmaps/{rid}")
            complete_count = sum(
                1 for s in data["steps"] if s["status"] == "complete"
            )
            assert complete_count == step_num


class TestSinglePROnOverview:
    """add_pr makes the PR visible in the overview API."""

    def test_single_pr_on_overview(self, dashboard_server):
        ds = dashboard_server
        rid = str(uuid.uuid4())

        ds.cli.create_roadmap("PRTest", id=rid)
        ds.cli.add_pr(
            rid, number=42, title="feat: test PR",
            url="https://github.com/test/repo/pull/42",
        )

        data = ds.api_get("/api/v1/roadmaps?detail=true")
        roadmap = next(r for r in data if r["id"] == rid)
        assert len(roadmap["prs"]) == 1
        assert roadmap["prs"][0]["number"] == 42
```

- [ ] **Step 2: Run the dashboard_sync tests**

```bash
pytest tests/integration/dashboard_sync/test_definition.py -v
```

Expected: all 5 tests pass.

- [ ] **Step 3: Commit**

```bash
git add tests/integration/dashboard_sync/test_definition.py
git commit -m "test: add dashboard_sync integration tests (5 tests)"
```

---

### Task 7: error_conditions tests

**Files:**
- Create: `tests/integration/error_conditions/test_definition.py`

**Depends on:** Task 1, 2, 3

- [ ] **Step 1: Write the test file**

`tests/integration/error_conditions/test_definition.py`:

```python
"""Error condition integration tests -- failure recovery and edge cases."""

import uuid
from pathlib import Path

import pytest

from conftest import _run_git, simulate_step, simulate_failed_step


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
```

- [ ] **Step 2: Run the error_conditions tests**

```bash
pytest tests/integration/error_conditions/test_definition.py -v
```

Expected: all 4 tests pass.

- [ ] **Step 3: Commit**

```bash
git add tests/integration/error_conditions/test_definition.py
git commit -m "test: add error_conditions integration tests (4 tests)"
```

---

### Task 8: git_workflow tests

**Files:**
- Create: `tests/integration/git_workflow/test_definition.py`

**Depends on:** Task 1, 2, 3

- [ ] **Step 1: Write the test file**

`tests/integration/git_workflow/test_definition.py`:

```python
"""Git workflow integration tests -- branch, worktree, PR, merge behavior."""

from pathlib import Path

import pytest

from conftest import (
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

        # No per-step branches created
        branch_result = _run_git(
            ["branch", "--list", "feature/*-step-*"], cwd=repo_path,
        )
        assert branch_result.stdout.strip() == "", (
            "Per-step branches should not exist"
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
```

- [ ] **Step 2: Run the git_workflow tests**

```bash
pytest tests/integration/git_workflow/test_definition.py -v
```

Expected: all 5 tests pass.

- [ ] **Step 3: Commit**

```bash
git add tests/integration/git_workflow/test_definition.py
git commit -m "test: add git_workflow integration tests (5 tests)"
```

---

### Task 9: cleanup tests

**Files:**
- Create: `tests/integration/cleanup/test_definition.py`

**Depends on:** Task 1, 2, 3

- [ ] **Step 1: Write the test file**

`tests/integration/cleanup/test_definition.py`:

```python
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
```

- [ ] **Step 2: Run the cleanup tests**

```bash
pytest tests/integration/cleanup/test_definition.py -v
```

Expected: all 2 tests pass.

- [ ] **Step 3: Commit**

```bash
git add tests/integration/cleanup/test_definition.py
git commit -m "test: add cleanup integration tests (2 tests)"
```

---

### Task 10: Run full suite and verify

- [ ] **Step 1: Run all unit tests**

```bash
pytest tests/unit/ -v
```

Expected: all 134 existing tests pass.

- [ ] **Step 2: Run all integration tests**

```bash
pytest tests/integration/ -v
```

Expected: all 22 integration tests pass.

- [ ] **Step 3: Run entire test suite**

```bash
pytest tests/ -v
```

Expected: 156 total tests pass (134 unit + 22 integration).

- [ ] **Step 4: Commit any final fixes**

If any tests required adjustments, commit the fixes:

```bash
git add -A
git commit -m "test: fix integration test issues found during full run"
```
