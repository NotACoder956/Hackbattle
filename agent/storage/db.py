"""
Private Agent Local Database & Storage Layer
Implements strict tenant isolation across all enterprise knowledge entities:
Documents, Chunks, Embeddings, Meetings, Transcripts, SOPs, Versions,
Conflicts, Gaps, Conversations, Citations, and Audit Events.
"""
import sqlite3
import os
import json
from typing import Optional, Dict, Any, List
from packages.schemas.models import (
    Document, DocumentChunk, Meeting, TranscriptSegment,
    SOP, SOPStep, SOPVersion, KnowledgeConflict, KnowledgeGap,
    Conversation, Message, Citation, AuditEvent,
    generate_id, current_timestamp
)
from packages.shared.constants import (
    Role, DepartmentScope, DataClassification, SOPStatus, AuditEventType
)
from agent.config import config

def get_connection():
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_agent_db():
    conn = get_connection()
    c = conn.cursor()

    # Documents
    c.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        document_id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        filename TEXT NOT NULL,
        title TEXT NOT NULL,
        mime_type TEXT NOT NULL,
        version TEXT NOT NULL,
        uploaded_by TEXT NOT NULL,
        checksum TEXT NOT NULL,
        classification TEXT NOT NULL,
        department TEXT NOT NULL,
        scope TEXT NOT NULL,
        status TEXT NOT NULL,
        total_pages INTEGER NOT NULL,
        total_chunks INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""")

    # Document Chunks (with serialized embedding vector)
    c.execute("""
    CREATE TABLE IF NOT EXISTS document_chunks (
        chunk_id TEXT PRIMARY KEY,
        document_id TEXT NOT NULL,
        tenant_id TEXT NOT NULL,
        version_id TEXT NOT NULL,
        content TEXT NOT NULL,
        page_number INTEGER,
        section_title TEXT,
        char_start INTEGER,
        char_end INTEGER,
        embedding TEXT,
        classification TEXT NOT NULL,
        department_scope TEXT NOT NULL,
        department TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (document_id) REFERENCES documents(document_id)
    )""")

    # Meetings
    c.execute("""
    CREATE TABLE IF NOT EXISTS meetings (
        meeting_id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        title TEXT NOT NULL,
        date TEXT NOT NULL,
        duration_seconds INTEGER NOT NULL,
        participants TEXT NOT NULL,
        recording_filename TEXT,
        summary TEXT NOT NULL,
        decisions TEXT NOT NULL,
        action_items TEXT NOT NULL,
        extracted_processes TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")

    # Transcript Segments
    c.execute("""
    CREATE TABLE IF NOT EXISTS transcript_segments (
        segment_id TEXT PRIMARY KEY,
        meeting_id TEXT NOT NULL,
        tenant_id TEXT NOT NULL,
        speaker TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        start_seconds REAL NOT NULL,
        end_seconds REAL NOT NULL,
        text TEXT NOT NULL,
        FOREIGN KEY (meeting_id) REFERENCES meetings(meeting_id)
    )""")

    # SOPs
    c.execute("""
    CREATE TABLE IF NOT EXISTS sops (
        sop_id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        title TEXT NOT NULL,
        purpose TEXT NOT NULL,
        scope TEXT NOT NULL,
        owner TEXT NOT NULL,
        roles_involved TEXT NOT NULL,
        prerequisites TEXT NOT NULL,
        required_tools TEXT NOT NULL,
        inputs TEXT NOT NULL,
        steps TEXT NOT NULL,
        decision_points TEXT NOT NULL,
        exceptions TEXT NOT NULL,
        common_mistakes TEXT NOT NULL,
        expected_output TEXT NOT NULL,
        related_documents TEXT NOT NULL,
        faqs TEXT NOT NULL,
        sources TEXT NOT NULL,
        status TEXT NOT NULL,
        version TEXT NOT NULL,
        completeness_score INTEGER NOT NULL,
        last_reviewed_at TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""")

    # SOP Versions
    c.execute("""
    CREATE TABLE IF NOT EXISTS sop_versions (
        version_id TEXT PRIMARY KEY,
        sop_id TEXT NOT NULL,
        tenant_id TEXT NOT NULL,
        version_number TEXT NOT NULL,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL,
        change_summary TEXT NOT NULL,
        source_events TEXT NOT NULL,
        snapshot TEXT NOT NULL,
        FOREIGN KEY (sop_id) REFERENCES sops(sop_id)
    )""")

    # Knowledge Conflicts
    c.execute("""
    CREATE TABLE IF NOT EXISTS knowledge_conflicts (
        conflict_id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        sop_id TEXT NOT NULL,
        sop_title TEXT NOT NULL,
        existing_statement TEXT NOT NULL,
        new_source_type TEXT NOT NULL,
        new_source_title TEXT NOT NULL,
        new_source_reference TEXT NOT NULL,
        new_statement TEXT NOT NULL,
        recommended_action TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")

    # Knowledge Gaps
    c.execute("""
    CREATE TABLE IF NOT EXISTS knowledge_gaps (
        gap_id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        question TEXT NOT NULL,
        frequency INTEGER NOT NULL,
        department TEXT NOT NULL,
        recommended_action TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")

    # Conversations
    c.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        conversation_id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        title TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""")

    # Messages & Citations
    c.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        message_id TEXT PRIMARY KEY,
        conversation_id TEXT NOT NULL,
        tenant_id TEXT NOT NULL,
        sender TEXT NOT NULL,
        content TEXT NOT NULL,
        citations TEXT NOT NULL,
        confidence TEXT NOT NULL,
        feedback TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
    )""")

    # Local Audit Events
    c.execute("""
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

# ----------------- REPOSITORY METHODS (ALL STRICTLY TENANT-SCOPED) -----------------

def store_document(tenant_id: str, doc: Document) -> None:
    doc.tenant_id = tenant_id
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT OR REPLACE INTO documents VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        doc.document_id, doc.tenant_id, doc.filename, doc.title, doc.mime_type, doc.version,
        doc.uploaded_by, doc.checksum, doc.classification.value, doc.department,
        doc.scope.value, doc.status, doc.total_pages, doc.total_chunks, doc.created_at, doc.updated_at
    ))
    conn.commit()
    conn.close()

def get_document(tenant_id: str, document_id: str) -> Optional[Document]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM documents WHERE tenant_id = ? AND document_id = ?", (tenant_id, document_id))
    r = c.fetchone()
    conn.close()
    if not r:
        return None
    return Document(
        document_id=r["document_id"], tenant_id=r["tenant_id"], filename=r["filename"],
        title=r["title"], mime_type=r["mime_type"], version=r["version"],
        uploaded_by=r["uploaded_by"], checksum=r["checksum"],
        classification=DataClassification(r["classification"]),
        department=r["department"], scope=DepartmentScope(r["scope"]),
        status=r["status"], total_pages=r["total_pages"], total_chunks=r["total_chunks"],
        created_at=r["created_at"], updated_at=r["updated_at"]
    )

def list_documents(tenant_id: str, department: Optional[str] = None) -> List[Document]:
    conn = get_connection()
    c = conn.cursor()
    if department:
        c.execute("SELECT * FROM documents WHERE tenant_id = ? AND (department = ? OR scope = 'PUBLIC_COMPANY') ORDER BY created_at DESC", (tenant_id, department))
    else:
        c.execute("SELECT * FROM documents WHERE tenant_id = ? ORDER BY created_at DESC", (tenant_id,))
    rows = c.fetchall()
    conn.close()
    docs = []
    for r in rows:
        docs.append(Document(
            document_id=r["document_id"], tenant_id=r["tenant_id"], filename=r["filename"],
            title=r["title"], mime_type=r["mime_type"], version=r["version"],
            uploaded_by=r["uploaded_by"], checksum=r["checksum"],
            classification=DataClassification(r["classification"]),
            department=r["department"], scope=DepartmentScope(r["scope"]),
            status=r["status"], total_pages=r["total_pages"], total_chunks=r["total_chunks"],
            created_at=r["created_at"], updated_at=r["updated_at"]
        ))
    return docs

def delete_document(tenant_id: str, document_id: str) -> bool:
    conn = get_connection()
    c = conn.cursor()
    # Delete chunks first (foreign key cascade cleanup)
    c.execute("DELETE FROM document_chunks WHERE tenant_id = ? AND document_id = ?", (tenant_id, document_id))
    c.execute("DELETE FROM documents WHERE tenant_id = ? AND document_id = ?", (tenant_id, document_id))
    affected = c.rowcount > 0
    conn.commit()
    conn.close()
    return affected

def store_chunks(tenant_id: str, chunks: List[DocumentChunk]) -> None:
    conn = get_connection()
    c = conn.cursor()
    for chk in chunks:
        chk.tenant_id = tenant_id
        c.execute("""
        INSERT OR REPLACE INTO document_chunks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            chk.chunk_id, chk.document_id, chk.tenant_id, chk.version_id, chk.content,
            chk.page_number, chk.section_title, chk.char_start, chk.char_end,
            json.dumps(chk.embedding), chk.classification.value, chk.department_scope.value,
            chk.department, chk.created_at
        ))
    conn.commit()
    conn.close()

def get_chunks_for_retrieval(tenant_id: str, department: str = "Operations", user_role: Role = Role.EMPLOYEE) -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    # Strict RBAC & Department Scope Filtering
    # Admin / Owner can access all department chunks; Employees restricted to their department or PUBLIC_COMPANY
    if user_role in {Role.OWNER, Role.ADMIN}:
        c.execute("SELECT * FROM document_chunks WHERE tenant_id = ?", (tenant_id,))
    else:
        c.execute("""
        SELECT * FROM document_chunks
        WHERE tenant_id = ?
        AND (department_scope = 'PUBLIC_COMPANY' OR department = ?)
        AND classification != 'HIGHLY_CONFIDENTIAL'
        """, (tenant_id, department))
    rows = c.fetchall()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "chunk_id": r["chunk_id"],
            "document_id": r["document_id"],
            "content": r["content"],
            "page_number": r["page_number"],
            "section_title": r["section_title"],
            "embedding": json.loads(r["embedding"]) if r["embedding"] else [],
            "classification": r["classification"],
            "department": r["department"]
        })
    return results

