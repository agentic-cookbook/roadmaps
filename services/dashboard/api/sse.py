"""Server-Sent Events (SSE) stream routes."""

import json
import queue
import threading

from flask import Response, g, jsonify, request

from . import api
from .. import models

# In-process SSE client queues
_clients = []
_clients_lock = threading.Lock()


def broadcast(event_type, data):
    """Push an event to all connected SSE clients."""
    msg = {"type": event_type, "data": data}
    with _clients_lock:
        dead = []
        for q in _clients:
            try:
                q.put_nowait(msg)
            except queue.Full:
                dead.append(q)
        for q in dead:
            _clients.remove(q)


def _sse_stream(roadmap_id=None):
    """Generator that yields SSE-formatted events."""
    q = queue.Queue(maxsize=256)
    with _clients_lock:
        _clients.append(q)
    try:
        # Send initial keepalive
        yield ": connected\n\n"
        while True:
            try:
                msg = q.get(timeout=30)
            except queue.Empty:
                # Send keepalive comment every 30s
                yield ": keepalive\n\n"
                continue
            # Filter by roadmap_id if specified
            if roadmap_id and msg["data"].get("roadmap_id") != roadmap_id:
                continue
            yield f"event: {msg['type']}\ndata: {json.dumps(msg['data'])}\n\n"
    finally:
        with _clients_lock:
            if q in _clients:
                _clients.remove(q)


@api.route("/events/stream", methods=["GET"])
def global_sse_stream():
    return Response(_sse_stream(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@api.route("/roadmaps/<roadmap_id>/events/stream", methods=["GET"])
def roadmap_sse_stream(roadmap_id):
    return Response(_sse_stream(roadmap_id), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# Runtime events (the dashboard log)
@api.route("/roadmaps/<roadmap_id>/events", methods=["GET"])
def list_events(roadmap_id):
    return jsonify(models.list_runtime_events(g.db, roadmap_id))


@api.route("/roadmaps/<roadmap_id>/events", methods=["POST"])
def add_event(roadmap_id):
    data = request.get_json(force=True)
    message = data.get("message")
    if not message:
        return jsonify({"error": "message is required"}), 400
    models.add_runtime_event(g.db, roadmap_id, message)
    broadcast("event_logged", {"roadmap_id": roadmap_id, "message": message})
    return jsonify({"ok": True}), 201
