# Test Suite Design

## Purpose

Add comprehensive automated tests to the cat-herding repo, which currently has zero test infrastructure. Covers the dashboard service, shared libraries, coordinator, and client library.

## Framework

pytest — installed via `pip3 install pytest`.

## Structure

```
tests/
  conftest.py              # shared fixtures
  test_roadmap_lib.py      # unit: frontmatter, state, discovery
  test_db.py               # unit: schema, migrations
  test_models.py           # unit: CRUD against in-memory SQLite
  test_coordinator.py      # unit: step parsing, resolution
  test_api_roadmaps.py     # integration: roadmap CRUD routes
  test_api_steps.py        # integration: step lifecycle routes
  test_api_state.py        # integration: state transitions
  test_api_sync.py         # integration: bulk sync
  test_api_controls.py     # integration: pause/resume/stop
  test_dashboard_client.py # integration: client library
```

## Fixtures (conftest.py)

- `db_conn` — in-memory SQLite connection with schema initialized, rolled back after each test
- `app` — Flask test app with in-memory DB
- `client` — Flask test client (from `app.test_client()`)
- `sample_roadmap` — creates a roadmap with 3 steps via the API, returns the ID
- `tmp_roadmap_dir` — temp directory with realistic File Record structure for roadmap_lib tests
- `coordinator_roadmap` — temp Roadmap.md file for coordinator tests

## Test Tiers

### Tier 1: Unit Tests

**test_roadmap_lib.py**
- `parse_frontmatter()` with valid YAML, missing frontmatter, empty file
- `current_state()` with multiple state files, empty dir, no State/ dir
- `is_active()` / `is_implementable()` for each state value
- `get_feature_name()` from directory name and from heading fallback
- `count_steps()` on Roadmap.md content
- `find_roadmap_dirs()` with new layout dirs
- `parse_inline_fields()` for old-format files
- `write_frontmatter()` round-trip

**test_db.py**
- `init_db()` creates all tables
- `init_db()` is idempotent (can run twice)
- Schema version is set
- Foreign keys are enforced
- WAL mode is enabled

**test_models.py**
- Roadmap CRUD: create, get, update, delete, list with filters
- Steps: bulk_create, update, begin (auto-stops prior), finish, error
- State transitions: add, list, updates roadmap.state
- History events: add, list
- Issues/PRs: upsert (insert + update)
- Controls: set, get, clear
- Runtime events: add, list
- Sync: create new, update existing, reconcile steps/issues/prs

**test_coordinator.py**
- `list_all_steps()` parses step blocks correctly
- `next-step` finds first non-complete, non-manual step
- `next-step` skips manual steps and reports them
- `next-step` returns "done" when all auto steps complete
- `resolve` finds roadmaps in new directory layout
- `summary` returns correct counts

### Tier 2: API Integration Tests

**test_api_roadmaps.py**
- POST /roadmaps — creates, returns 201 + id
- POST /roadmaps — 400 when name missing
- GET /roadmaps — lists all, filters by state/status
- GET /roadmaps/<id> — includes steps, issues, prs, events
- GET /roadmaps/<id> — 404 for missing
- PUT /roadmaps/<id> — updates fields
- DELETE /roadmaps/<id> — cascades
- POST /roadmaps/<id>/complete — sets status+state
- POST /roadmaps/<id>/error — sets status, logs event
- POST /roadmaps/<id>/shutdown — sets idle

**test_api_steps.py**
- POST /steps — bulk create
- GET /steps — lists in order
- PUT /steps/<n> — updates fields
- POST /steps/<n>/begin — sets in_progress, auto-stops prior
- POST /steps/<n>/finish — sets complete
- POST /steps/<n>/error — sets error with message

**test_api_state.py**
- GET /state — returns current + transitions
- POST /state — creates transition, updates roadmap

**test_api_sync.py**
- POST /sync — creates new roadmap from full payload
- POST /sync — updates existing roadmap, replaces steps/issues/prs

**test_api_controls.py**
- GET /control — returns null when no signal
- POST /control — sets pause/resume/stop
- POST /control — 400 for invalid action
- DELETE /control — clears signal
- GET /control — returns action after set

### Tier 3: Client Integration Tests

**test_dashboard_client.py**
- `ping()` succeeds against test server
- `create_roadmap()` + `get_roadmap()` round-trip
- `set_steps()` + step lifecycle (`begin_step`, `finish_step`)
- `sync()` with full payload
- `check_control()` returns None, then "pause" after set
- `log_event()` + verify via `get_roadmap()`
- `DashboardUnavailable` raised when server unreachable
- `DashboardError` raised on 400/404

## Running Tests

```bash
cd ~/projects/active/cat-herding
pip3 install pytest
python3 -m pytest tests/ -v
```

## Files Modified

- `tests/` — new directory with all test files
- No changes to production code