def store_meeting(tenant_id: str, meeting: Meeting) -> None:
    meeting.tenant_id = tenant_id
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT OR REPLACE INTO meetings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        meeting.meeting_id, meeting.tenant_id, meeting.title, meeting.date,
        meeting.duration_seconds, json.dumps(meeting.participants), meeting.recording_filename,
        meeting.summary, json.dumps(meeting.decisions), json.dumps(meeting.action_items),
        json.dumps(meeting.extracted_processes), meeting.status, meeting.created_at
    ))
    # Store segments
    for seg in meeting.segments:
        c.execute("""
        INSERT OR REPLACE INTO transcript_segments VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            seg.segment_id, meeting.meeting_id, tenant_id, seg.speaker,
            seg.timestamp, seg.start_seconds, seg.end_seconds, seg.text
        ))
    conn.commit()
    conn.close()

def get_meeting(tenant_id: str, meeting_id: str) -> Optional[Meeting]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM meetings WHERE tenant_id = ? AND meeting_id = ?", (tenant_id, meeting_id))
    r = c.fetchone()
    if not r:
        conn.close()
        return None
    c.execute("SELECT * FROM transcript_segments WHERE tenant_id = ? AND meeting_id = ? ORDER BY start_seconds ASC", (tenant_id, meeting_id))
    seg_rows = c.fetchall()
    conn.close()

    segments = [
        TranscriptSegment(
            segment_id=sr["segment_id"], speaker=sr["speaker"],
            timestamp=sr["timestamp"], start_seconds=sr["start_seconds"],
            end_seconds=sr["end_seconds"], text=sr["text"]
        ) for sr in seg_rows
    ]

    return Meeting(
        meeting_id=r["meeting_id"], tenant_id=r["tenant_id"], title=r["title"],
        date=r["date"], duration_seconds=r["duration_seconds"],
        participants=json.loads(r["participants"]) if r["participants"] else [],
        recording_filename=r["recording_filename"], summary=r["summary"],
        decisions=json.loads(r["decisions"]) if r["decisions"] else [],
        action_items=json.loads(r["action_items"]) if r["action_items"] else [],
        extracted_processes=json.loads(r["extracted_processes"]) if r["extracted_processes"] else [],
        segments=segments, status=r["status"], created_at=r["created_at"]
    )

def list_meetings(tenant_id: str) -> List[Meeting]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM meetings WHERE tenant_id = ? ORDER BY created_at DESC", (tenant_id,))
    rows = c.fetchall()
    conn.close()
    meetings = []
    for r in rows:
        meetings.append(Meeting(
            meeting_id=r["meeting_id"], tenant_id=r["tenant_id"], title=r["title"],
            date=r["date"], duration_seconds=r["duration_seconds"],
            participants=json.loads(r["participants"]) if r["participants"] else [],
            recording_filename=r["recording_filename"], summary=r["summary"],
            decisions=json.loads(r["decisions"]) if r["decisions"] else [],
            action_items=json.loads(r["action_items"]) if r["action_items"] else [],
            extracted_processes=json.loads(r["extracted_processes"]) if r["extracted_processes"] else [],
            status=r["status"], created_at=r["created_at"]
        ))
    return meetings

def store_sop(tenant_id: str, sop: SOP) -> None:
    sop.tenant_id = tenant_id
    conn = get_connection()
    c = conn.cursor()
    steps_json = json.dumps([s.__dict__ if hasattr(s, '__dict__') else s for s in sop.steps])
    c.execute("""
    INSERT OR REPLACE INTO sops VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        sop.sop_id, sop.tenant_id, sop.title, sop.purpose, sop.scope, sop.owner,
        json.dumps(sop.roles_involved), json.dumps(sop.prerequisites), json.dumps(sop.required_tools),
        json.dumps(sop.inputs), steps_json, json.dumps(sop.decision_points),
        json.dumps(sop.exceptions), json.dumps(sop.common_mistakes), sop.expected_output,
        json.dumps(sop.related_documents), json.dumps(sop.faqs), json.dumps(sop.sources),
        sop.status.value if hasattr(sop.status, 'value') else sop.status,
        sop.version, sop.completeness_score, sop.last_reviewed_at, sop.created_at, sop.updated_at
    ))
    conn.commit()
    conn.close()

