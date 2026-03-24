# plan-roadmap Testable Functions Design

## Goal

Extract plan-roadmap skill operations into testable Python functions in `roadmap_lib.py`, then add unit and integration tests with the same rigor as implement-roadmap.

## Background

The plan-roadmap skill (`skills/plan-roadmap/SKILL.md`) is a pure prompt — all logic lives in tool instructions. This makes it untestable. The implement-roadmap skill solved this by putting deterministic logic in `roadmap_lib.py` and `coordinator`, with 246 tests covering both.

We extract 5 functions into `roadmap_lib.py` covering directory creation, state files, issue body generation, placeholder replacement, and validation. The skill itself doesn't change — functions exist for testing and future programmatic callers.

## Design Decisions

- **`current_state()` reads from filenames, not file content.** State file body format is metadata for humans. We use the `event`/`date` format from SKILL.md, not the `id`/`created` format in older test fixtures.
- **Bare issue references (`#42`) are intentional.** Issues are always created in the same repo as the roadmap, so `owner/repo#42` is unnecessary.
- **`.gitignore` handling is not extracted.** It's a one-time setup operation (Step 0e), not a repeated planning operation.
- **Issue creation (`gh issue create`) is not extracted.** Integration tests use the existing `GHHelper` fixture. The `generate_issue_body()` function covers the templating logic; the `gh` CLI call is a one-liner.
- **ID/UUID generation is the caller's responsibility.** These functions create directory structure and state files. The skill prompt handles frontmatter `id` fields when writing Definition.md and Roadmap.md.
- **Only `{{REPO}}#{{ISSUE_NUMBER}}` placeholders are checked in validation.** Other template placeholders (`{{DESCRIPTION}}`, `{{N}}`, etc.) are filled by the LLM during planning. Issue placeholders are the only ones filled programmatically after planning.

## Functions

### `create_planning_dir(repo_dir, feature_name, date=None)`

Creates the full planning directory structure.

- **Input**: `repo_dir` (Path to repo root — `Roadmaps/` is appended internally, matching `find_roadmap_dirs()` convention), `feature_name` (PascalCase string), `date` (optional, defaults to today)
- **Output**: Path to the created roadmap directory
- **Creates**:
  ```
  Roadmaps/YYYY-MM-DD-<feature_name>/
    State/
    History/
  ```
- **Errors**: Raises `ValueError` if `feature_name` is empty. Raises `FileExistsError` if directory already exists. Raises `OSError` if parent is not writable.

### `create_state_file(roadmap_dir, event, date=None)`

Creates a state marker file in the State/ subdirectory.

- **Input**: `roadmap_dir` (Path to roadmap directory), `event` (string: "created", "planning", "ready", etc.), `date` (optional, defaults to today)
- **Output**: Path to the created state file
- **Creates**: `State/YYYY-MM-DD-<Event>.md` (event capitalized in filename) with content:
  ```yaml
  ---
  event: <event>
  date: YYYY-MM-DD
  ---
  ```
- **Note**: `current_state()` reads the state name from the filename, not the content. The YAML body is metadata for human readability.
- **Errors**: Raises `FileNotFoundError` if `roadmap_dir/State/` doesn't exist.

### `generate_issue_body(feature_name, step_description, acceptance_criteria, complexity, dependencies, roadmap_dir)`

Generates the markdown body for a GitHub issue.

- **Input**: All strings. `roadmap_dir` is the relative path (e.g., `Roadmaps/2026-03-24-MyFeature`).
- **Output**: Markdown string matching the template:
  ```markdown
  ## Context

  Part of the <feature_name> feature.
  Feature Definition: `<roadmap_dir>/Definition.md`
  Roadmap: `<roadmap_dir>/Roadmap.md`

  ## Step Details

  <step_description>

  ## Acceptance Criteria

  <acceptance_criteria>

  ## Complexity

  <complexity>

  ## Dependencies

  <dependencies>
  ```
- **Errors**: Raises `ValueError` if `feature_name` or `step_description` is empty.

### `replace_issue_placeholders(roadmap_file, step_issue_map)`

Replaces `{{REPO}}#{{ISSUE_NUMBER}}` placeholders in a Roadmap.md file with actual issue references.

