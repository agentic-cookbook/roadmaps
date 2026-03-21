#!/usr/bin/env python3
"""Tiny HTTP server for the progress dashboard.

Serves static files and accepts PUT requests to write control.json.
Usage: python3 server.py <port> <directory>
"""

import http.server
import os
import sys


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_PUT(self):
        if os.path.basename(self.path.strip("/")) != "control.json":
            self.send_error(403, "Only control.json can be written")
            return
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        filepath = os.path.join(self.directory, "control.json")
        with open(filepath, "wb") as f:
            f.write(body)
        self.send_response(204)
        self.end_headers()

    def log_message(self, format, *args):
        pass  # suppress request logs


def main():
    port = int(sys.argv[1])
    directory = sys.argv[2]
    os.chdir(directory)
    handler = DashboardHandler
    handler.directory = directory
    server = http.server.HTTPServer(("127.0.0.1", port), handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
