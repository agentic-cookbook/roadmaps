#!/usr/bin/env python3
"""Migrate completed roadmap directories to flat <Name>-Roadmap.md files.

For each repo in ~/projects with completed/archived/declined roadmaps:
1. Merges Definition.md content into Roadmap.md (if present)
2. Replaces Completion Checklist with Change History placeholder
3. Copies as <FeatureName>-Roadmap.md into Roadmaps/
4. Removes the old directory
5. Commits and pushes per repo

Usage:
    migrate-to-flat-roadmaps.py              Dry run (default)
    migrate-to-flat-roadmaps.py --apply      Execute migration
    migrate-to-flat-roadmaps.py --repo NAME  Single repo only
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import roadmap_lib as lib

PROJECTS_DIR = Path.home() / "projects"
TERMINAL_STATES = {"Complete", "Archived", "Declined"}
SKIP_DIRS = {"PartialComplete", "AllAuto3Step"}  # test fixtures

CHANGE_HISTORY_SECTION = """\
## Change History

_Populated automatically by /implement-roadmap when the feature is complete._

### Commits

| Hash | Description |
|------|-------------|

### Issues

| Issue | Title |
|-------|-------|

### Pull Request

_N/A — predates Change History feature_
"""


def get_feature_name(dirname):
    """Extract feature name from YYYY-MM-DD-Name or bare Name."""
    parts = dirname.split("-", 3)
    if len(parts) >= 4 and len(parts[0]) == 4:
        return parts[3]
    return dirname


def get_state(roadmap_dir):
    """Get the current state from State/ directory."""
    return lib.current_state(roadmap_dir)


def merge_definition_into_roadmap(roadmap_dir):
    """If Definition.md exists, merge its body into Roadmap.md after the heading."""
    def_path = roadmap_dir / "Definition.md"
    rm_path = roadmap_dir / "Roadmap.md"

    if not def_path.exists():
        return False

    def_content = def_path.read_text()
    rm_content = rm_path.read_text()

    # Extract definition body (after frontmatter and heading)
    _, def_body = lib.parse_frontmatter(def_path)
    # Strip the # heading line
    def_body = re.sub(r'^#[^\n]*\n+', '', def_body, count=1)

    if not def_body.strip():
        return False

    # Insert after the # Feature Roadmap: heading in Roadmap.md
    heading_match = re.search(r'^# .+\n', rm_content, re.MULTILINE)
    if heading_match:
        insert_pos = heading_match.end()
        rm_content = (
            rm_content[:insert_pos]
            + "\n" + def_body.strip() + "\n\n"
            + rm_content[insert_pos:]
        )
    else:
        # No heading found, prepend
        rm_content = def_body + "\n\n" + rm_content

    # Remove definition-id from frontmatter if present
    rm_content = re.sub(r'^definition-id:.*\n', '', rm_content, flags=re.MULTILINE)

    rm_path.write_text(rm_content)
    return True


def replace_completion_checklist(roadmap_path):
    """Replace Completion Checklist section with Change History."""
    content = roadmap_path.read_text()

    # Find and remove Completion Checklist section
    pattern = r'## Completion Checklist\n.*?(?=\n## |\Z)'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        content = content[:match.start()] + content[match.end():]

    # Add Change History if not already present
    if "## Change History" not in content:
        # Add before Deviations from Plan if it exists, otherwise at end
        dev_match = re.search(r'\n## Deviations from Plan', content)
        if dev_match:
            content = (
                content[:dev_match.start()]
                + "\n\n" + CHANGE_HISTORY_SECTION
                + content[dev_match.start():]
            )
        else:
            content = content.rstrip() + "\n\n" + CHANGE_HISTORY_SECTION

    roadmap_path.write_text(content)


def run_git(args, cwd):
    """Run a git command."""
    result = subprocess.run(
        ["git"] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"    git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.returncode == 0


def find_repos():
    """Find all repos in ~/projects/ that have Roadmaps/."""
    repos = []
    for d in sorted(PROJECTS_DIR.iterdir()):
        if d.is_dir() and (d / "Roadmaps").is_dir() and (d / ".git").exists():
            repos.append(d)
    return repos


def migrate_repo(repo_path, apply=False):
    """Migrate all terminal-state roadmaps in a single repo."""
    roadmaps_dir = repo_path / "Roadmaps"
    repo_name = repo_path.name
    migrated = []

    for d in sorted(roadmaps_dir.iterdir()):
        if not d.is_dir():
            continue
        if d.name in SKIP_DIRS:
            continue
        if not (d / "Roadmap.md").exists():
            continue

        state = get_state(d)
        if state not in TERMINAL_STATES:
            continue

        feature_name = get_feature_name(d.name)
        dest_name = f"{feature_name}-Roadmap.md"
        dest_path = roadmaps_dir / dest_name

        if dest_path.exists():
            print(f"  SKIP {d.name} → {dest_name} (already exists)")
            continue

        has_def = (d / "Definition.md").exists()
        print(f"  {'MIGRATE' if apply else 'WOULD MIGRATE'} {d.name} → {dest_name}  [{state}]"
              + (f"  (merge Definition.md)" if has_def else ""))

        if apply:
            # 1. Merge Definition.md if present
            if has_def:
                merge_definition_into_roadmap(d)

            # 2. Replace Completion Checklist with Change History
            replace_completion_checklist(d / "Roadmap.md")

            # 3. Copy as flat file
            shutil.copy2(str(d / "Roadmap.md"), str(dest_path))

            # 4. Remove old directory
            shutil.rmtree(str(d))

        migrated.append(dest_name)

    if migrated and apply:
        # Commit and push
        run_git(["add", "-A", "Roadmaps/"], cwd=repo_path)
        run_git(
            ["commit", "-m", f"refactor: migrate {len(migrated)} roadmaps to flat file format"],
            cwd=repo_path,
        )
        run_git(["push"], cwd=repo_path)
        print(f"  Committed and pushed {len(migrated)} migrations")

    return migrated


def main():
    parser = argparse.ArgumentParser(description="Migrate roadmap directories to flat files")
    parser.add_argument("--apply", action="store_true", help="Execute migration (default is dry run)")
    parser.add_argument("--repo", type=str, help="Migrate a single repo by name")
    args = parser.parse_args()

    if not args.apply:
        print("\n  DRY RUN — pass --apply to execute\n")

    repos = find_repos()
    if args.repo:
        repos = [r for r in repos if r.name == args.repo]
        if not repos:
            print(f"Repo '{args.repo}' not found in {PROJECTS_DIR}")
            sys.exit(1)

    total = 0
    for repo in repos:
        roadmap_dirs = [
            d for d in sorted((repo / "Roadmaps").iterdir())
            if d.is_dir() and (d / "Roadmap.md").exists()
            and d.name not in SKIP_DIRS
            and get_state(d) in TERMINAL_STATES
        ]
        if not roadmap_dirs:
            continue

        print(f"\n{repo.name}/")
        migrated = migrate_repo(repo, apply=args.apply)
        total += len(migrated)

    print(f"\n{'Migrated' if args.apply else 'Would migrate'}: {total} roadmaps\n")


if __name__ == "__main__":
    main()
