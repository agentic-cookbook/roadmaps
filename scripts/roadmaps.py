#!/usr/bin/env python3
"""Cross-repo roadmap CLI tool.

Scans all repos in a projects directory for active feature roadmaps
and progress dashboards.

Usage:
    roadmaps --list                         List active roadmaps (running + ready)
    roadmaps --list --running               Show only running roadmaps
    roadmaps --list --complete              Include completed roadmaps
    roadmaps --list --archived              Include archived roadmaps
    roadmaps --list --all                   Show everything (running + active + complete + archived)
    roadmaps --list --search <text>         Filter by name
    roadmaps --list --sort <field>          Sort by: number, name, modified, created (default: number)
    roadmaps --list-dashboards              List all dashboard URLs
    roadmaps --open-dashboards              Open all dashboard URLs in browser
    roadmaps --monitor [SECONDS]            Live monitor roadmaps + dashboards (default: 30s)
    roadmaps --archive-completed             Archive all completed roadmaps
    roadmaps --decline                      Interactively decline roadmaps
    roadmaps --projects-dir <path>          Override projects directory (default: ~/projects)

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
import time
from datetime import datetime
from pathlib import Path

# Add scripts/ to path for roadmap_lib
sys.path.insert(0, str(Path(__file__).parent))
import roadmap_lib as lib


# --- Roadmap scanning ---

def find_all_roadmaps(projects_dir):
    """Scan all repos for roadmaps. Returns flat list with repo_name on each entry."""
    results = []
    projects_path = Path(projects_dir).expanduser()
    if not projects_path.exists():
        return results

    for repo_dir in sorted(projects_path.iterdir()):
        if not repo_dir.is_dir():
            continue

        # New per-directory layout: Roadmaps/YYYY-MM-DD-Name/
        roadmap_dirs = lib.find_roadmap_dirs(repo_dir)
        if roadmap_dirs:
            for rd in roadmap_dirs:
                state = lib.current_state(rd)
                active = lib.is_active(rd)
                rm_file = lib.roadmap_path(rd)
                name = lib.get_feature_name(rd)
                total, complete = lib.count_steps(rm_file)
                # Extract number from dir name for sorting
                dirname = rd.name
                results.append({
                    "name": name,
                    "repo": repo_dir.name,
                    "path": str(rm_file),
                    "dir": dirname,
                    "roadmap_dir": str(rd),
                    "state": state,
                    "total": total,
                    "complete": complete,
                    "is_complete": state == "Complete",
                    "is_active": active and state != "Complete",
                    "is_running": active and complete > 0 and complete < total,
                    "is_archived": state in ("Archived", "Declined"),
                })
        else:
            # Old flat layout fallback
            old = lib.find_roadmaps_old_layout(repo_dir)
            for entry in old:
                if not entry.get("roadmap_path"):
                    continue
                rm_path = entry["roadmap_path"]
                is_completed = entry["location"] == "completed"
                name = lib.parse_roadmap_heading(rm_path) or entry["name"]
                total, complete = lib.count_steps(rm_path)
                results.append({
                    "name": name,
                    "repo": repo_dir.name,
                    "path": str(rm_path),
                    "dir": rm_path.parent.name,
                    "state": "Complete" if is_completed else "Ready",
                    "total": total,
                    "complete": complete,
                    "is_complete": is_completed,
                    "is_active": not is_completed,
                    "is_running": False,
                    "is_archived": is_completed,
                })

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


# --- CWD-based project detection ---

def detect_project(projects_dir):
    """Detect project name from CWD if inside a project subdirectory.

    Returns the project directory name if CWD is inside one, else None
    (meaning show all projects).
    """
    cwd = Path.cwd().resolve()
    projects_path = Path(projects_dir).expanduser().resolve()

    if not str(cwd).startswith(str(projects_path)):
        return None

    relative = cwd.relative_to(projects_path)
    parts = relative.parts
    if not parts:
        return None

    return parts[0]


# --- Commands ---

def cmd_list(projects_dir, project=None, show_running=True, show_active=True,
             show_complete=False, show_archived=False, search=None, sort_by="number"):
    """List roadmaps with filtering, sorting, and search."""
    all_roadmaps = find_all_roadmaps(projects_dir)

    if project:
        all_roadmaps = [r for r in all_roadmaps if r["repo"] == project]

    # Filter
    filtered = []
    for r in all_roadmaps:
        if show_running and r["is_running"]:
            filtered.append(r)
        elif show_active and r["is_active"]:
            filtered.append(r)
        elif show_complete and r["is_complete"] and not r["is_archived"]:
            filtered.append(r)
        elif show_archived and r["is_archived"]:
            filtered.append(r)

    # Search
    if search:
        search_lower = search.lower()
        filtered = [r for r in filtered if search_lower in r["name"].lower()]

    # Sort
    if sort_by == "name":
        filtered.sort(key=lambda r: r["name"].lower())
    elif sort_by == "modified":
        filtered.sort(key=lambda r: r["dir"], reverse=True)
    elif sort_by == "created":
        filtered.sort(key=lambda r: r["dir"])
    else:  # number (default) — by directory name which starts with date
        filtered.sort(key=lambda r: r["dir"])

    if not filtered:
        print("No roadmaps match the current filters.")
        return

    # Group by repo for display
    by_repo = {}
    for r in filtered:
        by_repo.setdefault(r["repo"], []).append(r)

    for repo_name, roadmaps in sorted(by_repo.items()):
        print(f"\033[1m{repo_name}\033[0m")
        for r in roadmaps:
            pct = round(r["complete"] / r["total"] * 100) if r["total"] > 0 else 0
            bar = progress_bar(r["complete"], r["total"])

            # State in parens with color
            state = r.get("state", "Unknown")
            if r["is_archived"]:
                state_str = f"\033[90m({state})\033[0m"
            elif r["is_complete"]:
                state_str = f"\033[32m({state})\033[0m"
            elif r["is_running"]:
                state_str = f"\033[33m({state})\033[0m"
            else:
                state_str = f"\033[90m({state})\033[0m"

            print(f"  {r['name']:<35} {r['complete']:>2}/{r['total']:<2} steps  {bar} {pct:>3}%  {state_str}")
        print()


def cmd_list_dashboards(project=None):
    """List all dashboard URLs, grouped by project."""
    dashboards = find_dashboards()

    if not dashboards:
        print("No dashboards found.")
        return

    # Group by repo
    by_repo = {}
    for d in dashboards:
        by_repo.setdefault(d["repo"], []).append(d)

    if project:
        by_repo = {k: v for k, v in by_repo.items() if k == project}
        if not by_repo:
            print("No dashboards found.")
            return

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
            print(f"    \033[90m{d['dir']}\033[0m")
        print()


def cmd_open_dashboards(project=None):
    """Open all dashboard URLs in browser."""
    dashboards = find_dashboards()

    if project:
        dashboards = [d for d in dashboards if d["repo"] == project]

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



def cmd_archive_completed(projects_dir, project=None):
    """Archive all completed roadmaps by transitioning them to Archived state."""
    all_roadmaps = find_all_roadmaps(projects_dir)

    if project:
        all_roadmaps = [r for r in all_roadmaps if r["repo"] == project]

    completed = [r for r in all_roadmaps if r["is_complete"]]

    if not completed:
        print("No completed roadmaps to archive.")
        return

    archived = 0
    for r in completed:
        roadmap_dir = r.get("roadmap_dir")
        if not roadmap_dir:
            print(f"  \033[90mSkipped: {r['name']} ({r['repo']}) — old layout\033[0m")
            continue
        if lib.archive_roadmap(roadmap_dir):
            print(f"  Archived: {r['name']} ({r['repo']})")
            archived += 1

    print(f"\nArchived {archived} roadmap(s).")


def cmd_decline(projects_dir, project=None):
    """Interactively decline roadmaps. Shows eligible roadmaps and prompts for selection."""
    all_roadmaps = find_all_roadmaps(projects_dir)

    if project:
        all_roadmaps = [r for r in all_roadmaps if r["repo"] == project]

    # Eligible: any active (non-archived, non-declined, non-complete) roadmap
    eligible = [r for r in all_roadmaps if not r["is_archived"] and not r["is_complete"]]

    if not eligible:
        print("No eligible roadmaps to decline.")
        return

    print("\033[1mRoadmaps eligible for decline:\033[0m\n")
    for i, r in enumerate(eligible, 1):
        pct = round(r["complete"] / r["total"] * 100) if r["total"] > 0 else 0
        state = r.get("state", "Unknown")
        print(f"  {i}) {r['name']:<30} {r['complete']:>2}/{r['total']:<2} steps  {pct:>3}%  \033[90m({state})\033[0m  [{r['repo']}]")

    print()
    selection = input("Enter numbers to decline (comma-separated, or 'all', or 'q' to cancel): ").strip()

    if not selection or selection.lower() == 'q':
        print("Cancelled.")
        return

    if selection.lower() == 'all':
        indices = list(range(len(eligible)))
    else:
        try:
            indices = [int(s.strip()) - 1 for s in selection.split(",")]
        except ValueError:
            print("Invalid input.")
            return

    declined = 0
    for idx in indices:
        if idx < 0 or idx >= len(eligible):
            print(f"  \033[31mSkipped: #{idx + 1} out of range\033[0m")
            continue
        r = eligible[idx]
        roadmap_dir = r.get("roadmap_dir")
        if not roadmap_dir:
            print(f"  \033[90mSkipped: {r['name']} — old layout\033[0m")
            continue
        if lib.decline_roadmap(roadmap_dir):
            print(f"  Declined: {r['name']} ({r['repo']})")
            declined += 1

    print(f"\nDeclined {declined} roadmap(s).")


def cmd_monitor(projects_dir, interval, project=None):
    """Live monitor: show roadmaps and dashboards, refresh in a loop."""
    try:
        while True:
            # Clear screen
            print("\033[2J\033[H", end="")
            print(f"\033[1mRoadmap Monitor\033[0m  \033[90m(every {interval}s — Ctrl-C to stop)  {datetime.now().strftime('%H:%M:%S')}\033[0m")
            print()

            # Roadmaps
            all_roadmaps = find_all_roadmaps(projects_dir)
            if project:
                all_roadmaps = [r for r in all_roadmaps if r["repo"] == project]
            # Show running + active in monitor
            active = [r for r in all_roadmaps if r["is_running"] or r["is_active"]]

            if active:
                print("\033[1m── Roadmaps ──\033[0m")
                print()
                by_repo = {}
                for r in active:
                    by_repo.setdefault(r["repo"], []).append(r)
                for repo_name, roadmaps in sorted(by_repo.items()):
                    print(f"\033[1m{repo_name}\033[0m")
                    for r in roadmaps:
                        pct = round(r["complete"] / r["total"] * 100) if r["total"] > 0 else 0
                        bar = progress_bar(r["complete"], r["total"])
                        state = r.get("state", "")
                        state_tag = f"  \033[33m[Running]\033[0m" if r["is_running"] else (f"  \033[90m[{state}]\033[0m" if state not in ("Ready", "") else "")
                        print(f"  {r['name']:<35} {r['complete']:>2}/{r['total']:<2} steps  {bar} {pct:>3}%{state_tag}")
                    print()

            # Dashboards
            dashboards = find_dashboards()
            if project:
                dashboards = [d for d in dashboards if d["repo"] == project]

            if dashboards:
                print("\033[1m── Dashboards ──\033[0m")
                print()
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

            if not active and not dashboards:
                print("No active roadmaps or dashboards found.")

            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\033[90mMonitoring stopped.\033[0m")


# --- Main ---

def main():
    parser = argparse.ArgumentParser(
        description="Cross-repo roadmap CLI tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  roadmaps --list\n  roadmaps --list-dashboards\n  roadmaps --open-dashboards",
    )
    parser.add_argument("--list", action="store_true", help="List roadmaps (default: running + active)")
    parser.add_argument("--running", action="store_true", help="Show running roadmaps")
    parser.add_argument("--active", action="store_true", help="Show active (non-complete) roadmaps")
    parser.add_argument("--complete", action="store_true", help="Show completed roadmaps")
    parser.add_argument("--archived", action="store_true", help="Show archived roadmaps")
    parser.add_argument("--all", action="store_true", help="Show all roadmaps (running + active + complete + archived)")
    parser.add_argument("--search", metavar="TEXT", help="Filter roadmaps by name")
    parser.add_argument("--sort", choices=["number", "name", "modified", "created"], default="number", help="Sort order (default: number)")
    parser.add_argument("--list-dashboards", action="store_true", help="List all dashboard URLs")
    parser.add_argument("--open-dashboards", action="store_true", help="Open all dashboard URLs in browser")
    parser.add_argument("--monitor", nargs="?", const=30, type=int, metavar="SECONDS", help="Live monitor (default: 30s interval)")
    parser.add_argument("--archive-completed", action="store_true", help="Archive all completed roadmaps")
    parser.add_argument("--decline", action="store_true", help="Interactively decline roadmaps in current/child dirs")
    parser.add_argument("--projects-dir", default=None, help="Projects directory (default: ~/projects)")
    args = parser.parse_args()

    projects_dir = args.projects_dir or os.environ.get("ROADMAPS_PROJECTS_DIR", "~/projects")
    project = detect_project(projects_dir)

    if args.archive_completed:
        cmd_archive_completed(projects_dir, project=project)
        return

    if args.decline:
        cmd_decline(projects_dir, project=project)
        return

    if args.list or not (args.list_dashboards or args.open_dashboards or args.monitor is not None):
        # Determine which filters are active
        if args.all:
            show_r, show_a, show_c, show_ar = True, True, True, True
        elif args.running or args.active or args.complete or args.archived:
            show_r = args.running
            show_a = args.active
            show_c = args.complete
            show_ar = args.archived
        else:
            # Default: running + active
            show_r, show_a, show_c, show_ar = True, True, False, False

        cmd_list(projects_dir, project=project,
                 show_running=show_r, show_active=show_a,
                 show_complete=show_c, show_archived=show_ar,
                 search=args.search, sort_by=args.sort)
    elif args.list_dashboards:
        cmd_list_dashboards(project=project)
    elif args.open_dashboards:
        cmd_open_dashboards(project=project)
    elif args.monitor is not None:
        cmd_monitor(projects_dir, args.monitor, project=project)


if __name__ == "__main__":
    main()
