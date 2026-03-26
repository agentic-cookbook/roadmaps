#!/usr/bin/env python3
"""Demo: watch the dashboard update in real time during a simulated /implement-roadmap run.

Starts a dashboard server on port 9888, opens a browser, and walks through
the full roadmap lifecycle with realistic timing so you can watch the
overview and detail pages update via polling.

Every transition waits for the UI to actually render the change (via
Playwright assertions) before pausing for the developer to see it.

Usage:
    python3 tests/integration/dashboard_ui/demo.py
"""

import os
import re
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
POLL_MS = 1000
HOLD = 2  # seconds to hold after content is confirmed visible
WAIT_TIMEOUT = 10000  # ms for Playwright expect() to find content
SCREENSHOT_DIR = "/tmp/dashboard-screenshots/demo"


STEPS = [
    "Create Draft PR",
    "Add authentication middleware",
    "Build user settings page",
    "Write integration tests",
    "Finalize & Merge PR",
]


def log(msg):
    print(f"  ▸ {msg}")


def screenshot(page, name):
    path = f"{SCREENSHOT_DIR}/{name}.png"
    page.screenshot(path=path, full_page=True)
    log(f"  📸 {name}.png")


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
    from playwright.sync_api import sync_playwright, expect

    db_path = f"/tmp/dashboard-demo-{os.getpid()}.db"
    base_url = f"http://127.0.0.1:{DEMO_PORT}"
    poll = f"?poll={POLL_MS}"
    n = len(STEPS)

    log("Starting dashboard server on port 9888...")
    proc = start_server(db_path)

    cli = dashboard_client.DashboardClient(base_url=base_url)
    rid = str(uuid.uuid4())

    try:
        # --- Create roadmap with steps ---
        log(f"Creating roadmap with {n} steps...")
        cli.create_roadmap("DemoFeature", id=rid, status="running")
        cli.set_steps(rid, [
            {"number": i + 1, "description": name,
             "status": "not_started", "step_type": "Auto",
             "complexity": ["S", "M", "L", "M", "M"][i]}
            for i, name in enumerate(STEPS)
        ])

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            # ── OVERVIEW ──────────────────────────────────────
            log("Overview: waiting for card to render...")
            page.goto(f"{base_url}/{poll}")

            card = page.locator(".roadmap-card").first
            expect(card).to_be_visible(timeout=WAIT_TIMEOUT)
            expect(card.locator(".card-name")).to_have_text("DemoFeature", timeout=WAIT_TIMEOUT)
            expect(card.locator(".progress-text")).to_contain_text(f"0/{n}", timeout=WAIT_TIMEOUT)
            log(f"Overview: card visible — DemoFeature, 0/{n} steps")
            screenshot(page, "01-overview-initial")
            time.sleep(HOLD)

            # ── NAVIGATE TO DETAIL ────────────────────────────
            log("Clicking card → detail page...")
            card.click()
            # Reload with poll param so we use polling instead of SSE
            page.goto(f"{base_url}/roadmap/{rid}{poll}")

            # Wait for all steps to render with their descriptions
            expect(page.locator("#title")).to_contain_text("DemoFeature", timeout=WAIT_TIMEOUT)
            steps_loc = page.locator("#steps .step")
            expect(steps_loc).to_have_count(n, timeout=WAIT_TIMEOUT)
            expect(page.locator("#progress-label")).to_contain_text(f"0 / {n}", timeout=WAIT_TIMEOUT)

            # Verify each step description is visible
            for i, name in enumerate(STEPS):
                expect(steps_loc.nth(i)).to_contain_text(name, timeout=WAIT_TIMEOUT)

            log(f"Detail: {n} steps loaded, all descriptions visible")
            screenshot(page, "02-detail-initial")
            time.sleep(HOLD)

            # ── STEP-BY-STEP PROGRESSION ──────────────────────
            for step_num in range(1, n + 1):
                name = STEPS[step_num - 1]
                step_el = steps_loc.nth(step_num - 1)

                # Begin step
                log(f"Step {step_num}/{n}: {name} — starting...")
                cli.begin_step(rid, step_num)

                # Wait for spinner (step-active class) to appear
                expect(step_el).to_have_class(
                    re.compile(r"step-active"), timeout=WAIT_TIMEOUT
                )
                log(f"Step {step_num}/{n}: spinner visible ⟳")
                screenshot(page, f"03-step{step_num}-active")
                time.sleep(HOLD)

                # Finish step
                cli.finish_step(rid, step_num)

                # Wait for checkmark icon
                expect(step_el.locator(".step-icon")).to_have_text(
                    "\u2713", timeout=WAIT_TIMEOUT
                )
                # Wait for progress to update
                expect(page.locator("#progress-label")).to_contain_text(
                    f"{step_num} / {n}", timeout=WAIT_TIMEOUT
                )
                pct = round(100 * step_num / n)
                log(f"Step {step_num}/{n}: {name} — complete ✓  ({pct}%)")
                screenshot(page, f"04-step{step_num}-complete")
                time.sleep(HOLD)

            # ── COMPLETE ──────────────────────────────────────
            log("Marking roadmap complete...")
            cli.complete(rid)

            expect(page.locator("#status-badge")).to_contain_text(
                "COMPLETE", timeout=WAIT_TIMEOUT
            )
            log("Detail: COMPLETE badge visible")
            screenshot(page, "05-detail-complete")
            time.sleep(HOLD)

            # ── BACK TO OVERVIEW ──────────────────────────────
            log("Returning to overview...")
            page.goto(f"{base_url}/{poll}")

            card = page.locator(".roadmap-card").first
            expect(card.locator(".progress-text")).to_contain_text(
                f"{n}/{n}", timeout=WAIT_TIMEOUT
            )
            expect(card.locator(".card-badges")).to_contain_text(
                "Complete", timeout=WAIT_TIMEOUT
            )
            log(f"Overview: card shows Complete, {n}/{n} steps")
            screenshot(page, "06-overview-complete")
            time.sleep(HOLD + 1)

            log("Demo complete.")
            time.sleep(2)
            browser.close()

    finally:
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
