"""SQLite database schema, migrations, and connection management."""

import os
import sqlite3
from pathlib import Path

SCHEMA_VERSION = 1

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
    name TEXT NOT NULL,
    created TEXT NOT NULL,
    modified TEXT NOT NULL,
    author TEXT,
    state TEXT NOT NULL DEFAULT 'Created',
    status TEXT NOT NULL DEFAULT 'idle',
    definition_id TEXT,
    repo TEXT,
    repo_url TEXT,
    branch TEXT,
    machine TEXT,
    worktree TEXT
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

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);
"""


def init_db(conn=None):
    """Create all tables and set schema version."""
    close = False
    if conn is None:
        conn = connect()
        close = True
    conn.executescript(SCHEMA_SQL)
    # Set version if not present
    cur = conn.execute("SELECT version FROM schema_version LIMIT 1")
    if cur.fetchone() is None:
        conn.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
    conn.commit()
    if close:
        conn.close()


def dict_from_row(row):
    """Convert a sqlite3.Row to a plain dict."""
    if row is None:
        return None
    return dict(row)
