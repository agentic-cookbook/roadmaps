"""Fixtures for Playwright dashboard UI tests."""

import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request

import pytest

from tests.integration.helpers import PROJECT_ROOT

sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
import dashboard_client


def _find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def dashboard_server(tmp_path_factory):
    """Start a real Flask dashboard server for UI testing.

    Module-scoped so the server is shared across all tests in the file.
    """
    from services.dashboard import db as dashboard_db

    tmp_path = tmp_path_factory.mktemp("dashboard_ui")
    db_path = str(tmp_path / "test-ui.db")
    port = _find_free_port()

    conn = dashboard_db.connect(db_path)
    dashboard_db.init_db(conn)
    conn.close()

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

    client = dashboard_client.DashboardClient(base_url=base_url)

    class ServerInfo:
        url = base_url
        cli = client
        pid = proc.pid

    yield ServerInfo()

    try:
        os.kill(proc.pid, signal.SIGTERM)
        proc.wait(timeout=5)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        proc.kill()
