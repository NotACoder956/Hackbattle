"""
Core Data Models and Schemas for SOPIQ
"""
import uuid
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from packages.shared.constants import (
    Role,
    DepartmentScope,
    DataClassification,
    SOPStatus,
    AgentStatus,
    AuditEventType,
)

def generate_id(prefix: str = "id") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

def current_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

@dataclass
class Tenant:
    tenant_id: str = field(default_factory=lambda: generate_id("ten"))
    name: str = ""
    domain: str = ""
    created_at: str = field(default_factory=current_timestamp)
    plan: str = "ENTERPRISE"
    active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class User:
    user_id: str = field(default_factory=lambda: generate_id("usr"))
    tenant_id: str = ""
    email: str = ""
    name: str = ""
    password_hash: str = ""
    role: Role = Role.EMPLOYEE
    department: str = "Operations"
    created_at: str = field(default_factory=current_timestamp)
    active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d.pop("password_hash", None)
        return d

@dataclass
class Agent:
    agent_id: str = field(default_factory=lambda: generate_id("agt"))
    tenant_id: str = ""
    name: str = "Private-Agent-01"
    version: str = "1.0.4"
    status: AgentStatus = AgentStatus.ENROLLED
    enrollment_token: str = ""
    auth_token: str = ""
    last_heartbeat: str = ""
    capabilities: List[str] = field(default_factory=lambda: [
        "local_transcription", "document_parsing", "pgvector_search",
        "sop_generation", "conflict_detection", "rag_qa"
    ])
    created_at: str = field(default_factory=current_timestamp)
    revoked_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d.pop("auth_token", None)
        return d

@dataclass
class DocumentChunk:
    chunk_id: str = field(default_factory=lambda: generate_id("chk"))
    document_id: str = ""
    tenant_id: str = ""
    version_id: str = "v1"
    content: str = ""
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    char_start: int = 0
    char_end: int = 0
    embedding: List[float] = field(default_factory=list)
    classification: DataClassification = DataClassification.INTERNAL
    department_scope: DepartmentScope = DepartmentScope.DEPARTMENT
    department: str = "Operations"
    created_at: str = field(default_factory=current_timestamp)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d.pop("embedding", None)  # Omit large vector payload in standard responses
        return d

@dataclass
class Document:
    document_id: str = field(default_factory=lambda: generate_id("doc"))
    tenant_id: str = ""
    filename: str = ""
    title: str = ""
    mime_type: str = "application/pdf"
    version: str = "v1"
    uploaded_by: str = ""
    checksum: str = ""
    classification: DataClassification = DataClassification.INTERNAL
    department: str = "Operations"
    scope: DepartmentScope = DepartmentScope.DEPARTMENT
    status: str = "PROCESSED"
    total_pages: int = 1
    total_chunks: int = 0
    created_at: str = field(default_factory=current_timestamp)
    updated_at: str = field(default_factory=current_timestamp)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class TranscriptSegment:
    segment_id: str = field(default_factory=lambda: generate_id("seg"))
    speaker: str = "Speaker"
    timestamp: str = "00:00:00"
    start_seconds: float = 0.0
    end_seconds: float = 0.0
    text: str = ""

@dataclass
class Meeting:
    meeting_id: str = field(default_factory=lambda: generate_id("mtg"))
    tenant_id: str = ""
    title: str = ""
    date: str = field(default_factory=current_timestamp)
    duration_seconds: int = 1800
    participants: List[str] = field(default_factory=list)
    recording_filename: Optional[str] = None
    summary: str = ""
    decisions: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    extracted_processes: List[Dict[str, Any]] = field(default_factory=list)
    segments: List[TranscriptSegment] = field(default_factory=list)
    status: str = "PROCESSED"
    created_at: str = field(default_factory=current_timestamp)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class SOPStep:
    step_number: int = 1
    title: str = ""
    description: str = ""
    responsible_role: str = ""
    required_tools: List[str] = field(default_factory=list)
    expected_output: str = ""

