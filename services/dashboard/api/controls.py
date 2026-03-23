"""Control signal routes (pause/resume/stop)."""

from flask import g, jsonify, request

from . import api
from .. import models


@api.route("/roadmaps/<roadmap_id>/control", methods=["GET"])
def get_control(roadmap_id):
    ctrl = models.get_control(g.db, roadmap_id)
    if ctrl and ctrl.get("action"):
        return jsonify({"action": ctrl["action"]})
    return jsonify({"action": None})


@api.route("/roadmaps/<roadmap_id>/control", methods=["POST"])
def set_control(roadmap_id):
    data = request.get_json(force=True)
    action = data.get("action")
    if action not in ("pause", "resume", "stop"):
        return jsonify({"error": "action must be pause, resume, or stop"}), 400
    models.set_control(g.db, roadmap_id, action)
    from .sse import broadcast
    broadcast("control_changed", {"roadmap_id": roadmap_id, "action": action})
    return jsonify({"ok": True})


@api.route("/roadmaps/<roadmap_id>/control", methods=["DELETE"])
def clear_control(roadmap_id):
    models.clear_control(g.db, roadmap_id)
    return jsonify({"ok": True})
