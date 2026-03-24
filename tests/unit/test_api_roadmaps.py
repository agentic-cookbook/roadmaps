"""Integration tests for roadmap CRUD and lifecycle routes."""

import uuid


class TestCreateRoadmap:
    def test_creates_and_returns_201(self, client):
        resp = client.post("/api/v1/roadmaps", json={
            "name": "NewFeature", "state": "Created",
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert "id" in data

    def test_400_when_name_missing(self, client):
        resp = client.post("/api/v1/roadmaps", json={"state": "Created"})
        assert resp.status_code == 400
        assert "name" in resp.get_json()["error"]


class TestListRoadmaps:
    def test_lists_all(self, client, sample_roadmap):
        resp = client.get("/api/v1/roadmaps")
        assert resp.status_code == 200
        roadmaps = resp.get_json()
        assert any(r["id"] == sample_roadmap for r in roadmaps)

    def test_filters_by_state(self, client, sample_roadmap):
        resp = client.get("/api/v1/roadmaps?state=Ready")
        assert resp.status_code == 200
        roadmaps = resp.get_json()
        assert all(r["state"] == "Ready" for r in roadmaps)
        assert any(r["id"] == sample_roadmap for r in roadmaps)

    def test_filters_by_status(self, client, sample_roadmap):
        resp = client.get("/api/v1/roadmaps?status=running")
        assert resp.status_code == 200
        roadmaps = resp.get_json()
        assert all(r["status"] == "running" for r in roadmaps)
        assert any(r["id"] == sample_roadmap for r in roadmaps)


class TestGetRoadmap:
    def test_returns_full_roadmap_with_nested_data(self, client, sample_roadmap):
        resp = client.get(f"/api/v1/roadmaps/{sample_roadmap}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["id"] == sample_roadmap
        assert data["name"] == "TestFeature"
        assert "steps" in data
        assert "issues" in data
        assert "prs" in data
        assert "events" in data
        assert len(data["steps"]) == 3

    def test_404_for_nonexistent(self, client):
        resp = client.get(f"/api/v1/roadmaps/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestUpdateRoadmap:
    def test_updates_name_and_state(self, client, sample_roadmap):
        resp = client.put(f"/api/v1/roadmaps/{sample_roadmap}", json={
            "name": "Renamed", "state": "In Progress",
        })
        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True

        # Verify the update persisted
        get_resp = client.get(f"/api/v1/roadmaps/{sample_roadmap}")
        data = get_resp.get_json()
        assert data["name"] == "Renamed"
        assert data["state"] == "In Progress"


class TestDeleteRoadmap:
    def test_deletes_and_subsequent_get_404(self, client, sample_roadmap):
        resp = client.delete(f"/api/v1/roadmaps/{sample_roadmap}")
        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True

        get_resp = client.get(f"/api/v1/roadmaps/{sample_roadmap}")
        assert get_resp.status_code == 404


class TestRoadmapLifecycle:
    def test_complete_sets_status_and_state(self, client, sample_roadmap):
        resp = client.post(f"/api/v1/roadmaps/{sample_roadmap}/complete")
        assert resp.status_code == 200

        data = client.get(f"/api/v1/roadmaps/{sample_roadmap}").get_json()
        assert data["status"] == "complete"
        assert data["state"] == "Complete"

    def test_error_sets_status(self, client, sample_roadmap):
        resp = client.post(f"/api/v1/roadmaps/{sample_roadmap}/error",
                           json={"message": "something broke"})
        assert resp.status_code == 200

        data = client.get(f"/api/v1/roadmaps/{sample_roadmap}").get_json()
        assert data["status"] == "error"

    def test_shutdown_sets_status_idle(self, client, sample_roadmap):
        resp = client.post(f"/api/v1/roadmaps/{sample_roadmap}/shutdown")
        assert resp.status_code == 200

        data = client.get(f"/api/v1/roadmaps/{sample_roadmap}").get_json()
        assert data["status"] == "idle"


class TestHealth:
    def test_health_returns_ok(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.get_json() == {"status": "ok"}
