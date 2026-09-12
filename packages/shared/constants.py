"""
SOPIQ Shared Constants and Enums
"""
from enum import Enum

class Role(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    KNOWLEDGE_MANAGER = "KNOWLEDGE_MANAGER"
    EMPLOYEE = "EMPLOYEE"
    VIEWER = "VIEWER"

class DepartmentScope(str, Enum):
    PUBLIC_COMPANY = "PUBLIC_COMPANY"
    DEPARTMENT = "DEPARTMENT"
    TEAM = "TEAM"
    ROLE = "ROLE"
    PRIVATE = "PRIVATE"

class DataClassification(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    HIGHLY_CONFIDENTIAL = "HIGHLY_CONFIDENTIAL"

class DataEgressMode(str, Enum):
    PRIVATE_ONLY = "PRIVATE_ONLY"
    SANITIZED = "SANITIZED"
    CUSTOMER_PROVIDER = "CUSTOMER_PROVIDER"
    REMOTE_PROVIDER = "REMOTE_PROVIDER"

class SOPStatus(str, Enum):
    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    ARCHIVED = "ARCHIVED"

class AgentStatus(str, Enum):
    ENROLLED = "ENROLLED"
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    REVOKED = "REVOKED"

class KnowledgeType(str, Enum):
    SOP = "SOP"
    POLICY = "POLICY"
    PROCESS = "PROCESS"
    WORKFLOW = "WORKFLOW"
    ROLE = "ROLE"
    SYSTEM = "SYSTEM"
    TERM = "TERM"
    FAQ = "FAQ"
    DECISION = "DECISION"
    MEETING_DECISION = "MEETING_DECISION"
    EXCEPTION = "EXCEPTION"
    DEPENDENCY = "DEPENDENCY"
    CHECKLIST = "CHECKLIST"

class AuditEventType(str, Enum):
    USER_LOGIN = "USER_LOGIN"
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    DOCUMENT_VIEWED = "DOCUMENT_VIEWED"
    DOCUMENT_DELETED = "DOCUMENT_DELETED"
    MEETING_CREATED = "MEETING_CREATED"
    MEETING_PROCESSED = "MEETING_PROCESSED"
    SOP_GENERATED = "SOP_GENERATED"
    SOP_EDITED = "SOP_EDITED"
    SOP_APPROVED = "SOP_APPROVED"
    SOP_REJECTED = "SOP_REJECTED"
    KNOWLEDGE_SEARCH = "KNOWLEDGE_SEARCH"
    AI_QUESTION = "AI_QUESTION"
    AI_EXTERNAL_CALL = "AI_EXTERNAL_CALL"
    PERMISSION_CHANGED = "PERMISSION_CHANGED"
    AGENT_REGISTERED = "AGENT_REGISTERED"
    AGENT_REVOKED = "AGENT_REVOKED"
    SECRET_DETECTED = "SECRET_DETECTED"
    EGRESS_BLOCKED = "EGRESS_BLOCKED"
    PROMPT_INJECTION_DEFLECTED = "PROMPT_INJECTION_DEFLECTED"

# Role hierarchy for permission checks
ROLE_PERMISSIONS = {
    Role.OWNER: {
        "manage_tenant", "manage_users", "manage_agents", "upload_docs", "delete_docs",
        "create_meetings", "approve_sops", "edit_sops", "ask_ai", "view_all", "view_audit"
    },
    Role.ADMIN: {
        "manage_users", "manage_agents", "upload_docs", "delete_docs", "create_meetings",
        "approve_sops", "edit_sops", "ask_ai", "view_all", "view_audit"
    },
    Role.MANAGER: {
        "create_meetings", "upload_docs", "approve_sops", "edit_sops", "ask_ai", "view_all"
    },
    Role.KNOWLEDGE_MANAGER: {
        "upload_docs", "delete_docs", "create_meetings", "edit_sops", "approve_sops", "ask_ai", "view_all"
    },
    Role.EMPLOYEE: {
        "ask_ai", "view_all", "view_onboarding"
    },
    Role.VIEWER: {
        "view_all"
    }
}
