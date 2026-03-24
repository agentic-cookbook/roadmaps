# Atomic Batch PR — Integration Test Suite Design

**Date:** 2026-03-24
**Branch:** feature/atomic-batch-pr
**Sandbox repo:** mikefullerton/cat-herding-tests

## Goal

Verify the atomic-batch-pr feature end-to-end: all steps commit to a single shared branch, one PR is created, the dashboard stays in sync, and error conditions are handled correctly. All tests run against real git and real GitHub (no mocks).

## Architecture

### Test Strategy

Tests simulate what the implement-step-agent would do — create files, commit, update roadmap status — without invoking the actual LLM. This makes tests fast and deterministic while exercising real git operations, real GitHub API (branches, PRs, issues), real coordinator logic, and a real dashboard server.

The coordinator script is called directly via subprocess (same as in production). The dashboard runs as a Flask test server on a random port with a temp SQLite DB.

### Sandbox Repo

`cat-herding-tests` (github.com/mikefullerton/cat-herding-tests) is the sandbox. Each test creates a fresh orphan branch to isolate from other tests and from the repo's existing content. Teardown deletes the branch locally and remotely.

### Directory Structure

```
tests/
  unit/                              # existing tests (moved from tests/)
    conftest.py
    test_coordinator.py
    test_api_roadmaps.py
    test_api_steps.py
    test_api_sync.py
    test_api_state.py
    test_api_controls.py
    test_dashboard_client.py
    test_db.py
    test_models.py
    test_roadmap_lib.py
  integration/
    conftest.py                      # shared fixtures
    happy_path/
      fixtures/
        all_auto_3step/              # Definition.md, Roadmap.md, State/, History/
        mixed_auto_manual/
        single_step/
      test_definition.py
    step_ordering/
      fixtures/
        all_auto_3step/
        with_dependencies/
        partial_complete/
      test_definition.py
    dashboard_sync/
      fixtures/
        all_auto_3step/
      test_definition.py
    error_conditions/
      fixtures/
        all_auto_3step/
      test_definition.py
    git_workflow/
      fixtures/
        all_auto_3step/
      test_definition.py
    cleanup/
      fixtures/
        already_complete/
        partial_complete/
      test_definition.py
```

Each test folder is self-contained: its `fixtures/` directory holds the roadmap files it needs, and `test_definition.py` contains the test cases. Similar fixtures may be duplicated across folders — that's intentional to keep tests decoupled.

## Shared Fixtures (integration/conftest.py)

### `test_repo`

Session-scoped. Points to the local clone of `cat-herding-tests`. Verifies the repo exists and the remote is correct. Does not clone — assumes the repo is already at `../cat-herding-tests` relative to the cat-herding project root.

### `test_branch(test_repo)`

Function-scoped. Creates a fresh orphan branch named `test/<test_name>-<short_uuid>` in the test repo. Commits an initial empty commit. Pushes the branch. Yields the branch name. Teardown: deletes the branch locally and remotely, removes any worktrees created for it.

### `roadmap_in_repo(test_branch)`

Fixture factory (function-scoped). Returns a callable `_copy(fixture_path, issue_map=None)` that:
1. Copies the fixture's roadmap directory into the test repo's `Roadmaps/` on the test branch
2. If `issue_map` is provided (dict of step_number → issue_number), patches the `Roadmap.md` to replace placeholder issue references with actual GitHub issue numbers
3. Commits and pushes
4. Returns the relative roadmap path (e.g., `Roadmaps/2026-03-24-TestFeature/Roadmap.md`)

Example usage in a test:
```python
def test_example(roadmap_in_repo, gh):
    issues = {1: gh.create_issue(REPO, "Step 1"), 2: gh.create_issue(REPO, "Step 2")}
    roadmap_path = roadmap_in_repo("happy_path/fixtures/all_auto_3step", issue_map=issues)
```

### `dashboard_server`

Function-scoped. Starts the Flask dashboard app in a daemon thread (`threading.Thread(daemon=True)`) on a random available port with a temp SQLite DB. Uses `app.run(threaded=True, use_reloader=False)`. Waits for the port to accept connections before yielding.

Yields a `DashboardHelper` object with:
- `url` — base URL (e.g., `http://localhost:54321`)
- `client` — configured `dashboard_client` instance
- `api(path)` — shortcut for GET requests to the API

