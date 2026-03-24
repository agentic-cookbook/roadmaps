"""Integration tests for history events and runtime events endpoints."""


class TestHistoryEvents:
    def test_add_history_event(self, client, sample_roadmap):
        resp = client.post(f"/api/v1/roadmaps/{sample_roadmap}/history", json={
            "event_type": "step_started",
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert "id" in data

    def test_list_history_events(self, client, sample_roadmap):
        client.post(f"/api/v1/roadmaps/{sample_roadmap}/history", json={
            "event_type": "step_started",
            "author": "tester",
            "details": "beginning step 1",
        })
        client.post(f"/api/v1/roadmaps/{sample_roadmap}/history", json={
            "event_type": "step_completed",
            "author": "tester",
        })

        resp = client.get(f"/api/v1/roadmaps/{sample_roadmap}/history")
        assert resp.status_code == 200
        events = resp.get_json()
        assert len(events) == 2
        assert events[0]["event_type"] == "step_started"
        assert events[1]["event_type"] == "step_completed"

    def test_history_event_with_step_number(self, client, sample_roadmap):
        resp = client.post(f"/api/v1/roadmaps/{sample_roadmap}/history", json={
            "event_type": "step_started",
            "step_number": 2,
        })
        assert resp.status_code == 201

        events = client.get(f"/api/v1/roadmaps/{sample_roadmap}/history").get_json()
        assert len(events) == 1
        assert events[0]["step_number"] == 2

    def test_add_history_event_400_when_event_type_missing(self, client, sample_roadmap):
        resp = client.post(f"/api/v1/roadmaps/{sample_roadmap}/history", json={
            "author": "tester",
        })
        assert resp.status_code == 400
        assert "event_type" in resp.get_json()["error"]


class TestRuntimeEvents:
    def test_log_runtime_event(self, client, sample_roadmap):
        resp = client.post(f"/api/v1/roadmaps/{sample_roadmap}/events", json={
            "message": "Worker started processing step 1",
        })
        assert resp.status_code == 201
        assert resp.get_json()["ok"] is True

    def test_list_runtime_events(self, client, sample_roadmap):
        client.post(f"/api/v1/roadmaps/{sample_roadmap}/events", json={
            "message": "Step 1 started",
        })
        client.post(f"/api/v1/roadmaps/{sample_roadmap}/events", json={
            "message": "Step 1 complete",
        })

        resp = client.get(f"/api/v1/roadmaps/{sample_roadmap}/events")
        assert resp.status_code == 200
        events = resp.get_json()
        assert len(events) == 2
        assert events[0]["message"] == "Step 1 started"
        assert events[1]["message"] == "Step 1 complete"

    def test_log_runtime_event_400_when_message_missing(self, client, sample_roadmap):
        resp = client.post(f"/api/v1/roadmaps/{sample_roadmap}/events", json={})
        assert resp.status_code == 400
        assert "message" in resp.get_json()["error"]
