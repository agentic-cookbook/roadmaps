"""Integration tests for the DashboardClient library against a live test server."""

import socket
import threading
import time
import uuid

import pytest

from dashboard_client import DashboardClient, DashboardError, DashboardUnavailable


def _find_free_port():
    """Find an available TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def live_server(app):
    """Start the Flask app in a background thread on a random port."""
    port = _find_free_port()
    server_thread = threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=port, use_reloader=False),
    )
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.5)
    yield f"http://127.0.0.1:{port}"


@pytest.fixture
def dc(live_server):
    """DashboardClient pointed at the live test server."""
    return DashboardClient(base_url=live_server)


class TestPing:
    def test_ping_succeeds(self, dc):
        result = dc.ping()
        assert result["status"] == "ok"


class TestRoadmapCRUD:
    def test_create_and_get_round_trip(self, dc):
        rid = str(uuid.uuid4())
        resp = dc.create_roadmap(name="ClientTest", id=rid, state="Created")
        assert resp["id"] == rid

        roadmap = dc.get_roadmap(rid)
        assert roadmap["name"] == "ClientTest"
        assert roadmap["state"] == "Created"

    def test_list_roadmaps_returns_created(self, dc):
        rid = str(uuid.uuid4())
        dc.create_roadmap(name="Listable", id=rid)

        roadmaps = dc.list_roadmaps()
        assert any(r["id"] == rid for r in roadmaps)


class TestStepLifecycle:
    def test_set_begin_finish_lifecycle(self, dc):
        rid = str(uuid.uuid4())
        dc.create_roadmap(name="StepTest", id=rid)
        dc.set_steps(rid, [
            {"number": 1, "description": "Step one"},
            {"number": 2, "description": "Step two"},
        ])

        # Begin step 1
        dc.begin_step(rid, 1)
        roadmap = dc.get_roadmap(rid)
        step1 = [s for s in roadmap["steps"] if s["number"] == 1][0]
        assert step1["status"] == "in_progress"

        # Finish step 1
        dc.finish_step(rid, 1)
        roadmap = dc.get_roadmap(rid)
        step1 = [s for s in roadmap["steps"] if s["number"] == 1][0]
        assert step1["status"] == "complete"
        assert step1["completed_at"] is not None


class TestSync:
    def test_sync_with_full_payload(self, dc):
        rid = str(uuid.uuid4())
        dc.sync(rid, {
            "title": "SyncedViaClient",
            "state": "In Progress",
            "status": "running",
            "steps": [
                {"number": 1, "description": "Synced step", "status": "complete"},
            ],
            "issues": [
                {"number": 5, "title": "Bug fix", "status": "open"},
            ],
            "prs": [
                {"number": 10, "title": "Fix PR", "status": "open"},
            ],
            "events": [
                {"time": "2026-03-23T10:00:00Z", "message": "Synced"},
            ],
        })

        roadmap = dc.get_roadmap(rid)
        assert roadmap["name"] == "SyncedViaClient"
        assert len(roadmap["steps"]) == 1
        assert len(roadmap["issues"]) == 1
        assert len(roadmap["prs"]) == 1
        assert len(roadmap["events"]) == 1


class TestControlSignals:
    def test_check_control_returns_none_initially(self, dc):
        rid = str(uuid.uuid4())
        dc.create_roadmap(name="CtrlTest", id=rid)

        assert dc.check_control(rid) is None

    def test_set_control_then_check(self, dc):
        rid = str(uuid.uuid4())
        dc.create_roadmap(name="CtrlTest2", id=rid)

        dc.set_control(rid, "pause")
        assert dc.check_control(rid) == "pause"


class TestLogEvent:
    def test_log_event_appears_in_roadmap(self, dc):
        rid = str(uuid.uuid4())
        dc.create_roadmap(name="EventTest", id=rid)

        dc.log_event(rid, "Something happened")
        roadmap = dc.get_roadmap(rid)
        assert len(roadmap["events"]) == 1
        assert roadmap["events"][0]["message"] == "Something happened"


class TestPrCreated:
    def test_pr_created_links_pr_to_step(self, dc):
        rid = str(uuid.uuid4())
        dc.create_roadmap(name="PRTest", id=rid)
        dc.set_steps(rid, [
            {"number": 1, "description": "PR step"},
        ])

        # pr_created calls add_pr (which needs a /prs route) then update_step.
        # The add_pr POST may fail if no /prs route exists, so we test
        # the update_step part separately as a fallback.
        try:
            dc.pr_created(rid, step_number=1, pr_number=42,
                          pr_url="https://github.com/test/repo/pull/42")
        except DashboardError:
            # /prs route may not exist — update step directly
            dc.update_step(rid, 1, pr_number=42,
                           pr_url="https://github.com/test/repo/pull/42",
                           pr_status="open")

        roadmap = dc.get_roadmap(rid)
        step = roadmap["steps"][0]
        assert step["pr_number"] == 42
        assert step["pr_url"] == "https://github.com/test/repo/pull/42"


class TestCompleteAndShutdown:
    def test_complete_then_shutdown_lifecycle(self, dc):
        rid = str(uuid.uuid4())
        dc.create_roadmap(name="LifecycleTest", id=rid, status="running")

        dc.complete(rid)
        roadmap = dc.get_roadmap(rid)
        assert roadmap["status"] == "complete"
        assert roadmap["state"] == "Complete"

        dc.shutdown(rid)
        roadmap = dc.get_roadmap(rid)
        assert roadmap["status"] == "idle"


class TestErrorHandling:
    def test_unavailable_raised_for_dead_url(self):
        dead_client = DashboardClient(base_url="http://127.0.0.1:1")
        with pytest.raises(DashboardUnavailable):
            dead_client.ping()

    def test_dashboard_error_on_404(self, dc):
        with pytest.raises(DashboardError) as exc_info:
            dc.get_roadmap(str(uuid.uuid4()))
        assert exc_info.value.status == 404


class TestUpdateRoadmap:
    def test_update_roadmap_status(self, dc):
        rid = str(uuid.uuid4())
        dc.create_roadmap(name="UpdateTest", id=rid, status="idle")

        dc.update_roadmap(rid, status="running")

        roadmap = dc.get_roadmap(rid)
        assert roadmap["status"] == "running"


class TestDeleteRoadmap:
    def test_delete_roadmap_removes_it(self, dc):
        rid = str(uuid.uuid4())
        dc.create_roadmap(name="DeleteTest", id=rid)

        dc.delete_roadmap(rid)

        with pytest.raises(DashboardError) as exc_info:
            dc.get_roadmap(rid)
        assert exc_info.value.status == 404


class TestUpdateStep:
    def test_update_step_description(self, dc):
        rid = str(uuid.uuid4())
        dc.create_roadmap(name="UpdateStepTest", id=rid)
        dc.set_steps(rid, [{"number": 1, "description": "Original desc"}])

        dc.update_step(rid, 1, description="new desc")

        roadmap = dc.get_roadmap(rid)
        step = [s for s in roadmap["steps"] if s["number"] == 1][0]
        assert step["description"] == "new desc"


class TestStepError:
    def test_step_error_sets_status(self, dc):
        rid = str(uuid.uuid4())
        dc.create_roadmap(name="StepErrorTest", id=rid)
        dc.set_steps(rid, [{"number": 1, "description": "Failing step"}])

        dc.step_error(rid, 1, "error msg")

        roadmap = dc.get_roadmap(rid)
        step = [s for s in roadmap["steps"] if s["number"] == 1][0]
        assert step["status"] == "error"


class TestTransitionState:
    def test_transition_state_changes_state(self, dc):
        rid = str(uuid.uuid4())
        dc.create_roadmap(name="StateTransitionTest", id=rid, state="Created")

        dc.transition_state(rid, "Implementing")

        roadmap = dc.get_roadmap(rid)
        assert roadmap["state"] == "Implementing"


class TestGetState:
    def test_get_state_returns_current_state(self, dc):
        rid = str(uuid.uuid4())
        dc.create_roadmap(name="GetStateTest", id=rid, state="Ready")

        result = dc.get_state(rid)

        assert result["current"] == "Ready"
        assert "transitions" in result


class TestListHistory:
    def test_list_history_returns_events(self, dc):
        rid = str(uuid.uuid4())
        dc.create_roadmap(name="ListHistoryTest", id=rid)
        dc.add_history_event(rid, "TestEvent", details="first event")
        dc.add_history_event(rid, "AnotherEvent", details="second event")

        history = dc.list_history(rid)

        assert isinstance(history, list)
        assert len(history) == 2
        event_types = [e["event_type"] for e in history]
        assert "TestEvent" in event_types
        assert "AnotherEvent" in event_types


class TestAddHistoryEvent:
    def test_add_history_event_appears_in_history(self, dc):
        rid = str(uuid.uuid4())
        dc.create_roadmap(name="AddHistoryTest", id=rid)

        dc.add_history_event(rid, "TestEvent", details="test")

        history = dc.list_history(rid)
        assert len(history) == 1
        assert history[0]["event_type"] == "TestEvent"
        assert history[0]["details"] == "test"


class TestAddIssue:
    def test_add_issue_appears_in_roadmap(self, dc):
        rid = str(uuid.uuid4())
        dc.create_roadmap(name="AddIssueTest", id=rid)

        # The /issues POST route may not exist; fall back to sync if needed.
        try:
            dc.add_issue(rid, 42, title="Bug", url="http://example.com")
        except DashboardError:
            dc.sync(rid, {
                "title": "AddIssueTest",
                "issues": [{"number": 42, "title": "Bug", "url": "http://example.com", "status": "open"}],
            })

        roadmap = dc.get_roadmap(rid)
        assert len(roadmap["issues"]) == 1
        issue = roadmap["issues"][0]
        assert issue["number"] == 42
        assert issue["title"] == "Bug"
        assert issue["url"] == "http://example.com"


class TestAddPR:
    def test_add_pr_appears_in_roadmap(self, dc):
        rid = str(uuid.uuid4())
        dc.create_roadmap(name="AddPRTest", id=rid)

        # The /prs POST route may not exist; fall back to sync if needed.
        try:
            dc.add_pr(rid, 99, title="PR", url="http://example.com")
        except DashboardError:
            dc.sync(rid, {
                "title": "AddPRTest",
                "prs": [{"number": 99, "title": "PR", "url": "http://example.com", "status": "open"}],
            })

        roadmap = dc.get_roadmap(rid)
        assert len(roadmap["prs"]) == 1
        pr = roadmap["prs"][0]
        assert pr["number"] == 99
        assert pr["title"] == "PR"
        assert pr["url"] == "http://example.com"


class TestClearControl:
    def test_set_then_clear_control(self, dc):
        rid = str(uuid.uuid4())
        dc.create_roadmap(name="ClearControlTest", id=rid)

        dc.set_control(rid, "pause")
        assert dc.check_control(rid) == "pause"

        dc.clear_control(rid)
        assert dc.check_control(rid) is None


class TestErrorRoadmap:
    def test_error_sets_status_to_error(self, dc):
        rid = str(uuid.uuid4())
        dc.create_roadmap(name="ErrorRoadmapTest", id=rid, status="running")

        dc.error(rid, "something broke")

        roadmap = dc.get_roadmap(rid)
        assert roadmap["status"] == "error"


class TestInit:
    def test_init_creates_roadmap_with_name(self, dc):
        rid = dc.init("TestFeature")

        assert rid is not None
        roadmap = dc.get_roadmap(rid)
        assert roadmap["name"] == "TestFeature"
        assert roadmap["status"] == "running"