def get_sop(tenant_id: str, sop_id: str) -> Optional[SOP]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM sops WHERE tenant_id = ? AND sop_id = ?", (tenant_id, sop_id))
    r = c.fetchone()
    conn.close()
    if not r:
        return None
    raw_steps = json.loads(r["steps"]) if r["steps"] else []
    steps = [SOPStep(**s) if isinstance(s, dict) else s for s in raw_steps]

    return SOP(
        sop_id=r["sop_id"], tenant_id=r["tenant_id"], title=r["title"],
        purpose=r["purpose"], scope=r["scope"], owner=r["owner"],
        roles_involved=json.loads(r["roles_involved"]) if r["roles_involved"] else [],
        prerequisites=json.loads(r["prerequisites"]) if r["prerequisites"] else [],
        required_tools=json.loads(r["required_tools"]) if r["required_tools"] else [],
        inputs=json.loads(r["inputs"]) if r["inputs"] else [],
        steps=steps, decision_points=json.loads(r["decision_points"]) if r["decision_points"] else [],
        exceptions=json.loads(r["exceptions"]) if r["exceptions"] else [],
        common_mistakes=json.loads(r["common_mistakes"]) if r["common_mistakes"] else [],
        expected_output=r["expected_output"],
        related_documents=json.loads(r["related_documents"]) if r["related_documents"] else [],
        faqs=json.loads(r["faqs"]) if r["faqs"] else [],
        sources=json.loads(r["sources"]) if r["sources"] else [],
        status=SOPStatus(r["status"]), version=r["version"],
        completeness_score=r["completeness_score"], last_reviewed_at=r["last_reviewed_at"],
        created_at=r["created_at"], updated_at=r["updated_at"]
    )

