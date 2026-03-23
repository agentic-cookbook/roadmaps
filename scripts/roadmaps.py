#!/usr/bin/env python3
"""Cross-repo roadmap CLI tool.

Scans all repos in a projects directory for active feature roadmaps
and progress dashboards.

Usage:
    roadmaps --list                     List all active roadmaps across all repos
    roadmaps --list --all               List all roadmaps including archived/completed
    roadmaps --list-dashboards          List all dashboard URLs
    roadmaps --open-dashboards          Open all dashboard URLs in browser
    roadmaps --monitor [SECONDS]        Live monitor roadmaps + dashboards (default: 30s)
    roadmaps --cleanup                  Remove dead dashboard dirs and kill orphaned servers
    roadmaps --projects-dir <path>      Override projects directory (default: ~/projects)

Environment:
    ROADMAPS_PROJECTS_DIR   Override default projects directory
"""

import argparse
import json
import os
import re
import signal
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

def find_all_roadmaps(projects_dir, include_archived=False):
    """Scan all repos for roadmaps. Optionally include completed/archived ones."""
    results = {}
    projects_path = Path(projects_dir).expanduser()
    if not projects_path.exists():
        return results

    for repo_dir in sorted(projects_path.iterdir()):
        if not repo_dir.is_dir():
            continue

        roadmaps = []

        # New per-directory layout: Roadmaps/YYYY-MM-DD-Name/
        roadmap_dirs = lib.find_roadmap_dirs(repo_dir)
        if roadmap_dirs:
            for rd in roadmap_dirs:
                state = lib.current_state(rd)
                active = lib.is_active(rd)
                if not active and not include_archived:
                    continue
                rm_file = lib.roadmap_path(rd)
                name = lib.get_feature_name(rd)
                total, complete = lib.count_steps(rm_file)
                meta = {
                    "name": name,
                    "path": str(rm_file),
                    "state": state,
                    "total": total,
                    "complete": complete,
                    "archived": not active,
                }
                roadmaps.append(meta)
        else:
            # Old flat layout fallback
            old = lib.find_roadmaps_old_layout(repo_dir)
            for entry in old:
                if not entry.get("roadmap_path"):
                    continue
                rm_path = entry["roadmap_path"]
                is_completed = entry["location"] == "completed"
                if is_completed and not include_archived:
                    continue
                name = lib.parse_roadmap_heading(rm_path) or entry["name"]
                total, complete = lib.count_steps(rm_path)
                meta = {
                    "name": name,
                    "path": str(rm_path),
                    "state": "Complete" if is_completed else "Ready",
                    "total": total,
                    "complete": complete,
                    "archived": is_completed,
                }
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

def cmd_list(projects_dir, project=None, include_archived=False):
    """List all roadmaps across all repos."""
    all_roadmaps = find_all_roadmaps(projects_dir, include_archived=include_archived)

    if project:
        all_roadmaps = {k: v for k, v in all_roadmaps.items() if k == project}

    if not all_roadmaps:
        label = "roadmaps" if include_archived else "active roadmaps"
        print(f"No {label} found.")
        return

    for repo_name, roadmaps in all_roadmaps.items():
        print(f"\033[1m{repo_name}\033[0m")
        for r in roadmaps:
            pct = round(r["complete"] / r["total"] * 100) if r["total"] > 0 else 0
            bar = progress_bar(r["complete"], r["total"])
            state = r.get("state", "")
            state_tag = f"  \033[90m[{state}]\033[0m" if state not in ("Ready", "") else ""
            archived_tag = "  \033[32m[Archived]\033[0m" if r.get("archived") else ""
            print(f"  {r['name']:<35} {r['complete']:>2}/{r['total']:<2} steps  {bar} {pct:>3}%{state_tag}{archived_tag}")
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


