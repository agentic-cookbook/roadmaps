# Draft Roadmaps Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move roadmap drafting to `~/.roadmaps/drafts/<project>/`, add issue creation and PR steps to every roadmap, simplify implement-roadmap by removing special-cased steps.

**Architecture:** plan-roadmap writes drafts to a global directory, then moves them to the repo on main. Every roadmap now has Step 1 (Create GitHub Issues) and Step N (Create & Review Feature PR) built into the Roadmap.md itself — no special logic in implement-roadmap.

**Tech Stack:** Python (roadmap_lib.py), Markdown skills (SKILL.md), pytest, bash (git operations)

---

### Task 1: Add `move_draft_to_repo` function to roadmap_lib.py

Add a function that moves a completed draft from `~/.roadmaps/drafts/<project>/` to `<repo>/Roadmaps/`, handling the git operations (stash, checkout main, commit, push, restore).

**Files:**
- Modify: `scripts/roadmap_lib.py`
- Create: `tests/unit/test_roadmap_lib_draft.py`

- [ ] **Step 1: Write tests for `draft_dir_for` helper**

```python
# tests/unit/test_roadmap_lib_draft.py

class TestDraftDirFor:
    def test_returns_correct_path(self, tmp_path):
        result = lib.draft_dir_for("temporal", base=str(tmp_path))
        assert result == tmp_path / "drafts" / "temporal"

    def test_default_base_is_home_roadmaps(self):
        result = lib.draft_dir_for("myproject")
        assert str(result).endswith(".roadmaps/drafts/myproject")
        assert str(result).startswith(str(Path.home()))
```

- [ ] **Step 2: Implement `draft_dir_for`**

```python
def draft_dir_for(project_name, base=None):
    """Return the draft directory path for a project.

    Default base is ~/.roadmaps.
    """
    if base is None:
        base = Path.home() / ".roadmaps"
    return Path(base) / "drafts" / project_name
```

- [ ] **Step 3: Run tests, verify passing**

```bash
python3 -m pytest tests/unit/test_roadmap_lib_draft.py -v
```

- [ ] **Step 4: Write tests for `move_draft_to_repo`**

```python
class TestMoveDraftToRepo:
    def test_moves_directory_to_repo_roadmaps(self, tmp_path):
        # Setup: create draft dir with files
        draft = tmp_path / "drafts" / "myproject" / "2026-03-24-Feature"
        draft.mkdir(parents=True)
        (draft / "Definition.md").write_text("def")
        (draft / "Roadmap.md").write_text("rm")
        (draft / "State").mkdir()

        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "Roadmaps").mkdir()

        result = lib.move_draft_to_repo(str(draft), str(repo))

        assert result == repo / "Roadmaps" / "2026-03-24-Feature"
        assert (result / "Definition.md").read_text() == "def"
        assert (result / "Roadmap.md").read_text() == "rm"
        assert not draft.exists()  # draft removed

    def test_raises_if_target_exists(self, tmp_path):
        draft = tmp_path / "draft" / "2026-03-24-Feature"
        draft.mkdir(parents=True)
        (draft / "Roadmap.md").write_text("rm")

        repo = tmp_path / "repo"
        (repo / "Roadmaps" / "2026-03-24-Feature").mkdir(parents=True)

        with pytest.raises(FileExistsError):
            lib.move_draft_to_repo(str(draft), str(repo))

    def test_creates_roadmaps_dir_if_missing(self, tmp_path):
        draft = tmp_path / "draft" / "2026-03-24-Feature"
        draft.mkdir(parents=True)
        (draft / "Roadmap.md").write_text("rm")

        repo = tmp_path / "repo"
        repo.mkdir()

        result = lib.move_draft_to_repo(str(draft), str(repo))
        assert result.exists()
```

- [ ] **Step 5: Implement `move_draft_to_repo`**

```python
def move_draft_to_repo(draft_dir, repo_dir):
    """Move a completed draft roadmap directory to the repo's Roadmaps/ directory.

    Returns the Path to the moved directory in the repo.
    Raises FileExistsError if the target already exists.
    """
    draft = Path(draft_dir)
    repo = Path(repo_dir)
    target = repo / "Roadmaps" / draft.name

    if target.exists():
        raise FileExistsError(f"Roadmap already exists in repo: {target}")

    (repo / "Roadmaps").mkdir(parents=True, exist_ok=True)
    shutil.move(str(draft), str(target))
    return target
```

