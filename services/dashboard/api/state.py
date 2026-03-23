"""State transition routes."""

from flask import g, jsonify, request

from . import api
from .. import models


@api.route("/roadmaps/<roadmap_id>/state", methods=["GET"])
def get_state(roadmap_id):
    row = g.db.execute("SELECT state FROM roadmaps WHERE id = ?", (roadmap_id,)).fetchone()
    if not row:
        return jsonify({"error": "not found"}), 404
    transitions = models.list_state_transitions(g.db, roadmap_id)
    return jsonify({"current": row["state"], "transitions": transitions})


@api.route("/roadmaps/<roadmap_id>/state", methods=["POST"])
def transition_state(roadmap_id):
    data = request.get_json(force=True)
    state = data.get("state")
    if not state:
        return jsonify({"error": "state is required"}), 400
    tid = models.add_state_transition(
        g.db, roadmap_id, state,
        author=data.get("author"),
        previous_state=data.get("previous_state"),
    )
    from .sse import broadcast
    broadcast("state_changed", {"roadmap_id": roadmap_id, "state": state})
    return jsonify({"id": tid}), 201
