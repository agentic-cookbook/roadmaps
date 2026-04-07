"""Shared fixtures for integration tests against roadmaps-tests repo."""

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

from tests.integration.helpers import (
    _run_git,
    _run_gh,
    COORDINATOR,
    PROJECT_ROOT,
    TEST_REPO_PATH,
    TEST_REPO_REMOTE,
    WORKTREE_DIR,
)

# Add project paths
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from services.dashboard import db
from services.dashboard.app import create_app


# ---------------------------------------------------------------------------
# Helpers (local to conftest)
# ---------------------------------------------------------------------------

def _find_free_port():
    """Find an available TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


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

    # Ensure worktree output dir exists
    WORKTREE_DIR.mkdir(parents=True, exist_ok=True)

    # Verify remote
    result = _run_git(["remote", "get-url", "origin"], cwd=TEST_REPO_PATH)
    remote = result.stdout.strip()
    if "roadmaps-tests" not in remote:
        pytest.skip(f"Test repo remote is {remote}, expected roadmaps-tests")

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
    """Fixture factory. Returns a callable that copies a fixture roadmap into the test repo."""
    def _copy(fixture_relpath, issue_map=None):
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
        cwd = str(Path(roadmap_path).resolve().parent.parent.parent)
        result = subprocess.run(
            [sys.executable, str(COORDINATOR), "next-step", roadmap_path],
            capture_output=True, text=True, cwd=cwd,
        )
        if result.returncode != 0:
            raise RuntimeError(f"coordinator next-step failed: {result.stderr}")
        return json.loads(result.stdout)

    def resolve(self, feature_name, cwd):
        result = subprocess.run(
            [sys.executable, str(COORDINATOR), "resolve", feature_name],
            capture_output=True, text=True, cwd=str(cwd),
        )
        if result.returncode != 0:
            raise RuntimeError(f"coordinator resolve failed: {result.stderr}")
        return json.loads(result.stdout)

    def summary(self, roadmap_path):
        cwd = str(Path(roadmap_path).resolve().parent.parent.parent)
        result = subprocess.run(
            [sys.executable, str(COORDINATOR), "summary", roadmap_path],
            capture_output=True, text=True, cwd=cwd,
        )
        if result.returncode != 0:
            raise RuntimeError(f"coordinator summary failed: {result.stderr}")
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
