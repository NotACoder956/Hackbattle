"""
SOPIQ Private Agent Main Entry Point
Runs locally inside the customer environment.
Hosts internal knowledge endpoints on /internal/v1/... and maintains outbound heartbeat with Control Plane.
"""
import os
import sys
import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# Ensure root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agent.config import config
from agent.api.routes import private_agent_router
import agent.storage.db as db

class PrivateAgentHTTPHandler(BaseHTTPRequestHandler):
    def _send_response(self, status: int, data: dict):
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
        headers = {k: v for k, v in self.headers.items()}
        res = private_agent_router.handle_request("GET", parsed.path, headers)
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
        res = private_agent_router.handle_request("POST", parsed.path, headers, body_dict)
        self._send_response(res["status"], res["body"])

    def do_DELETE(self):
        parsed = urlparse(self.path)
        headers = {k: v for k, v in self.headers.items()}
        res = private_agent_router.handle_request("DELETE", parsed.path, headers)
        self._send_response(res["status"], res["body"])

    def log_message(self, format, *args):
        # Clean logging without leaking company content
        sys.stderr.write(f"[SOPIQ Private Agent] {self.address_string()} - {args[0]} {args[1]}\n")

def run_agent_server(host: str = "0.0.0.0", port: int = 8001):
    db.init_agent_db()
    server = HTTPServer((host, port), PrivateAgentHTTPHandler)
    print(f"[SOPIQ Private Agent] Started successfully on http://{host}:{port}")
    print(f"[SOPIQ Private Agent] Egress Policy: {config.DATA_EGRESS_MODE.value}")
    print(f"[SOPIQ Private Agent] Zero company data is permitted to leave local perimeter.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()

if __name__ == "__main__":
    port = int(os.environ.get("AGENT_PORT", 8001))
    run_agent_server(port=port)