def list_sops(tenant_id: str) -> List[SOP]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM sops WHERE tenant_id = ? ORDER BY updated_at DESC", (tenant_id,))
    rows = c.fetchall()
    conn.close()
    sops = []
    for r in rows:
        raw_steps = json.loads(r["steps"]) if r["steps"] else []
        steps = [SOPStep(**s) if isinstance(s, dict) else s for s in raw_steps]
        sops.append(SOP(
            sop_id=r["sop_id"], tenant_id=r["tenant_id"], title=r["title"],
            purpose=r["purpose"], scope=r["scope"], owner=r["owner"],
            roles_involved=json.loads(r["roles_involved"]) if r["roles_involved"] else [],
            prerequisites=json.loads(r["prerequisites"]) if r["prerequisites"] else [],
            required_tools=json.loads(r["required_tools"]) if r["required_tools"] else [],
            inputs=json.loads(r["inputs"]) if r["inputs"] else [],
            steps=steps, decision_points=json.loads(r["decision_points"]) if r["decision_points"] else [],
            exceptions=json.loads(r["exceptions"]) if r["exceptions"] else [],
            common_mistakes=json.loads(r["common_mistakes"]) if r["common_mistakes"] else [],
            expected_output=r["expected_output"],
            related_documents=json.loads(r["related_documents"]) if r["related_documents"] else [],
            faqs=json.loads(r["faqs"]) if r["faqs"] else [],
            sources=json.loads(r["sources"]) if r["sources"] else [],
            status=SOPStatus(r["status"]), version=r["version"],
            completeness_score=r["completeness_score"], last_reviewed_at=r["last_reviewed_at"],
            created_at=r["created_at"], updated_at=r["updated_at"]
        ))
    return sops