Teardown: shuts down the server, deletes the temp DB.

### `coordinator`

Session-scoped. Returns a `CoordinatorHelper` with:
- `next_step(roadmap_path)` — calls `coordinator next-step` via subprocess, returns parsed JSON
- `resolve(feature_name, cwd)` — calls `coordinator resolve`, returns parsed JSON
- `summary(roadmap_path)` — calls `coordinator summary`, returns parsed JSON

All methods pass `cwd` to `subprocess.run` so the coordinator operates in the correct directory (the test repo, not the pytest working directory). `next_step` and `summary` derive `cwd` from the roadmap path's parent. `resolve` takes an explicit `cwd` parameter.

### `gh`

Session-scoped. Returns a `GHHelper` with convenience methods:
- `create_issue(repo, title)` — creates issue, returns number
- `close_issue(repo, number)` — closes issue
- `get_issue(repo, number)` — returns issue data
- `list_prs(repo, head)` — lists PRs for a branch
- `get_pr(repo, number)` — returns PR data
- `delete_branch(repo, branch)` — deletes remote branch

### `simulate_step(test_branch, worktree_path, step_number, roadmap_path)`

Helper function. Simulates what the implement-step-agent does for one step:
1. Creates a file `step_<N>_output.txt` in the worktree
2. Updates the roadmap: marks step N as `Complete`, updates progress table
3. Commits both changes to the branch
Returns the commit SHA.

### `simulate_failed_step(test_branch, worktree_path, step_number)`

Helper function. Simulates a worker that fails:
1. Creates a partial file in the worktree
2. Does NOT update the roadmap status (step stays `Not Started`)
3. Commits the partial work
Returns the commit SHA.

## Fixture Roadmaps

Each fixture is a complete File Record directory. Steps describe trivial work (create/append to a text file) so the simulated agent can execute them deterministically.

### all_auto_3step

3 auto steps, no dependencies, no manual steps. Each step creates `step_N_output.txt`. The `Roadmap.md` uses placeholder issue references (`__ISSUE_1__`, `__ISSUE_2__`, `__ISSUE_3__`) which `roadmap_in_repo` patches with actual issue numbers created via `gh.create_issue()` at test setup time.

### mixed_auto_manual

4 steps: steps 1, 2, 4 are Auto; step 3 is Manual. Tests that manual steps are skipped.

### single_step

1 auto step. Tests the degenerate case — still creates branch, worktree, PR.

### with_dependencies

3 steps: step 2 depends on step 1, step 3 has no dependency. Tests dependency ordering.

### already_complete

3 auto steps, all marked Complete. Tests that coordinator returns "done" immediately.

### partial_complete

3 auto steps: step 1 is Complete, steps 2-3 are Not Started. Tests resume from step 2.

## Test Cases

### happy_path/test_definition.py (3 tests)

**`test_all_auto_steps_single_pr`** — Fixture: `all_auto_3step`. Create worktree + branch. Run coordinator loop: for each step, simulate_step, verify coordinator advances. After all steps: push branch, create PR with `Closes #N` lines (using actual issue numbers from setup), merge with `--merge`. Review steps are skipped in integration tests — they require LLM invocation. Assert: single PR exists, all 3 issues closed, 3 step commits + completion commit visible in main history.

**`test_mixed_auto_manual_skips_manual`** — Fixture: `mixed_auto_manual`. Run coordinator loop. Assert: steps 1, 2, 4 dispatched (step 3 skipped as manual). PR body lists only auto steps. Manual step's issue NOT closed.

**`test_single_step_roadmap`** — Fixture: `single_step`. Full workflow with 1 step. Assert: branch created, worktree created, PR created and merged, issue closed.

### step_ordering/test_definition.py (3 tests)

**`test_steps_execute_in_numerical_order`** — Fixture: `all_auto_3step`. Call `coordinator next-step` repeatedly, simulating completion between calls. Assert: returns step 1, then 2, then 3, then done.

**`test_skips_already_complete_steps`** — Fixture: `partial_complete`. Call `coordinator next-step`. Assert: returns step 2 (step 1 already complete).

