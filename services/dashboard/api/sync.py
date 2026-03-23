"""Bulk sync route — full state reconciliation."""

from flask import g, jsonify, request

from . import api
from .. import models


@api.route("/roadmaps/<roadmap_id>/sync", methods=["POST"])
def sync_roadmap(roadmap_id):
    data = request.get_json(force=True)
    models.sync_roadmap(g.db, roadmap_id, data)
    from .sse import broadcast
    broadcast("roadmap_synced", {"roadmap_id": roadmap_id})
    return jsonify({"ok": True})