@dataclass
class SOPVersion:
    version_id: str = field(default_factory=lambda: generate_id("sopv"))
    sop_id: str = ""
    version_number: str = "v1"
    created_by: str = ""
    created_at: str = field(default_factory=current_timestamp)
    change_summary: str = ""
    source_events: List[str] = field(default_factory=list)
    snapshot: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SOP:
    sop_id: str = field(default_factory=lambda: generate_id("sop"))
    tenant_id: str = ""
    title: str = ""
    purpose: str = ""
    scope: str = ""
    owner: str = "Operations"
    roles_involved: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    required_tools: List[str] = field(default_factory=list)
    inputs: List[str] = field(default_factory=list)
    steps: List[SOPStep] = field(default_factory=list)
    decision_points: List[str] = field(default_factory=list)
    exceptions: List[str] = field(default_factory=list)
    common_mistakes: List[str] = field(default_factory=list)
    expected_output: str = ""
    related_documents: List[str] = field(default_factory=list)
    faqs: List[Dict[str, str]] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    status: SOPStatus = SOPStatus.DRAFT
    version: str = "v1"
    completeness_score: int = 85
    last_reviewed_at: str = field(default_factory=current_timestamp)
    created_at: str = field(default_factory=current_timestamp)
    updated_at: str = field(default_factory=current_timestamp)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class KnowledgeConflict:
    conflict_id: str = field(default_factory=lambda: generate_id("cnf"))
    tenant_id: str = ""
    sop_id: str = ""
    sop_title: str = ""
    existing_statement: str = ""
    new_source_type: str = "MEETING"  # MEETING or DOCUMENT
    new_source_title: str = ""
    new_source_reference: str = ""
    new_statement: str = ""
    recommended_action: str = "Review and update SOP step"
    status: str = "PENDING_REVIEW"  # PENDING_REVIEW, RESOLVED, DISMISSED
    created_at: str = field(default_factory=current_timestamp)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class KnowledgeGap:
    gap_id: str = field(default_factory=lambda: generate_id("gap"))
    tenant_id: str = ""
    question: str = ""
    frequency: int = 1
    department: str = "Operations"
    recommended_action: str = "Create new SOP"
    status: str = "OPEN"
    created_at: str = field(default_factory=current_timestamp)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Citation:
    citation_id: str = field(default_factory=lambda: generate_id("cit"))
    source_title: str = ""
    source_type: str = "SOP"  # SOP, MEETING, DOCUMENT
    source_id: str = ""
    reference: str = ""  # e.g., "Step 4", "14:21", "Page 12"
    snippet: str = ""
    confidence: float = 0.95

@dataclass
class Message:
    message_id: str = field(default_factory=lambda: generate_id("msg"))
    conversation_id: str = ""
    sender: str = "user"  # "user" or "assistant"
    content: str = ""
    citations: List[Citation] = field(default_factory=list)
    confidence: str = "High"  # High, Medium, Low, Insufficient Evidence
    feedback: Optional[str] = None  # "up", "down", None
    created_at: str = field(default_factory=current_timestamp)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Conversation:
    conversation_id: str = field(default_factory=lambda: generate_id("cnv"))
    tenant_id: str = ""
    user_id: str = ""
    title: str = "New Inquiry"
    created_at: str = field(default_factory=current_timestamp)
    updated_at: str = field(default_factory=current_timestamp)
    messages: List[Message] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class AuditEvent:
    event_id: str = field(default_factory=lambda: generate_id("aud"))
    tenant_id: str = ""
    actor: str = "system"
    event_type: AuditEventType = AuditEventType.USER_LOGIN
    resource: str = ""
    result: str = "SUCCESS"
    correlation_id: str = field(default_factory=lambda: generate_id("cor"))
    timestamp: str = field(default_factory=current_timestamp)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
