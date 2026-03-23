"""Tests for services/dashboard/models.py."""

import uuid

import pytest

from services.dashboard import models


def _rid():
    return str(uuid.uuid4())


def _create_roadmap(conn, **overrides):
    """Helper: create a roadmap and return its ID."""
    data = {"name": "Test", "state": "Ready", "status": "idle"}
    data.update(overrides)
    return models.create_roadmap(conn, data)


# ---------------------------------------------------------------------------
# Roadmap CRUD
# ---------------------------------------------------------------------------

class TestRoadmapCRUD:
    def test_create_returns_uuid(self, db_conn):
        rid = _create_roadmap(db_conn)
        assert isinstance(rid, str)
        assert len(rid) == 36  # UUID format

    def test_get_includes_related(self, db_conn):
        rid = _create_roadmap(db_conn)
        r = models.get_roadmap(db_conn, rid)
        assert r is not None
        assert "steps" in r
        assert "issues" in r
        assert "prs" in r
        assert "events" in r

    def test_update_fields(self, db_conn):
        rid = _create_roadmap(db_conn)
        models.update_roadmap(db_conn, rid, {"name": "Updated", "status": "running"})
        r = models.get_roadmap(db_conn, rid)
        assert r["name"] == "Updated"
        assert r["status"] == "running"

    def test_update_no_fields_returns_false(self, db_conn):
        rid = _create_roadmap(db_conn)
        result = models.update_roadmap(db_conn, rid, {})
        assert result is False

    def test_delete_cascades(self, db_conn):
        rid = _create_roadmap(db_conn)
        models.bulk_create_steps(db_conn, rid, [
            {"number": 1, "description": "Step 1"},
        ])
        models.upsert_issue(db_conn, rid, 1, title="Issue 1")
        models.upsert_pr(db_conn, rid, 1, title="PR 1")
        models.add_history_event(db_conn, rid, "test")
        models.add_state_transition(db_conn, rid, "Ready")

        models.delete_roadmap(db_conn, rid)
        assert models.get_roadmap(db_conn, rid) is None
        assert models.list_steps(db_conn, rid) == []
        assert models.list_issues(db_conn, rid) == []
        assert models.list_prs(db_conn, rid) == []
        assert models.list_history_events(db_conn, rid) == []
        assert models.list_state_transitions(db_conn, rid) == []

    def test_list_with_state_filter(self, db_conn):
        _create_roadmap(db_conn, name="A", state="Ready")
        _create_roadmap(db_conn, name="B", state="Complete")
        results = models.list_roadmaps(db_conn, state="Ready")
        assert all(r["state"] == "Ready" for r in results)
        assert any(r["name"] == "A" for r in results)

    def test_list_with_status_filter(self, db_conn):
        _create_roadmap(db_conn, name="C", status="running")
        _create_roadmap(db_conn, name="D", status="idle")
        results = models.list_roadmaps(db_conn, status="running")
        assert all(r["status"] == "running" for r in results)


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------

class TestSteps:
    def test_bulk_create_replaces_all(self, db_conn):
        rid = _create_roadmap(db_conn)
        models.bulk_create_steps(db_conn, rid, [
            {"number": 1, "description": "Old step"},
        ])
        assert len(models.list_steps(db_conn, rid)) == 1

        models.bulk_create_steps(db_conn, rid, [
            {"number": 1, "description": "New step 1"},
            {"number": 2, "description": "New step 2"},
        ])
        steps = models.list_steps(db_conn, rid)
        assert len(steps) == 2
        assert steps[0]["description"] == "New step 1"

    def test_update_single_field(self, db_conn):
        rid = _create_roadmap(db_conn)
        models.bulk_create_steps(db_conn, rid, [
            {"number": 1, "description": "Step 1", "status": "not_started"},
        ])
        models.update_step(db_conn, rid, 1, {"status": "in_progress"})
        step = models.get_step(db_conn, rid, 1)
        assert step["status"] == "in_progress"
        assert step["updated_at"] is not None

    def test_begin_step_auto_stops_prior(self, db_conn):
        rid = _create_roadmap(db_conn)
        models.bulk_create_steps(db_conn, rid, [
            {"number": 1, "description": "Step 1"},
            {"number": 2, "description": "Step 2"},
        ])
        models.begin_step(db_conn, rid, 1)
        s1 = models.get_step(db_conn, rid, 1)
        assert s1["status"] == "in_progress"

        models.begin_step(db_conn, rid, 2)
        s1 = models.get_step(db_conn, rid, 1)
        s2 = models.get_step(db_conn, rid, 2)
        assert s1["status"] == "complete"
        assert s1["completed_at"] is not None
        assert s2["status"] == "in_progress"

    def test_finish_step(self, db_conn):
        rid = _create_roadmap(db_conn)
        models.bulk_create_steps(db_conn, rid, [
            {"number": 1, "description": "Step 1"},
        ])
        models.begin_step(db_conn, rid, 1)
        models.finish_step(db_conn, rid, 1)
        step = models.get_step(db_conn, rid, 1)
        assert step["status"] == "complete"
        assert step["completed_at"] is not None

    def test_error_step(self, db_conn):
        rid = _create_roadmap(db_conn)
        models.bulk_create_steps(db_conn, rid, [
            {"number": 1, "description": "Step 1"},
        ])
        models.begin_step(db_conn, rid, 1)
        models.error_step(db_conn, rid, 1, "Something broke")
        step = models.get_step(db_conn, rid, 1)
        assert step["status"] == "error"
        assert step["detail"] == "Something broke"
        r = models.get_roadmap(db_conn, rid)
        assert r["status"] == "error"


