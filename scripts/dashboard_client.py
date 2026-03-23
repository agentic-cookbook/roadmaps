"""Dashboard service client library.

Uses only stdlib (urllib) — no third-party dependencies.

Configuration (in priority order):
    1. DASHBOARD_URL environment variable
    2. ~/.claude/dashboard.conf (INI-style: url = http://...)
    3. Default: http://localhost:8888

Usage:
    from dashboard_client import DashboardClient

    client = DashboardClient()
    rid = client.create_roadmap(name="MyFeature")
    client.begin_step(rid, 1)
    client.finish_step(rid, 1)
    client.complete(rid)
"""

import json
import os
import urllib.error
import urllib.request
from pathlib import Path


class DashboardUnavailable(Exception):
    """Service is not reachable."""


class DashboardError(Exception):
    """Service returned an HTTP error."""
    def __init__(self, status, body):
        self.status = status
        self.body = body
        super().__init__(f"HTTP {status}: {body}")


def _default_url():
    """Resolve the dashboard service URL."""
    # 1. Environment variable
    url = os.environ.get("DASHBOARD_URL")
    if url:
        return url.rstrip("/")

    # 2. Config file
    conf_path = Path.home() / ".claude" / "dashboard.conf"
    if conf_path.exists():
        for line in conf_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("url") and "=" in line:
                return line.split("=", 1)[1].strip().rstrip("/")

    # 3. Default
    return "http://localhost:8888"