def store_sop_version(tenant_id: str, version: SOPVersion) -> None:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT OR REPLACE INTO sop_versions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        version.version_id, version.sop_id, tenant_id, version.version_number,
        version.created_by, version.created_at, version.change_summary,
        json.dumps(version.source_events), json.dumps(version.snapshot)
    ))
    conn.commit()
    conn.close()

def list_sop_versions(tenant_id: str, sop_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM sop_versions WHERE tenant_id = ? AND sop_id = ? ORDER BY created_at DESC", (tenant_id, sop_id))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def store_conflict(tenant_id: str, conflict: KnowledgeConflict) -> None:
    conflict.tenant_id = tenant_id
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT OR REPLACE INTO knowledge_conflicts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        conflict.conflict_id, conflict.tenant_id, conflict.sop_id, conflict.sop_title,
        conflict.existing_statement, conflict.new_source_type, conflict.new_source_title,
        conflict.new_source_reference, conflict.new_statement, conflict.recommended_action,
        conflict.status, conflict.created_at
    ))
    conn.commit()
    conn.close()

def list_conflicts(tenant_id: str, status: Optional[str] = None) -> List[KnowledgeConflict]:
    conn = get_connection()
    c = conn.cursor()
    if status:
        c.execute("SELECT * FROM knowledge_conflicts WHERE tenant_id = ? AND status = ? ORDER BY created_at DESC", (tenant_id, status))
    else:
        c.execute("SELECT * FROM knowledge_conflicts WHERE tenant_id = ? ORDER BY created_at DESC", (tenant_id,))
    rows = c.fetchall()
    conn.close()
    conflicts = []
    for r in rows:
        conflicts.append(KnowledgeConflict(
            conflict_id=r["conflict_id"], tenant_id=r["tenant_id"], sop_id=r["sop_id"],
            sop_title=r["sop_title"], existing_statement=r["existing_statement"],
            new_source_type=r["new_source_type"], new_source_title=r["new_source_title"],
            new_source_reference=r["new_source_reference"], new_statement=r["new_statement"],
            recommended_action=r["recommended_action"], status=r["status"], created_at=r["created_at"]
        ))
    return conflicts

