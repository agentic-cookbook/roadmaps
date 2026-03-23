"""Flask application for the roadmap dashboard service."""

import os
from pathlib import Path

from flask import Flask, g, jsonify, send_from_directory

from . import db
from .api import init_app

DEFAULT_PORT = 5111


def create_app():
    app = Flask(__name__, static_folder="static")

    # Initialize database on first request
    @app.before_request
    def before_request():
        g.db = db.connect()

    @app.teardown_appcontext
    def close_db(exception):
        conn = g.pop("db", None)
        if conn is not None:
            conn.close()

    # Register API blueprints
    init_app(app)

    # Health check
    @app.route("/api/v1/health")
    def health():
        return jsonify({"status": "ok"})

    # Serve overview page at root
    @app.route("/")
    def overview():
        return send_from_directory(app.static_folder, "overview.html")

    # Serve roadmap detail page
    @app.route("/roadmap/<roadmap_id>")
    def roadmap_detail(roadmap_id):
        return send_from_directory(app.static_folder, "dashboard.html")

    return app


def main():
    """Run the dashboard service."""
    port = int(os.environ.get("DASHBOARD_PORT", DEFAULT_PORT))
    app = create_app()

    # Ensure database is initialized
    conn = db.connect()
    db.init_db(conn)
    conn.close()

    print(f"Dashboard service starting on http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, threaded=True)


if __name__ == "__main__":
    main()
