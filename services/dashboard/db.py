"""SQLite database schema, migrations, and connection management."""

import os
import sqlite3
from pathlib import Path

SCHEMA_VERSION = 3

DEFAULT_DB_PATH = os.path.join(Path.home(), ".claude", "dashboard.db")


def get_db_path():
    return os.environ.get("DASHBOARD_DB", DEFAULT_DB_PATH)


def connect(db_path=None):
    """Create a new database connection with WAL mode and foreign keys."""
    path = db_path or get_db_path()
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS roadmaps (
    id TEXT PRIMARY KEY,
    roadmap_number INTEGER,
    name TEXT NOT NULL,
    created TEXT NOT NULL,
    modified TEXT NOT NULL,
    author TEXT,
    state TEXT NOT NULL DEFAULT 'Created',
    status TEXT NOT NULL DEFAULT 'idle',
    archived INTEGER NOT NULL DEFAULT 0,
    definition_id TEXT,
    repo TEXT,
    repo_url TEXT,
    branch TEXT,
    machine TEXT,
    worktree TEXT,
    description TEXT
);

CREATE TABLE IF NOT EXISTS definitions (
    id TEXT PRIMARY KEY,
    roadmap_id TEXT NOT NULL REFERENCES roadmaps(id) ON DELETE CASCADE,
    goal TEXT,
    platform TEXT,
    acceptance_criteria TEXT,
    verification_strategy TEXT,
    created TEXT NOT NULL,
    modified TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS steps (
    id TEXT PRIMARY KEY,
    roadmap_id TEXT NOT NULL REFERENCES roadmaps(id) ON DELETE CASCADE,
    number INTEGER NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'not_started',
    step_type TEXT DEFAULT 'Auto',
    complexity TEXT,
    detail TEXT,
    issue_number INTEGER,
    issue_url TEXT,
    issue_title TEXT,
    issue_status TEXT,
    pr_number INTEGER,
    pr_url TEXT,
    pr_title TEXT,
    pr_status TEXT,
    started_at TEXT,
    completed_at TEXT,
    updated_at TEXT,
    UNIQUE(roadmap_id, number)
);

CREATE TABLE IF NOT EXISTS step_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    step_id TEXT NOT NULL REFERENCES steps(id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    url TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS state_transitions (
    id TEXT PRIMARY KEY,
    roadmap_id TEXT NOT NULL REFERENCES roadmaps(id) ON DELETE CASCADE,
    state TEXT NOT NULL,
    previous_state TEXT,
    created TEXT NOT NULL,
    author TEXT
);

CREATE TABLE IF NOT EXISTS history_events (
    id TEXT PRIMARY KEY,
    roadmap_id TEXT NOT NULL REFERENCES roadmaps(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    step_number INTEGER,
    created TEXT NOT NULL,
    author TEXT,
    details TEXT
);

CREATE TABLE IF NOT EXISTS issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roadmap_id TEXT NOT NULL REFERENCES roadmaps(id) ON DELETE CASCADE,
    number INTEGER NOT NULL,
    title TEXT,
    url TEXT,
    status TEXT DEFAULT 'open',
    UNIQUE(roadmap_id, number)
);

CREATE TABLE IF NOT EXISTS pull_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roadmap_id TEXT NOT NULL REFERENCES roadmaps(id) ON DELETE CASCADE,
    number INTEGER NOT NULL,
    title TEXT,
    url TEXT,
    status TEXT DEFAULT 'open',
    UNIQUE(roadmap_id, number)
);

CREATE TABLE IF NOT EXISTS controls (
    roadmap_id TEXT PRIMARY KEY REFERENCES roadmaps(id) ON DELETE CASCADE,
    action TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS runtime_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roadmap_id TEXT NOT NULL REFERENCES roadmaps(id) ON DELETE CASCADE,
    time TEXT NOT NULL,
    message TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ui_preferences (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);
"""

MIGRATIONS = {
    2: [
        "ALTER TABLE roadmaps ADD COLUMN roadmap_number INTEGER",
        "ALTER TABLE roadmaps ADD COLUMN archived INTEGER NOT NULL DEFAULT 0",
        "CREATE TABLE IF NOT EXISTS ui_preferences (key TEXT PRIMARY KEY, value TEXT NOT NULL)",
    ],
    3: [
        "ALTER TABLE roadmaps ADD COLUMN description TEXT",
    ],
}


def init_db(conn=None):
    """Create all tables and run migrations."""
    close = False
    if conn is None:
        conn = connect()
        close = True
    conn.executescript(SCHEMA_SQL)

    # Check current version
    cur = conn.execute("SELECT version FROM schema_version LIMIT 1")
    row = cur.fetchone()
    current_version = row[0] if row else 0

    if current_version == 0:
        conn.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
    else:
        # Run migrations
        for ver in sorted(MIGRATIONS.keys()):
            if ver > current_version:
                for sql in MIGRATIONS[ver]:
                    try:
                        conn.execute(sql)
                    except sqlite3.OperationalError:
                        pass  # Column/table already exists
                conn.execute("UPDATE schema_version SET version = ?", (ver,))

    # Assign roadmap_numbers to any roadmaps that don't have one
    _assign_roadmap_numbers(conn)

    conn.commit()
    if close:
        conn.close()


def _assign_roadmap_numbers(conn):
    """Assign sequential roadmap_number to roadmaps that don't have one."""
    # Get the current max
    cur = conn.execute("SELECT MAX(roadmap_number) FROM roadmaps")
    row = cur.fetchone()
    next_num = (row[0] or 0) + 1

    # Find roadmaps without a number, ordered by created date
    unnumbered = conn.execute(
        "SELECT id FROM roadmaps WHERE roadmap_number IS NULL ORDER BY created"
    ).fetchall()
    for row in unnumbered:
        conn.execute("UPDATE roadmaps SET roadmap_number = ? WHERE id = ?", (next_num, row[0]))
        next_num += 1


def next_roadmap_number(conn):
    """Get the next available roadmap number."""
    cur = conn.execute("SELECT MAX(roadmap_number) FROM roadmaps")
    row = cur.fetchone()
    return (row[0] or 0) + 1


def dict_from_row(row):
    """Convert a sqlite3.Row to a plain dict."""
    if row is None:
        return None
    return dict(row)
