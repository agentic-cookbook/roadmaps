# Playwright Dashboard Verification Tests

**Date:** 2026-03-25
**Status:** Approved

## Goal

Add a Playwright-based integration test that verifies the dashboard UI renders correctly during the `/implement-roadmap` lifecycle. The test drives state changes via the REST API and confirms both the overview page and detail page update visually through the polling mechanism.

## Motivation

Existing dashboard integration tests (`tests/integration/dashboard_sync/`) validate API behavior only — they confirm the server returns correct JSON. No test currently verifies that the HTML pages render that data correctly in a browser. This test closes that gap.

## Design

### One End-to-End Test

A single test simulates the full `/implement-roadmap` dashboard lifecycle:

```
1.  API: create roadmap + bulk-create 3 steps
2.  OVERVIEW: verify card appears with name, "0/3 steps (0%)", Running badge
3.  OVERVIEW: click the card
4.  DETAIL: verify page loads with title, 3 steps listed, all Not Started
5.  API: begin-step 1
6.  DETAIL: wait for poll → step 1 shows In Progress, progress "0/3"
7.  API: finish-step 1
8.  DETAIL: wait for poll → step 1 shows Complete, progress "1/3 (33%)"
9.  API: begin-step 2 + finish-step 2
10. DETAIL: wait for poll → progress "2/3 (66%)"
11. API: begin-step 3 + finish-step 3
12. DETAIL: wait for poll → progress "3/3 (100%)"
13. API: complete roadmap
14. DETAIL: wait for poll → status badge shows Complete
15. Navigate back to overview
16. OVERVIEW: wait for poll → card shows Complete badge, "3/3 steps (100%)"
```

### Polling Interval Override

Both HTML pages (`overview.html`, `dashboard.html`) use `setInterval` for polling. A `?poll=<ms>` query parameter override is added so tests can set the interval to 1000ms (1s) instead of the default 10000ms. This tests the real polling path without 60s+ waits.

Implementation: ~3 lines per page — read `new URLSearchParams(location.search).get('poll')`, use it as the interval if present.

### Test Infrastructure

- **Dependency**: `pytest-playwright` (pip install). Provides `page` and `browser` fixtures.
- **Location**: `tests/integration/dashboard_ui/test_dashboard_lifecycle.py`
- **Server fixture**: Reuses the existing `real_dashboard_server` fixture from `tests/integration/dashboard_sync/test_definition.py` — starts Flask on a random port with a temp database.
- **Browser**: Headless Chromium (Playwright default).
- **Assertions**: Use Playwright's `expect()` auto-waiting locators to wait for elements to appear/change after each API action. This handles the polling delay naturally — Playwright retries until the assertion passes or times out.

### Fixture Design

```python
@pytest.fixture
def dashboard_page(real_dashboard_server, page):
    """Provide a Playwright page pointed at the test dashboard."""
    base_url, pid, db_path, port = real_dashboard_server
    page._base_url = base_url
    yield page, base_url
```

The test uses `dashboard_client.DashboardClient` (configured for the test server URL) to drive API mutations, and Playwright `page` to verify the browser renders them.

### DOM Selectors

**Overview page:**
- Card container: `#roadmap-list`
- Card element: `.roadmap-card`
- Card name: `.card-name`
- Progress text: `.progress-text`
- Badge: `.card-badges`

**Detail page:**
- Title: `#title`
- Status badge: `#status-badge`
- Progress label: `#progress-label`
- Progress percentage: `#progress-pct`
- Step list: `#steps`
- Step items: `.step` (with `.step-complete`, `.active` classes)

### What Gets Verified

- **Overview page**: card renders with correct name, progress bar percentage, status badge, step count
- **Detail page**: step list renders all steps, status badges update as steps progress, progress bar advances, completion state shown
- **Polling works**: changes driven via API appear in the browser without manual refresh
- **Navigation**: clicking a card on overview reaches the correct detail page

### What's NOT in Scope

- Filter/sort/search testing on overview
- Control buttons (pause/resume/stop) on detail page
- SSE streaming (polling only)
- Sidebar interactions on detail page
- Screenshot comparison / visual regression

## Files Changed

| File | Change |
|------|--------|
| `services/dashboard/static/overview.html` | Add `?poll=` query param support (~3 lines) |
| `services/dashboard/static/dashboard.html` | Add `?poll=` query param support (~3 lines) |
| `tests/integration/dashboard_ui/__init__.py` | New empty file |
| `tests/integration/dashboard_ui/test_dashboard_lifecycle.py` | New test file (~100 lines) |
| `tests/integration/dashboard_ui/conftest.py` | Playwright fixtures |

## Safety

- **Production dashboard untouched** — test uses its own Flask server on a random port with a temp database
- **No port 8888 usage** — random free port assigned by the OS
- **Headless browser** — no visible window, no display needed
