#!/usr/bin/env python3
"""Migrate roadmaps from flat layout to per-directory File Record structure.

For each repo in ~/projects with a Roadmaps/ directory:
1. Groups files by feature name from Active/, Completed/, Definitions/
2. Creates Roadmaps/YYYY-MM-DD-FeatureName/ with State/ and History/
3. git mv files to new locations with simplified names
4. Converts inline **Field**: value to YAML frontmatter
5. Removes **Status**/**Phase** from Roadmap.md (State/ is authoritative)
6. Creates initial State/ and History/ entries
7. Removes empty Active/, Completed/, Definitions/ directories
8. Commits and pushes per repo

Usage:
    migrate-roadmaps.py                Run on all repos
    migrate-roadmaps.py --dry-run      Show what would be done without changes
    migrate-roadmaps.py --repo NAME    Run on a single repo
"""

import argparse
import os
import re
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add scripts/ to path for roadmap_lib
sys.path.insert(0, str(Path(__file__).parent))
from roadmap_lib import parse_inline_fields, write_frontmatter

PROJECTS_DIR = Path.home() / "projects"
NOW = datetime.now()
NOW_DATE = NOW.strftime("%Y-%m-%d")
NOW_TIMESTAMP = NOW.strftime("%Y-%m-%d-%H%M%S")

REPOS_WITH_ROADMAPS = [
    "tests/roadmaps-tests",  # test repo first
    "active/cat-herding",
    "active/catnip",
    "deprecated/claude-config",
    "active/scratching-post",
    "active/temporal",
]


def get_git_author(repo_dir):
    """Get user.name and user.email from git config, preferring local."""
    def git_config(key):
        for flag in ["--local", None]:
            try:
                cmd = ["git", "-C", str(repo_dir), "config"]
                if flag:
                    cmd.append(flag)
                cmd.append(key)
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
            except Exception:
                pass
        return None

    name = git_config("user.name")
    email = git_config("user.email")
    if name and email:
        return f"{name} <{email}>"
    return name or "Unknown"


