"""Playwright test: verify dashboard UI renders correctly during /implement-roadmap lifecycle.

Drives state changes via the REST API and confirms both the overview page
and detail page update visually through the polling mechanism.

Opens TWO browser tabs — overview and detail — so both are visible
simultaneously during headed runs.

Screenshots are saved to /tmp/dashboard-screenshots/test/ at each key state.
"""

import json
import re
import uuid
from pathlib import Path

import pytest
from playwright.sync_api import expect

POLL_MS = 1000
POLL_TIMEOUT = 8000  # max wait for polled UI update
SCREENSHOT_DIR = "/tmp/dashboard-screenshots/test"
COUNTER_FILE = Path(__file__).parent / ".test-run-counter"

STEPS = [
    {"number": 1, "description": "Create Draft PR",
     "status": "not_started", "step_type": "Auto", "complexity": "S"},
    {"number": 2, "description": "Add authentication middleware",
     "status": "not_started", "step_type": "Auto", "complexity": "M"},
    {"number": 3, "description": "Build user settings page",
     "status": "not_started", "step_type": "Auto", "complexity": "L"},
    {"number": 4, "description": "Write integration tests",
     "status": "not_started", "step_type": "Auto", "complexity": "M"},
    {"number": 5, "description": "Finalize & Merge PR",
     "status": "not_started", "step_type": "Auto", "complexity": "M"},
]

STEP_NAMES = [s["description"] for s in STEPS]


def _next_test_number():
    """Read and increment a persisted test run counter."""
    try:
        n = int(COUNTER_FILE.read_text().strip())
    except (FileNotFoundError, ValueError):
        n = 0
    n += 1
    COUNTER_FILE.write_text(str(n))
    return n


def screenshot(page, name):
    import os
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    page.screenshot(path=f"{SCREENSHOT_DIR}/{name}.png", full_page=True)