# ---------------------------------------------------------------------------
# State Transitions
# ---------------------------------------------------------------------------

class TestStateTransitions:
    def test_add_creates_transition_and_updates_roadmap(self, db_conn):
        rid = _create_roadmap(db_conn, state="Created")
        models.add_state_transition(db_conn, rid, "Ready")
        r = models.get_roadmap(db_conn, rid)
        assert r["state"] == "Ready"

        transitions = models.list_state_transitions(db_conn, rid)
        assert len(transitions) == 1
        assert transitions[0]["state"] == "Ready"
        assert transitions[0]["previous_state"] == "Created"

    def test_list_returns_in_order(self, db_conn):
        rid = _create_roadmap(db_conn, state="Created")
        models.add_state_transition(db_conn, rid, "Planning")
        models.add_state_transition(db_conn, rid, "Ready")
        transitions = models.list_state_transitions(db_conn, rid)
        assert len(transitions) == 2
        assert transitions[0]["state"] == "Planning"
        assert transitions[1]["state"] == "Ready"


# ---------------------------------------------------------------------------
# History Events
# ---------------------------------------------------------------------------

class TestHistoryEvents:
    def test_add_and_list(self, db_conn):
        rid = _create_roadmap(db_conn)
        models.add_history_event(db_conn, rid, "step_complete", step_number=1,
                                  details="Finished step 1")
        events = models.list_history_events(db_conn, rid)
        assert len(events) == 1
        assert events[0]["event_type"] == "step_complete"
        assert events[0]["step_number"] == 1
        assert events[0]["details"] == "Finished step 1"


# ---------------------------------------------------------------------------
# Issues
# ---------------------------------------------------------------------------

class TestIssues:
    def test_upsert_creates_new(self, db_conn):
        rid = _create_roadmap(db_conn)
        models.upsert_issue(db_conn, rid, 42, title="Bug report",
                            url="https://github.com/test/42", status="open")
        issues = models.list_issues(db_conn, rid)
        assert len(issues) == 1
        assert issues[0]["number"] == 42
        assert issues[0]["title"] == "Bug report"

    def test_upsert_updates_existing(self, db_conn):
        rid = _create_roadmap(db_conn)
        models.upsert_issue(db_conn, rid, 42, title="Bug report", status="open")
        models.upsert_issue(db_conn, rid, 42, title="Updated title", status="closed")
        issues = models.list_issues(db_conn, rid)
        assert len(issues) == 1
        assert issues[0]["title"] == "Updated title"
        assert issues[0]["status"] == "closed"


# ---------------------------------------------------------------------------
# Pull Requests
# ---------------------------------------------------------------------------

class TestPullRequests:
    def test_upsert_creates_new(self, db_conn):
        rid = _create_roadmap(db_conn)
        models.upsert_pr(db_conn, rid, 10, title="Add feature",
                         url="https://github.com/test/pr/10", status="open")
        prs = models.list_prs(db_conn, rid)
        assert len(prs) == 1
        assert prs[0]["number"] == 10
        assert prs[0]["title"] == "Add feature"

    def test_upsert_updates_existing(self, db_conn):
        rid = _create_roadmap(db_conn)
        models.upsert_pr(db_conn, rid, 10, title="Add feature", status="open")
        models.upsert_pr(db_conn, rid, 10, title="Add feature (v2)", status="merged")
        prs = models.list_prs(db_conn, rid)
        assert len(prs) == 1
        assert prs[0]["title"] == "Add feature (v2)"
        assert prs[0]["status"] == "merged"


