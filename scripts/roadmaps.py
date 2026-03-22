#!/usr/bin/env python3
"""Cross-repo roadmap CLI tool.

Scans all repos in a projects directory for active feature roadmaps
and progress dashboards.

Usage:
    roadmaps --list                     List all roadmaps across all repos
    roadmaps --list-dashboards          List all dashboard URLs
    roadmaps --open-dashboards          Open all dashboard URLs in browser
    roadmaps --projects-dir <path>      Override projects directory (default: ~/projects)

Environment:
    ROADMAPS_PROJECTS_DIR   Override default projects directory
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


# --- Roadmap parsing (same logic as coordinator) ---

def count_steps(roadmap_path):
    """Count total and complete steps in a roadmap file."""
    content = Path(roadmap_path).read_text()
    total = len(re.findall(r"^### Step \d+:", content, re.MULTILINE))
    complete = len(re.findall(r"^\- \*\*Status\*\*:\s*Complete", content, re.MULTILINE | re.IGNORECASE))
    return total, complete


def parse_roadmap_meta(roadmap_path):
    """Parse top-level metadata from a roadmap file."""
    content = Path(roadmap_path).read_text()
    name_match = re.search(r"^# Feature Roadmap:\s*(.+)", content, re.MULTILINE)
    phase_match = re.search(r"\*\*Phase\*\*:\s*(\w+)", content)
    status_match = re.search(r"^\*\*Status\*\*:\s*(.+)", content, re.MULTILINE)

    name = name_match.group(1).strip() if name_match else Path(roadmap_path).stem.replace("-FeatureRoadmap", "")
    phase = phase_match.group(1) if phase_match else "Ready"
    status = status_match.group(1).strip() if status_match else "Not Started"
    total, complete = count_steps(roadmap_path)

    return {
        "name": name,
        "path": str(roadmap_path),
        "phase": phase,
        "status": status,
        "total": total,
        "complete": complete,
    }


def find_all_roadmaps(projects_dir):
    """Scan all repos for active roadmaps."""
    results = {}
    projects_path = Path(projects_dir).expanduser()
    if not projects_path.exists():
        return results

    for repo_dir in sorted(projects_path.iterdir()):
        if not repo_dir.is_dir():
            continue
        roadmap_dir = repo_dir / ".claude" / "Features" / "Active-Roadmaps"
        if not roadmap_dir.exists():
            continue
        roadmaps = []
        for f in sorted(roadmap_dir.glob("*-FeatureRoadmap.md")):
            meta = parse_roadmap_meta(f)
            if meta["status"].lower() != "complete":
                roadmaps.append(meta)
        if roadmaps:
            results[repo_dir.name] = roadmaps

    return results


# --- Dashboard scanning ---

def find_dashboards():
    """Find all dashboard directories in TMPDIR."""
    tmpdir = Path(os.environ.get("TMPDIR", "/tmp")).resolve()
    dashboards = []

    for d in sorted(tmpdir.glob("progress-dashboard-*")):
        if d.name == "progress-dashboard-active":
            continue
        if not d.is_dir():
            continue

        progress_file = d / "progress.json"
        port_file = d / "port"

        if not progress_file.exists():
            continue

        try:
            data = json.loads(progress_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        port = None
        if port_file.exists():
            try:
                port = int(port_file.read_text().strip())
            except (ValueError, OSError):
                pass

        title = data.get("title", d.name.replace("progress-dashboard-", ""))
        status = data.get("status", "unknown")
        url = f"http://127.0.0.1:{port}" if port else None

        # Check if server is actually running
        alive = False
        if port:
            try:
                import urllib.request
                urllib.request.urlopen(url, timeout=1)
                alive = True
            except Exception:
                pass

        env = data.get("environment", {})
        repo = env.get("repo", "unknown")
        # repo is like "org/repo-name" — take just the repo name
        repo_name = repo.split("/")[-1] if "/" in repo else repo

        dashboards.append({
            "title": title,
            "status": status,
            "port": port,
            "url": url,
            "alive": alive,
            "dir": str(d),
            "repo": repo_name,
        })

    return dashboards


# --- Display helpers ---

def progress_bar(complete, total, width=16):
    """Render a progress bar."""
    if total == 0:
        return "\u2591" * width
    filled = round(complete / total * width)
    return "\u2588" * filled + "\u2591" * (width - filled)


def status_color(status):
    """ANSI color for status."""
    s = status.lower()
    if s == "running":
        return "\033[33m"  # yellow
    elif s == "complete":
        return "\033[32m"  # green
    elif s in ("error", "stopped", "not running"):
        return "\033[31m"  # red
    return "\033[90m"  # gray


def reset_color():
    return "\033[0m"


# --- Commands ---

def cmd_list(projects_dir):
    """List all roadmaps across all repos."""
    all_roadmaps = find_all_roadmaps(projects_dir)

    if not all_roadmaps:
        print("No active roadmaps found.")
        return

    for repo_name, roadmaps in all_roadmaps.items():
        print(f"\033[1m{repo_name}\033[0m")
        for r in roadmaps:
            pct = round(r["complete"] / r["total"] * 100) if r["total"] > 0 else 0
            bar = progress_bar(r["complete"], r["total"])
            phase_tag = f"  \033[90m[{r['phase']}]\033[0m" if r["phase"] != "Ready" else ""
            print(f"  {r['name']:<35} {r['complete']:>2}/{r['total']:<2} steps  {bar} {pct:>3}%{phase_tag}")
        print()


def cmd_list_dashboards():
    """List all dashboard URLs, grouped by project."""
    dashboards = find_dashboards()

    if not dashboards:
        print("No dashboards found.")
        return

    # Group by repo
    by_repo = {}
    for d in dashboards:
        by_repo.setdefault(d["repo"], []).append(d)

    for repo_name in sorted(by_repo.keys()):
        print(f"\033[1m{repo_name}\033[0m")
        for d in by_repo[repo_name]:
            display_status = d["status"]
            if not d["alive"] and d["status"] == "running":
                display_status = "not running"
            color = status_color(display_status)
            alive_indicator = "\033[32m\u25CF\033[0m" if d["alive"] else "\033[90m\u25CB\033[0m"
            url_str = d["url"] or "no port"
            print(f"  {alive_indicator} {d['title']:<30} {url_str:<30} {color}{display_status}{reset_color()}")
        print()


def cmd_open_dashboards():
    """Open all dashboard URLs in browser."""
    dashboards = find_dashboards()
    opened = 0

    for d in dashboards:
        if d["url"] and d["alive"]:
            if sys.platform == "darwin":
                subprocess.Popen(["open", d["url"]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif shutil.which("xdg-open"):
                subprocess.Popen(["xdg-open", d["url"]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"  Opened: {d['title']} — {d['url']}")
            opened += 1
        elif d["url"]:
            print(f"  Skipped: {d['title']} — server not running")
        else:
            print(f"  Skipped: {d['title']} — no port")

    if opened == 0:
        print("No running dashboards to open.")


# --- Main ---

def main():
    parser = argparse.ArgumentParser(
        description="Cross-repo roadmap CLI tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  roadmaps --list\n  roadmaps --list-dashboards\n  roadmaps --open-dashboards",
    )
    parser.add_argument("--list", action="store_true", help="List all roadmaps across all repos")
    parser.add_argument("--list-dashboards", action="store_true", help="List all dashboard URLs")
    parser.add_argument("--open-dashboards", action="store_true", help="Open all dashboard URLs in browser")
    parser.add_argument("--projects-dir", default=None, help="Projects directory (default: ~/projects)")
    args = parser.parse_args()

    projects_dir = args.projects_dir or os.environ.get("ROADMAPS_PROJECTS_DIR", "~/projects")

    if args.list:
        cmd_list(projects_dir)
    elif args.list_dashboards:
        cmd_list_dashboards()
    elif args.open_dashboards:
        cmd_open_dashboards()
    else:
        # Default: show list
        cmd_list(projects_dir)


if __name__ == "__main__":
    main()
