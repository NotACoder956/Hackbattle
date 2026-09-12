"""
SOPIQ Hosted Control Plane API
Entry point for Cloud Control Plane operations:
Tenant registration, user management, agent lifecycle (enroll, heartbeat, revoke),
licensing, jobs dispatch, and privacy boundary enforcement.
"""
import json
import os
import sys
from typing import Dict, Any, Optional

# Ensure project root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from packages.schemas.models import (
    Tenant, User, Agent, AuditEvent, generate_id, current_timestamp
)
from packages.shared.constants import (
    Role, AgentStatus, AuditEventType, ROLE_PERMISSIONS
)
from apps.control_api.privacy_guard import inspect_payload_for_company_content
import apps.control_api.db as db

class ControlPlaneApp:
    """
    Modular HTTP Handler for Control Plane API.
    Can be run as an independent HTTP server or mounted with ASGI/FastAPI.
    """
    def __init__(self):
        db.init_db()

    def handle_request(self, method: str, path: str, headers: Dict[str, str], body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # 1. Zero-Knowledge Privacy Boundary Inspection
        if body and inspect_payload_for_company_content(body):
            return {
                "status": 422,
                "body": {
                    "error": "PRIVACY_VIOLATION_BLOCKED",
                    "message": "The central control plane strictly forbids receiving raw company documents, recordings, chunks, or company questions. Company data must stay inside the Private Agent."
                }
            }

        # 2. Authentication token check
        auth_header = headers.get("Authorization", headers.get("authorization", ""))
        current_user = None
        current_agent = None

        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            if token.startswith("sopq_usr_"):
                # Mock decode user session/token
                pass

        # 3. Route Dispatch
        # --- Health Check ---
        if path == "/api/v1/health" and method == "GET":
            return {
                "status": 200,
                "body": {
                    "status": "HEALTHY",
                    "plane": "RANKPILOT_SOPIQ_CONTROL_PLANE",
                    "privacy_mode": "ZERO_COMPANY_KNOWLEDGE_STORED",
                    "timestamp": current_timestamp()
                }
            }

        # --- Auth / Login ---
        if path == "/api/v1/auth/login" and method == "POST":
            body = body or {}
            email = body.get("email", "").strip()
            password = body.get("password", "").strip()
            user = db.authenticate_user(email, password)
            if not user:
                return {"status": 401, "body": {"error": "Invalid email or password"}}
            db.record_audit(user.tenant_id, user.email, AuditEventType.USER_LOGIN, "user_session", "SUCCESS")
            return {
                "status": 200,
                "body": {
                    "token": f"sopq_usr_{user.user_id}",
                    "user": user.to_dict()
                }
            }

        # --- Tenant Registration ---
        if path == "/api/v1/tenants" and method == "POST":
            body = body or {}
            name = body.get("name", "").strip()
            domain = body.get("domain", "").strip()
            admin_email = body.get("admin_email", "").strip()
            admin_password = body.get("admin_password", "").strip()
            if not name or not admin_email or not admin_password:
                return {"status": 400, "body": {"error": "Missing required fields"}}
            tenant = db.create_tenant(name, domain)
            admin_user = db.create_user(tenant.tenant_id, admin_email, "Administrator", admin_password, role=Role.OWNER)
            db.record_audit(tenant.tenant_id, admin_email, AuditEventType.PERMISSION_CHANGED, "tenant_init", "SUCCESS")
            return {
                "status": 201,
                "body": {
                    "tenant": tenant.to_dict(),
                    "admin": admin_user.to_dict()
                }
            }

        # --- Agent Enrollment (Generate Enrollment Token) ---
        if path == "/api/v1/agents/enroll" and method == "POST":
            body = body or {}
            tenant_id = body.get("tenant_id")
            if not tenant_id:
                return {"status": 400, "body": {"error": "tenant_id required"}}
            enrollment = db.create_agent_enrollment(tenant_id, body.get("name", "Private-Agent-01"))
            return {"status": 201, "body": enrollment}

        # --- Agent Registration (Called by Private Agent inside customer network) ---
        if path == "/api/v1/agents/register" and method == "POST":
            body = body or {}
            enrollment_token = body.get("enrollment_token")
            version = body.get("version", "1.0.4")
            capabilities = body.get("capabilities", [])
            if not enrollment_token:
                return {"status": 400, "body": {"error": "enrollment_token required"}}
            reg_result = db.register_agent(enrollment_token, version, capabilities)
            if not reg_result:
                return {"status": 403, "body": {"error": "Invalid or expired enrollment token"}}
            db.record_audit(reg_result["tenant_id"], reg_result["agent_id"], AuditEventType.AGENT_REGISTERED, "agent", "SUCCESS")
            return {"status": 200, "body": reg_result}

        # --- Agent Heartbeat (Periodic outbound status ping) ---
        if path == "/api/v1/agents/heartbeat" and method == "POST":
            body = body or {}
            agent_id = body.get("agent_id")
            auth_token = body.get("auth_token")
            version = body.get("version", "1.0.4")
            capabilities = body.get("capabilities", [])
            if not agent_id or not auth_token:
                return {"status": 401, "body": {"error": "agent_id and auth_token required"}}
            agent = db.record_heartbeat(agent_id, auth_token, version, capabilities)
            if not agent:
                return {"status": 403, "body": {"error": "Agent is unauthorized, invalid token or revoked"}}
            return {
                "status": 200,
                "body": {
                    "status": "ACK",
                    "agent_status": agent.status.value,
                    "server_time": current_timestamp(),
                    "pending_jobs": []
                }
            }

        # --- Agent Revocation ---
        if path.startswith("/api/v1/agents/") and path.endswith("/revoke") and method == "POST":
            parts = path.strip("/").split("/")
            agent_id = parts[3]
            body = body or {}
            tenant_id = body.get("tenant_id")
            if not tenant_id:
                return {"status": 400, "body": {"error": "tenant_id required"}}
            success = db.revoke_agent(tenant_id, agent_id)
            if not success:
                return {"status": 404, "body": {"error": "Agent not found or already revoked"}}
            db.record_audit(tenant_id, "admin", AuditEventType.AGENT_REVOKED, agent_id, "REVOKED")
            return {"status": 200, "body": {"message": f"Agent {agent_id} has been revoked successfully"}}

        # --- List Agents ---
        if path == "/api/v1/agents" and method == "GET":
            tenant_id = headers.get("X-Tenant-ID", "")
            if not tenant_id:
                return {"status": 400, "body": {"error": "X-Tenant-ID header required"}}
            agents = db.list_agents(tenant_id)
            return {"status": 200, "body": {"agents": [a.to_dict() for a in agents]}}

        # --- List Non-Sensitive Audit Logs ---
        if path == "/api/v1/audit" and method == "GET":
            tenant_id = headers.get("X-Tenant-ID", "")
            if not tenant_id:
                return {"status": 400, "body": {"error": "X-Tenant-ID header required"}}
            events = db.list_audit_events(tenant_id)
            return {"status": 200, "body": {"events": events}}

        return {"status": 404, "body": {"error": f"Endpoint not found: {method} {path}"}}

control_plane_app = ControlPlaneApp()
