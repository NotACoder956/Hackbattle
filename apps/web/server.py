"""
SOPIQ Web Server
Serves the responsive single-page enterprise web application on port 3000,
routing internal queries seamlessly to the Private Agent and Control Plane.
"""
import os
import sys
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

# Ensure root in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agent.api.routes import private_agent_router
from apps.control_api.main import control_plane_app

STATIC_DIR = os.path.join(current_dir, "static")

class SOPIQWebHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def _send_json(self, status: int, data: dict):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Tenant-ID, X-User-Role, X-User-Department, X-User-Email, X-Old-Version, X-New-Version")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Tenant-ID, X-User-Role, X-User-Department, X-User-Email, X-Old-Version, X-New-Version")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Route API queries
        if path.startswith("/internal/v1/"):
            headers = {k: v for k, v in self.headers.items()}
            res = private_agent_router.handle_request("GET", path, headers)
            self._send_json(res["status"], res["body"])
            return

        if path.startswith("/api/v1/"):
            headers = {k: v for k, v in self.headers.items()}
            res = control_plane_app.handle_request("GET", path, headers)
            self._send_json(res["status"], res["body"])
            return

        # Serve static assets / index
        if path == "/" or not os.path.exists(os.path.join(STATIC_DIR, path.lstrip("/"))):
            self.path = "/index.html"

        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len) if content_len > 0 else b"{}"

        try:
            body_dict = json.loads(post_body.decode("utf-8")) if post_body else {}
        except Exception:
            body_dict = {"raw": post_body.decode("utf-8", errors="replace")}

        headers = {k: v for k, v in self.headers.items()}

        if path.startswith("/internal/v1/"):
            res = private_agent_router.handle_request("POST", path, headers, body_dict)
            self._send_json(res["status"], res["body"])
            return

        if path.startswith("/api/v1/"):
            res = control_plane_app.handle_request("POST", path, headers, body_dict)
            self._send_json(res["status"], res["body"])
            return

        self._send_json(404, {"error": "Not found"})

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path
        headers = {k: v for k, v in self.headers.items()}

        if path.startswith("/internal/v1/"):
            res = private_agent_router.handle_request("DELETE", path, headers)
            self._send_json(res["status"], res["body"])
            return

        self._send_json(404, {"error": "Not found"})

    def log_message(self, format, *args):
        # Quiet clean logging
        pass

def run_web_server(host: str = "0.0.0.0", port: int = 3000):
    server = HTTPServer((host, port), SOPIQWebHandler)
    print(f"[SOPIQ Web] Interactive UI live on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()

if __name__ == "__main__":
    port = int(os.environ.get("WEB_PORT", 3000))
    run_web_server(port=port)
