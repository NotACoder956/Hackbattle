"""
Control Plane Server Runner
"""
import os
import sys
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from apps.control_api.main import control_plane_app
import apps.control_api.db as db

class ControlPlaneHTTPHandler(BaseHTTPRequestHandler):
    def _send_response(self, status: int, data: dict):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Tenant-ID")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Tenant-ID")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        headers = {k: v for k, v in self.headers.items()}
        res = control_plane_app.handle_request("GET", parsed.path, headers)
        self._send_response(res["status"], res["body"])

    def do_POST(self):
        parsed = urlparse(self.path)
        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len) if content_len > 0 else b"{}"
        try:
            body_dict = json.loads(post_body.decode("utf-8")) if post_body else {}
        except Exception:
            body_dict = {"raw": post_body.decode("utf-8", errors="replace")}

        headers = {k: v for k, v in self.headers.items()}
        res = control_plane_app.handle_request("POST", parsed.path, headers, body_dict)
        self._send_response(res["status"], res["body"])

    def log_message(self, format, *args):
        sys.stderr.write(f"[SOPIQ Control Plane] {self.address_string()} - {args[0]} {args[1]}\n")

def run_control_plane_server(host: str = "0.0.0.0", port: int = 8000):
    db.init_db()
    server = HTTPServer((host, port), ControlPlaneHTTPHandler)
    print(f"[SOPIQ Control Plane] Running on http://{host}:{port}")
    print("[SOPIQ Control Plane] Zero company knowledge policy enforced.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()

if __name__ == "__main__":
    port = int(os.environ.get("CONTROL_PLANE_PORT", 8000))
    run_control_plane_server(port=port)
