"""Shared test fixtures."""

import os
import sys
import tempfile
import uuid
from pathlib import Path

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from services.dashboard import db
from services.dashboard.app import create_app


@pytest.fixture
def db_conn():
    """In-memory SQLite connection with schema initialized."""
    conn = db.connect(":memory:")
    db.init_db(conn)
    yield conn
    conn.close()


@pytest.fixture
def app(tmp_path):
    """Flask test app with temp SQLite database."""
    db_path = str(tmp_path / "test.db")
    os.environ["DASHBOARD_DB"] = db_path
    application = create_app()
    application.config["TESTING"] = True

    # Initialize DB
    conn = db.connect(db_path)
    db.init_db(conn)
    conn.close()

    yield application
    os.environ.pop("DASHBOARD_DB", None)


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def sample_roadmap(client):
    """Create a roadmap with 3 steps, return the ID."""
    rid = str(uuid.uuid4())
    resp = client.post("/api/v1/roadmaps", json={
        "id": rid, "name": "TestFeature", "state": "Ready", "status": "running",
        "repo": "test/repo", "repo_url": "https://github.com/test/repo",
    })
    assert resp.status_code == 201
    client.post(f"/api/v1/roadmaps/{rid}/steps", json=[
        {"number": 1, "description": "First step", "status": "not_started", "step_type": "Auto", "complexity": "S"},
        {"number": 2, "description": "Second step", "status": "not_started", "step_type": "Auto", "complexity": "M"},
        {"number": 3, "description": "Third step", "status": "not_started", "step_type": "Manual", "complexity": "L"},
    ])
    return rid


@pytest.fixture
def tmp_roadmap_dir(tmp_path):
    """Create a realistic File Record directory structure for roadmap_lib tests."""
    roadmaps = tmp_path / "Roadmaps"

    # Create two roadmap directories
    rd1 = roadmaps / "2026-03-21-FeatureAlpha"
    rd1.mkdir(parents=True)
    (rd1 / "State").mkdir()
    (rd1 / "History").mkdir()

    (rd1 / "Definition.md").write_text(
        "---\nid: def-alpha-id\ncreated: 2026-03-21\nmodified: 2026-03-21\nauthor: Test User <test@test.com>\n"
        "change-history:\n  - date: 2026-03-21\n    author: Test User <test@test.com>\n    summary: Initial\n---\n\n"
        "# Feature Definition: FeatureAlpha\n\n## Goal and Purpose\n\nTest feature.\n"
    )
    (rd1 / "Roadmap.md").write_text(
        "---\nid: rm-alpha-id\ncreated: 2026-03-21\nmodified: 2026-03-21\nauthor: Test User <test@test.com>\n"
        "definition-id: def-alpha-id\nchange-history:\n  - date: 2026-03-21\n    author: Test User <test@test.com>\n    summary: Initial\n---\n\n"
        "# Feature Roadmap: FeatureAlpha\n\n## Implementation Steps\n\n"
        "### Step 1: Do thing one\n\n- **Status**: Complete\n- **Type**: Auto\n- **Complexity**: S\n\n"
        "### Step 2: Do thing two\n\n- **Status**: Not Started\n- **Type**: Auto\n- **Complexity**: M\n\n"
        "### Step 3: Manual review\n\n- **Status**: Not Started\n- **Type**: Manual\n- **Complexity**: S\n"
    )
    (rd1 / "State" / "2026-03-21-Created.md").write_text("---\nid: s1\ncreated: 2026-03-21\n---\n\n# State: Created\n")
    (rd1 / "State" / "2026-03-21-Ready.md").write_text("---\nid: s2\ncreated: 2026-03-21\n---\n\n# State: Ready\n")

    rd2 = roadmaps / "2026-03-22-FeatureBeta"
    rd2.mkdir(parents=True)
    (rd2 / "State").mkdir()
    (rd2 / "History").mkdir()
    (rd2 / "Roadmap.md").write_text(
        "---\nid: rm-beta-id\ncreated: 2026-03-22\n---\n\n"
        "# Feature Roadmap: FeatureBeta\n\n### Step 1: Only step\n\n- **Status**: Complete\n"
    )
    (rd2 / "State" / "2026-03-22-Complete.md").write_text("---\nid: s3\n---\n\n# State: Complete\n")

    return tmp_path


@pytest.fixture
def coordinator_roadmap(tmp_path):
    """Create a temp Roadmap.md for coordinator tests."""
    roadmap_dir = tmp_path / "Roadmaps" / "2026-03-21-TestFeature"
    roadmap_dir.mkdir(parents=True)
    (roadmap_dir / "State").mkdir()
    (roadmap_dir / "State" / "2026-03-21-Ready.md").write_text("# State: Ready\n")

    roadmap = roadmap_dir / "Roadmap.md"
    roadmap.write_text(
        "# Feature Roadmap: TestFeature\n\n"
        "### Step 1: First step\n\n"
        "- **GitHub Issue**: #10\n- **Type**: Auto\n- **Status**: Complete\n- **Complexity**: S\n\n"
        "### Step 2: Second step\n\n"
        "- **GitHub Issue**: #11\n- **Type**: Auto\n- **Status**: Not Started\n- **Complexity**: M\n\n"
        "### Step 3: Manual step\n\n"
        "- **GitHub Issue**: #12\n- **Type**: Manual\n- **Status**: Not Started\n- **Complexity**: S\n\n"
        "### Step 4: Last step\n\n"
        "- **GitHub Issue**: #13\n- **Type**: Auto\n- **Status**: Not Started\n- **Complexity**: L\n"
    )
    return tmp_path
