"""Integration tests for step CRUD and lifecycle routes."""


class TestBulkCreateSteps:
    def test_creates_steps_returns_201(self, client, sample_roadmap):
        # sample_roadmap already has 3 steps; bulk create replaces them
        resp = client.post(f"/api/v1/roadmaps/{sample_roadmap}/steps", json=[
            {"number": 1, "description": "Alpha", "step_type": "Auto", "complexity": "S"},
            {"number": 2, "description": "Beta", "step_type": "Manual", "complexity": "L"},
        ])
        assert resp.status_code == 201
        assert resp.get_json()["ok"] is True

        # Verify replacement
        steps = client.get(f"/api/v1/roadmaps/{sample_roadmap}/steps").get_json()
        assert len(steps) == 2
        assert steps[0]["description"] == "Alpha"

    def test_400_for_non_array_body(self, client, sample_roadmap):
        resp = client.post(f"/api/v1/roadmaps/{sample_roadmap}/steps",
                           json={"number": 1, "description": "Bad"})
        assert resp.status_code == 400
        assert "array" in resp.get_json()["error"]


class TestListSteps:
    def test_returns_steps_ordered_by_number(self, client, sample_roadmap):
        resp = client.get(f"/api/v1/roadmaps/{sample_roadmap}/steps")
        assert resp.status_code == 200
        steps = resp.get_json()
        assert len(steps) == 3
        assert [s["number"] for s in steps] == [1, 2, 3]


class TestGetStep:
    def test_returns_single_step(self, client, sample_roadmap):
        resp = client.get(f"/api/v1/roadmaps/{sample_roadmap}/steps/1")
        assert resp.status_code == 200
        step = resp.get_json()
        assert step["number"] == 1
        assert step["description"] == "First step"

    def test_404_for_missing_step(self, client, sample_roadmap):
        resp = client.get(f"/api/v1/roadmaps/{sample_roadmap}/steps/99")
        assert resp.status_code == 404


class TestUpdateStep:
    def test_updates_description_and_detail(self, client, sample_roadmap):
        resp = client.put(f"/api/v1/roadmaps/{sample_roadmap}/steps/1", json={
            "description": "Updated first step",
            "detail": "Some extra detail",
        })
        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True

        step = client.get(f"/api/v1/roadmaps/{sample_roadmap}/steps/1").get_json()
        assert step["description"] == "Updated first step"
        assert step["detail"] == "Some extra detail"


class TestBeginStep:
    def test_sets_in_progress(self, client, sample_roadmap):
        resp = client.post(f"/api/v1/roadmaps/{sample_roadmap}/steps/1/begin")
        assert resp.status_code == 200

        step = client.get(f"/api/v1/roadmaps/{sample_roadmap}/steps/1").get_json()
        assert step["status"] == "in_progress"
        assert step["started_at"] is not None

    def test_auto_completes_prior_active_step(self, client, sample_roadmap):
        # Begin step 1
        client.post(f"/api/v1/roadmaps/{sample_roadmap}/steps/1/begin")
        step1 = client.get(f"/api/v1/roadmaps/{sample_roadmap}/steps/1").get_json()
        assert step1["status"] == "in_progress"

        # Begin step 2 — should auto-complete step 1
        client.post(f"/api/v1/roadmaps/{sample_roadmap}/steps/2/begin")
        step1 = client.get(f"/api/v1/roadmaps/{sample_roadmap}/steps/1").get_json()
        assert step1["status"] == "complete"
        assert step1["completed_at"] is not None

        step2 = client.get(f"/api/v1/roadmaps/{sample_roadmap}/steps/2").get_json()
        assert step2["status"] == "in_progress"


class TestFinishStep:
    def test_sets_complete_with_timestamp(self, client, sample_roadmap):
        client.post(f"/api/v1/roadmaps/{sample_roadmap}/steps/1/begin")
        resp = client.post(f"/api/v1/roadmaps/{sample_roadmap}/steps/1/finish")
        assert resp.status_code == 200

        step = client.get(f"/api/v1/roadmaps/{sample_roadmap}/steps/1").get_json()
        assert step["status"] == "complete"
        assert step["completed_at"] is not None


class TestErrorStep:
    def test_sets_error_with_message(self, client, sample_roadmap):
        resp = client.post(f"/api/v1/roadmaps/{sample_roadmap}/steps/1/error",
                           json={"message": "Build failed"})
        assert resp.status_code == 200

        step = client.get(f"/api/v1/roadmaps/{sample_roadmap}/steps/1").get_json()
        assert step["status"] == "error"
        assert step["detail"] == "Build failed"
