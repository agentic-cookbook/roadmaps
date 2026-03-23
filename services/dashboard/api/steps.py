"""Step CRUD and lifecycle routes."""

from flask import g, jsonify, request

from . import api
from .. import models


@api.route("/roadmaps/<roadmap_id>/steps", methods=["GET"])
def list_steps(roadmap_id):
    return jsonify(models.list_steps(g.db, roadmap_id))


@api.route("/roadmaps/<roadmap_id>/steps", methods=["POST"])
def bulk_create_steps(roadmap_id):
    data = request.get_json(force=True)
    if not isinstance(data, list):
        return jsonify({"error": "expected a JSON array of steps"}), 400
    models.bulk_create_steps(g.db, roadmap_id, data)
    from .sse import broadcast
    broadcast("steps_updated", {"roadmap_id": roadmap_id})
    return jsonify({"ok": True}), 201


@api.route("/roadmaps/<roadmap_id>/steps/<int:number>", methods=["GET"])
def get_step(roadmap_id, number):
    step = models.get_step(g.db, roadmap_id, number)
    if not step:
        return jsonify({"error": "step not found"}), 404
    return jsonify(step)


@api.route("/roadmaps/<roadmap_id>/steps/<int:number>", methods=["PUT"])
def update_step(roadmap_id, number):
    data = request.get_json(force=True)
    models.update_step(g.db, roadmap_id, number, data)
    from .sse import broadcast
    broadcast("step_updated", {"roadmap_id": roadmap_id, "step_number": number, **data})
    return jsonify({"ok": True})


@api.route("/roadmaps/<roadmap_id>/steps/<int:number>/begin", methods=["POST"])
def begin_step(roadmap_id, number):
    models.begin_step(g.db, roadmap_id, number)
    from .sse import broadcast
    broadcast("step_updated", {"roadmap_id": roadmap_id, "step_number": number, "status": "in_progress"})
    return jsonify({"ok": True})


@api.route("/roadmaps/<roadmap_id>/steps/<int:number>/finish", methods=["POST"])
def finish_step(roadmap_id, number):
    models.finish_step(g.db, roadmap_id, number)
    from .sse import broadcast
    broadcast("step_updated", {"roadmap_id": roadmap_id, "step_number": number, "status": "complete"})
    return jsonify({"ok": True})


@api.route("/roadmaps/<roadmap_id>/steps/<int:number>/error", methods=["POST"])
def error_step(roadmap_id, number):
    data = request.get_json(force=True) if request.data else {}
    message = data.get("message", "Unknown error")
    models.error_step(g.db, roadmap_id, number, message)
    from .sse import broadcast
    broadcast("step_updated", {"roadmap_id": roadmap_id, "step_number": number, "status": "error"})
    return jsonify({"ok": True})
