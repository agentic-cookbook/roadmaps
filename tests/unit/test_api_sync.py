"""Integration tests for the bulk sync route."""

import uuid


def _full_sync_payload():
    """Return a complete sync payload for testing."""
    return {
        "title": "SyncedFeature",
        "state": "In Progress",
        "status": "running",
        "environment": {
            "repo": "test/repo",
            "repo_url": "https://github.com/test/repo",
            "branch": "feature/sync",
            "machine": "ci-box",
            "worktree": "/tmp/wt",
        },
        "steps": [
            {"number": 1, "description": "Sync step A", "status": "complete",
             "step_type": "Auto", "complexity": "S"},
            {"number": 2, "description": "Sync step B", "status": "in_progress",
             "step_type": "Auto", "complexity": "M"},
        ],
        "issues": [
            {"number": 10, "title": "Issue ten", "url": "https://github.com/issues/10", "status": "open"},
            {"number": 11, "title": "Issue eleven", "url": "https://github.com/issues/11", "status": "closed"},
        ],
        "prs": [
            {"number": 20, "title": "PR twenty", "url": "https://github.com/pulls/20", "status": "open"},
        ],
        "events": [
            {"time": "2026-03-23T10:00:00Z", "message": "Started sync"},
            {"time": "2026-03-23T10:01:00Z", "message": "Step 1 done"},
        ],
    }


class TestSyncCreatesNewRoadmap:
    def test_creates_from_full_payload(self, client):
        rid = str(uuid.uuid4())
        payload = _full_sync_payload()
        resp = client.post(f"/api/v1/roadmaps/{rid}/sync", json=payload)
        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True

        # Verify the roadmap was created with correct fields
        data = client.get(f"/api/v1/roadmaps/{rid}").get_json()
        assert data["name"] == "SyncedFeature"
        assert data["state"] == "In Progress"
        assert data["status"] == "running"
        assert data["repo"] == "test/repo"
        assert data["branch"] == "feature/sync"
        assert len(data["steps"]) == 2
        assert len(data["issues"]) == 2
        assert len(data["prs"]) == 1
        assert len(data["events"]) == 2


class TestSyncUpdatesExisting:
    def test_updates_roadmap_and_replaces_steps(self, client, sample_roadmap):
        # sample_roadmap has 3 steps; sync will replace them with 2
        payload = _full_sync_payload()
        resp = client.post(f"/api/v1/roadmaps/{sample_roadmap}/sync", json=payload)
        assert resp.status_code == 200

        data = client.get(f"/api/v1/roadmaps/{sample_roadmap}").get_json()
        assert data["name"] == "SyncedFeature"
        assert data["state"] == "In Progress"

    def test_old_steps_replaced_with_new(self, client, sample_roadmap):
        payload = _full_sync_payload()
        client.post(f"/api/v1/roadmaps/{sample_roadmap}/sync", json=payload)

        steps = client.get(f"/api/v1/roadmaps/{sample_roadmap}/steps").get_json()
        assert len(steps) == 2
        assert steps[0]["description"] == "Sync step A"
        assert steps[1]["description"] == "Sync step B"
        # Original "First step", "Second step", "Third step" should be gone

    def test_issues_synced(self, client, sample_roadmap):
        payload = _full_sync_payload()
        client.post(f"/api/v1/roadmaps/{sample_roadmap}/sync", json=payload)

        data = client.get(f"/api/v1/roadmaps/{sample_roadmap}").get_json()
        issues = data["issues"]
        assert len(issues) == 2
        assert issues[0]["number"] == 10
        assert issues[1]["number"] == 11

    def test_prs_synced(self, client, sample_roadmap):
        payload = _full_sync_payload()
        client.post(f"/api/v1/roadmaps/{sample_roadmap}/sync", json=payload)

        data = client.get(f"/api/v1/roadmaps/{sample_roadmap}").get_json()
        prs = data["prs"]
        assert len(prs) == 1
        assert prs[0]["number"] == 20
        assert prs[0]["title"] == "PR twenty"

    def test_runtime_events_synced(self, client, sample_roadmap):
        payload = _full_sync_payload()
        client.post(f"/api/v1/roadmaps/{sample_roadmap}/sync", json=payload)

        data = client.get(f"/api/v1/roadmaps/{sample_roadmap}").get_json()
        events = data["events"]
        assert len(events) == 2
        assert events[0]["message"] == "Started sync"
        assert events[1]["message"] == "Step 1 done"


class TestSyncDescription:
    def test_sync_creates_with_description(self, client):
        rid = str(uuid.uuid4())
        payload = _full_sync_payload()
        payload["description"] = "Menu bar app for session monitoring"
        resp = client.post(f"/api/v1/roadmaps/{rid}/sync", json=payload)
        assert resp.status_code == 200

        data = client.get(f"/api/v1/roadmaps/{rid}").get_json()
        assert data["description"] == "Menu bar app for session monitoring"

    def test_sync_updates_description(self, client, sample_roadmap):
        payload = _full_sync_payload()
        payload["description"] = "Original description"
        client.post(f"/api/v1/roadmaps/{sample_roadmap}/sync", json=payload)

        payload["description"] = "Updated description"
        client.post(f"/api/v1/roadmaps/{sample_roadmap}/sync", json=payload)

        data = client.get(f"/api/v1/roadmaps/{sample_roadmap}").get_json()
        assert data["description"] == "Updated description"

    def test_sync_without_description_is_null(self, client):
        rid = str(uuid.uuid4())
        payload = _full_sync_payload()
        resp = client.post(f"/api/v1/roadmaps/{rid}/sync", json=payload)
        assert resp.status_code == 200

        data = client.get(f"/api/v1/roadmaps/{rid}").get_json()
        assert data["description"] is None
