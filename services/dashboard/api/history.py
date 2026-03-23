"""History event routes."""

from flask import g, jsonify, request

from . import api
from .. import models


@api.route("/roadmaps/<roadmap_id>/history", methods=["GET"])
def list_history(roadmap_id):
    return jsonify(models.list_history_events(g.db, roadmap_id))


@api.route("/roadmaps/<roadmap_id>/history", methods=["POST"])
def add_history(roadmap_id):
    data = request.get_json(force=True)
    event_type = data.get("event_type")
    if not event_type:
        return jsonify({"error": "event_type is required"}), 400
    eid = models.add_history_event(
        g.db, roadmap_id, event_type,
        step_number=data.get("step_number"),
        author=data.get("author"),
        details=data.get("details"),
    )
    from .sse import broadcast
    broadcast("history_event", {"roadmap_id": roadmap_id, "event_type": event_type})
    return jsonify({"id": eid}), 201