**`test_dependencies_respected`** — Fixture: `with_dependencies`. Call `coordinator next-step` when step 1 is not yet complete. Assert: step 2 (which depends on step 1) is not returned; step 1 or step 3 (no dependency) is returned instead.

### dashboard_sync/test_definition.py (5 tests)

**`test_step_status_transitions`** — Create roadmap in dashboard, set steps. Call begin_step(1), assert step status is `in_progress`. Call finish_step(1), assert step status is `complete`.

**`test_roadmap_status_lifecycle`** — Create roadmap (status=idle). Update to running. Complete. Assert transitions: idle → running → complete.

**`test_roadmap_state_lifecycle`** — Create roadmap (state=Ready). Transition to Implementing. Transition to Complete. Assert state history recorded.

**`test_dashboard_reflects_current_state`** — Run simulated 3-step workflow. After each step, GET the roadmap from the API. Assert: step count, completion count, and current step status all match expected state.

**`test_single_pr_on_overview`** — Create roadmap, add a PR via `add_pr`. GET `/api/v1/roadmaps?detail=true`. Assert: the roadmap's `prs` array contains exactly one PR with the correct number and URL.

### error_conditions/test_definition.py (4 tests)

**`test_worker_failure_stops_loop`** — Fixture: `all_auto_3step`. Simulate step 1 success, step 2 failure (step not marked Complete). Call `coordinator next-step` — returns step 2 again (because it is still Not Started). This is what the skill detects in step 3e: after a worker returns, it checks whether the step's status changed to Complete. If it didn't, the skill stops the loop. This test verifies the coordinator returns the same step (enabling that detection) and that the worktree is preserved for manual recovery.

**`test_worker_failure_dashboard_shows_error`** — After simulated failure, call `step_error` on the dashboard. GET the step. Assert status is `error` and the roadmap's step reflects the failure.

**`test_existing_worktree_handled`** — Create a worktree at the expected path. Attempt to create it again. Assert: either reuses it or errors cleanly (not a crash). Cleanup both.

**`test_existing_remote_branch_handled`** — Push a branch with the expected name. Attempt to create worktree with `-b` for the same branch name. Assert: git error is handled (branch already exists). Test the recovery: use `git worktree add <path> <existing-branch>` without `-b`.

### git_workflow/test_definition.py (5 tests)

**`test_all_commits_on_single_branch`** — Fixture: `all_auto_3step`. Create worktree + branch. Simulate 3 steps. Assert: `git log` on the branch shows all 3 step commits plus the initial commit. No other branches created.

**`test_worktree_created_at_expected_path`** — Create worktree via the skill's formula: `../$(basename $(pwd))-wt/<feature_name>`. Assert: the directory exists and is a valid git worktree.

**`test_worktree_cleaned_up_on_success`** — Full workflow through completion. Run `git worktree remove`. Assert: worktree directory gone, `git worktree list` no longer includes it.

**`test_pr_uses_merge_not_squash`** — Create PR, merge with `--merge`. Assert: individual step commits are visible in the target branch's history (not squashed into one).

**`test_pr_body_contains_closes_lines`** — Create PR with the template body using actual issue numbers from `gh.create_issue()`. Assert: body contains `Closes #N` for each step's actual issue number.

### cleanup/test_definition.py (2 tests)

**`test_already_complete_roadmap_returns_done`** — Fixture: `already_complete`. Call `coordinator next-step`. Assert: returns `{"action": "done"}` immediately.

**`test_partial_completion_resumes`** — Fixture: `partial_complete`. Call `coordinator next-step`. Assert: returns step 2 (skips completed step 1). Simulate step 2. Call again. Assert: returns step 3.

## Running

```bash
# Unit tests only (fast)
pytest tests/unit/

# Integration tests only (requires cat-herding-tests repo + GitHub access)
pytest tests/integration/

# All tests
pytest tests/

# Single test group
pytest tests/integration/happy_path/

# Verbose single test
pytest tests/integration/happy_path/test_definition.py::test_all_auto_steps_single_pr -v
```

## Prerequisites

- `cat-herding-tests` repo cloned at `../cat-herding-tests` (relative to cat-herding root)
- `gh` CLI authenticated with push access to `mikefullerton/cat-herding-tests`
- Python 3.10+ with pytest, flask installed
