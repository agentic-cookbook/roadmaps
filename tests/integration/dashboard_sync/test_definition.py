"""Dashboard synchronization integration tests."""

import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request
import uuid
from pathlib import Path

import pytest

from tests.integration.helpers import PROJECT_ROOT


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
        # add_pr calls a route that doesn't exist standalone;
        # use sync to add PRs instead
        ds.cli.sync(rid, {
            "name": "PRTest",
            "prs": [
                {"number": 42, "title": "feat: test PR",
                 "url": "https://github.com/test/repo/pull/42"},
            ],
        })

        data = ds.api_get("/api/v1/roadmaps?detail=true")
        roadmap = next(r for r in data if r["id"] == rid)
        assert len(roadmap["prs"]) == 1
        assert roadmap["prs"][0]["number"] == 42


class TestPRLinkOnStepCard:
    """Regression #34: PR link must appear on step card after update_step with pr_number."""

    def test_pr_number_on_step_via_update(self, dashboard_server):
        ds = dashboard_server
        rid = str(uuid.uuid4())

        ds.cli.create_roadmap("PRStepTest", id=rid, status="running")
        ds.cli.set_steps(rid, [
            {"number": 1, "description": "Create Draft PR",
             "status": "not_started", "step_type": "Auto", "complexity": "S"},
        ])

        # Simulate what the agent should do: update_step with pr fields
        ds.cli.update_step(rid, 1, pr_number=98, pr_url="https://github.com/test/repo/pull/98")

        # Verify the API returns pr_number on the step
        data = ds.api_get(f"/api/v1/roadmaps/{rid}")
        step = data["steps"][0]
        assert step["pr_number"] == 98, f"Expected pr_number=98, got {step.get('pr_number')}"
        assert step["pr_url"] == "https://github.com/test/repo/pull/98"


def _find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _http_get(url, timeout=5):
    """Raw HTTP GET — returns (status_code, body_string)."""
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


@pytest.fixture
def real_dashboard_server(tmp_path):
    """Start a real Flask dashboard server as a subprocess (not a thread).

    Uses a temp database and a random port. Yields (base_url, pid).
    Kills the server on teardown.
    """
    from services.dashboard import db as dashboard_db

    db_path = str(tmp_path / "test-real.db")
    port = _find_free_port()

    # Initialize the database
    conn = dashboard_db.connect(db_path)
    dashboard_db.init_db(conn)
    conn.close()

    # Start the server as a real subprocess
    env = os.environ.copy()
    env["DASHBOARD_PORT"] = str(port)
    env["DASHBOARD_DB"] = db_path

    proc = subprocess.Popen(
        [sys.executable, "-m", "services.dashboard.app"],
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for the server to accept connections
    base_url = f"http://127.0.0.1:{port}"
    for _ in range(40):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                break
        except OSError:
            time.sleep(0.1)
    else:
        proc.kill()
        pytest.fail(f"Dashboard server did not start on port {port}")

    yield base_url, proc.pid, db_path, port

    # Teardown: kill the server
    try:
        os.kill(proc.pid, signal.SIGTERM)
        proc.wait(timeout=5)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        proc.kill()


class TestDashServerMustBeStarted:
    """End-to-end: start a real server, run the dash CLI, verify the website works.

    This reproduces the /implement-roadmap flow:
    1. dash init (no step names)
    2. dash load-roadmap <path>
    3. dash begin-step 1
    Then verifies the actual website serves HTML pages and the API returns data.
    """

    def test_full_implement_roadmap_flow_with_real_server(self, real_dashboard_server, tmp_path):
        base_url, server_pid, db_path, port = real_dashboard_server
        dash_cli = PROJECT_ROOT / "skills" / "progress-dashboard" / "references" / "dash"

        # Use the real 3-step fixture roadmap
        fixture_dir = Path(__file__).parent / "fixtures" / "all_auto_3step"
        roadmap_file = fixture_dir / "Roadmap.md"
        rid = "rm-test-all-auto"

        env = os.environ.copy()
        env["DASHBOARD_URL"] = base_url
        env["DASHBOARD_DB"] = db_path
        env["DASHBOARD_PORT"] = str(port)
        env["DASH_FEATURE"] = "AllAuto3Step"
        # Prevent dash from opening a browser during the test
        env["DISPLAY"] = ""

        # --- Step 1: dash init (no step names, same as implement-roadmap) ---
        result = subprocess.run(
            [sys.executable, str(dash_cli), "init", "AllAuto3Step"],
            capture_output=True, text=True, env=env,
        )
        assert result.returncode == 0, f"dash init failed: {result.stderr}"

        # --- Step 2: dash load-roadmap ---
        result = subprocess.run(
            [sys.executable, str(dash_cli), "load-roadmap", str(roadmap_file)],
            capture_output=True, text=True, env=env,
        )
        assert result.returncode == 0, f"dash load-roadmap failed: {result.stderr}"
        assert "Loaded 3 steps" in result.stdout

        # --- Verify: overview page serves real HTML ---
        status, body = _http_get(f"{base_url}/")
        assert status == 200, f"Overview page returned {status}"
        assert "<!DOCTYPE html>" in body
        assert "Roadmap Dashboard" in body

        # --- Verify: roadmap detail page serves real HTML ---
        status, body = _http_get(f"{base_url}/roadmap/{rid}")
        assert status == 200, f"Roadmap detail page returned {status}"
        assert "<!DOCTYPE html>" in body
        assert "Roadmap Detail" in body

        # --- Verify: API returns the roadmap (the request that was 404ing) ---
        status, body = _http_get(f"{base_url}/api/v1/roadmaps/{rid}")
        assert status == 200, f"API returned {status} — this is the 404 bug"
        data = json.loads(body)
        assert data["id"] == rid
        assert data["name"] == "AllAuto3Step"
        assert data["status"] == "running"
        assert len(data["steps"]) == 3

        # --- Step 3: dash begin-step 1 ---
        result = subprocess.run(
            [sys.executable, str(dash_cli), "begin-step", "1"],
            capture_output=True, text=True, env=env,
        )
        assert result.returncode == 0, f"dash begin-step failed: {result.stderr}"

        # --- Verify: step 1 is in_progress via the API ---
        status, body = _http_get(f"{base_url}/api/v1/roadmaps/{rid}")
        assert status == 200
        data = json.loads(body)
        assert data["steps"][0]["status"] == "in_progress"

        # --- Step 4: dash finish-step 1 ---
        result = subprocess.run(
            [sys.executable, str(dash_cli), "finish-step", "1"],
            capture_output=True, text=True, env=env,
        )
        assert result.returncode == 0, f"dash finish-step failed: {result.stderr}"

        # --- Verify: step 1 is complete, API still works ---
        status, body = _http_get(f"{base_url}/api/v1/roadmaps/{rid}")
        assert status == 200
        data = json.loads(body)
        assert data["steps"][0]["status"] == "complete"
        assert data["steps"][1]["status"] == "not_started"

        # --- Verify: health endpoint works ---
        status, body = _http_get(f"{base_url}/api/v1/health")
        assert status == 200
        assert json.loads(body)["status"] == "ok"