class TestImplementRoadmapDashboardLifecycle:
    """End-to-end: overview + detail pages open simultaneously, step progression → completion.

    Fixes #28: overview progress increments during test
    Fixes #29: detail page uses ?poll= to avoid SSE error
    Fixes #30: descriptive name with persisted test number
    """

    def test_full_lifecycle(self, dashboard_server, context):
        ds = dashboard_server
        rid = str(uuid.uuid4())
        poll = f"?poll={POLL_MS}"
        n = len(STEPS)
        test_num = _next_test_number()
        roadmap_name = f"Dashboard Lifecycle Test #{test_num}"

        # --- 1. Create roadmap with steps via API ---
        ds.cli.create_roadmap(roadmap_name, id=rid, status="running")
        ds.cli.set_steps(rid, STEPS)

        # --- 2. Open overview page in tab 1 ---
        overview = context.new_page()
        overview.goto(f"{ds.url}/{poll}")
        card = overview.locator(".roadmap-card").first
        expect(card).to_be_visible(timeout=POLL_TIMEOUT)
        expect(card.locator(".card-name")).to_have_text(roadmap_name)
        expect(card.locator(".progress-text")).to_contain_text(f"0/{n}")
        screenshot(overview, "01-overview-initial")

        # --- 3. Open detail page in tab 2 (with poll param) ---
        detail = context.new_page()
        detail.goto(f"{ds.url}/roadmap/{rid}{poll}")
        expect(detail.locator("#title")).to_contain_text(roadmap_name, timeout=POLL_TIMEOUT)
        steps = detail.locator("#steps .step")
        expect(steps).to_have_count(n, timeout=POLL_TIMEOUT)
        expect(detail.locator("#progress-label")).to_contain_text(f"0 / {n}")

        # Verify each step description is visible
        for i, name in enumerate(STEP_NAMES):
            expect(steps.nth(i)).to_contain_text(name, timeout=POLL_TIMEOUT)
        screenshot(detail, "02-detail-initial")

        # --- 4. Step 1: Create Draft PR ---
        ds.cli.begin_step(rid, 1)
        step1 = steps.nth(0)
        expect(step1).to_have_class(re.compile(r"step-active"), timeout=POLL_TIMEOUT)

        # Simulate: PR created, registered on step 1
        ds.cli.update_step(rid, 1, pr_number=42, pr_url="https://github.com/test/repo/pull/42")
        ds.cli.finish_step(rid, 1)

        expect(step1.locator(".step-icon")).to_have_text("\u2713", timeout=POLL_TIMEOUT)
        expect(step1).to_contain_text("PR #42", timeout=POLL_TIMEOUT)
        screenshot(detail, "03-step1-pr-link")

        # Verify overview updates (#28)
        expect(card.locator(".progress-text")).to_contain_text(f"1/{n}", timeout=POLL_TIMEOUT)
        screenshot(overview, "04-overview-after-step1")

        # --- 5-7. Steps 2-4: standard implementation ---
        for step_num in range(2, n):
            step_el = steps.nth(step_num - 1)

            ds.cli.begin_step(rid, step_num)
            expect(step_el).to_have_class(
                re.compile(r"step-active"), timeout=POLL_TIMEOUT
            )
            screenshot(detail, f"05-step{step_num}-active")

            ds.cli.finish_step(rid, step_num)
            expect(step_el.locator(".step-icon")).to_have_text(
                "\u2713", timeout=POLL_TIMEOUT
            )
            expect(detail.locator("#progress-label")).to_contain_text(
                f"{step_num} / {n}", timeout=POLL_TIMEOUT
            )
            screenshot(detail, f"06-step{step_num}-complete")

        # Verify overview shows 4/5 (#28)
        expect(card.locator(".progress-text")).to_contain_text(f"{n-1}/{n}", timeout=POLL_TIMEOUT)
        screenshot(overview, "07-overview-after-step4")

        # --- 8. Step 5: Finalize & Merge PR ---
        ds.cli.begin_step(rid, n)
        ds.cli.finish_step(rid, n)
        expect(detail.locator("#progress-label")).to_contain_text(
            f"{n} / {n}", timeout=POLL_TIMEOUT
        )
        screenshot(detail, f"08-step{n}-complete")

        # --- 9. Complete roadmap ---
        ds.cli.complete(rid)

        # --- 10. Detail: status badge shows COMPLETE ---
        expect(detail.locator("#status-badge")).to_contain_text("COMPLETE", timeout=POLL_TIMEOUT)
        screenshot(detail, "09-detail-complete")

        # --- 11. Overview: card shows Complete (#28) ---
        expect(card.locator(".progress-text")).to_contain_text(f"{n}/{n}", timeout=POLL_TIMEOUT)
        expect(card.locator(".card-badges")).to_contain_text("Complete", timeout=POLL_TIMEOUT)
        screenshot(overview, "10-overview-complete")

        # Clean up pages
        detail.close()
        overview.close()


class TestProgressUpdatesWithoutPollParam:
    """Detail page must show progress updates without ?poll= parameter.

    This tests the real-world path: the dash CLI opens the browser
    without ?poll=, relying on the default polling fallback.
    """

    def test_progress_increments_without_poll_param(self, dashboard_server, context):
        ds = dashboard_server
        rid = str(uuid.uuid4())
        n = 3

        ds.cli.create_roadmap("NoPollTest", id=rid, status="running")
        ds.cli.set_steps(rid, [
            {"number": i, "description": f"Step {i}",
             "status": "not_started", "step_type": "Auto", "complexity": "S"}
            for i in range(1, n + 1)
        ])

        # Open detail page WITHOUT ?poll= — the real-world case
        detail = context.new_page()
        detail.goto(f"{ds.url}/roadmap/{rid}")
        expect(detail.locator("#progress-label")).to_contain_text(
            f"0 / {n}", timeout=POLL_TIMEOUT
        )

        # Complete each step and verify progress updates
        for step_num in range(1, n + 1):
            ds.cli.begin_step(rid, step_num)
            ds.cli.finish_step(rid, step_num)
            expect(detail.locator("#progress-label")).to_contain_text(
                f"{step_num} / {n}", timeout=POLL_TIMEOUT
            )

        detail.close()