def git_first_commit_date(repo_dir, filepath):
    """Get the date of the first commit that introduced a file."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_dir), "log", "--diff-filter=A",
             "--format=%aI", "--", str(filepath)],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            # Parse ISO date, return YYYY-MM-DD
            date_str = result.stdout.strip().split("\n")[-1]
            return date_str[:10]
    except Exception:
        pass
    return None


def run_git(repo_dir, *args, check=True):
    """Run a git command in the given repo."""
    cmd = ["git", "-C", str(repo_dir)] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"  ERROR: git {' '.join(args)}: {result.stderr.strip()}")
    return result


def discover_features(repo_dir):
    """Discover all features from old layout, grouped by name.

    Returns dict: feature_name -> {
        'definition_path': Path or None,
        'roadmap_path': Path or None,
        'summary_path': Path or None,
        'location': 'active' | 'completed',
    }
    """
    roadmaps_dir = Path(repo_dir) / "Roadmaps"
    features = {}

    # Scan definitions
    defs_dir = roadmaps_dir / "Definitions"
    if defs_dir.exists():
        for f in sorted(defs_dir.glob("*-Definition.md")):
            name = f.stem.replace("-Definition", "")
            features.setdefault(name, {})["definition_path"] = f

    # Scan active roadmaps
    active_dir = roadmaps_dir / "Active"
    if active_dir.exists():
        for f in sorted(list(active_dir.glob("*-Roadmap.md")) +
                        list(active_dir.glob("*-FeatureRoadmap.md"))):
            name = f.stem.replace("-Roadmap", "").replace("-FeatureRoadmap", "")
            features.setdefault(name, {})["roadmap_path"] = f
            features[name]["location"] = "active"

    # Scan completed roadmaps + summaries
    completed_dir = roadmaps_dir / "Completed"
    if completed_dir.exists():
        for f in sorted(list(completed_dir.glob("*-Roadmap.md")) +
                        list(completed_dir.glob("*-FeatureRoadmap.md"))):
            name = f.stem.replace("-Roadmap", "").replace("-FeatureRoadmap", "")
            features.setdefault(name, {})["roadmap_path"] = f
            features[name]["location"] = "completed"

        for f in sorted(completed_dir.glob("*-Summary.md")):
            name = f.stem.replace("-Summary", "")
            features.setdefault(name, {})["summary_path"] = f

    return features


def get_creation_date(repo_dir, feature):
    """Determine the creation date for a feature.

    Priority: **Created**: field in Definition > git log > today.
    """
    # Try Definition file
    def_path = feature.get("definition_path")
    if def_path and def_path.exists():
        content = def_path.read_text()
        fields = parse_inline_fields(content)
        created = fields.get("Created")
        if created and re.match(r"\d{4}-\d{2}-\d{2}", created):
            return created

    # Try Roadmap file
    rm_path = feature.get("roadmap_path")
    if rm_path and rm_path.exists():
        content = rm_path.read_text()
        fields = parse_inline_fields(content)
        created = fields.get("Created")
        if created and re.match(r"\d{4}-\d{2}-\d{2}", created):
            return created

    # Try git log
    for path_key in ["definition_path", "roadmap_path"]:
        fpath = feature.get(path_key)
        if fpath and fpath.exists():
            git_date = git_first_commit_date(repo_dir, fpath)
            if git_date:
                return git_date

    return NOW_DATE


def get_roadmap_state(feature):
    """Determine the initial state based on old layout location and fields."""
    rm_path = feature.get("roadmap_path")
    location = feature.get("location", "active")

    if location == "completed":
        return "Complete"

    if rm_path and rm_path.exists():
        content = rm_path.read_text()
        fields = parse_inline_fields(content)
        phase = fields.get("Phase", "Ready")
        status = fields.get("Status", "Not Started")

        if status.lower() == "complete":
            return "Complete"
        if phase == "Planning":
            return "Planning"
        if phase == "Ready":
            return "Ready"

    return "Ready"


def convert_to_frontmatter(content, file_type, author, definition_id=None,
                            existing_id=None, created_date=None):
    """Convert a file's inline **Field**: value metadata to YAML frontmatter.

    Strips inline metadata fields from the body and creates a frontmatter block.
    For Roadmap.md, also removes **Status**:, **Phase**:, **Implementing**:
    since State/ is now authoritative.

    Returns (frontmatter_str + body_str).
    """
    # Extract existing inline fields
    fields = parse_inline_fields(content)

    # Build frontmatter metadata
    file_id = existing_id or fields.get("ID") or str(uuid.uuid4())
    created = created_date or fields.get("Created") or fields.get("Completed") or NOW_DATE
    author_val = fields.get("Author") or author

    meta = {
        "id": file_id,
        "created": created,
        "modified": NOW_DATE,
        "author": author_val,
    }

    if definition_id:
        meta["definition-id"] = definition_id

    meta["change-history"] = [{
        "date": NOW_DATE,
        "author": author_val,
        "summary": "Migrated to per-directory File Record structure",
    }]

    # Remove inline metadata fields from body
    # Fields to remove from ALL file types
    remove_fields = {"ID", "Author", "Created", "Modified", "Definition-ID",
                     "Completion Date", "Feature Definition"}

    # For roadmaps, also remove lifecycle fields (State/ is authoritative)
    if file_type == "roadmap":
        remove_fields.update({"Status", "Phase", "Implementing"})

    # For summaries, "Completed" becomes "created" in frontmatter
    if file_type == "summary":
        remove_fields.add("Completed")

    # Remove field lines and any surrounding blank lines that become excessive
    body_lines = content.split("\n")
    cleaned_lines = []
    for line in body_lines:
        should_remove = False
        for field in remove_fields:
            if re.match(rf"^\*\*{re.escape(field)}\*\*:", line):
                should_remove = True
                break
        # Also remove HTML comments about Phase
        if line.strip().startswith("<!-- Phase:"):
            should_remove = True
        if not should_remove:
            cleaned_lines.append(line)

    # Collapse multiple consecutive blank lines into at most two
    body = "\n".join(cleaned_lines)
    body = re.sub(r"\n{3,}", "\n\n", body)
    body = body.strip()

    return write_frontmatter(meta, body)


def migrate_feature(repo_dir, name, feature, author, dry_run=False):
    """Migrate a single feature to the new per-directory layout."""
    roadmaps_dir = Path(repo_dir) / "Roadmaps"
    created_date = get_creation_date(repo_dir, feature)
    state = get_roadmap_state(feature)
    new_dir = roadmaps_dir / f"{created_date}-{name}"

    print(f"\n  {name}")
    print(f"    Created: {created_date}, State: {state}")
    print(f"    Dir: {new_dir.name}/")

    if dry_run:
        for key in ["definition_path", "roadmap_path", "summary_path"]:
            if feature.get(key):
                new_name = {"definition_path": "Definition.md",
                            "roadmap_path": "Roadmap.md",
                            "summary_path": "Summary.md"}[key]
                print(f"    {feature[key].name} → {new_name}")
        return

    # Create directory structure
    (new_dir / "State").mkdir(parents=True, exist_ok=True)
    (new_dir / "History").mkdir(parents=True, exist_ok=True)

    # Get or generate the definition ID (foreign key for other files)
    definition_id = None
    def_path = feature.get("definition_path")
    if def_path and def_path.exists():
        fields = parse_inline_fields(def_path.read_text())
        definition_id = fields.get("ID") or str(uuid.uuid4())

    # Process Definition file
    if def_path and def_path.exists():
        content = def_path.read_text()
        new_content = convert_to_frontmatter(
            content, "definition", author,
            existing_id=definition_id, created_date=created_date,
        )
        # Write converted content, then git mv
        def_path.write_text(new_content)
        new_def = new_dir / "Definition.md"
        run_git(repo_dir, "mv", str(def_path), str(new_def))
        print(f"    ✓ Definition.md")

    # Process Roadmap file
    rm_path = feature.get("roadmap_path")
    if rm_path and rm_path.exists():
        content = rm_path.read_text()
        # Get roadmap's own ID
        rm_fields = parse_inline_fields(content)
        rm_id = rm_fields.get("ID") or str(uuid.uuid4())
        new_content = convert_to_frontmatter(
            content, "roadmap", author,
            definition_id=definition_id, existing_id=rm_id,
            created_date=created_date,
        )
        rm_path.write_text(new_content)
        new_rm = new_dir / "Roadmap.md"
        run_git(repo_dir, "mv", str(rm_path), str(new_rm))
        print(f"    ✓ Roadmap.md")

    # Process Summary file
    sum_path = feature.get("summary_path")
    if sum_path and sum_path.exists():
        content = sum_path.read_text()
        sum_fields = parse_inline_fields(content)
        sum_id = sum_fields.get("ID") or str(uuid.uuid4())
        sum_created = sum_fields.get("Completed") or created_date
        new_content = convert_to_frontmatter(
            content, "summary", author,
            definition_id=definition_id, existing_id=sum_id,
            created_date=sum_created,
        )
        sum_path.write_text(new_content)
        new_sum = new_dir / "Summary.md"
        run_git(repo_dir, "mv", str(sum_path), str(new_sum))
        print(f"    ✓ Summary.md")

    # Create State file
    state_id = str(uuid.uuid4())
    state_meta = {
        "id": state_id,
        "created": NOW_DATE,
        "author": author,
        "definition-id": definition_id or "unknown",
        "previous-state": "none",
    }
    state_body = f"# State: {state}\n\nMigrated from {'Completed/' if state == 'Complete' else 'Active/'} directory."
    state_content = write_frontmatter(state_meta, state_body)
    state_file = new_dir / "State" / f"{NOW_DATE}-{state}.md"
    state_file.write_text(state_content)
    print(f"    ✓ State/{state_file.name}")

    # Create History entry
    history_id = str(uuid.uuid4())
    history_meta = {
        "id": history_id,
        "created": NOW_DATE,
        "author": author,
        "definition-id": definition_id or "unknown",
    }
    history_body = f"# Event: Migrated\n\nMigrated from flat layout (Active/Completed/Definitions) to per-directory File Record structure."
    history_content = write_frontmatter(history_meta, history_body)
    history_file = new_dir / "History" / f"{NOW_TIMESTAMP}-Migrated.md"
    history_file.write_text(history_content)
    print(f"    ✓ History/{history_file.name}")


def cleanup_empty_dirs(repo_dir, dry_run=False):
    """Remove empty Active/, Completed/, Definitions/ directories."""
    roadmaps_dir = Path(repo_dir) / "Roadmaps"
    for subdir in ["Active", "Completed", "Definitions"]:
        d = roadmaps_dir / subdir
        if d.exists():
            remaining = list(d.iterdir())
            if not remaining:
                if dry_run:
                    print(f"    Would remove empty: {subdir}/")
                else:
                    d.rmdir()
                    print(f"    Removed empty: {subdir}/")
            else:
                print(f"    WARNING: {subdir}/ still has files: {[f.name for f in remaining]}")


def process_repo(repo_name, dry_run=False):
    """Migrate all roadmaps in a single repo."""
    repo_dir = PROJECTS_DIR / repo_name
    roadmaps_dir = repo_dir / "Roadmaps"

    if not roadmaps_dir.exists():
        print(f"\n{repo_name}: no Roadmaps/ directory, skipping")
        return

    # Check if already migrated (new layout dirs exist)
    new_dirs = [d for d in roadmaps_dir.iterdir()
                if d.is_dir() and (d / "Roadmap.md").exists()]
    if new_dirs:
        print(f"\n{repo_name}: already migrated ({len(new_dirs)} roadmap dirs found), skipping")
        return

    features = discover_features(repo_dir)
    if not features:
        print(f"\n{repo_name}: no features found, skipping")
        return

    author = get_git_author(repo_dir)

    print(f"\n{'=' * 60}")
    print(f"  {repo_name} ({len(features)} features)")
    print(f"{'=' * 60}")
    print(f"  Author: {author}")
    if dry_run:
        print(f"  ** DRY RUN **")

    for name, feature_data in sorted(features.items()):
        migrate_feature(repo_dir, name, feature_data, author, dry_run=dry_run)

    # Cleanup empty old directories
    if not dry_run:
        print()
        cleanup_empty_dirs(repo_dir)

        # Stage and commit
        run_git(repo_dir, "add", "-A", "Roadmaps/")
        run_git(repo_dir, "commit", "-m",
                "refactor: migrate roadmaps to per-directory File Record structure\n\n"
                "Each roadmap now lives in its own Roadmaps/YYYY-MM-DD-Name/ directory\n"
                "with Definition.md, Roadmap.md, State/, and History/ subdirectories.\n"
                "Metadata converted from inline **Field**: value to YAML frontmatter.\n"
                "Status/Phase removed from Roadmap.md — State/ is now authoritative.\n\n"
                "Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>")
        run_git(repo_dir, "push")
        print(f"  Committed and pushed.")
    else:
        print()
        cleanup_empty_dirs(repo_dir, dry_run=True)


def main():
    parser = argparse.ArgumentParser(description="Migrate roadmaps to per-directory structure")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--repo", help="Run on a single repo")
    args = parser.parse_args()

    repos = [args.repo] if args.repo else REPOS_WITH_ROADMAPS

    print("Migrating roadmaps to per-directory File Record structure")
    print(f"Projects dir: {PROJECTS_DIR}")

    for repo_name in repos:
        process_repo(repo_name, dry_run=args.dry_run)

    print("\nDone!")


if __name__ == "__main__":
    main()