class DashboardClient:
    """Client for the roadmap dashboard REST API."""

    def __init__(self, base_url=None):
        self.base_url = base_url or _default_url()
        self._api = f"{self.base_url}/api/v1"

    def _request(self, method, path, data=None):
        """Make an HTTP request to the API."""
        url = f"{self._api}{path}"
        body = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Content-Type", "application/json")
        try:
            resp = urllib.request.urlopen(req, timeout=10)
            return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body_text = e.read().decode("utf-8", errors="replace")
            raise DashboardError(e.code, body_text)
        except (urllib.error.URLError, OSError) as e:
            raise DashboardUnavailable(str(e))

    def _get(self, path):
        return self._request("GET", path)

    def _post(self, path, data=None):
        return self._request("POST", path, data or {})

    def _put(self, path, data=None):
        return self._request("PUT", path, data or {})

    def _delete(self, path):
        return self._request("DELETE", path)

    # --- Health ---

    def ping(self):
        """Check if the service is reachable."""
        return self._get("/health")

    # --- Roadmaps ---

    def list_roadmaps(self, state=None, status=None):
        params = []
        if state:
            params.append(f"state={state}")
        if status:
            params.append(f"status={status}")
        qs = "?" + "&".join(params) if params else ""
        return self._get(f"/roadmaps{qs}")

    def create_roadmap(self, name, id=None, state="Created", status="idle",
                       author=None, repo=None, repo_url=None, branch=None,
                       machine=None, worktree=None):
        data = {"name": name, "state": state, "status": status}
        if id:
            data["id"] = id
        if author:
            data["author"] = author
        if repo:
            data["repo"] = repo
        if repo_url:
            data["repo_url"] = repo_url
        if branch:
            data["branch"] = branch
        if machine:
            data["machine"] = machine
        if worktree:
            data["worktree"] = worktree
        return self._post("/roadmaps", data)

    def get_roadmap(self, roadmap_id):
        return self._get(f"/roadmaps/{roadmap_id}")

    def update_roadmap(self, roadmap_id, **kwargs):
        return self._put(f"/roadmaps/{roadmap_id}", kwargs)

    def delete_roadmap(self, roadmap_id):
        return self._delete(f"/roadmaps/{roadmap_id}")

    # --- Steps ---

    def set_steps(self, roadmap_id, steps):
        """Bulk create/replace steps. steps is a list of dicts."""
        return self._post(f"/roadmaps/{roadmap_id}/steps", steps)

    def update_step(self, roadmap_id, number, **kwargs):
        return self._put(f"/roadmaps/{roadmap_id}/steps/{number}", kwargs)

    def begin_step(self, roadmap_id, number):
        return self._post(f"/roadmaps/{roadmap_id}/steps/{number}/begin")

    def finish_step(self, roadmap_id, number):
        return self._post(f"/roadmaps/{roadmap_id}/steps/{number}/finish")

    def step_error(self, roadmap_id, number, message):
        return self._post(f"/roadmaps/{roadmap_id}/steps/{number}/error",
                          {"message": message})

    # --- State ---

    def get_state(self, roadmap_id):
        return self._get(f"/roadmaps/{roadmap_id}/state")

    def transition_state(self, roadmap_id, state, author=None):
        data = {"state": state}
        if author:
            data["author"] = author
        return self._post(f"/roadmaps/{roadmap_id}/state", data)

    # --- History ---

    def list_history(self, roadmap_id):
        return self._get(f"/roadmaps/{roadmap_id}/history")

    def add_history_event(self, roadmap_id, event_type, step_number=None,
                          author=None, details=None):
        data = {"event_type": event_type}
        if step_number is not None:
            data["step_number"] = step_number
        if author:
            data["author"] = author
        if details:
            data["details"] = details
        return self._post(f"/roadmaps/{roadmap_id}/history", data)

    # --- Runtime Events ---

    def log_event(self, roadmap_id, message):
        return self._post(f"/roadmaps/{roadmap_id}/events", {"message": message})

    # --- Issues & PRs ---

    def add_issue(self, roadmap_id, number, title=None, url=None, status=None):
        data = {"number": number}
        if title:
            data["title"] = title
        if url:
            data["url"] = url
        if status:
            data["status"] = status
        return self._post(f"/roadmaps/{roadmap_id}/issues", data)

    def add_pr(self, roadmap_id, number, title=None, url=None, status=None):
        data = {"number": number}
        if title:
            data["title"] = title
        if url:
            data["url"] = url
        if status:
            data["status"] = status
        return self._post(f"/roadmaps/{roadmap_id}/prs", data)

    def pr_created(self, roadmap_id, step_number, pr_number, pr_url):
        """Convenience: link a PR to a step and add it to the PR list."""
        self.add_pr(roadmap_id, pr_number, url=pr_url, status="open")
        self.update_step(roadmap_id, step_number,
                         pr_number=pr_number, pr_url=pr_url, pr_status="open")

    # --- Controls ---

    def check_control(self, roadmap_id):
        """Returns the control action or None."""
        result = self._get(f"/roadmaps/{roadmap_id}/control")
        return result.get("action")

    def set_control(self, roadmap_id, action):
        return self._post(f"/roadmaps/{roadmap_id}/control", {"action": action})

    def clear_control(self, roadmap_id):
        return self._delete(f"/roadmaps/{roadmap_id}/control")

    # --- Lifecycle ---

    def complete(self, roadmap_id):
        return self._post(f"/roadmaps/{roadmap_id}/complete")

    def error(self, roadmap_id, message=None):
        data = {"message": message} if message else {}
        return self._post(f"/roadmaps/{roadmap_id}/error", data)

    def shutdown(self, roadmap_id):
        return self._post(f"/roadmaps/{roadmap_id}/shutdown")

    # --- Sync ---

    def sync(self, roadmap_id, data):
        """Full state sync — send complete roadmap state."""
        return self._post(f"/roadmaps/{roadmap_id}/sync", data)

    # --- Init (high-level convenience) ---

    def init(self, name, steps=None, environment=None, roadmap_id=None):
        """Create a roadmap and optionally set steps. Returns roadmap ID."""
        import uuid
        rid = roadmap_id or str(uuid.uuid4())
        data = {"id": rid, "name": name, "status": "running"}
        if environment:
            data.update({
                "repo": environment.get("repo"),
                "repo_url": environment.get("repo_url"),
                "branch": environment.get("branch"),
                "machine": environment.get("machine"),
                "worktree": environment.get("worktree"),
            })
        self.create_roadmap(**{k: v for k, v in data.items() if v is not None})
        if steps:
            step_data = []
            for i, name in enumerate(steps, 1):
                step_data.append({"number": i, "description": name})
            self.set_steps(rid, step_data)
        return rid
