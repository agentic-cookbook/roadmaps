"""Roadmap CRUD routes."""

from flask import g, jsonify, request

from . import api
from .. import models


@api.route("/roadmaps", methods=["GET"])
def list_roadmaps():
    state = request.args.get("state")
    status = request.args.get("status")
    return jsonify(models.list_roadmaps(g.db, state=state, status=status))


@api.route("/roadmaps", methods=["POST"])
def create_roadmap():
    data = request.get_json(force=True)
    if not data.get("name"):
        return jsonify({"error": "name is required"}), 400
    rid = models.create_roadmap(g.db, data)
    return jsonify({"id": rid}), 201


@api.route("/roadmaps/<roadmap_id>", methods=["GET"])
def get_roadmap(roadmap_id):
    result = models.get_roadmap(g.db, roadmap_id)
    if not result:
        return jsonify({"error": "not found"}), 404
    return jsonify(result)


@api.route("/roadmaps/<roadmap_id>", methods=["PUT"])
def update_roadmap(roadmap_id):
    data = request.get_json(force=True)
    if not models.update_roadmap(g.db, roadmap_id, data):
        return jsonify({"error": "no valid fields to update"}), 400
    from .sse import broadcast
    broadcast("roadmap_updated", {"roadmap_id": roadmap_id, **data})
    return jsonify({"ok": True})


@api.route("/roadmaps/<roadmap_id>", methods=["DELETE"])
def delete_roadmap(roadmap_id):
    models.delete_roadmap(g.db, roadmap_id)
    from .sse import broadcast
    broadcast("roadmap_deleted", {"roadmap_id": roadmap_id})
    return jsonify({"ok": True})


@api.route("/roadmaps/<roadmap_id>/complete", methods=["POST"])
def complete_roadmap(roadmap_id):
    models.update_roadmap(g.db, roadmap_id, {"status": "complete", "state": "Complete"})
    from .sse import broadcast
    broadcast("roadmap_updated", {"roadmap_id": roadmap_id, "status": "complete", "state": "Complete"})
    return jsonify({"ok": True})


@api.route("/roadmaps/<roadmap_id>/error", methods=["POST"])
def error_roadmap(roadmap_id):
    data = request.get_json(force=True) if request.data else {}
    models.update_roadmap(g.db, roadmap_id, {"status": "error"})
    if data.get("message"):
        models.add_runtime_event(g.db, roadmap_id, f"Error: {data['message']}")
    from .sse import broadcast
    broadcast("roadmap_updated", {"roadmap_id": roadmap_id, "status": "error"})
    return jsonify({"ok": True})


@api.route("/roadmaps/<roadmap_id>/shutdown", methods=["POST"])
def shutdown_roadmap(roadmap_id):
    models.update_roadmap(g.db, roadmap_id, {"status": "idle"})
    from .sse import broadcast
    broadcast("roadmap_updated", {"roadmap_id": roadmap_id, "status": "idle"})
    return jsonify({"ok": True})