- [ ] **Step 6: Run all tests, verify passing**

```bash
python3 -m pytest tests/unit/test_roadmap_lib_draft.py tests/unit/test_roadmap_lib_planning.py -v
```

- [ ] **Step 7: Write test for `validate_planning_complete` with `allow_placeholders`**

```python
class TestValidateAllowPlaceholders:
    def test_passes_with_placeholders_when_allowed(self, tmp_path):
        # Create a valid draft with placeholders
        rd = tmp_path / "Roadmaps" / "2026-01-01-Test"
        rd.mkdir(parents=True)
        (rd / "State").mkdir()
        (rd / "Definition.md").write_text("# def\n")
        (rd / "Roadmap.md").write_text(
            "# Feature Roadmap: Test\n\n"
            "### Step 1: Do thing\n\n"
            "- **GitHub Issue**: {{REPO}}#{{ISSUE_NUMBER}}\n"
        )
        lib.create_state_file(rd, "Created", date="2026-01-01")
        lib.create_state_file(rd, "Planning", date="2026-01-01")
        lib.create_state_file(rd, "Ready", date="2026-01-01")

        ok, errors = lib.validate_planning_complete(rd, allow_placeholders=True)
        assert ok, f"Unexpected errors: {errors}"

    def test_fails_with_placeholders_when_not_allowed(self, tmp_path):
        # Same setup but allow_placeholders=False (default)
        rd = tmp_path / "Roadmaps" / "2026-01-01-Test"
        rd.mkdir(parents=True)
        (rd / "State").mkdir()
        (rd / "Definition.md").write_text("# def\n")
        (rd / "Roadmap.md").write_text(
            "# Feature Roadmap: Test\n\n"
            "### Step 1: Do thing\n\n"
            "- **GitHub Issue**: {{REPO}}#{{ISSUE_NUMBER}}\n"
        )
        lib.create_state_file(rd, "Created", date="2026-01-01")
        lib.create_state_file(rd, "Planning", date="2026-01-01")
        lib.create_state_file(rd, "Ready", date="2026-01-01")

        ok, errors = lib.validate_planning_complete(rd)
        assert not ok
        assert any("placeholder" in e.lower() for e in errors)
```

- [ ] **Step 8: Update `validate_planning_complete` to accept `allow_placeholders` parameter**

Add `allow_placeholders=False` parameter. When True, skip the placeholder check.

- [ ] **Step 9: Run all tests, commit**

```bash
python3 -m pytest tests/unit/ -v --tb=short
git add scripts/roadmap_lib.py tests/unit/test_roadmap_lib_draft.py
git commit -m "feat: add draft_dir_for, move_draft_to_repo, allow_placeholders in validate"
```

---

### Task 2: Update plan-roadmap SKILL.md for draft workflow

Modify the skill to write drafts to `~/.roadmaps/drafts/<project>/`, remove issue creation, add Step 1 (Create GitHub Issues) and Step N (Create & Review Feature PR) to every roadmap, and move to repo on completion.

**Files:**
- Modify: `skills/plan-roadmap/SKILL.md`

- [ ] **Step 1: Update Step 5 — write to draft directory instead of repo**

Change the file creation section to use `~/.roadmaps/drafts/<project>/` as the base directory. The project name comes from the repo basename detected via `git rev-parse --show-toplevel`.

Replace:
```
Roadmaps/YYYY-MM-DD-<FeatureName>/
```
With:
```
~/.roadmaps/drafts/<project>/YYYY-MM-DD-<FeatureName>/
```

Where `<project>` is `$(basename $(git rev-parse --show-toplevel))`.

- [ ] **Step 2: Update the Roadmap.md template — add Step 1 and Step N**

The generated Roadmap.md must always include:

First step:
```markdown
### Step 1: Create GitHub Issues

- **GitHub Issue**: (none — this step creates the issues)
- **Type**: Auto
- **Status**: Not Started
- **Complexity**: S
- **Dependencies**: None
- **Acceptance Criteria**:
  - [ ] GitHub issues created for all implementation steps
  - [ ] Issue numbers populated in this roadmap
```

