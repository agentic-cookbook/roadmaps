#!/usr/bin/env python3
"""One-off script to add author and GUID metadata to all roadmap files.

For each repo in ~/projects:
- Definition files get **Author** and **ID** (GUID)
- Roadmap and Summary files get their own **ID** (GUID) and **Definition-ID**
  (the GUID of their corresponding Definition file)

Author info comes from git config (local preferred over global) per repo.
GUIDs are generated fresh (uuid4) and written once — re-running skips files
that already have an **ID** field.
"""

import re
import subprocess
import uuid
from pathlib import Path


PROJECTS_DIR = Path.home() / "projects"

# Repos that have Roadmaps/ directories
REPOS_WITH_ROADMAPS = [
    "cat-herding",
    "cat-herding-tests",
    "catnip",
    "claude-config",
    "scratching-post",
    "temporal",
]


def get_git_author(repo_dir):
    """Get user.name and user.email from git config, preferring local."""
    def git_config(key):
        # Try local first
        try:
            result = subprocess.run(
                ["git", "-C", str(repo_dir), "config", "--local", key],
                capture_output=True, text=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass
        # Fall back to effective config (includes global)
        try:
            result = subprocess.run(
                ["git", "-C", str(repo_dir), "config", key],
                capture_output=True, text=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass
        return None

    name = git_config("user.name")
    email = git_config("user.email")
    if name and email:
        return f"{name} <{email}>"
    elif name:
        return name
    return "Unknown"


def has_field(content, field_name):
    """Check if a markdown bold field already exists."""
    return bool(re.search(rf"^\*\*{field_name}\*\*:", content, re.MULTILINE))


def add_field_after(content, after_field, new_line):
    """Insert new_line after the line containing **after_field**:."""
    pattern = rf"(^\*\*{after_field}\*\*:.*$)"
    match = re.search(pattern, content, re.MULTILINE)
    if match:
        pos = match.end()
        return content[:pos] + "\n" + new_line + content[pos:]
    return None


def add_field_after_heading(content, new_line):
    """Insert new_line after the first markdown heading."""
    match = re.search(r"(^# .+$)", content, re.MULTILINE)
    if match:
        pos = match.end()
        return content[:pos] + "\n\n" + new_line + content[pos:]
    return None


def process_definition(filepath, author):
    """Add Author and ID to a Definition file."""
    content = filepath.read_text()
    modified = False

    if has_field(content, "ID"):
        print(f"  SKIP (has ID): {filepath.name}")
        return None  # already processed

    file_id = str(uuid.uuid4())

    # Add ID — try after Created, fall back to after heading
    if not has_field(content, "ID"):
        result = add_field_after(content, "Created", f"**ID**: {file_id}")
        if not result:
            result = add_field_after_heading(content, f"**ID**: {file_id}")
        if result:
            content = result
            modified = True

    if not has_field(content, "Author"):
        result = add_field_after(content, "ID", f"**Author**: {author}")
        if result:
            content = result
            modified = True

    if modified:
        filepath.write_text(content)
        print(f"  UPDATED: {filepath.name} (ID: {file_id[:8]}...)")
        return file_id
    return None


def process_roadmap_or_summary(filepath, definition_id, file_type):
    """Add ID and Definition-ID to a Roadmap or Summary file."""
    content = filepath.read_text()

    if has_field(content, "ID"):
        print(f"  SKIP (has ID): {filepath.name}")
        return

    file_id = str(uuid.uuid4())
    modified = False

    # Try anchors in order of preference
    if file_type == "roadmap":
        anchors = ["Created", "Phase", "Status", "Feature Definition"]
    else:
        anchors = ["Completed", "Feature Definition"]

    if not has_field(content, "ID"):
        result = None
        for anchor in anchors:
            result = add_field_after(content, anchor, f"**ID**: {file_id}")
            if result:
                break
        if not result:
            result = add_field_after_heading(content, f"**ID**: {file_id}")
        if result:
            content = result
            modified = True

    if not has_field(content, "Definition-ID") and definition_id:
        result = add_field_after(content, "ID", f"**Definition-ID**: {definition_id}")
        if result:
            content = result
            modified = True

    if modified:
        filepath.write_text(content)
        print(f"  UPDATED: {filepath.name} (ID: {file_id[:8]}..., Def-ID: {definition_id[:8] if definition_id else 'N/A'}...)")


def process_repo(repo_name):
    """Process all roadmap files in a single repo."""
    repo_dir = PROJECTS_DIR / repo_name
    roadmaps_dir = repo_dir / "Roadmaps"

    if not roadmaps_dir.exists():
        print(f"\n{repo_name}: no Roadmaps/ directory, skipping")
        return

    print(f"\n{'=' * 60}")
    print(f"  {repo_name}")
    print(f"{'=' * 60}")

    author = get_git_author(repo_dir)
    print(f"  Author: {author}")

    definitions_dir = roadmaps_dir / "Definitions"
    active_dir = roadmaps_dir / "Active"
    completed_dir = roadmaps_dir / "Completed"

    # Step 1: Process all Definition files, collecting their IDs
    definition_ids = {}  # feature_name -> guid
    if definitions_dir.exists():
        for f in sorted(definitions_dir.glob("*-Definition.md")):
            feature_name = f.name.replace("-Definition.md", "")
            file_id = process_definition(f, author)
            if file_id:
                definition_ids[feature_name] = file_id
            else:
                # Already has ID — read it
                content = f.read_text()
                match = re.search(r"^\*\*ID\*\*:\s*(.+)$", content, re.MULTILINE)
                if match:
                    definition_ids[feature_name] = match.group(1).strip()

    # Step 2: Process Roadmap files (Active + Completed)
    for roadmap_dir in [active_dir, completed_dir]:
        if not roadmap_dir.exists():
            continue
        for f in sorted(list(roadmap_dir.glob("*-Roadmap.md")) + list(roadmap_dir.glob("*-FeatureRoadmap.md"))):
            feature_name = f.name.replace("-Roadmap.md", "").replace("-FeatureRoadmap.md", "")
            def_id = definition_ids.get(feature_name)
            if not def_id:
                print(f"  WARNING: No Definition ID found for {feature_name}")
            process_roadmap_or_summary(f, def_id, "roadmap")

    # Step 3: Process Summary files (in Completed)
    if completed_dir.exists():
        for f in sorted(completed_dir.glob("*-Summary.md")):
            feature_name = f.name.replace("-Summary.md", "")
            def_id = definition_ids.get(feature_name)
            if not def_id:
                print(f"  WARNING: No Definition ID found for {feature_name}")
            process_roadmap_or_summary(f, def_id, "summary")


def main():
    print("Adding author and GUID metadata to all roadmap files")
    print(f"Projects dir: {PROJECTS_DIR}")

    for repo_name in REPOS_WITH_ROADMAPS:
        process_repo(repo_name)

    print("\nDone! Review changes with 'git diff' in each repo before committing.")


if __name__ == "__main__":
    main()
