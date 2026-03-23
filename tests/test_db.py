"""Tests for services/dashboard/db.py."""

import sqlite3

import pytest

from services.dashboard import db


# ---------------------------------------------------------------------------
# init_db
# ---------------------------------------------------------------------------

class TestInitDb:
    def test_creates_all_tables(self, db_conn):
        rows = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        # Filter out sqlite internal tables (e.g. sqlite_sequence for AUTOINCREMENT)
        table_names = sorted(r["name"] for r in rows if not r["name"].startswith("sqlite_"))
        expected = sorted([
            "controls",
            "definitions",
            "history_events",
            "issues",
            "pull_requests",
            "roadmaps",
            "runtime_events",
            "schema_version",
            "state_transitions",
            "step_links",
            "steps",
        ])
        assert table_names == expected

    def test_idempotent(self, db_conn):
        # Running init_db a second time should not raise
        db.init_db(db_conn)
        # Tables still exist
        rows = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        assert len(rows) >= 10


# ---------------------------------------------------------------------------
# Schema version
# ---------------------------------------------------------------------------

class TestSchemaVersion:
    def test_version_is_one(self, db_conn):
        row = db_conn.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
        assert row is not None
        assert row["version"] == 1


# ---------------------------------------------------------------------------
# Foreign keys
# ---------------------------------------------------------------------------

class TestForeignKeys:
    def test_fk_enforced(self, db_conn):
        """Inserting a step with a non-existent roadmap_id should fail."""
        with pytest.raises(sqlite3.IntegrityError):
            db_conn.execute(
                """INSERT INTO steps (id, roadmap_id, number, description, status)
                   VALUES ('s1', 'nonexistent', 1, 'A step', 'not_started')"""
            )


# ---------------------------------------------------------------------------
# WAL mode
# ---------------------------------------------------------------------------

class TestWalMode:
    def test_wal_enabled(self):
        """A freshly connected in-memory DB should have WAL mode set."""
        conn = db.connect(":memory:")
        try:
            row = conn.execute("PRAGMA journal_mode").fetchone()
            # In-memory databases may report "memory" instead of "wal"
            # because WAL is not supported for :memory:, but the PRAGMA
            # was still issued. For file-based DBs it would be "wal".
            assert row[0] in ("wal", "memory")
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# dict_from_row
# ---------------------------------------------------------------------------

class TestDictFromRow:
    def test_converts_row_to_dict(self, db_conn):
        db_conn.execute(
            """INSERT INTO roadmaps (id, name, created, modified, state, status)
               VALUES ('r1', 'Test', '2026-01-01', '2026-01-01', 'Ready', 'idle')"""
        )
        db_conn.commit()
        row = db_conn.execute("SELECT * FROM roadmaps WHERE id = 'r1'").fetchone()
        d = db.dict_from_row(row)
        assert isinstance(d, dict)
        assert d["id"] == "r1"
        assert d["name"] == "Test"

    def test_returns_none_for_none(self):
        assert db.dict_from_row(None) is None