Last step:
```markdown
### Step N: Create & Review Feature PR

- **GitHub Issue**: (none — this step creates the PR)
- **Type**: Auto
- **Status**: Not Started
- **Complexity**: M
- **Dependencies**: Step N-1
- **Acceptance Criteria**:
  - [ ] Feature branch pushed
  - [ ] PR created with Closes lines for all issues
  - [ ] Code review passed
  - [ ] PR merged with --merge
  - [ ] All issues closed
  - [ ] Worktree cleaned up
```

Implementation steps are numbered 2 through N-1.

- [ ] **Step 3: Remove Step 6 (Create GitHub Issues)**

Delete the entire Step 6 section from the skill. Issues are no longer created during planning.

- [ ] **Step 4: Replace the commit/push steps with draft validation and move-to-repo**

After the user approves the roadmap, the skill should:

1. Validate the draft (allow_placeholders=True since issues aren't created yet)
2. Detect the repo root: `REPO_ROOT=$(git rev-parse --show-toplevel)`
3. Stash any uncommitted changes: `git stash`
4. Checkout main: `git checkout main && git pull`
5. Move draft to repo: `mv ~/.roadmaps/drafts/<project>/YYYY-MM-DD-<Feature> $REPO_ROOT/Roadmaps/`
6. Commit and push: `git add Roadmaps/ && git commit -m "docs: add roadmap for <Feature>" && git push`
7. Restore previous branch: `git checkout - && git stash pop`

- [ ] **Step 5: Bump version to v6**

- [ ] **Step 6: Commit**

```bash
git add skills/plan-roadmap/SKILL.md
git commit -m "feat: plan-roadmap v6 — draft to ~/.roadmaps, issue+PR steps in roadmap"
```

---

### Task 3: Simplify implement-roadmap SKILL.md

Remove the special-cased PR step (Step 4) and the dashboard step injection (Step 2c). The coordinator now dispatches all steps including issue creation and PR creation uniformly.

**Files:**
- Modify: `skills/implement-roadmap/SKILL.md`

- [ ] **Step 1: Remove Step 2c (Add PR Step to Dashboard)**

Delete the entire Step 2c section. The PR step is already in the roadmap, so `load-roadmap` puts it in the dashboard automatically.

- [ ] **Step 2: Remove Step 4 (Create & Review Feature PR)**

Delete the entire Step 4 section (4a through 4g). The coordinator dispatches the PR step like any other step, and the worker agent handles it.

- [ ] **Step 3: Update the "action: done" handler**

When the coordinator returns `done`, the skill should now just:
1. Write State/History files
2. Commit to feature branch
3. Dashboard complete + shutdown

The PR creation, review, merge, issue closing, and worktree cleanup are all handled by the PR step's worker agent.

- [ ] **Step 4: Bump version to v18**

- [ ] **Step 5: Commit**

```bash
git add skills/implement-roadmap/SKILL.md
git commit -m "feat: implement-roadmap v18 — remove special-cased PR step, all steps uniform"
```

---

### Task 4: Update implement-step-agent for issue creation and PR steps

The worker agent needs to handle two new step types: creating GitHub issues and creating/reviewing/merging the feature PR.

**Files:**
- Modify: `agents/implement-step-agent.md`

- [ ] **Step 1: Add "Create GitHub Issues" step handling**

When the step description is "Create GitHub Issues", the agent should:
1. Read the Roadmap.md to find all implementation steps (steps between issue creation and PR creation)
2. For each step, create a GitHub issue via `gh issue create`
3. Replace `{{REPO}}#{{ISSUE_NUMBER}}` placeholders in Roadmap.md with actual issue numbers
4. Commit the updated Roadmap.md
5. Comment on each issue noting it was created

Add this as a recognized pattern in the agent's implementation section.

- [ ] **Step 2: Add "Create & Review Feature PR" step handling**

When the step description contains "Create & Review Feature PR", the agent should:
1. Push the feature branch
2. Create a PR with `Closes #N` lines for all step issues
3. Run code review + security review
4. Fix issues (max 3 review iterations)
5. Merge with `--merge`
6. Close any issues not auto-closed
7. Clean up the worktree

This is the logic from the old Step 4 in implement-roadmap, moved to the agent.

- [ ] **Step 3: Bump version to v5**

- [ ] **Step 4: Commit**

```bash
git add agents/implement-step-agent.md
git commit -m "feat: implement-step-agent v5 — handle issue creation and PR steps"
```

---

### Task 5: Update unit tests

Update existing tests and add new ones for the changed behavior.

**Files:**
- Modify: `tests/unit/test_roadmap_lib_planning.py`
- Verify: `tests/unit/test_coordinator.py` (coordinator should still work — steps are steps)

- [ ] **Step 1: Update `validate_planning_complete` tests**

The validation should now accept placeholders when `allow_placeholders=True` (already done in Task 1 Step 7-8).

Add a test that validates a roadmap with both the issue creation step and PR step present.

- [ ] **Step 2: Run all unit tests**

```bash
python3 -m pytest tests/unit/ -v --tb=short
```

All tests must pass.

- [ ] **Step 3: Commit**

```bash
git add tests/
git commit -m "test: update unit tests for draft roadmap workflow"
```

---

### Task 6: Update integration tests

Add integration tests for the new workflow: draft creation, move to repo, issue creation step, PR step.

**Files:**
- Create: `tests/integration/draft_workflow/`
- Modify: existing integration tests if needed

- [ ] **Step 1: Create draft_workflow integration test fixtures**

Create `tests/integration/draft_workflow/fixtures/simple_draft/` with a 4-step roadmap:
- Step 1: Create GitHub Issues (Auto, S)
- Step 2: Create test file (Auto, S)
- Step 3: Append to test file (Auto, S)
- Step 4: Create & Review Feature PR (Auto, M)

Use `{{REPO}}#{{ISSUE_NUMBER}}` placeholders for steps 2-3.

- [ ] **Step 2: Write draft lifecycle test**

Test that:
1. Draft created in temp ~/.roadmaps/drafts/<project>/
2. `validate_planning_complete` passes with `allow_placeholders=True`
3. `move_draft_to_repo` moves it to the repo
4. Roadmap.md has placeholders
5. Coordinator resolves it and returns Step 1 first

- [ ] **Step 3: Write issue creation step test**

Test that:
1. Worker agent creates GitHub issues for steps 2-3 (not step 1 or 4)
2. Roadmap.md placeholders replaced with real issue numbers
3. Coordinator advances to Step 2 after Step 1 completes

- [ ] **Step 4: Run all integration tests**

```bash
python3 -m pytest tests/integration/ -v --tb=short
```

- [ ] **Step 5: Commit**

```bash
git add tests/integration/draft_workflow/
git commit -m "test: add draft workflow integration tests"
```

---

### Task 7: Update demo.sh and run live test

Update the demo to show the new workflow and run a live end-to-end test.

**Files:**
- Modify: `skills/progress-dashboard/references/demo.sh`

- [ ] **Step 1: Update demo roadmap to include issue creation and PR steps**

The demo roadmap should have 5 steps:
1. Create GitHub Issues
2. Project scaffolding
3. Core widget engine
4. API endpoints
5. Create & Review Feature PR

- [ ] **Step 2: Update demo script flow**

Step 1 logs issue creation events. Steps 2-4 log implementation events. Step 5 logs PR events.

- [ ] **Step 3: Run the demo against Flask service**

```bash
bash skills/progress-dashboard/references/demo.sh
```

Verify dashboard shows all 5 steps.

- [ ] **Step 4: Run live end-to-end test against cat-herding-tests**

Create a test roadmap with issue creation and PR steps, run the full workflow with real agents, verify dashboard and GitHub results via Playwright.

- [ ] **Step 5: Commit**

```bash
git add skills/progress-dashboard/references/demo.sh
git commit -m "feat: update demo for draft roadmap workflow with issue+PR steps"
```

---

### Task 8: Run full test suite and verify

- [ ] **Step 1: Run unit tests**

```bash
python3 -m pytest tests/unit/ -v --tb=short
```

- [ ] **Step 2: Run integration tests**

```bash
python3 -m pytest tests/integration/ -v --tb=short
```

- [ ] **Step 3: Fix any failures and commit**

- [ ] **Step 4: Verify demo runs clean**

```bash
bash skills/progress-dashboard/references/demo.sh
```

Screenshot with Playwright and verify.
