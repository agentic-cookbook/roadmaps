"""Tests for scripts/roadmap_lib.py."""

import tempfile
from pathlib import Path

import pytest

import roadmap_lib as lib


# ---------------------------------------------------------------------------
# parse_frontmatter
# ---------------------------------------------------------------------------

class TestParseFrontmatter:
    def test_valid_yaml(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("---\ntitle: Hello\nauthor: Alice\n---\n\nBody text here.\n")
        meta, body = lib.parse_frontmatter(f)
        assert meta["title"] == "Hello"
        assert meta["author"] == "Alice"
        assert "Body text here." in body

    def test_no_frontmatter(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("# Just a heading\n\nSome content.\n")
        meta, body = lib.parse_frontmatter(f)
        assert meta == {}
        assert "Just a heading" in body

    def test_empty_file(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("")
        meta, body = lib.parse_frontmatter(f)
        assert meta == {}
        assert body == ""

    def test_quoted_values(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text('---\ntitle: "Quoted Value"\nauthor: \'Single\'\n---\n\nBody\n')
        meta, body = lib.parse_frontmatter(f)
        assert meta["title"] == "Quoted Value"
        assert meta["author"] == "Single"

    def test_nested_list(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text(
            "---\nid: abc\nchange-history:\n  - date: 2026-03-21\n"
            "    author: Test User\n    summary: Initial\n---\n\n# Body\n"
        )
        meta, body = lib.parse_frontmatter(f)
        assert meta["id"] == "abc"
        assert isinstance(meta["change-history"], list)
        assert len(meta["change-history"]) == 1
        assert meta["change-history"][0]["date"] == "2026-03-21"


# ---------------------------------------------------------------------------
# write_frontmatter + round-trip
# ---------------------------------------------------------------------------

class TestWriteFrontmatter:
    def test_round_trip(self, tmp_path):
        original_meta = {"title": "Test", "author": "Alice"}
        original_body = "# Body\n\nSome text.\n"
        content = lib.write_frontmatter(original_meta, original_body)

        f = tmp_path / "roundtrip.md"
        f.write_text(content)

        meta, body = lib.parse_frontmatter(f)
        assert meta["title"] == "Test"
        assert meta["author"] == "Alice"
        assert "Body" in body

    def test_write_no_body(self):
        content = lib.write_frontmatter({"key": "val"})
        assert content.startswith("---\n")
        assert content.endswith("---\n")
        assert "key: val" in content

    def test_write_with_list(self):
        meta = {"items": [{"a": "1", "b": "2"}]}
        content = lib.write_frontmatter(meta, "body")
        assert "items:" in content
        assert "  - a: 1" in content
        assert "    b: 2" in content


# ---------------------------------------------------------------------------
# current_state
# ---------------------------------------------------------------------------

class TestCurrentState:
    def test_multiple_state_files(self, tmp_roadmap_dir):
        rd = tmp_roadmap_dir / "Roadmaps" / "2026-03-21-FeatureAlpha"
        state = lib.current_state(rd)
        # Should pick the newest by name sort: Ready > Created
        assert state == "Ready"

    def test_empty_state_dir(self, tmp_path):
        rd = tmp_path / "EmptyRoadmap"
        rd.mkdir()
        (rd / "State").mkdir()
        state = lib.current_state(rd)
        assert state == "Unknown"

    def test_no_state_dir(self, tmp_path):
        rd = tmp_path / "NoStateRoadmap"
        rd.mkdir()
        state = lib.current_state(rd)
        assert state == "Unknown"


# ---------------------------------------------------------------------------
# is_active
# ---------------------------------------------------------------------------

class TestIsActive:
    @pytest.mark.parametrize("state_name", ["Created", "Planning", "Ready", "Implementing", "Paused"])
    def test_active_states(self, tmp_path, state_name):
        rd = tmp_path / "2026-03-21-Test"
        rd.mkdir()
        (rd / "State").mkdir()
        (rd / "State" / f"2026-03-21-{state_name}.md").write_text(f"# State: {state_name}\n")
        assert lib.is_active(rd) is True

    def test_complete_is_not_active(self, tmp_path):
        rd = tmp_path / "2026-03-21-Test"
        rd.mkdir()
        (rd / "State").mkdir()
        (rd / "State" / "2026-03-21-Complete.md").write_text("# State: Complete\n")
        assert lib.is_active(rd) is False


# ---------------------------------------------------------------------------
# is_implementable
# ---------------------------------------------------------------------------

class TestIsImplementable:
    def test_ready_is_implementable(self, tmp_roadmap_dir):
        rd = tmp_roadmap_dir / "Roadmaps" / "2026-03-21-FeatureAlpha"
        assert lib.is_implementable(rd) is True

    def test_complete_not_implementable(self, tmp_roadmap_dir):
        rd = tmp_roadmap_dir / "Roadmaps" / "2026-03-22-FeatureBeta"
        assert lib.is_implementable(rd) is False

    @pytest.mark.parametrize("state_name", ["Created", "Planning", "Implementing", "Paused"])
    def test_non_ready_not_implementable(self, tmp_path, state_name):
        rd = tmp_path / "2026-03-21-Test"
        rd.mkdir()
        (rd / "State").mkdir()
        (rd / "State" / f"2026-03-21-{state_name}.md").write_text(f"# State: {state_name}\n")
        assert lib.is_implementable(rd) is False


# ---------------------------------------------------------------------------
# get_feature_name
# ---------------------------------------------------------------------------

class TestGetFeatureName:
    def test_from_dir_name(self, tmp_roadmap_dir):
        rd = tmp_roadmap_dir / "Roadmaps" / "2026-03-21-FeatureAlpha"
        assert lib.get_feature_name(rd) == "FeatureAlpha"

    def test_heading_fallback(self, tmp_path):
        rd = tmp_path / "NoDateDir"
        rd.mkdir()
        (rd / "Roadmap.md").write_text("# Feature Roadmap: FallbackName\n\nContent\n")
        assert lib.get_feature_name(rd) == "FallbackName"

    def test_bare_dirname_fallback(self, tmp_path):
        rd = tmp_path / "JustAName"
        rd.mkdir()
        # No Roadmap.md and no date prefix
        assert lib.get_feature_name(rd) == "JustAName"


# ---------------------------------------------------------------------------
# count_steps
# ---------------------------------------------------------------------------

class TestCountSteps:
    def test_counts_total_and_complete(self, tmp_roadmap_dir):
        rm = tmp_roadmap_dir / "Roadmaps" / "2026-03-21-FeatureAlpha" / "Roadmap.md"
        total, complete = lib.count_steps(rm)
        assert total == 3
        assert complete == 1

    def test_all_complete(self, tmp_roadmap_dir):
        rm = tmp_roadmap_dir / "Roadmaps" / "2026-03-22-FeatureBeta" / "Roadmap.md"
        total, complete = lib.count_steps(rm)
        assert total == 1
        assert complete == 1


# ---------------------------------------------------------------------------
# find_roadmap_dirs
# ---------------------------------------------------------------------------

class TestFindRoadmapDirs:
    def test_finds_dirs_with_roadmap_md(self, tmp_roadmap_dir):
        dirs = lib.find_roadmap_dirs(tmp_roadmap_dir)
        names = [d.name for d in dirs]
        assert "2026-03-21-FeatureAlpha" in names
        assert "2026-03-22-FeatureBeta" in names

    def test_empty_when_no_roadmaps_dir(self, tmp_path):
        dirs = lib.find_roadmap_dirs(tmp_path)
        assert dirs == []

    def test_skips_dirs_without_roadmap_md(self, tmp_path):
        roadmaps = tmp_path / "Roadmaps"
        empty_dir = roadmaps / "2026-01-01-NoRoadmap"
        empty_dir.mkdir(parents=True)
        dirs = lib.find_roadmap_dirs(tmp_path)
        assert len(dirs) == 0


# ---------------------------------------------------------------------------
# parse_inline_fields
# ---------------------------------------------------------------------------

class TestParseInlineFields:
    def test_parses_field_value_pairs(self):
        content = (
            "Some text\n"
            "**Status**: Complete\n"
            "**Type**: Auto\n"
            "**Complexity**: S\n"
            "More text\n"
        )
        fields = lib.parse_inline_fields(content)
        assert fields["Status"] == "Complete"
        assert fields["Type"] == "Auto"
        assert fields["Complexity"] == "S"

    def test_empty_content(self):
        fields = lib.parse_inline_fields("")
        assert fields == {}

    def test_no_matching_fields(self):
        fields = lib.parse_inline_fields("Just plain text\nNo fields here\n")
        assert fields == {}
