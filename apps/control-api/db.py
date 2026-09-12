"""
Control Plane Database & State Management
Stores only tenant metadata, user accounts, agent enrollment/heartbeat, and jobs.
NEVER stores raw documents, transcripts, or company embeddings.
"""
import sqlite3
import os
import hashlib
import hmac
import secrets
import json
from typing import Optional, Dict, Any, List
from packages.schemas.models import (
    Tenant, User, Agent, AuditEvent, generate_id, current_timestamp
)
from packages.shared.constants import Role, AgentStatus, AuditEventType

DB_PATH = os.environ.get("CONTROL_PLANE_DB_PATH", os.path.join(os.path.dirname(__file__), "control_plane.db"))

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return f"{salt}:{key.hex()}"

def verify_password(password: str, hashed: str) -> bool:
    if not hashed or ":" not in hashed:
        return False
    salt, key_hex = hashed.split(":", 1)
    test_key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return hmac.compare_digest(test_key.hex(), key_hex)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tenants (
        tenant_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        domain TEXT NOT NULL,
        plan TEXT NOT NULL,
        active INTEGER NOT NULL,
        created_at TEXT NOT NULL
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        department TEXT NOT NULL,
        active INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agents (
        agent_id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        name TEXT NOT NULL,
        version TEXT NOT NULL,
        status TEXT NOT NULL,
        enrollment_token TEXT UNIQUE,
        auth_token TEXT UNIQUE,
        last_heartbeat TEXT,
        capabilities TEXT NOT NULL,
        created_at TEXT NOT NULL,
        revoked_at TEXT,
        FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        job_id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        agent_id TEXT NOT NULL,
        job_type TEXT NOT NULL,
        payload TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_events (
        event_id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        actor TEXT NOT NULL,
        event_type TEXT NOT NULL,
        resource TEXT NOT NULL,
        result TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        details TEXT NOT NULL
    )""")

    conn.commit()
    conn.close()

# Repository methods
def create_tenant(name: str, domain: str, plan: str = "ENTERPRISE") -> Tenant:
    tenant = Tenant(name=name, domain=domain, plan=plan)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tenants VALUES (?, ?, ?, ?, ?, ?)",
        (tenant.tenant_id, tenant.name, tenant.domain, tenant.plan, 1 if tenant.active else 0, tenant.created_at)
    )
    conn.commit()
    conn.close()
    return tenant

def get_tenant(tenant_id: str) -> Optional[Tenant]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tenants WHERE tenant_id = ?", (tenant_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return Tenant(
            tenant_id=row["tenant_id"],
            name=row["name"],
            domain=row["domain"],
            plan=row["plan"],
            active=bool(row["active"]),
            created_at=row["created_at"]
        )
    return None

def create_user(tenant_id: str, email: str, name: str, password: str, role: Role = Role.EMPLOYEE, department: str = "Operations") -> User:
    hashed = hash_password(password)
    user = User(tenant_id=tenant_id, email=email, name=name, password_hash=hashed, role=role, department=department)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (user.user_id, user.tenant_id, user.email, user.name, user.password_hash, user.role.value, user.department, 1, user.created_at)
    )
    conn.commit()
    conn.close()
    return user

def authenticate_user(email: str, password: str) -> Optional[User]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ? AND active = 1", (email,))
    row = cursor.fetchone()
    conn.close()
    if row and verify_password(password, row["password_hash"]):
        return User(
            user_id=row["user_id"],
            tenant_id=row["tenant_id"],
            email=row["email"],
            name=row["name"],
            password_hash=row["password_hash"],
            role=Role(row["role"]),
            department=row["department"],
            active=bool(row["active"]),
            created_at=row["created_at"]
        )
    return None

def create_agent_enrollment(tenant_id: str, name: str = "Private-Agent-01") -> Dict[str, str]:
    enrollment_token = f"sopq_enr_{secrets.token_urlsafe(24)}"
    agent_id = generate_id("agt")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO agents (agent_id, tenant_id, name, version, status, enrollment_token, capabilities, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (agent_id, tenant_id, name, "1.0.4", AgentStatus.ENROLLED.value, enrollment_token, json.dumps(["local_transcription", "document_parsing", "pgvector_search", "sop_generation"]), current_timestamp())
    )
    conn.commit()
    conn.close()
    return {"agent_id": agent_id, "enrollment_token": enrollment_token}

def register_agent(enrollment_token: str, version: str = "1.0.4", capabilities: List[str] = None) -> Optional[Dict[str, str]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM agents WHERE enrollment_token = ? AND status = ?", (enrollment_token, AgentStatus.ENROLLED.value))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    auth_token = f"sopq_agt_{secrets.token_urlsafe(32)}"
    caps = json.dumps(capabilities or ["local_transcription", "document_parsing", "pgvector_search", "sop_generation"])
    now = current_timestamp()
    cursor.execute(
        "UPDATE agents SET status = ?, auth_token = ?, version = ?, capabilities = ?, last_heartbeat = ? WHERE agent_id = ?",
        (AgentStatus.ONLINE.value, auth_token, version, caps, now, row["agent_id"])
    )
    conn.commit()
    conn.close()
    return {
        "agent_id": row["agent_id"],
        "tenant_id": row["tenant_id"],
        "auth_token": auth_token,
        "status": AgentStatus.ONLINE.value
    }

def record_heartbeat(agent_id: str, auth_token: str, version: str, capabilities: List[str]) -> Optional[Agent]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM agents WHERE agent_id = ? AND auth_token = ?", (agent_id, auth_token))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    if row["status"] == AgentStatus.REVOKED.value:
        conn.close()
        return None  # Revoked agents cannot heartbeat
    now = current_timestamp()
    cursor.execute(
        "UPDATE agents SET status = ?, last_heartbeat = ?, version = ? WHERE agent_id = ?",
        (AgentStatus.ONLINE.value, now, version, agent_id)
    )
    conn.commit()
    conn.close()
    return Agent(
        agent_id=row["agent_id"],
        tenant_id=row["tenant_id"],
        name=row["name"],
        version=version,
        status=AgentStatus.ONLINE,
        last_heartbeat=now,
        capabilities=json.loads(row["capabilities"]) if row["capabilities"] else []
    )

def revoke_agent(tenant_id: str, agent_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    now = current_timestamp()
    cursor.execute(
        "UPDATE agents SET status = ?, revoked_at = ?, auth_token = NULL WHERE agent_id = ? AND tenant_id = ?",
        (AgentStatus.REVOKED.value, now, agent_id, tenant_id)
    )
    affected = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return affected

def list_agents(tenant_id: str) -> List[Agent]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM agents WHERE tenant_id = ?", (tenant_id,))
    rows = cursor.fetchall()
    conn.close()
    agents = []
    for r in rows:
        agents.append(Agent(
            agent_id=r["agent_id"],
            tenant_id=r["tenant_id"],
            name=r["name"],
            version=r["version"],
            status=AgentStatus(r["status"]),
            last_heartbeat=r["last_heartbeat"] or "",
            capabilities=json.loads(r["capabilities"]) if r["capabilities"] else [],
            created_at=r["created_at"],
            revoked_at=r["revoked_at"]
        ))
    return agents

def record_audit(tenant_id: str, actor: str, event_type: AuditEventType, resource: str, result: str = "SUCCESS", details: Dict[str, Any] = None):
    conn = get_connection()
    cursor = conn.cursor()
    event_id = generate_id("aud")
    now = current_timestamp()
    cursor.execute(
        "INSERT INTO audit_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (event_id, tenant_id, actor, event_type.value, resource, result, generate_id("cor"), now, json.dumps(details or {}))
    )
    conn.commit()
    conn.close()

def list_audit_events(tenant_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_events WHERE tenant_id = ? ORDER BY timestamp DESC LIMIT ?", (tenant_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

init_db()