- **Input**: `roadmap_file` (Path to Roadmap.md), `step_issue_map` (dict mapping step number int → issue number int, e.g., `{1: 42, 2: 43}`)
- **Output**: Number of replacements made (int)
- **Behavior**: For each step N in the map, finds the `### Step N:` section (between one `### Step` heading and the next) and replaces the `{{REPO}}#{{ISSUE_NUMBER}}` placeholder within that section with `#<issue_number>`. This section-based matching is consistent with how `count_steps()` parses step blocks using `### Step \d+:` markers.
- **Errors**: Raises `FileNotFoundError` if file doesn't exist. Raises `ValueError` if step_issue_map is empty. Returns 0 if no placeholders found (caller decides if this is an error).

### `validate_planning_complete(roadmap_dir)`

Validates that all planning artifacts are present and correct.

- **Input**: `roadmap_dir` (Path to roadmap directory)
- **Output**: Tuple of `(ok: bool, errors: list[str])`
- **Checks**:
  1. `Definition.md` exists and is non-empty
  2. `Roadmap.md` exists and is non-empty
  3. `State/` contains a Created state file
  4. `State/` contains a Planning state file
  5. `State/` contains a Ready state file
  6. `Roadmap.md` contains no `{{REPO}}#{{ISSUE_NUMBER}}` placeholders
- **Returns**: `(True, [])` if all pass; `(False, ["Missing Definition.md", ...])` listing failures

## Test Structure

### Unit Tests: `tests/unit/test_roadmap_lib_planning.py`

Uses `tmp_path` fixture (pytest built-in). No git, no GitHub.

**create_planning_dir:**
- Creates correct directory structure (Roadmaps/YYYY-MM-DD-Name/State/, History/)
- Uses today's date when date=None
- Uses provided date when specified
- Raises ValueError on empty feature_name
- Raises FileExistsError if directory already exists

**create_state_file:**
- Creates file with correct YAML frontmatter (event + date)
- Uses correct filename format (YYYY-MM-DD-Event.md)
- Event name is capitalized in filename (e.g., "created" → "Created")
- Works with `current_state()` (filename-based state reading)
- Raises FileNotFoundError if State/ doesn't exist

**generate_issue_body:**
- Returns correct markdown with all fields populated
- Raises ValueError on empty feature_name
- Raises ValueError on empty step_description

**replace_issue_placeholders:**
- Replaces placeholder in correct step section
- Handles multiple steps
- Doesn't replace placeholder in wrong section
- Returns 0 when no placeholders found
- Raises FileNotFoundError for missing file
- Raises ValueError for empty step_issue_map
- Preserves rest of file content

**validate_planning_complete:**
- Returns (True, []) for complete directory
- Returns (False, errors) listing each missing file
- Catches remaining placeholders in Roadmap.md
- Handles missing State/ directory gracefully

### Integration Tests: `tests/integration/planning/test_definition.py`

Uses `cat-herding-tests` repo with real git and GitHub.

**Fixtures needed** (in `tests/integration/planning/conftest.py`):
- `planning_dir` — calls `create_planning_dir()` in test repo, yields path, cleans up
- Reuses existing `test_repo`, `test_branch`, `gh` fixtures from parent conftest

**Fixture cleanup**: `planning_dir` teardown removes the directory. Tests that create GitHub issues must close them in teardown using the existing `gh.close_issue()` helper.

**Test scenarios:**

1. **Full planning flow** — create dir, write Definition.md and Roadmap.md (from fixture), create state files (Created, Planning), create real GitHub issues via `gh` fixture, replace placeholders, create Ready state, validate. Assert all files present, all issues created, validation passes.

2. **Validation catches incomplete** — create dir with missing files, assert validation returns correct errors.

3. **Issue placeholder replacement** — create Roadmap.md with N placeholders, create N real issues, replace, verify file has actual issue numbers and no remaining placeholders.

## Files Modified/Created

- **Modified**: `scripts/roadmap_lib.py` — add 5 functions
- **Created**: `tests/unit/test_roadmap_lib_planning.py` — unit tests
- **Created**: `tests/integration/planning/__init__.py`
- **Created**: `tests/integration/planning/conftest.py` — planning-specific fixtures
- **Created**: `tests/integration/planning/test_definition.py` — integration tests
- **Created**: `tests/integration/planning/fixtures/` — test roadmap fixture files

## What Does NOT Change

- `skills/plan-roadmap/SKILL.md` — no changes beyond v5 (already done)
- `skills/implement-roadmap/` — no changes
- Existing tests — no changes
- `.gitignore` handling (Step 0e) — remains prompt-only, not extracted
