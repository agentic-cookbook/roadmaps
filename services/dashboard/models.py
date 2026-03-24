"""Data access functions for all dashboard tables."""

import uuid
from datetime import datetime, timezone

from . import db


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _uuid():
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Roadmaps
# ---------------------------------------------------------------------------

def list_roadmaps(conn, state=None, status=None, archived=None):
    sql = "SELECT * FROM roadmaps WHERE 1=1"
    params = []
    if state:
        sql += " AND state = ?"
        params.append(state)
    if status:
        sql += " AND status = ?"
        params.append(status)
    if archived is not None:
        sql += " AND archived = ?"
        params.append(1 if archived else 0)
    sql += " ORDER BY roadmap_number DESC"
    return [db.dict_from_row(r) for r in conn.execute(sql, params).fetchall()]


def get_roadmap(conn, roadmap_id):
    row = conn.execute("SELECT * FROM roadmaps WHERE id = ?", (roadmap_id,)).fetchone()
    if not row:
        return None
    result = db.dict_from_row(row)
    result["steps"] = list_steps(conn, roadmap_id)
    result["issues"] = list_issues(conn, roadmap_id)
    result["prs"] = list_prs(conn, roadmap_id)
    result["events"] = list_runtime_events(conn, roadmap_id)
    return result


def create_roadmap(conn, data, clock=None, id_gen=None):
    _clock = clock or _now
    _id = id_gen or _uuid
    rid = data.get("id") or _id()
    now = _clock()
    roadmap_number = data.get("roadmap_number") or db.next_roadmap_number(conn)
    conn.execute(
        """INSERT INTO roadmaps (id, roadmap_number, name, created, modified, author, state, status,
           archived, definition_id, repo, repo_url, branch, machine, worktree, description)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (rid, roadmap_number, data["name"], data.get("created", now), now,
         data.get("author"), data.get("state", "Created"), data.get("status", "idle"),
         0, data.get("definition_id"), data.get("repo"), data.get("repo_url"),
         data.get("branch"), data.get("machine"), data.get("worktree"),
         data.get("description")),
    )
    conn.commit()
    return rid


def update_roadmap(conn, roadmap_id, data, clock=None):
    _clock = clock or _now
    fields = []
    params = []
    allowed = ["name", "author", "state", "status", "archived", "definition_id",
               "repo", "repo_url", "branch", "machine", "worktree", "description"]
    for key in allowed:
        if key in data:
            fields.append(f"{key} = ?")
            params.append(data[key])
    if not fields:
        return False
    fields.append("modified = ?")
    params.append(_clock())
    params.append(roadmap_id)
    conn.execute(f"UPDATE roadmaps SET {', '.join(fields)} WHERE id = ?", params)
    conn.commit()
    return True


def delete_roadmap(conn, roadmap_id):
    conn.execute("DELETE FROM roadmaps WHERE id = ?", (roadmap_id,))
    conn.commit()


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------

def list_steps(conn, roadmap_id):
    rows = conn.execute(
        "SELECT * FROM steps WHERE roadmap_id = ? ORDER BY number", (roadmap_id,)
    ).fetchall()
    return [db.dict_from_row(r) for r in rows]


def get_step(conn, roadmap_id, number):
    row = conn.execute(
        "SELECT * FROM steps WHERE roadmap_id = ? AND number = ?",
        (roadmap_id, number),
    ).fetchone()
    return db.dict_from_row(row)


def bulk_create_steps(conn, roadmap_id, steps_data, id_gen=None):
    """Replace all steps for a roadmap."""
    _id = id_gen or _uuid
    conn.execute("DELETE FROM steps WHERE roadmap_id = ?", (roadmap_id,))
    for s in steps_data:
        sid = s.get("id") or _id()
        conn.execute(
            """INSERT INTO steps (id, roadmap_id, number, description, status,
               step_type, complexity, detail, issue_number, issue_url, issue_title,
               issue_status, pr_number, pr_url, pr_title, pr_status,
               started_at, completed_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (sid, roadmap_id, s["number"], s["description"],
             s.get("status", "not_started"), s.get("step_type", "Auto"),
             s.get("complexity"), s.get("detail"),
             s.get("issue_number"), s.get("issue_url"), s.get("issue_title"),
             s.get("issue_status"),
             s.get("pr_number"), s.get("pr_url"), s.get("pr_title"),
             s.get("pr_status"),
             s.get("started_at"), s.get("completed_at"), s.get("updated_at")),
        )
    conn.commit()


def update_step(conn, roadmap_id, number, data, clock=None):
    _clock = clock or _now
    fields = []
    params = []
    allowed = ["description", "status", "step_type", "complexity", "detail",
               "issue_number", "issue_url", "issue_title", "issue_status",
               "pr_number", "pr_url", "pr_title", "pr_status",
               "started_at", "completed_at"]
    for key in allowed:
        if key in data:
            fields.append(f"{key} = ?")
            params.append(data[key])
    if not fields:
        return False
    fields.append("updated_at = ?")
    params.append(_clock())
    params.extend([roadmap_id, number])
    conn.execute(
        f"UPDATE steps SET {', '.join(fields)} WHERE roadmap_id = ? AND number = ?",
        params,
    )
    conn.commit()
    return True


def begin_step(conn, roadmap_id, number, clock=None):
    """Mark step as in_progress. Auto-stop any other active step."""
    _clock = clock or _now
    now = _clock()
    # Stop any currently active step
    conn.execute(
        """UPDATE steps SET status = 'complete', completed_at = ?, updated_at = ?
           WHERE roadmap_id = ? AND status = 'in_progress'""",
        (now, now, roadmap_id),
    )
    conn.execute(
        """UPDATE steps SET status = 'in_progress', started_at = ?, updated_at = ?
           WHERE roadmap_id = ? AND number = ?""",
        (now, now, roadmap_id, number),
    )
    update_roadmap(conn, roadmap_id, {"status": "running"}, clock=clock)
    conn.commit()


def finish_step(conn, roadmap_id, number, clock=None):
    _clock = clock or _now
    now = _clock()
    conn.execute(
        """UPDATE steps SET status = 'complete', completed_at = ?, updated_at = ?
           WHERE roadmap_id = ? AND number = ?""",
        (now, now, roadmap_id, number),
    )
    conn.commit()


def error_step(conn, roadmap_id, number, message, clock=None):
    _clock = clock or _now
    now = _clock()
    conn.execute(
        """UPDATE steps SET status = 'error', detail = ?, updated_at = ?
           WHERE roadmap_id = ? AND number = ?""",
        (message, now, roadmap_id, number),
    )
    update_roadmap(conn, roadmap_id, {"status": "error"}, clock=clock)
    conn.commit()


# ---------------------------------------------------------------------------
# State Transitions
# ---------------------------------------------------------------------------

def list_state_transitions(conn, roadmap_id):
    rows = conn.execute(
        "SELECT * FROM state_transitions WHERE roadmap_id = ? ORDER BY created",
        (roadmap_id,),
    ).fetchall()
    return [db.dict_from_row(r) for r in rows]


def add_state_transition(conn, roadmap_id, state, author=None, previous_state=None,
                         clock=None, id_gen=None):
    _clock = clock or _now
    _id = id_gen or _uuid
    tid = _id()
    now = _clock()
    if previous_state is None:
        row = conn.execute("SELECT state FROM roadmaps WHERE id = ?", (roadmap_id,)).fetchone()
        previous_state = row["state"] if row else None
    conn.execute(
        """INSERT INTO state_transitions (id, roadmap_id, state, previous_state, created, author)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (tid, roadmap_id, state, previous_state, now, author),
    )
    conn.execute("UPDATE roadmaps SET state = ?, modified = ? WHERE id = ?",
                 (state, now, roadmap_id))
    conn.commit()
    return tid


# ---------------------------------------------------------------------------
# History Events
# ---------------------------------------------------------------------------

def list_history_events(conn, roadmap_id):
    rows = conn.execute(
        "SELECT * FROM history_events WHERE roadmap_id = ? ORDER BY created",
        (roadmap_id,),
    ).fetchall()
    return [db.dict_from_row(r) for r in rows]


def add_history_event(conn, roadmap_id, event_type, step_number=None,
                      author=None, details=None, clock=None, id_gen=None):
    _clock = clock or _now
    _id = id_gen or _uuid
    eid = _id()
    now = _clock()
    conn.execute(
        """INSERT INTO history_events (id, roadmap_id, event_type, step_number,
           created, author, details) VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (eid, roadmap_id, event_type, step_number, now, author, details),
    )
    conn.commit()
    return eid


# ---------------------------------------------------------------------------
# Issues
# ---------------------------------------------------------------------------

def list_issues(conn, roadmap_id):
    rows = conn.execute(
        "SELECT * FROM issues WHERE roadmap_id = ? ORDER BY number", (roadmap_id,)
    ).fetchall()
    return [db.dict_from_row(r) for r in rows]


def upsert_issue(conn, roadmap_id, number, title=None, url=None, status=None):
    existing = conn.execute(
        "SELECT id FROM issues WHERE roadmap_id = ? AND number = ?",
        (roadmap_id, number),
    ).fetchone()
    if existing:
        fields, params = [], []
        if title is not None:
            fields.append("title = ?"); params.append(title)
        if url is not None:
            fields.append("url = ?"); params.append(url)
        if status is not None:
            fields.append("status = ?"); params.append(status)
        if fields:
            params.extend([roadmap_id, number])
            conn.execute(
                f"UPDATE issues SET {', '.join(fields)} WHERE roadmap_id = ? AND number = ?",
                params,
            )
    else:
        conn.execute(
            "INSERT INTO issues (roadmap_id, number, title, url, status) VALUES (?, ?, ?, ?, ?)",
            (roadmap_id, number, title, url, status or "open"),
        )
    conn.commit()


# ---------------------------------------------------------------------------
# Pull Requests
# ---------------------------------------------------------------------------

def list_prs(conn, roadmap_id):
    rows = conn.execute(
        "SELECT * FROM pull_requests WHERE roadmap_id = ? ORDER BY number", (roadmap_id,)
    ).fetchall()
    return [db.dict_from_row(r) for r in rows]


def upsert_pr(conn, roadmap_id, number, title=None, url=None, status=None):
    existing = conn.execute(
        "SELECT id FROM pull_requests WHERE roadmap_id = ? AND number = ?",
        (roadmap_id, number),
    ).fetchone()
    if existing:
        fields, params = [], []
        if title is not None:
            fields.append("title = ?"); params.append(title)
        if url is not None:
            fields.append("url = ?"); params.append(url)
        if status is not None:
            fields.append("status = ?"); params.append(status)
        if fields:
            params.extend([roadmap_id, number])
            conn.execute(
                f"UPDATE pull_requests SET {', '.join(fields)} WHERE roadmap_id = ? AND number = ?",
                params,
            )
    else:
        conn.execute(
            "INSERT INTO pull_requests (roadmap_id, number, title, url, status) VALUES (?, ?, ?, ?, ?)",
            (roadmap_id, number, title, url, status or "open"),
        )
    conn.commit()


# ---------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------

def get_control(conn, roadmap_id):
    row = conn.execute(
        "SELECT * FROM controls WHERE roadmap_id = ?", (roadmap_id,)
    ).fetchone()
    return db.dict_from_row(row)


def set_control(conn, roadmap_id, action, clock=None):
    _clock = clock or _now
    now = _clock()
    conn.execute(
        """INSERT INTO controls (roadmap_id, action, updated_at) VALUES (?, ?, ?)
           ON CONFLICT(roadmap_id) DO UPDATE SET action = ?, updated_at = ?""",
        (roadmap_id, action, now, action, now),
    )
    conn.commit()


def clear_control(conn, roadmap_id):
    conn.execute("DELETE FROM controls WHERE roadmap_id = ?", (roadmap_id,))
    conn.commit()


# ---------------------------------------------------------------------------
# Runtime Events
# ---------------------------------------------------------------------------

def list_runtime_events(conn, roadmap_id):
    rows = conn.execute(
        "SELECT * FROM runtime_events WHERE roadmap_id = ? ORDER BY id", (roadmap_id,)
    ).fetchall()
    return [db.dict_from_row(r) for r in rows]


def add_runtime_event(conn, roadmap_id, message, clock=None):
    _clock = clock or _now
    now = _clock()
    conn.execute(
        "INSERT INTO runtime_events (roadmap_id, time, message) VALUES (?, ?, ?)",
        (roadmap_id, now, message),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Sync (bulk reconciliation)
# ---------------------------------------------------------------------------

def sync_roadmap(conn, roadmap_id, data, clock=None, id_gen=None):
    """Full state sync — create or update a roadmap and all related data."""
    _clock = clock or _now
    existing = conn.execute("SELECT id FROM roadmaps WHERE id = ?", (roadmap_id,)).fetchone()

    env = data.get("environment", {})
    roadmap_data = {
        "name": data.get("title") or data.get("name", "Unknown"),
        "state": data.get("state", "Ready"),
        "status": data.get("status", "running"),
        "author": data.get("author"),
        "description": data.get("description"),
        "repo": env.get("repo"),
        "repo_url": env.get("repo_url"),
        "branch": env.get("branch"),
        "machine": env.get("machine"),
        "worktree": env.get("worktree"),
    }

    if existing:
        update_roadmap(conn, roadmap_id, roadmap_data, clock=clock)
    else:
        roadmap_data["id"] = roadmap_id
        create_roadmap(conn, roadmap_data, clock=clock, id_gen=id_gen)

    # Sync steps
    if "steps" in data:
        bulk_create_steps(conn, roadmap_id, data["steps"], id_gen=id_gen)

    # Sync issues
    if "issues" in data:
        conn.execute("DELETE FROM issues WHERE roadmap_id = ?", (roadmap_id,))
        for issue in data["issues"]:
            upsert_issue(conn, roadmap_id, issue["number"],
                         issue.get("title"), issue.get("url"), issue.get("status"))

    # Sync PRs
    if "prs" in data:
        conn.execute("DELETE FROM pull_requests WHERE roadmap_id = ?", (roadmap_id,))
        for pr in data["prs"]:
            upsert_pr(conn, roadmap_id, pr["number"],
                      pr.get("title"), pr.get("url"), pr.get("status"))

    # Sync runtime events
    if "events" in data:
        conn.execute("DELETE FROM runtime_events WHERE roadmap_id = ?", (roadmap_id,))
        for event in data["events"]:
            conn.execute(
                "INSERT INTO runtime_events (roadmap_id, time, message) VALUES (?, ?, ?)",
                (roadmap_id, event.get("time", _clock()), event.get("message", "")),
            )

    conn.commit()
    return roadmap_id


# ---------------------------------------------------------------------------
# UI Preferences
# ---------------------------------------------------------------------------

def get_preference(conn, key, default=None):
    row = conn.execute("SELECT value FROM ui_preferences WHERE key = ?", (key,)).fetchone()
    return row[0] if row else default


def set_preference(conn, key, value):
    conn.execute(
        """INSERT INTO ui_preferences (key, value) VALUES (?, ?)
           ON CONFLICT(key) DO UPDATE SET value = ?""",
        (key, value, value),
    )
    conn.commit()


def get_all_preferences(conn):
    rows = conn.execute("SELECT key, value FROM ui_preferences").fetchall()
    return {r[0]: r[1] for r in rows}