def cmd_cleanup():
    """Remove dead dashboard dirs and kill orphaned server processes."""
    tmpdir = Path(os.environ.get("TMPDIR", "/tmp")).resolve()

    # 1. Find dashboard dirs where the server is dead
    dead_dirs = []
    for d in sorted(tmpdir.glob("progress-dashboard-*")):
        if d.name == "progress-dashboard-active":
            continue
        if not d.is_dir():
            continue

        port_file = d / "port"
        if not port_file.exists():
            dead_dirs.append(d)
            continue

        try:
            port = int(port_file.read_text().strip())
        except (ValueError, OSError):
            dead_dirs.append(d)
            continue

        url = f"http://127.0.0.1:{port}"
        try:
            import urllib.request
            urllib.request.urlopen(url, timeout=1)
        except Exception:
            dead_dirs.append(d)

    # 2. Find orphaned Python processes whose cwd is a deleted dashboard dir
    orphaned_pids = []
    try:
        result = subprocess.run(
            ["lsof", "-c", "Python", "-a", "-d", "cwd", "-Fn"],
            capture_output=True, text=True, timeout=5,
        )
        lines = result.stdout.strip().split("\n")
        pid = None
        for line in lines:
            if line.startswith("p"):
                pid = int(line[1:])
            elif line.startswith("n") and pid:
                cwd_path = Path(line[1:])
                if "progress-dashboard-" in str(cwd_path) and not cwd_path.exists():
                    orphaned_pids.append((pid, str(cwd_path)))
                pid = None
    except Exception:
        pass

    if not dead_dirs and not orphaned_pids:
        print("Nothing to clean up.")
        return

    # 3. Report and clean
    if dead_dirs:
        print(f"\033[1mRemoving {len(dead_dirs)} dead dashboard dir(s):\033[0m")
        for d in dead_dirs:
            title = d.name.replace("progress-dashboard-", "")
            print(f"  {title:<30} {d}")
            shutil.rmtree(d)
        print()

    if orphaned_pids:
        print(f"\033[1mKilling {len(orphaned_pids)} orphaned server process(es):\033[0m")
        for pid, cwd_path in orphaned_pids:
            dirname = Path(cwd_path).name.replace("progress-dashboard-", "")
            print(f"  PID {pid:<8} {dirname:<30} (dir deleted)")
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError as e:
                print(f"    \033[31mfailed: {e}\033[0m")
        print()

    # 4. Clean up the active symlink/file if it points to a dead dir
    active = tmpdir / "progress-dashboard-active"
    if active.exists():
        try:
            content = active.read_text().strip()
            if content and not Path(content).exists():
                active.unlink()
                print(f"Removed stale active pointer: {content}")
        except OSError:
            pass

    print("Cleanup complete.")


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
                all_roadmaps = {k: v for k, v in all_roadmaps.items() if k == project}

            if all_roadmaps:
                print("\033[1m── Roadmaps ──\033[0m")
                print()
                for repo_name, roadmaps in all_roadmaps.items():
                    print(f"\033[1m{repo_name}\033[0m")
                    for r in roadmaps:
                        pct = round(r["complete"] / r["total"] * 100) if r["total"] > 0 else 0
                        bar = progress_bar(r["complete"], r["total"])
                        state = r.get("state", "")
                        state_tag = f"  \033[90m[{state}]\033[0m" if state not in ("Ready", "") else ""
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

            if not all_roadmaps and not dashboards:
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
    parser.add_argument("--list", action="store_true", help="List all roadmaps across all repos")
    parser.add_argument("--all", action="store_true", help="Include archived/completed roadmaps (use with --list)")
    parser.add_argument("--list-dashboards", action="store_true", help="List all dashboard URLs")
    parser.add_argument("--open-dashboards", action="store_true", help="Open all dashboard URLs in browser")
    parser.add_argument("--monitor", nargs="?", const=30, type=int, metavar="SECONDS", help="Live monitor (default: 30s interval)")
    parser.add_argument("--cleanup", action="store_true", help="Remove dead dashboard dirs and kill orphaned servers")
    parser.add_argument("--projects-dir", default=None, help="Projects directory (default: ~/projects)")
    args = parser.parse_args()

    projects_dir = args.projects_dir or os.environ.get("ROADMAPS_PROJECTS_DIR", "~/projects")
    project = detect_project(projects_dir)

    if args.list:
        cmd_list(projects_dir, project=project, include_archived=args.all)
    elif args.list_dashboards:
        cmd_list_dashboards(project=project)
    elif args.open_dashboards:
        cmd_open_dashboards(project=project)
    elif args.monitor is not None:
        cmd_monitor(projects_dir, args.monitor, project=project)
    elif args.cleanup:
        cmd_cleanup()
    else:
        # Default: show list
        cmd_list(projects_dir, project=project, include_archived=args.all)


if __name__ == "__main__":
    main()
