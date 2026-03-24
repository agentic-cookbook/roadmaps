"""Dashboard synchronization integration tests."""

import uuid

import pytest


class TestStepStatusTransitions:
    """begin_step -> in_progress, finish_step -> complete."""

    def test_step_status_transitions(self, dashboard_server):
        ds = dashboard_server
        rid = str(uuid.uuid4())

        ds.cli.create_roadmap("SyncTest", id=rid)
        ds.cli.set_steps(rid, [
            {
                "number": 1, "description": "Step 1",
                "status": "not_started", "step_type": "Auto",
                "complexity": "S",
            },
        ])

        # Begin
        ds.cli.begin_step(rid, 1)
        data = ds.api_get(f"/api/v1/roadmaps/{rid}")
        assert data["steps"][0]["status"] == "in_progress"

        # Finish
        ds.cli.finish_step(rid, 1)
        data = ds.api_get(f"/api/v1/roadmaps/{rid}")
        assert data["steps"][0]["status"] == "complete"


class TestRoadmapStatusLifecycle:
    """idle -> running -> complete."""

    def test_roadmap_status_lifecycle(self, dashboard_server):
        ds = dashboard_server
        rid = str(uuid.uuid4())

        ds.cli.create_roadmap("StatusTest", id=rid, status="idle")
        data = ds.api_get(f"/api/v1/roadmaps/{rid}")
        assert data["status"] == "idle"

        ds.cli.update_roadmap(rid, status="running")
        data = ds.api_get(f"/api/v1/roadmaps/{rid}")
        assert data["status"] == "running"

        ds.cli.complete(rid)
        data = ds.api_get(f"/api/v1/roadmaps/{rid}")
        assert data["status"] == "complete"


class TestRoadmapStateLifecycle:
    """Ready -> Implementing -> Complete with state history."""

    def test_roadmap_state_lifecycle(self, dashboard_server):
        ds = dashboard_server
        rid = str(uuid.uuid4())

        ds.cli.create_roadmap("StateTest", id=rid, state="Ready")
        ds.cli.transition_state(rid, "Implementing")
        ds.cli.transition_state(rid, "Complete")

        data = ds.api_get(f"/api/v1/roadmaps/{rid}")
        assert data["state"] == "Complete"


class TestDashboardReflectsCurrentState:
    """After each simulated step, dashboard shows correct completion count."""

    def test_dashboard_reflects_current_state(self, dashboard_server):
        ds = dashboard_server
        rid = str(uuid.uuid4())

        ds.cli.create_roadmap("ReflectTest", id=rid, status="running")
        ds.cli.set_steps(rid, [
            {
                "number": i, "description": f"Step {i}",
                "status": "not_started", "step_type": "Auto",
                "complexity": "S",
            }
            for i in range(1, 4)
        ])

        for step_num in range(1, 4):
            ds.cli.begin_step(rid, step_num)
            ds.cli.finish_step(rid, step_num)
            data = ds.api_get(f"/api/v1/roadmaps/{rid}")
            complete_count = sum(
                1 for s in data["steps"] if s["status"] == "complete"
            )
            assert complete_count == step_num


class TestSinglePROnOverview:
    """add_pr makes the PR visible in the overview API."""

    def test_single_pr_on_overview(self, dashboard_server):
        ds = dashboard_server
        rid = str(uuid.uuid4())

        ds.cli.create_roadmap("PRTest", id=rid)
        ds.cli.add_pr(
            rid, number=42, title="feat: test PR",
            url="https://github.com/test/repo/pull/42",
        )

        data = ds.api_get("/api/v1/roadmaps?detail=true")
        roadmap = next(r for r in data if r["id"] == rid)
        assert len(roadmap["prs"]) == 1
        assert roadmap["prs"][0]["number"] == 42
