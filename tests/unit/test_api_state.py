"""Integration tests for state transition routes."""


class TestGetState:
    def test_returns_current_state_and_empty_transitions(self, client, sample_roadmap):
        resp = client.get(f"/api/v1/roadmaps/{sample_roadmap}/state")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["current"] == "Ready"
        assert data["transitions"] == []


class TestTransitionState:
    def test_creates_transition_with_state_and_author(self, client, sample_roadmap):
        resp = client.post(f"/api/v1/roadmaps/{sample_roadmap}/state", json={
            "state": "In Progress", "author": "tester",
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert "id" in data

    def test_400_when_state_missing(self, client, sample_roadmap):
        resp = client.post(f"/api/v1/roadmaps/{sample_roadmap}/state", json={
            "author": "tester",
        })
        assert resp.status_code == 400
        assert "state" in resp.get_json()["error"]

    def test_updates_roadmap_current_state(self, client, sample_roadmap):
        client.post(f"/api/v1/roadmaps/{sample_roadmap}/state", json={
            "state": "In Progress",
        })
        resp = client.get(f"/api/v1/roadmaps/{sample_roadmap}/state")
        assert resp.get_json()["current"] == "In Progress"

    def test_multiple_transitions_returned_in_order(self, client, sample_roadmap):
        client.post(f"/api/v1/roadmaps/{sample_roadmap}/state", json={
            "state": "In Progress",
        })
        client.post(f"/api/v1/roadmaps/{sample_roadmap}/state", json={
            "state": "Review",
        })
        client.post(f"/api/v1/roadmaps/{sample_roadmap}/state", json={
            "state": "Complete",
        })

        resp = client.get(f"/api/v1/roadmaps/{sample_roadmap}/state")
        data = resp.get_json()
        assert data["current"] == "Complete"
        transitions = data["transitions"]
        assert len(transitions) == 3
        assert transitions[0]["state"] == "In Progress"
        assert transitions[1]["state"] == "Review"
        assert transitions[2]["state"] == "Complete"

    def test_previous_state_auto_detected(self, client, sample_roadmap):
        # Initial state is "Ready" from sample_roadmap fixture
        client.post(f"/api/v1/roadmaps/{sample_roadmap}/state", json={
            "state": "In Progress",
        })
        resp = client.get(f"/api/v1/roadmaps/{sample_roadmap}/state")
        transitions = resp.get_json()["transitions"]
        assert transitions[0]["previous_state"] == "Ready"

        # Second transition should auto-detect "In Progress"
        client.post(f"/api/v1/roadmaps/{sample_roadmap}/state", json={
            "state": "Review",
        })
        resp = client.get(f"/api/v1/roadmaps/{sample_roadmap}/state")
        transitions = resp.get_json()["transitions"]
        assert transitions[1]["previous_state"] == "In Progress"
