#!/usr/bin/env python3
"""Demo: watch the dashboard update in real time during a simulated /implement-roadmap run.

Starts a dashboard server on port 9888, opens a browser, and walks through
the full roadmap lifecycle with realistic timing so you can watch the
overview and detail pages update via polling.

Usage:
    python3 tests/integration/dashboard_ui/demo.py
"""

import os
import signal
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import dashboard_client


DEMO_PORT = 9888
POLL_MS = 1500
STEP_PAUSE = 3       # seconds to hold on each state change
TRANSITION_PAUSE = 2  # seconds between begin/finish of a step


def log(msg):
    print(f"  ▸ {msg}")


def start_server(db_path):
    from services.dashboard import db as dashboard_db

    conn = dashboard_db.connect(db_path)
    dashboard_db.init_db(conn)
    conn.close()

    env = os.environ.copy()
    env["DASHBOARD_PORT"] = str(DEMO_PORT)
    env["DASHBOARD_DB"] = db_path

    proc = subprocess.Popen(
        [sys.executable, "-m", "services.dashboard.app"],
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    for _ in range(40):
        try:
            with socket.create_connection(("127.0.0.1", DEMO_PORT), timeout=0.5):
                break
        except OSError:
            time.sleep(0.1)
    else:
        proc.kill()
        print("ERROR: Dashboard server did not start")
        sys.exit(1)

    return proc


def run_demo():
    from playwright.sync_api import sync_playwright

    # --- Start server ---
    db_path = f"/tmp/dashboard-demo-{os.getpid()}.db"
    base_url = f"http://127.0.0.1:{DEMO_PORT}"
    poll = f"?poll={POLL_MS}"

    log("Starting dashboard server on port 9888...")
    proc = start_server(db_path)

    cli = dashboard_client.DashboardClient(base_url=base_url)
    rid = str(uuid.uuid4())

    try:
        # --- Create roadmap ---
        log("Creating roadmap with 5 steps...")
        cli.create_roadmap("DemoFeature", id=rid, status="running")
        cli.set_steps(rid, [
            {"number": 1, "description": "Create GitHub Issues",
             "status": "not_started", "step_type": "Auto", "complexity": "S"},
            {"number": 2, "description": "Add authentication middleware",
             "status": "not_started", "step_type": "Auto", "complexity": "M"},
            {"number": 3, "description": "Build user settings page",
             "status": "not_started", "step_type": "Auto", "complexity": "L"},
            {"number": 4, "description": "Write integration tests",
             "status": "not_started", "step_type": "Auto", "complexity": "M"},
            {"number": 5, "description": "Create & Review Feature PR",
             "status": "not_started", "step_type": "Auto", "complexity": "M"},
        ])

        # --- Open browser ---
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            # --- Overview ---
            log("Opening overview page...")
            page.goto(f"{base_url}/{poll}")
            time.sleep(STEP_PAUSE)

            # --- Click through to detail ---
            log("Clicking through to detail page...")
            page.locator(".roadmap-card").first.click()
            page.goto(page.url + poll)  # add poll param
            time.sleep(STEP_PAUSE)

            # --- Walk through each step ---
            for step_num in range(1, 6):
                step_name = ["Create GitHub Issues",
                             "Add authentication middleware",
                             "Build user settings page",
                             "Write integration tests",
                             "Create & Review Feature PR"][step_num - 1]

                log(f"Step {step_num}: {step_name} — starting...")
                cli.begin_step(rid, step_num)
                time.sleep(TRANSITION_PAUSE)

                log(f"Step {step_num}: {step_name} — complete ✓")
                cli.finish_step(rid, step_num)
                time.sleep(STEP_PAUSE)

            # --- Complete ---
            log("Marking roadmap complete...")
            cli.complete(rid)
            time.sleep(STEP_PAUSE)

            # --- Back to overview ---
            log("Returning to overview...")
            page.goto(f"{base_url}/{poll}")
            time.sleep(STEP_PAUSE)

            log("Demo complete. Closing in 3 seconds...")
            time.sleep(3)
            browser.close()

    finally:
        # Clean up
        try:
            os.kill(proc.pid, signal.SIGTERM)
            proc.wait(timeout=5)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            proc.kill()
        try:
            os.unlink(db_path)
        except OSError:
            pass


if __name__ == "__main__":
    print()
    print("  ╔══════════════════════════════════════════╗")
    print("  ║  Dashboard Demo — /implement-roadmap     ║")
    print("  ╚══════════════════════════════════════════╝")
    print()
    run_demo()
    print()
