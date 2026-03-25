"""Integration tests for the roadmap working directory workflow.

Tests the full lifecycle: validate → copy to branch → resolve → implement → cleanup.
These tests do NOT use GitHub — they work purely with the filesystem
and the coordinator subprocess.
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests.integration.helpers import COORDINATOR, PROJECT_ROOT

sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
import roadmap_lib as lib


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
SIMPLE_DRAFT_FIXTURE = FIXTURES_DIR / "simple_draft"


def _copy_fixture_as(draft_name, dest_parent):
    """Copy the simple_draft fixture into dest_parent/<draft_name>/."""
    dest = dest_parent / draft_name
    shutil.copytree(SIMPLE_DRAFT_FIXTURE, dest)
    return dest


def _run_coordinator(args, cwd):
    """Run the coordinator subprocess and return parsed JSON."""
    result = subprocess.run(
        [sys.executable, str(COORDINATOR)] + args,
        capture_output=True,
        text=True,
        cwd=str(cwd),
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"coordinator {' '.join(args)} failed:\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return json.loads(result.stdout)


class TestRoadmapWorkDirLifecycle:
    """Full lifecycle WITHOUT GitHub: validate → copy to branch → resolve → cleanup."""

    def test_full_lifecycle(self, tmp_path):
        # 1. Set up working directory at ~/.roadmaps/<project>/SimpleDraft
        work_root = tmp_path / ".roadmaps" / "test-project"
        work_root.mkdir(parents=True)
        roadmap_dir = _copy_fixture_as("SimpleDraft", work_root)

        # 2. Validate with allow_placeholders=True — should pass
        ok, errors = lib.validate_planning_complete(roadmap_dir, allow_placeholders=True)
        assert ok is True, f"validate_planning_complete failed: {errors}"

        # 3. Copy roadmap to a simulated worktree/Roadmaps/
        worktree = tmp_path / "worktree"
        worktree.mkdir()
        target = worktree / "Roadmaps"
        new_path = lib.copy_roadmap_to_branch(roadmap_dir, target)
        assert new_path.exists()
        assert (new_path / "Roadmap.md").exists()

        # 4. Source still exists (copy, not move)
        assert roadmap_dir.exists()

        # 5. Coordinator can resolve from the worktree
        resolve_result = _run_coordinator(["resolve", "SimpleDraft"], cwd=worktree)
        assert "path" in resolve_result
        assert "SimpleDraft" in resolve_result["path"]

        # 6. Coordinator returns Step 1 first
        roadmap_file = resolve_result["path"]
        next_result = _run_coordinator(["next-step", roadmap_file], cwd=worktree)
        assert next_result["action"] == "implement"
        assert next_result["step"] == 1
        assert "Create GitHub Issues" in next_result["description"]

        # 7. After "merge", cleanup the working directory
        assert lib.cleanup_roadmap(roadmap_dir) is True
        assert not roadmap_dir.exists()


class TestValidateCatchesIncompleteDraft:
    """validate_planning_complete returns errors for incomplete drafts."""

    def test_missing_roadmap_returns_errors(self, tmp_path):
        # Draft with no Roadmap.md
        draft_dir = tmp_path / "NoRoadmap"
        draft_dir.mkdir()
        state_dir = draft_dir / "State"
        state_dir.mkdir()
        (draft_dir / "History").mkdir()
        (state_dir / "2026-01-01-Created.md").write_text(
            "---\nevent: created\ndate: 2026-01-01\n---\n"
        )
        (state_dir / "2026-01-01-Planning.md").write_text(
            "---\nevent: planning\ndate: 2026-01-01\n---\n"
        )
        (state_dir / "2026-01-01-Ready.md").write_text(
            "---\nevent: ready\ndate: 2026-01-01\n---\n"
        )

        ok, errors = lib.validate_planning_complete(draft_dir)
        assert ok is False
        assert any("Roadmap.md" in e for e in errors)

    def test_empty_roadmap_returns_errors(self, tmp_path):
        # Draft with empty Roadmap.md
        draft_dir = tmp_path / "EmptyRoadmap"
        draft_dir.mkdir()
        state_dir = draft_dir / "State"
        state_dir.mkdir()
        (draft_dir / "History").mkdir()
        (draft_dir / "Roadmap.md").write_text("")  # empty
        (state_dir / "2026-01-01-Created.md").write_text(
            "---\nevent: created\ndate: 2026-01-01\n---\n"
        )
        (state_dir / "2026-01-01-Planning.md").write_text(
            "---\nevent: planning\ndate: 2026-01-01\n---\n"
        )
        (state_dir / "2026-01-01-Ready.md").write_text(
            "---\nevent: ready\ndate: 2026-01-01\n---\n"
        )

        ok, errors = lib.validate_planning_complete(draft_dir)
        assert ok is False
        assert any("Roadmap.md" in e for e in errors)


class TestCopyFailsIfExists:
    """copy_roadmap_to_branch raises FileExistsError when target already exists."""

    def test_copy_fails_if_target_exists(self, tmp_path):
        # Copy fixture into working area
        work_root = tmp_path / "work"
        work_root.mkdir()
        roadmap_dir = _copy_fixture_as("SimpleDraft", work_root)

        # Pre-create the same directory in the target
        target = tmp_path / "worktree" / "Roadmaps"
        (target / "SimpleDraft").mkdir(parents=True)

        # Should raise FileExistsError
        with pytest.raises(FileExistsError):
            lib.copy_roadmap_to_branch(roadmap_dir, target)

        # Source should still be there
        assert roadmap_dir.exists()


class TestPlaceholderReplacement:
    """replace_issue_placeholders correctly substitutes issue numbers."""

    def test_placeholder_replacement(self, tmp_path):
        # 1. Copy fixture to a temp dir (not a draft area — just needs the file)
        draft_dir = _copy_fixture_as("SimpleDraft", tmp_path)
        roadmap_file = draft_dir / "Roadmap.md"

        # 2. Replace placeholders for steps 2 and 3
        count = lib.replace_issue_placeholders(roadmap_file, {2: 42, 3: 43})
        assert count == 2

        content = roadmap_file.read_text()

        # 3. Steps 2 and 3 now have real issue numbers
        step2_match = re.search(
            r"### Step 2:.*?(?=### Step \d+:|\Z)", content, re.DOTALL
        )
        assert step2_match, "Step 2 section not found"
        assert "#42" in step2_match.group(0), (
            "Step 2 should reference #42"
        )

        step3_match = re.search(
            r"### Step 3:.*?(?=### Step \d+:|\Z)", content, re.DOTALL
        )
        assert step3_match, "Step 3 section not found"
        assert "#43" in step3_match.group(0), (
            "Step 3 should reference #43"
        )

        # 4. Steps 1 and 4 are unchanged (they never had placeholders)
        step1_match = re.search(
            r"### Step 1:.*?(?=### Step \d+:|\Z)", content, re.DOTALL
        )
        assert step1_match, "Step 1 section not found"
        assert "{{REPO}}" not in step1_match.group(0)
        assert "{{ISSUE_NUMBER}}" not in step1_match.group(0)
        assert "N/A" in step1_match.group(0), (
            "Step 1 should still say N/A"
        )

        step4_match = re.search(
            r"### Step 4:.*?(?=### Step \d+:|\Z)", content, re.DOTALL
        )
        assert step4_match, "Step 4 section not found"
        assert "{{REPO}}" not in step4_match.group(0)
        assert "{{ISSUE_NUMBER}}" not in step4_match.group(0)
        assert "N/A" in step4_match.group(0), (
            "Step 4 should still say N/A"
        )

        # No placeholders remain in the whole file
        assert "{{REPO}}" not in content
        assert "{{ISSUE_NUMBER}}" not in content
