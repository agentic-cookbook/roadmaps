# plan-roadmap Testable Functions Design

## Goal

Extract plan-roadmap skill operations into testable Python functions in `roadmap_lib.py`, then add unit and integration tests with the same rigor as implement-roadmap.

## Background

The plan-roadmap skill (`skills/plan-roadmap/SKILL.md`) is a pure prompt — all logic lives in tool instructions. This makes it untestable. The implement-roadmap skill solved this by putting deterministic logic in `roadmap_lib.py` and `coordinator`, with 246 tests covering both.

We extract 5 functions into `roadmap_lib.py` covering directory creation, state files, issue body generation, placeholder replacement, and validation. The skill itself doesn't change — functions exist for testing and future programmatic callers.

## Functions

### `create_planning_dir(base_dir, feature_name, date=None)`

Creates the full planning directory structure.

- **Input**: `base_dir` (Path to repo root or Roadmaps/ parent), `feature_name` (PascalCase string), `date` (optional, defaults to today)
- **Output**: Path to the created roadmap directory
- **Creates**:
  ```
  Roadmaps/YYYY-MM-DD-<feature_name>/
    State/
    History/
  ```
- **Errors**: Raises `ValueError` if `feature_name` is empty. Raises `FileExistsError` if directory already exists. Raises `OSError` if `base_dir` is not writable.

### `create_state_file(roadmap_dir, event, date=None)`

Creates a state marker file in the State/ subdirectory.

- **Input**: `roadmap_dir` (Path to roadmap directory), `event` (string: "created", "planning", "ready", etc.), `date` (optional, defaults to today)
- **Output**: Path to the created state file
- **Creates**: `State/YYYY-MM-DD-<Event>.md` with content:
  ```yaml
  ---
  event: <event>
  date: YYYY-MM-DD
  ---
  ```
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
- **Behavior**: For each step N in the map, finds the Nth occurrence of `{{REPO}}#{{ISSUE_NUMBER}}` and replaces it with `#<issue_number>`. Writes the file back in-place.
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
- Creates correct directory structure
- Uses today's date when date=None
- Uses provided date when specified
- Raises ValueError on empty feature_name
- Raises FileExistsError if directory already exists

**create_state_file:**
- Creates file with correct YAML frontmatter
- Uses correct filename format (YYYY-MM-DD-Event.md)
- Event name is capitalized in filename (e.g., "created" → "Created")
- Raises FileNotFoundError if State/ doesn't exist

**generate_issue_body:**
- Returns correct markdown with all fields populated
- Raises ValueError on empty feature_name
- Raises ValueError on empty step_description

**replace_issue_placeholders:**
- Replaces correct number of placeholders
- Handles multiple steps in order
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

**Test scenarios:**

1. **Full planning flow** — create dir, write Definition.md and Roadmap.md (from fixture), create state files (Created, Planning), create real GitHub issues, replace placeholders, create Ready state, validate. Assert all files present, all issues created, validation passes.

2. **Validation catches incomplete** — create dir with missing files, assert validation returns correct errors.

3. **Issue placeholder replacement** — create Roadmap.md with N placeholders, create N real issues, replace, verify file has actual issue numbers.

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