# ---------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------

class TestControls:
    def test_set_and_get(self, db_conn):
        rid = _create_roadmap(db_conn)
        models.set_control(db_conn, rid, "pause")
        ctrl = models.get_control(db_conn, rid)
        assert ctrl is not None
        assert ctrl["action"] == "pause"

    def test_set_overwrites(self, db_conn):
        rid = _create_roadmap(db_conn)
        models.set_control(db_conn, rid, "pause")
        models.set_control(db_conn, rid, "resume")
        ctrl = models.get_control(db_conn, rid)
        assert ctrl["action"] == "resume"

    def test_clear(self, db_conn):
        rid = _create_roadmap(db_conn)
        models.set_control(db_conn, rid, "pause")
        models.clear_control(db_conn, rid)
        ctrl = models.get_control(db_conn, rid)
        assert ctrl is None

    def test_get_nonexistent(self, db_conn):
        rid = _create_roadmap(db_conn)
        ctrl = models.get_control(db_conn, rid)
        assert ctrl is None


# ---------------------------------------------------------------------------
# Runtime Events
# ---------------------------------------------------------------------------

class TestRuntimeEvents:
    def test_add_and_list(self, db_conn):
        rid = _create_roadmap(db_conn)
        models.add_runtime_event(db_conn, rid, "Started processing")
        models.add_runtime_event(db_conn, rid, "Finished processing")
        events = models.list_runtime_events(db_conn, rid)
        assert len(events) == 2
        assert events[0]["message"] == "Started processing"
        assert events[1]["message"] == "Finished processing"

    def test_list_empty(self, db_conn):
        rid = _create_roadmap(db_conn)
        events = models.list_runtime_events(db_conn, rid)
        assert events == []


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------

class TestSync:
    def test_creates_new_roadmap(self, db_conn):
        rid = _rid()
        models.sync_roadmap(db_conn, rid, {
            "title": "SyncFeature",
            "state": "Ready",
            "status": "running",
            "environment": {"repo": "test/repo", "branch": "main"},
            "steps": [
                {"number": 1, "description": "Step 1", "status": "not_started"},
                {"number": 2, "description": "Step 2", "status": "not_started"},
            ],
            "issues": [{"number": 10, "title": "Issue 10"}],
            "prs": [{"number": 5, "title": "PR 5"}],
        })
        r = models.get_roadmap(db_conn, rid)
        assert r is not None
        assert r["name"] == "SyncFeature"
        assert len(r["steps"]) == 2
        assert len(r["issues"]) == 1
        assert len(r["prs"]) == 1

    def test_updates_existing_roadmap(self, db_conn):
        rid = _create_roadmap(db_conn, name="Original")
        models.sync_roadmap(db_conn, rid, {
            "title": "Updated",
            "state": "Implementing",
            "status": "running",
            "steps": [
                {"number": 1, "description": "New step"},
            ],
        })
        r = models.get_roadmap(db_conn, rid)
        assert r["name"] == "Updated"
        assert r["state"] == "Implementing"
        assert len(r["steps"]) == 1
        assert r["steps"][0]["description"] == "New step"

    def test_replaces_steps_issues_prs(self, db_conn):
        rid = _create_roadmap(db_conn)
        models.bulk_create_steps(db_conn, rid, [
            {"number": 1, "description": "Old step"},
        ])
        models.upsert_issue(db_conn, rid, 1, title="Old issue")
        models.upsert_pr(db_conn, rid, 1, title="Old PR")

        models.sync_roadmap(db_conn, rid, {
            "title": "Synced",
            "steps": [
                {"number": 1, "description": "Replaced step 1"},
                {"number": 2, "description": "Replaced step 2"},
            ],
            "issues": [
                {"number": 99, "title": "New issue"},
            ],
            "prs": [
                {"number": 88, "title": "New PR"},
            ],
        })
        r = models.get_roadmap(db_conn, rid)
        assert len(r["steps"]) == 2
        assert r["steps"][0]["description"] == "Replaced step 1"
        assert len(r["issues"]) == 1
        assert r["issues"][0]["number"] == 99
        assert len(r["prs"]) == 1
        assert r["prs"][0]["number"] == 88
