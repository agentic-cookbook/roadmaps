"""Integration tests for control signal routes."""


class TestGetControl:
    def test_returns_null_action_when_no_signal(self, client, sample_roadmap):
        resp = client.get(f"/api/v1/roadmaps/{sample_roadmap}/control")
        assert resp.status_code == 200
        assert resp.get_json()["action"] is None


class TestSetControl:
    def test_sets_pause(self, client, sample_roadmap):
        resp = client.post(f"/api/v1/roadmaps/{sample_roadmap}/control",
                           json={"action": "pause"})
        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True

        ctrl = client.get(f"/api/v1/roadmaps/{sample_roadmap}/control").get_json()
        assert ctrl["action"] == "pause"

    def test_sets_resume(self, client, sample_roadmap):
        client.post(f"/api/v1/roadmaps/{sample_roadmap}/control",
                    json={"action": "pause"})
        resp = client.post(f"/api/v1/roadmaps/{sample_roadmap}/control",
                           json={"action": "resume"})
        assert resp.status_code == 200

        ctrl = client.get(f"/api/v1/roadmaps/{sample_roadmap}/control").get_json()
        assert ctrl["action"] == "resume"

    def test_sets_stop(self, client, sample_roadmap):
        resp = client.post(f"/api/v1/roadmaps/{sample_roadmap}/control",
                           json={"action": "stop"})
        assert resp.status_code == 200

        ctrl = client.get(f"/api/v1/roadmaps/{sample_roadmap}/control").get_json()
        assert ctrl["action"] == "stop"

    def test_400_for_invalid_action(self, client, sample_roadmap):
        resp = client.post(f"/api/v1/roadmaps/{sample_roadmap}/control",
                           json={"action": "invalid"})
        assert resp.status_code == 400
        assert "action" in resp.get_json()["error"]


class TestClearControl:
    def test_clears_signal_and_subsequent_get_returns_null(self, client, sample_roadmap):
        # Set a signal first
        client.post(f"/api/v1/roadmaps/{sample_roadmap}/control",
                    json={"action": "pause"})
        ctrl = client.get(f"/api/v1/roadmaps/{sample_roadmap}/control").get_json()
        assert ctrl["action"] == "pause"

        # Clear it
        resp = client.delete(f"/api/v1/roadmaps/{sample_roadmap}/control")
        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True

        ctrl = client.get(f"/api/v1/roadmaps/{sample_roadmap}/control").get_json()
        assert ctrl["action"] is None