def resolve_conflict(tenant_id: str, conflict_id: str, status: str = "RESOLVED") -> bool:
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE knowledge_conflicts SET status = ? WHERE tenant_id = ? AND conflict_id = ?", (status, tenant_id, conflict_id))
    affected = c.rowcount > 0
    conn.commit()
    conn.close()
    return affected

def record_knowledge_gap(tenant_id: str, question: str, department: str = "Operations") -> None:
    conn = get_connection()
    c = conn.cursor()
    # Check if question already exists for this tenant
    c.execute("SELECT * FROM knowledge_gaps WHERE tenant_id = ? AND question = ?", (tenant_id, question))
    r = c.fetchone()
    if r:
        c.execute("UPDATE knowledge_gaps SET frequency = frequency + 1 WHERE gap_id = ?", (r["gap_id"],))
    else:
        gap_id = generate_id("gap")
        c.execute("""
        INSERT INTO knowledge_gaps VALUES (?, ?, ?, 1, ?, 'Create new SOP or knowledge article', 'OPEN', ?)
        """, (gap_id, tenant_id, question, department, current_timestamp()))
    conn.commit()
    conn.close()

def list_knowledge_gaps(tenant_id: str) -> List[KnowledgeGap]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM knowledge_gaps WHERE tenant_id = ? ORDER BY frequency DESC, created_at DESC", (tenant_id,))
    rows = c.fetchall()
    conn.close()
    gaps = []
    for r in rows:
        gaps.append(KnowledgeGap(
            gap_id=r["gap_id"], tenant_id=r["tenant_id"], question=r["question"],
            frequency=r["frequency"], department=r["department"],
            recommended_action=r["recommended_action"], status=r["status"],
            created_at=r["created_at"]
        ))
    return gaps

def store_message(tenant_id: str, conversation_id: str, message: Message) -> None:
    conn = get_connection()
    c = conn.cursor()
    # Ensure conversation exists
    c.execute("INSERT OR IGNORE INTO conversations VALUES (?, ?, 'user', 'Inquiry', ?, ?)", (conversation_id, tenant_id, message.created_at, message.created_at))
    citations_json = json.dumps([cit.__dict__ if hasattr(cit, '__dict__') else cit for cit in message.citations])
    c.execute("""
    INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        message.message_id, conversation_id, tenant_id, message.sender, message.content,
        citations_json, message.confidence, message.feedback, message.created_at
    ))
    conn.commit()
    conn.close()

def record_local_audit(tenant_id: str, actor: str, event_type: AuditEventType, resource: str, result: str = "SUCCESS", details: Dict[str, Any] = None):
    conn = get_connection()
    c = conn.cursor()
    event_id = generate_id("aud")
    c.execute("""
    INSERT INTO audit_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event_id, tenant_id, actor, event_type.value, resource, result,
        generate_id("cor"), current_timestamp(), json.dumps(details or {})
    ))
    conn.commit()
    conn.close()

def list_local_audit_events(tenant_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM audit_events WHERE tenant_id = ? ORDER BY timestamp DESC LIMIT ?", (tenant_id, limit))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

init_agent_db()
