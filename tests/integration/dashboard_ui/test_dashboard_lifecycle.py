"""Playwright test: verify dashboard UI renders correctly during /implement-roadmap lifecycle.

Drives state changes via the REST API and confirms both the overview page
and detail page update visually through the polling mechanism.

Screenshots are saved to /tmp/dashboard-screenshots/test/ at each key state
for comparison with the demo script's screenshots.
"""

import re
import uuid

import pytest
from playwright.sync_api import expect

POLL_MS = 1000
POLL_TIMEOUT = 8000  # max wait for polled UI update
SCREENSHOT_DIR = "/tmp/dashboard-screenshots/test"

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


def screenshot(page, name):
    import os
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    page.screenshot(path=f"{SCREENSHOT_DIR}/{name}.png", full_page=True)


class TestImplementRoadmapDashboardLifecycle:
    """End-to-end: overview card → detail page → step progression → completion."""

    def test_full_lifecycle(self, dashboard_server, page):
        ds = dashboard_server
        rid = str(uuid.uuid4())
        poll = f"?poll={POLL_MS}"
        n = len(STEPS)

        # --- 1. Create roadmap with steps via API ---
        ds.cli.create_roadmap("DemoFeature", id=rid, status="running")
        ds.cli.set_steps(rid, STEPS)

        # --- 2. Overview: verify card appears ---
        page.goto(f"{ds.url}/{poll}")
        card = page.locator(".roadmap-card").first
        expect(card).to_be_visible(timeout=POLL_TIMEOUT)
        expect(card.locator(".card-name")).to_have_text("DemoFeature")
        expect(card.locator(".progress-text")).to_contain_text(f"0/{n}")
        screenshot(page, "01-overview-initial")

        # --- 3. Overview: click the card to navigate to detail ---
        card.click()
        expect(page).to_have_url(f"{ds.url}/roadmap/{rid}")

        # --- 4. Detail: verify initial state ---
        page.goto(f"{ds.url}/roadmap/{rid}{poll}")
        expect(page.locator("#title")).to_contain_text("DemoFeature", timeout=POLL_TIMEOUT)
        steps = page.locator("#steps .step")
        expect(steps).to_have_count(n, timeout=POLL_TIMEOUT)
        expect(page.locator("#progress-label")).to_contain_text(f"0 / {n}")

        # Verify each step description is visible
        for i, name in enumerate(STEP_NAMES):
            expect(steps.nth(i)).to_contain_text(name, timeout=POLL_TIMEOUT)
        screenshot(page, "02-detail-initial")

        # --- 5. Step 1: Create Draft PR — begin + register PR + finish ---
        ds.cli.begin_step(rid, 1)
        step1 = steps.nth(0)
        expect(step1).to_have_class(re.compile(r"step-active"), timeout=POLL_TIMEOUT)

        # Simulate: PR created, registered on step 1 (update_step sets pr fields)
        ds.cli.update_step(rid, 1, pr_number=42, pr_url="https://github.com/test/repo/pull/42")
        ds.cli.finish_step(rid, 1)

        expect(step1.locator(".step-icon")).to_have_text("\u2713", timeout=POLL_TIMEOUT)

        # Verify PR link appears on step 1
        expect(step1).to_contain_text("PR #42", timeout=POLL_TIMEOUT)
        screenshot(page, "03-step1-pr-link")

        # --- 6-8. Steps 2-4: standard implementation ---
        for step_num in range(2, n):
            step_el = steps.nth(step_num - 1)

            ds.cli.begin_step(rid, step_num)
            expect(step_el).to_have_class(
                re.compile(r"step-active"), timeout=POLL_TIMEOUT
            )
            screenshot(page, f"03-step{step_num}-active")

            ds.cli.finish_step(rid, step_num)
            expect(step_el.locator(".step-icon")).to_have_text(
                "\u2713", timeout=POLL_TIMEOUT
            )
            expect(page.locator("#progress-label")).to_contain_text(
                f"{step_num} / {n}", timeout=POLL_TIMEOUT
            )
            screenshot(page, f"04-step{step_num}-complete")

        # --- 9. Step 5: Finalize & Merge PR ---
        ds.cli.begin_step(rid, n)
        ds.cli.finish_step(rid, n)
        expect(page.locator("#progress-label")).to_contain_text(
            f"{n} / {n}", timeout=POLL_TIMEOUT
        )
        screenshot(page, f"04-step{n}-complete")

        # --- 10. Complete roadmap ---
        ds.cli.complete(rid)

        # --- 11. Detail: status badge shows COMPLETE ---
        expect(page.locator("#status-badge")).to_contain_text("COMPLETE", timeout=POLL_TIMEOUT)
        screenshot(page, "05-detail-complete")

        # --- 12. Navigate back to overview ---
        page.goto(f"{ds.url}/{poll}")

        # --- 13. Overview: card shows Complete with PR link ---
        card = page.locator(".roadmap-card").first
        expect(card.locator(".progress-text")).to_contain_text(f"{n}/{n}", timeout=POLL_TIMEOUT)
        expect(card.locator(".card-badges")).to_contain_text("Complete", timeout=POLL_TIMEOUT)
        screenshot(page, "06-overview-complete")
