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
    roadmaps --list --json                  Output as JSON instead of formatted table
    roadmaps --show <name>                  Show detailed view of a single roadmap
    roadmaps --logs <name>                  Show log files for a roadmap
    roadmaps --cancel <name>               Cancel a stuck roadmap (cleanup worktree, branches, PRs)
    roadmaps --stale [hours]               Find roadmaps stuck in Implementing state (default: 24h)
    roadmaps --dashboard                   Show dashboard server status
    roadmaps --dashboard-sync              Sync all roadmaps to the dashboard
    roadmaps --list-dashboards              List all dashboard URLs
    roadmaps --open-dashboards              Open all dashboard URLs in browser
    roadmaps --monitor [SECONDS]            Live monitor roadmaps + dashboards (default: 30s)
    roadmaps --archive-completed             Archive all completed roadmaps
    roadmaps --decline                      Interactively decline roadmaps
    roadmaps --projects-dir <path>          Override projects directory (default: ~/projects)

Environment:
    ROADMAPS_PROJECTS_DIR   Override default projects directory
    DASHBOARD_URL           Dashboard service URL (default: http://localhost:8888)
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

def find_all_roadmaps(projects_dir, workdir_root=None):
    """Scan all repos for roadmaps. Returns flat list with repo_name on each entry.

    Scans three locations:
    1. Per-directory layout: <repo>/Roadmaps/YYYY-MM-DD-Name/Roadmap.md
    2. Flat file layout: <repo>/Roadmaps/<Name>-Roadmap.md
    3. Working directory: ~/.roadmaps/<project>/YYYY-MM-DD-Name/Roadmap.md
    """
    results = []
    projects_path = Path(projects_dir).expanduser()
    if not projects_path.exists():
        return results

    if workdir_root is None:
        workdir_root = Path.home() / ".roadmaps"

    # Track what we've seen to avoid duplicates
    seen_ids = set()

    for repo_dir in sorted(projects_path.iterdir()):
        if not repo_dir.is_dir():
            continue

        # 1. Per-directory layout: Roadmaps/YYYY-MM-DD-Name/
        roadmap_dirs = lib.find_roadmap_dirs(repo_dir)
        for rd in roadmap_dirs:
            state = lib.current_state(rd)
            active = lib.is_active(rd)
            rm_file = lib.roadmap_path(rd)
            name = lib.get_feature_name(rd)
            total, complete = lib.count_steps(rm_file)
            meta, _ = lib.parse_frontmatter(rm_file)
            rid = meta.get("id", "")
            if rid:
                seen_ids.add(rid)
            results.append({
                "name": name,
                "repo": repo_dir.name,
                "path": str(rm_file),
                "dir": rd.name,
                "roadmap_dir": str(rd),
                "state": state,
                "total": total,
                "complete": complete,
                "is_complete": state == "Complete",
                "is_active": active and state != "Complete",
                "is_running": state == "Implementing",
                "is_archived": state in ("Archived", "Declined"),
                "source": "repo",
            })

        # 2. Flat file layout: Roadmaps/<Name>-Roadmap.md
        flat_files = lib.find_roadmap_files(repo_dir)
        for rf in flat_files:
            meta, _ = lib.parse_frontmatter(rf)
            rid = meta.get("id", "")
            if rid and rid in seen_ids:
                continue  # already found as directory
            if rid:
                seen_ids.add(rid)
            name = lib.parse_roadmap_heading(rf) or rf.stem.replace("-Roadmap", "")
            total, complete = lib.count_steps(rf)
            state = meta.get("state", "Complete")  # flat files are finished
            results.append({
                "name": name,
                "repo": repo_dir.name,
                "path": str(rf),
                "dir": rf.name,
                "state": state,
                "total": total,
                "complete": complete,
                "is_complete": True,
                "is_active": False,
                "is_running": False,
                "is_archived": True,
                "source": "repo-flat",
            })

        # 3. Working directory: ~/.roadmaps/<project>/
        work_project_dir = workdir_root / repo_dir.name
        if work_project_dir.exists():
            for wd in sorted(work_project_dir.iterdir()):
                if not wd.is_dir() or not (wd / "Roadmap.md").exists():
                    continue
                meta, _ = lib.parse_frontmatter(wd / "Roadmap.md")
                rid = meta.get("id", "")
                if rid and rid in seen_ids:
                    continue
                if rid:
                    seen_ids.add(rid)
                state = lib.current_state(wd)
                active = lib.is_active(wd)
                rm_file = wd / "Roadmap.md"
                name = lib.get_feature_name(wd)
                total, complete = lib.count_steps(rm_file)
                results.append({
                    "name": name,
                    "repo": repo_dir.name,
                    "path": str(rm_file),
                    "dir": wd.name,
                    "roadmap_dir": str(wd),
                    "state": state,
                    "total": total,
                    "complete": complete,
                    "is_complete": state == "Complete",
                    "is_active": active and state != "Complete",
                    "is_running": state == "Implementing",
                    "is_archived": state in ("Archived", "Declined"),
                    "source": "workdir",
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
            display_state = "Running" if r["is_running"] else state
            if r["is_archived"]:
                state_str = f"\033[90m({display_state})\033[0m"
            elif r["is_complete"]:
                state_str = f"\033[32m({display_state})\033[0m"
            elif r["is_running"]:
                state_str = f"\033[33m({display_state})\033[0m"
            else:
                state_str = f"\033[90m({display_state})\033[0m"

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


def _find_roadmap_by_name(projects_dir, name):
    """Find a single roadmap by case-insensitive substring match on name.

    Returns (roadmap_dict, error_message). One of them is always None.
    """
    all_roadmaps = find_all_roadmaps(projects_dir)
    name_lower = name.lower()
    matches = [r for r in all_roadmaps if name_lower in r["name"].lower()]

    if not matches:
        return None, f"No roadmap found matching '{name}'."
    if len(matches) > 1:
        names = ", ".join(r["name"] for r in matches)
        return None, f"Multiple roadmaps match '{name}': {names}. Be more specific."
    return matches[0], None


def _parse_steps_detail(roadmap_file):
    """Parse detailed step info from a Roadmap.md file.

    Returns a list of dicts with keys: number, title, status, type, complexity.
    """
    content = Path(roadmap_file).read_text()
    steps = []
    # Find all ### Step N: Title sections
    pattern = r"^### Step (\d+):\s*(.+?)$"
    step_matches = list(re.finditer(pattern, content, re.MULTILINE))
    for i, m in enumerate(step_matches):
        step_num = int(m.group(1))
        step_title = m.group(2).strip()
        # Extract the section text (until next step or end)
        start = m.end()
        end = step_matches[i + 1].start() if i + 1 < len(step_matches) else len(content)
        section = content[start:end]

        status = "Unknown"
        step_type = "Unknown"
        complexity = "Unknown"
        sm = re.search(r"^\- \*\*Status\*\*:\s*(.+)", section, re.MULTILINE)
        if sm:
            status = sm.group(1).strip()
        tm = re.search(r"^\- \*\*Type\*\*:\s*(.+)", section, re.MULTILINE)
        if tm:
            step_type = tm.group(1).strip()
        cm = re.search(r"^\- \*\*Complexity\*\*:\s*(.+)", section, re.MULTILINE)
        if cm:
            complexity = cm.group(1).strip()

        steps.append({
            "number": step_num,
            "title": step_title,
            "status": status,
            "type": step_type,
            "complexity": complexity,
        })
    return steps


def _extract_pr_link(roadmap_file):
    """Extract PR link from a roadmap file (frontmatter or Change History section)."""
    meta, body = lib.parse_frontmatter(roadmap_file)

    # Check frontmatter change-history for PR links
    change_history = meta.get("change-history", [])
    if isinstance(change_history, list):
        for entry in change_history:
            if isinstance(entry, dict):
                pr = entry.get("pr") or entry.get("PR") or entry.get("pr-url")
                if pr:
                    return pr

    # Check body for PR links in Change History section
    pr_match = re.search(r"https://github\.com/[^\s)]+/pull/\d+", body)
    if pr_match:
        return pr_match.group(0)

    return None


def _dashboard_url():
    """Get the dashboard URL from environment or default."""
    return os.environ.get("DASHBOARD_URL", "http://localhost:8888").rstrip("/")


def _dashboard_request(method, path, data=None, timeout=5):
    """Make an HTTP request to the dashboard API. Returns (response_dict, error_string)."""
    import urllib.request
    import urllib.error
    url = f"{_dashboard_url()}/api/v1{path}"
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(resp.read().decode("utf-8")), None
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        return None, f"HTTP {e.code}: {body_text}"
    except (urllib.error.URLError, OSError) as e:
        return None, str(e)


def cmd_show(projects_dir, name):
    """Show detailed view of a single roadmap."""
    roadmap, err = _find_roadmap_by_name(projects_dir, name)
    if err:
        print(err)
        return

    # Header
    print(f"\033[1m{roadmap['name']}\033[0m")
    print(f"  Repo:    {roadmap['repo']}")
    print(f"  State:   {roadmap.get('state', 'Unknown')}")
    print(f"  Source:  {roadmap.get('source', 'unknown')}")
    print(f"  Path:    {roadmap['path']}")

    # Progress bar
    pct = round(roadmap["complete"] / roadmap["total"] * 100) if roadmap["total"] > 0 else 0
    bar = progress_bar(roadmap["complete"], roadmap["total"], width=24)
    print(f"\n  Progress: {bar} {roadmap['complete']}/{roadmap['total']} steps ({pct}%)")

    # PR link
    pr_link = _extract_pr_link(roadmap["path"])
    if pr_link:
        print(f"  PR:      {pr_link}")

    # Steps detail
    steps = _parse_steps_detail(roadmap["path"])
    if steps:
        print(f"\n  \033[1mSteps:\033[0m")
        for s in steps:
            status_icon = "\033[32m✓\033[0m" if s["status"].lower() == "complete" else "\033[90m○\033[0m"
            print(f"    {status_icon} Step {s['number']}: {s['title']}")
            print(f"      Status: {s['status']}  Type: {s['type']}  Complexity: {s['complexity']}")
    print()


def cmd_logs(projects_dir, name):
    """Show log files for a roadmap."""
    roadmap, err = _find_roadmap_by_name(projects_dir, name)
    if err:
        print(err)
        return

    roadmap_dir = roadmap.get("roadmap_dir")
    if not roadmap_dir:
        print(f"No roadmap directory found for '{roadmap['name']}' (flat layout).")
        return

    rd = Path(roadmap_dir)
    log_files = sorted(rd.glob("*.log"))

    if not log_files:
        print(f"No log files found in {roadmap_dir}")
        return

    for log_file in log_files:
        print(f"\033[1m── {log_file.name} ──\033[0m")
        print(log_file.read_text())
        print()


def cmd_cancel(projects_dir, name, confirm_fn=None):
    """Cancel a stuck roadmap: remove state, worktree, branches, PR.

    confirm_fn is a callable that takes a prompt string and returns bool.
    Defaults to interactive input if None.
    """
    roadmap, err = _find_roadmap_by_name(projects_dir, name)
    if err:
        print(err)
        return

    roadmap_dir = roadmap.get("roadmap_dir")
    feature_name = roadmap["name"]
    repo = roadmap["repo"]

    # Determine branch name (convention: feature/<name> or the dir name)
    branch_name = f"feature/{feature_name}"

    # Show plan
    print(f"\033[1mCancel plan for: {feature_name}\033[0m")
    print(f"  Repo:     {repo}")
    print(f"  State:    {roadmap.get('state', 'Unknown')}")
    if roadmap_dir:
        print(f"  Dir:      {roadmap_dir}")
    print(f"  Branch:   {branch_name}")
    print()
    print("Actions to perform:")
    if roadmap_dir:
        print("  1. Remove Implementing state file")
    print("  2. Remove git worktree (if exists)")
    print("  3. Delete local branch (if exists)")
    print("  4. Delete remote branch (if exists)")
    print("  5. Close open PR on branch (if any)")
    print("  6. Mark as error on dashboard (if running)")
    print()

    # Confirm
    if confirm_fn is None:
        response = input("Proceed? (y/n): ").strip().lower()
        confirmed = response == "y"
    else:
        confirmed = confirm_fn("Proceed? (y/n): ")

    if not confirmed:
        print("Cancelled.")
        return

    summary = []

    # 1. Remove Implementing state file
    if roadmap_dir:
        state_dir = Path(roadmap_dir) / "State"
        if state_dir.exists():
            for sf in state_dir.glob("*-Implementing.md"):
                sf.unlink()
                summary.append(f"Removed state file: {sf.name}")

    # 2. Remove worktree
    repo_path = Path(projects_dir).expanduser() / repo
    try:
        result = subprocess.run(
            ["git", "worktree", "remove", "--force", branch_name],
            capture_output=True, text=True, cwd=str(repo_path)
        )
        if result.returncode == 0:
            summary.append(f"Removed worktree: {branch_name}")
    except Exception:
        pass

    # 3. Delete local branch
    try:
        result = subprocess.run(
            ["git", "branch", "-D", branch_name],
            capture_output=True, text=True, cwd=str(repo_path)
        )
        if result.returncode == 0:
            summary.append(f"Deleted local branch: {branch_name}")
    except Exception:
        pass

    # 4. Delete remote branch
    try:
        result = subprocess.run(
            ["git", "push", "origin", "--delete", branch_name],
            capture_output=True, text=True, cwd=str(repo_path)
        )
        if result.returncode == 0:
            summary.append(f"Deleted remote branch: {branch_name}")
    except Exception:
        pass

    # 5. Close PR
    try:
        result = subprocess.run(
            ["gh", "pr", "close", branch_name],
            capture_output=True, text=True, cwd=str(repo_path)
        )
        if result.returncode == 0:
            summary.append(f"Closed PR on branch: {branch_name}")
    except Exception:
        pass

    # 6. Dashboard: mark as error + archive
    meta, _ = lib.parse_frontmatter(roadmap["path"])
    rid = meta.get("id", "")
    if rid:
        resp, dash_err = _dashboard_request("POST", f"/roadmaps/{rid}/error", {"message": "Cancelled by user"})
        if resp:
            summary.append("Marked as error on dashboard")

    # Print summary
    print()
    if summary:
        print("\033[1mCleanup summary:\033[0m")
        for item in summary:
            print(f"  \033[32m✓\033[0m {item}")
    else:
        print("No cleanup actions were needed.")
    print()


def cmd_json_list(projects_dir, project=None, show_running=True, show_active=True,
                  show_complete=False, show_archived=False, search=None, sort_by="number"):
    """Output filtered roadmap list as JSON to stdout."""
    all_roadmaps = find_all_roadmaps(projects_dir)

    if project:
        all_roadmaps = [r for r in all_roadmaps if r["repo"] == project]

    # Filter (same logic as cmd_list)
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
    else:
        filtered.sort(key=lambda r: r["dir"])

    print(json.dumps(filtered, indent=2))


def cmd_stale(projects_dir, hours=24, project=None):
    """Find roadmaps in Implementing state with state files older than N hours."""
    all_roadmaps = find_all_roadmaps(projects_dir)

    if project:
        all_roadmaps = [r for r in all_roadmaps if r["repo"] == project]

    stale = []
    now = time.time()
    cutoff = hours * 3600

    for r in all_roadmaps:
        if not r["is_running"]:
            continue
        roadmap_dir = r.get("roadmap_dir")
        if not roadmap_dir:
            continue
        state_dir = Path(roadmap_dir) / "State"
        if not state_dir.exists():
            continue
        for sf in state_dir.glob("*-Implementing.md"):
            age_seconds = now - sf.stat().st_mtime
            if age_seconds > cutoff:
                r["stale_hours"] = round(age_seconds / 3600, 1)
                r["state_file"] = str(sf)
                stale.append(r)
                break

    if not stale:
        print(f"No stale roadmaps (older than {hours}h) found.")
        return

    print(f"\033[1mStale roadmaps (Implementing > {hours}h):\033[0m\n")
    for r in stale:
        print(f"  {r['name']:<35} {r['repo']:<20} {r['stale_hours']}h old")
        print(f"    \033[90m{r['state_file']}\033[0m")
    print(f"\n{len(stale)} stale roadmap(s) found.")


def cmd_dashboard_status():
    """Show the dashboard server status."""
    url = _dashboard_url()

    # Check health
    import urllib.request
    import urllib.error
    print(f"\033[1mDashboard Status\033[0m")
    print(f"  URL: {url}")

    try:
        req = urllib.request.Request(f"{url}/api/v1/health", method="GET")
        resp = urllib.request.urlopen(req, timeout=5)
        health = json.loads(resp.read().decode("utf-8"))
        print(f"  Status: \033[32mrunning\033[0m")
    except Exception:
        print(f"  Status: \033[31mnot running\033[0m")
        return

    # Get roadmaps
    data, err = _dashboard_request("GET", "/roadmaps")
    if err:
        print(f"  Could not fetch roadmaps: {err}")
        return

    roadmaps_list = data if isinstance(data, list) else data.get("roadmaps", [])
    print(f"  Roadmaps: {len(roadmaps_list)}")

    if roadmaps_list:
        print(f"\n  \033[1mRoadmaps on dashboard:\033[0m")
        for r in roadmaps_list:
            name = r.get("name", "?")
            state = r.get("state", "?")
            status = r.get("status", "?")
            print(f"    {name:<35} state={state}  status={status}")
    print()


def cmd_dashboard_sync(projects_dir, project=None):
    """Sync all active/running roadmaps from filesystem to the dashboard."""
    all_roadmaps = find_all_roadmaps(projects_dir)

    if project:
        all_roadmaps = [r for r in all_roadmaps if r["repo"] == project]

    # Only sync active or running roadmaps
    syncable = [r for r in all_roadmaps if r["is_active"] or r["is_running"]]

    if not syncable:
        print("No active roadmaps to sync.")
        return

    synced = 0
    errors = 0
    for r in syncable:
        meta, _ = lib.parse_frontmatter(r["path"])
        rid = meta.get("id", "")
        if not rid:
            print(f"  \033[90mSkipped: {r['name']} — no ID in frontmatter\033[0m")
            continue

        sync_data = {
            "name": r["name"],
            "state": r.get("state", "Unknown"),
            "status": "running" if r["is_running"] else "idle",
            "repo": r["repo"],
        }

        # Add steps info
        steps = _parse_steps_detail(r["path"])
        if steps:
            sync_data["steps"] = [
                {"number": s["number"], "description": s["title"], "status": s["status"]}
                for s in steps
            ]

        resp, err = _dashboard_request("POST", f"/roadmaps/{rid}/sync", sync_data)
        if err:
            print(f"  \033[31mError syncing {r['name']}: {err}\033[0m")
            errors += 1
        else:
            print(f"  \033[32m✓\033[0m {r['name']}")
            synced += 1

    print(f"\nSynced {synced} roadmap(s).")
    if errors:
        print(f"\033[31m{errors} error(s)\033[0m")


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
                        display_state = "Running" if r["is_running"] else state
                        state_tag = f"  \033[33m[Running]\033[0m" if r["is_running"] else (f"  \033[90m[{display_state}]\033[0m" if display_state not in ("Ready", "") else "")
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
    parser.add_argument("--json", action="store_true", help="Output --list results as JSON")
    parser.add_argument("--show", metavar="NAME", help="Show detailed view of a single roadmap")
    parser.add_argument("--logs", metavar="NAME", help="Show log files for a roadmap")
    parser.add_argument("--cancel", metavar="NAME", help="Cancel a stuck roadmap (cleanup worktree, branches, PRs)")
    parser.add_argument("--stale", nargs="?", const=24, type=int, metavar="HOURS", help="Find stale Implementing roadmaps (default: 24h)")
    parser.add_argument("--dashboard", action="store_true", help="Show dashboard server status")
    parser.add_argument("--dashboard-sync", action="store_true", help="Sync all roadmaps to the dashboard")
    parser.add_argument("--list-dashboards", action="store_true", help="List all dashboard URLs")
    parser.add_argument("--open-dashboards", action="store_true", help="Open all dashboard URLs in browser")
    parser.add_argument("--monitor", nargs="?", const=30, type=int, metavar="SECONDS", help="Live monitor (default: 30s interval)")
    parser.add_argument("--archive-completed", action="store_true", help="Archive all completed roadmaps")
    parser.add_argument("--decline", action="store_true", help="Interactively decline roadmaps in current/child dirs")
    parser.add_argument("--projects-dir", default=None, help="Projects directory (default: ~/projects)")
    args = parser.parse_args()

    projects_dir = args.projects_dir or os.environ.get("ROADMAPS_PROJECTS_DIR", "~/projects")
    project = detect_project(projects_dir)

    if args.show:
        cmd_show(projects_dir, args.show)
        return

    if args.logs:
        cmd_logs(projects_dir, args.logs)
        return

    if args.cancel:
        cmd_cancel(projects_dir, args.cancel)
        return

    if args.stale is not None:
        cmd_stale(projects_dir, hours=args.stale, project=project)
        return

    if args.dashboard:
        cmd_dashboard_status()
        return

    if args.dashboard_sync:
        cmd_dashboard_sync(projects_dir, project=project)
        return

    if args.archive_completed:
        cmd_archive_completed(projects_dir, project=project)
        return

    if args.decline:
        cmd_decline(projects_dir, project=project)
        return

    # Check if --list or default (no other command given)
    is_list_cmd = args.list or args.json or not (
        args.list_dashboards or args.open_dashboards or args.monitor is not None
    )

    if is_list_cmd:
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

        if args.json:
            cmd_json_list(projects_dir, project=project,
                          show_running=show_r, show_active=show_a,
                          show_complete=show_c, show_archived=show_ar,
                          search=args.search, sort_by=args.sort)
        else:
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
