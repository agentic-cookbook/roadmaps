"""Integration tests for archive/unarchive endpoints."""

import uuid


class TestArchiveRoadmap:
    def test_archive_roadmap(self, client, sample_roadmap):
        resp = client.post(f"/api/v1/roadmaps/{sample_roadmap}/archive")
        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True

        data = client.get(f"/api/v1/roadmaps/{sample_roadmap}").get_json()
        assert data["archived"] == 1

    def test_unarchive_roadmap(self, client, sample_roadmap):
        client.post(f"/api/v1/roadmaps/{sample_roadmap}/archive")
        resp = client.post(f"/api/v1/roadmaps/{sample_roadmap}/unarchive")
        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True

        data = client.get(f"/api/v1/roadmaps/{sample_roadmap}").get_json()
        assert data["archived"] == 0

    def test_archive_nonexistent_roadmap(self, client):
        resp = client.post(f"/api/v1/roadmaps/{uuid.uuid4()}/archive")
        assert resp.status_code == 404

    def test_list_archived_roadmaps(self, client, sample_roadmap):
        client.post(f"/api/v1/roadmaps/{sample_roadmap}/archive")

        resp = client.get("/api/v1/roadmaps?archived=true")
        assert resp.status_code == 200
        roadmaps = resp.get_json()
        assert any(r["id"] == sample_roadmap for r in roadmaps)

    def test_archived_excluded_by_default(self, client, sample_roadmap):
        client.post(f"/api/v1/roadmaps/{sample_roadmap}/archive")

        resp = client.get("/api/v1/roadmaps")
        assert resp.status_code == 200
        roadmaps = resp.get_json()
        assert not any(r["id"] == sample_roadmap for r in roadmaps)
