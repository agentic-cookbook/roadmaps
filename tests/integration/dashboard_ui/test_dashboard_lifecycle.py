"""Playwright test: verify dashboard UI renders correctly during /implement-roadmap lifecycle.

Drives state changes via the REST API and confirms both the overview page
and detail page update visually through the polling mechanism.
"""

import re
import uuid

import pytest
from playwright.sync_api import expect

POLL_MS = 1000
POLL_TIMEOUT = 8000  # max wait for polled UI update


class TestImplementRoadmapDashboardLifecycle:
    """End-to-end: overview card → detail page → step progression → completion."""

    def test_full_lifecycle(self, dashboard_server, page):
        ds = dashboard_server
        rid = str(uuid.uuid4())
        poll = f"?poll={POLL_MS}"

        # --- 1. Create roadmap with 3 steps via API ---
        ds.cli.create_roadmap("PlaywrightTest", id=rid, status="running")
        ds.cli.set_steps(rid, [
            {"number": 1, "description": "Create GitHub Issues",
             "status": "not_started", "step_type": "Auto", "complexity": "S"},
            {"number": 2, "description": "Implement widget",
             "status": "not_started", "step_type": "Auto", "complexity": "M"},
            {"number": 3, "description": "Create & Review Feature PR",
             "status": "not_started", "step_type": "Auto", "complexity": "M"},
        ])

        # --- 2. Overview: verify card appears ---
        page.goto(f"{ds.url}/{poll}")
        card = page.locator(".roadmap-card").first
        expect(card).to_be_visible(timeout=POLL_TIMEOUT)
        expect(card.locator(".card-name")).to_have_text("PlaywrightTest")
        expect(card.locator(".progress-text")).to_contain_text("0/3")

        # --- 3. Overview: click the card to navigate to detail ---
        card.click()
        expect(page).to_have_url(f"{ds.url}/roadmap/{rid}")

        # --- 4. Detail: verify initial state ---
        # Navigate with poll param for polling mode (instead of SSE)
        page.goto(f"{ds.url}/roadmap/{rid}{poll}")
        expect(page.locator("#title")).to_contain_text("PlaywrightTest", timeout=POLL_TIMEOUT)
        steps = page.locator("#steps .step")
        expect(steps).to_have_count(3, timeout=POLL_TIMEOUT)
        expect(page.locator("#progress-label")).to_contain_text("0 / 3")

        # --- 5. API: begin step 1 ---
        ds.cli.begin_step(rid, 1)

        # --- 6. Detail: step 1 shows In Progress (spinner, step-active class) ---
        step1 = steps.nth(0)
        expect(step1).to_have_class(re.compile(r"step-active"), timeout=POLL_TIMEOUT)

        # --- 7. API: finish step 1 ---
        ds.cli.finish_step(rid, 1)

        # --- 8. Detail: step 1 Complete (✓ icon), progress 1/3 ---
        # Completed steps show ✓ icon and lose the step-active class
        expect(step1.locator(".step-icon")).to_have_text("\u2713", timeout=POLL_TIMEOUT)
        expect(page.locator("#progress-label")).to_contain_text("1 / 3", timeout=POLL_TIMEOUT)
        expect(page.locator("#progress-pct")).to_contain_text("33%", timeout=POLL_TIMEOUT)

        # --- 9. API: steps 2 and 3 ---
        ds.cli.begin_step(rid, 2)
        ds.cli.finish_step(rid, 2)

        # --- 10. Detail: progress 2/3 ---
        expect(page.locator("#progress-label")).to_contain_text("2 / 3", timeout=POLL_TIMEOUT)

        ds.cli.begin_step(rid, 3)
        ds.cli.finish_step(rid, 3)

        # --- 12. Detail: progress 3/3 ---
        expect(page.locator("#progress-label")).to_contain_text("3 / 3", timeout=POLL_TIMEOUT)
        expect(page.locator("#progress-pct")).to_contain_text("100%", timeout=POLL_TIMEOUT)

        # --- 13. API: complete roadmap ---
        ds.cli.complete(rid)

        # --- 14. Detail: status badge shows COMPLETE ---
        expect(page.locator("#status-badge")).to_contain_text("COMPLETE", timeout=POLL_TIMEOUT)

        # --- 15. Navigate back to overview ---
        page.goto(f"{ds.url}/{poll}")

        # --- 16. Overview: card shows Complete ---
        card = page.locator(".roadmap-card").first
        expect(card.locator(".progress-text")).to_contain_text("3/3", timeout=POLL_TIMEOUT)
        expect(card.locator(".card-badges")).to_contain_text("Complete", timeout=POLL_TIMEOUT)
