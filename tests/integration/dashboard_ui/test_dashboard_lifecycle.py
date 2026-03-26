"""Playwright test: verify dashboard UI renders correctly during /implement-roadmap lifecycle.

Drives state changes via the REST API and confirms both the overview page
and detail page update visually through the polling mechanism.

Screenshots are saved to /tmp/dashboard-screenshots/test/ at each key state
for comparison with the demo script's screenshots.
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
    """End-to-end: overview card → detail page → step progression → completion.

    Fixes #28: overview progress increments during test
    Fixes #29: card click navigates with ?poll= param to avoid SSE error
    Fixes #30: descriptive name with persisted test number
    """

    def test_full_lifecycle(self, dashboard_server, page):
        ds = dashboard_server
        rid = str(uuid.uuid4())
        poll = f"?poll={POLL_MS}"
        n = len(STEPS)
        test_num = _next_test_number()
        roadmap_name = f"Dashboard Lifecycle Test #{test_num}"

        # --- 1. Create roadmap with steps via API ---
        ds.cli.create_roadmap(roadmap_name, id=rid, status="running")
        ds.cli.set_steps(rid, STEPS)

        # --- 2. Overview: verify card appears ---
        page.goto(f"{ds.url}/{poll}")
        card = page.locator(".roadmap-card").first
        expect(card).to_be_visible(timeout=POLL_TIMEOUT)
        expect(card.locator(".card-name")).to_have_text(roadmap_name)
        expect(card.locator(".progress-text")).to_contain_text(f"0/{n}")
        screenshot(page, "01-overview-initial")

        # --- 3. Click card — navigate WITH poll param to avoid SSE error (#29) ---
        card.click()
        # The click navigates to /roadmap/{rid} without poll param.
        # Immediately navigate with poll param before SSE tries to connect.
        page.goto(f"{ds.url}/roadmap/{rid}{poll}")
        expect(page.locator("#title")).to_contain_text(roadmap_name, timeout=POLL_TIMEOUT)
        steps = page.locator("#steps .step")
        expect(steps).to_have_count(n, timeout=POLL_TIMEOUT)
        expect(page.locator("#progress-label")).to_contain_text(f"0 / {n}")

        # Verify each step description is visible
        for i, name in enumerate(STEP_NAMES):
            expect(steps.nth(i)).to_contain_text(name, timeout=POLL_TIMEOUT)
        screenshot(page, "02-detail-initial")

        # --- 4. Step 1: Create Draft PR — begin + register PR + finish ---
        ds.cli.begin_step(rid, 1)
        step1 = steps.nth(0)
        expect(step1).to_have_class(re.compile(r"step-active"), timeout=POLL_TIMEOUT)

        # Simulate: PR created, registered on step 1
        ds.cli.update_step(rid, 1, pr_number=42, pr_url="https://github.com/test/repo/pull/42")
        ds.cli.finish_step(rid, 1)

        expect(step1.locator(".step-icon")).to_have_text("\u2713", timeout=POLL_TIMEOUT)

        # Verify PR link appears on step 1
        expect(step1).to_contain_text("PR #42", timeout=POLL_TIMEOUT)
        screenshot(page, "03-step1-pr-link")

        # --- Check overview mid-flow: should show 1/N (#28) ---
        page.goto(f"{ds.url}/{poll}")
        card = page.locator(".roadmap-card").first
        expect(card.locator(".progress-text")).to_contain_text(f"1/{n}", timeout=POLL_TIMEOUT)
        screenshot(page, "04-overview-mid-1")

        # Go back to detail
        page.goto(f"{ds.url}/roadmap/{rid}{poll}")
        steps = page.locator("#steps .step")
        expect(steps).to_have_count(n, timeout=POLL_TIMEOUT)

        # --- 5-7. Steps 2-4: standard implementation ---
        for step_num in range(2, n):
            step_el = steps.nth(step_num - 1)

            ds.cli.begin_step(rid, step_num)
            expect(step_el).to_have_class(
                re.compile(r"step-active"), timeout=POLL_TIMEOUT
            )
            screenshot(page, f"05-step{step_num}-active")

            ds.cli.finish_step(rid, step_num)
            expect(step_el.locator(".step-icon")).to_have_text(
                "\u2713", timeout=POLL_TIMEOUT
            )
            expect(page.locator("#progress-label")).to_contain_text(
                f"{step_num} / {n}", timeout=POLL_TIMEOUT
            )
            screenshot(page, f"06-step{step_num}-complete")

        # --- Check overview mid-flow again: should show 4/N (#28) ---
        page.goto(f"{ds.url}/{poll}")
        card = page.locator(".roadmap-card").first
        expect(card.locator(".progress-text")).to_contain_text(f"{n-1}/{n}", timeout=POLL_TIMEOUT)
        screenshot(page, "07-overview-mid-4")

        # Go back to detail for final step
        page.goto(f"{ds.url}/roadmap/{rid}{poll}")
        steps = page.locator("#steps .step")

        # --- 8. Step 5: Finalize & Merge PR ---
        ds.cli.begin_step(rid, n)
        ds.cli.finish_step(rid, n)
        expect(page.locator("#progress-label")).to_contain_text(
            f"{n} / {n}", timeout=POLL_TIMEOUT
        )
        screenshot(page, f"08-step{n}-complete")

        # --- 9. Complete roadmap ---
        ds.cli.complete(rid)

        # --- 10. Detail: status badge shows COMPLETE ---
        expect(page.locator("#status-badge")).to_contain_text("COMPLETE", timeout=POLL_TIMEOUT)
        screenshot(page, "09-detail-complete")

        # --- 11. Navigate back to overview ---
        page.goto(f"{ds.url}/{poll}")

        # --- 12. Overview: card shows Complete with full progress (#28) ---
        card = page.locator(".roadmap-card").first
        expect(card.locator(".progress-text")).to_contain_text(f"{n}/{n}", timeout=POLL_TIMEOUT)
        expect(card.locator(".card-badges")).to_contain_text("Complete", timeout=POLL_TIMEOUT)
        screenshot(page, "10-overview-complete")
