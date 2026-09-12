"""
Private Agent Internal API Router
Exposes /internal/v1 endpoints operating entirely inside the company perimeter.
"""
import json
import base64
from typing import Dict, Any, Optional
from packages.schemas.models import (
    Document, Meeting, SOP, Role, DepartmentScope, DataClassification, AuditEventType, generate_id, current_timestamp
)
from packages.shared.constants import ROLE_PERMISSIONS
from agent.security.validator import validate_file_upload
from agent.security.secret_detector import scan_and_redact_secrets
from agent.parsing.parsers import ParserFactory
from agent.chunking.chunker import default_chunker
from agent.embeddings.provider import embedding_provider
from agent.meetings.pipeline import meeting_pipeline
from agent.sop.engine import sop_engine
from agent.knowledge.conflicts import conflict_engine
from agent.workflows.generator import workflow_generator
from agent.rag.grounded_qa import grounded_qa_engine
from agent.onboarding.assistant import onboarding_assistant
from agent.config import config
import agent.storage.db as db

class PrivateAgentRouter:
    def handle_request(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        body: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        # Tenant Context Enforcement:
        # Tenant ID is securely extracted from headers/token, NEVER trusted from client body alone
        tenant_id = headers.get("X-Tenant-ID", config.TENANT_ID)
        user_role = Role(headers.get("X-User-Role", Role.EMPLOYEE.value))
        user_dept = headers.get("X-User-Department", "Operations")
        user_email = headers.get("X-User-Email", "yash@acme.corp")

        # --- Health & Privacy Status ---
        if path == "/internal/v1/health" and method == "GET":
            return {
                "status": 200,
                "body": {
                    "status": "ONLINE",
                    "agent_id": config.AGENT_ID,
                    "version": config.VERSION,
                    "storage_location": "CUSTOMER_INFRASTRUCTURE",
                    "egress_mode": config.DATA_EGRESS_MODE.value,
                    "vector_db": "LOCAL_PGVECTOR_EMBEDDINGS",
                    "transcription": "LOCAL_WHISPER",
                    "llm_engine": config.LLM_MODE,
                    "timestamp": current_timestamp()
                }
            }

        if path == "/internal/v1/privacy-status" and method == "GET":
            return {
                "status": 200,
                "body": {
                    "raw_company_data_sent_to_cloud": False,
                    "data_processing_location": "Customer Infrastructure",
                    "transcription": "Local / Customer Provider",
                    "llm": f"Local ({config.LLM_MODE})",
                    "embeddings": "Customer Infrastructure (Local pgvector)",
                    "vector_database": "Customer Infrastructure",
                    "document_storage": "Customer Infrastructure",
                    "meeting_recordings": "Customer Infrastructure",
                    "egress_policy": config.DATA_EGRESS_MODE.value,
                    "secret_redaction_active": True,
                    "prompt_injection_guard_active": True
                }
            }

        # --- Documents Ingestion ---
        if path == "/internal/v1/documents/upload" and method == "POST":
            # RBAC Check: Only Roles with upload_docs permission
            if "upload_docs" not in ROLE_PERMISSIONS.get(user_role, set()):
                return {"status": 403, "body": {"error": f"Permission denied: {user_role.value} cannot upload documents"}}

            body = body or {}
            filename = body.get("filename", "document.pdf")
            raw_content = body.get("content", "")
            classification = DataClassification(body.get("classification", DataClassification.INTERNAL.value))
            scope = DepartmentScope(body.get("scope", DepartmentScope.DEPARTMENT.value))
            department = body.get("department", user_dept)

            # Convert base64 or plain string to bytes
            if body.get("is_base64", False):
                try:
                    file_bytes = base64.b64decode(raw_content)
                except Exception:
                    return {"status": 400, "body": {"error": "Invalid base64 payload"}}
            else:
                file_bytes = raw_content.encode("utf-8")

            # 1. File Security & Path Traversal Validation
            valid, msg, ext = validate_file_upload(filename, file_bytes, config.MAX_FILE_SIZE)
            if not valid:
                return {"status": 400, "body": {"error": msg}}

            # 2. Parse Document
            parser = ParserFactory.get_parser(ext)
            sections = parser.parse(file_bytes, filename)

            # 3. Create Document Entity
            doc_id = generate_id("doc")
            doc = Document(
                document_id=doc_id,
                tenant_id=tenant_id,
                filename=filename,
                title=body.get("title", filename.rsplit(".", 1)[0].replace("_", " ").title()),
                mime_type=f"application/{ext}",
                version="v1",
                uploaded_by=user_email,
                checksum=generate_id("chksum"),
                classification=classification,
                department=department,
                scope=scope,
                status="PROCESSED",
                total_pages=len(sections),
                total_chunks=0,
                created_at=current_timestamp()
            )

            # 4. Chunk & Generate Embeddings
            all_chunks = []
            for s in sections:
                chunks = default_chunker.chunk_section(
                    document_id=doc_id,
                    version_id="v1",
                    tenant_id=tenant_id,
                    content=s.content,
                    section_title=s.title,
                    page_number=s.page_number,
                    classification=classification,
                    department_scope=scope,
                    department=department
                )
                for chk in chunks:
                    chk.embedding = embedding_provider.generate_embedding(chk.content)
                    all_chunks.append(chk)

            doc.total_chunks = len(all_chunks)
            db.store_document(tenant_id, doc)
            db.store_chunks(tenant_id, all_chunks)
            db.record_local_audit(tenant_id, user_email, AuditEventType.DOCUMENT_UPLOADED, doc_id, "SUCCESS")

            return {
                "status": 201,
                "body": {
                    "document": doc.to_dict(),
                    "total_chunks_indexed": len(all_chunks)
                }
            }

        if path == "/internal/v1/documents" and method == "GET":
            docs = db.list_documents(tenant_id, department=None if user_role in {Role.OWNER, Role.ADMIN} else user_dept)
            return {"status": 200, "body": {"documents": [d.to_dict() for d in docs]}}

        if path.startswith("/internal/v1/documents/") and method == "GET":
            doc_id = path.split("/")[-1]
            doc = db.get_document(tenant_id, doc_id)
            if not doc:
                return {"status": 404, "body": {"error": "Document not found"}}
            return {"status": 200, "body": {"document": doc.to_dict()}}

        if path.startswith("/internal/v1/documents/") and method == "DELETE":
            if "delete_docs" not in ROLE_PERMISSIONS.get(user_role, set()):
                return {"status": 403, "body": {"error": "Permission denied"}}
            doc_id = path.split("/")[-1]
            success = db.delete_document(tenant_id, doc_id)
            if not success:
                return {"status": 404, "body": {"error": "Document not found"}}
            db.record_local_audit(tenant_id, user_email, AuditEventType.DOCUMENT_DELETED, doc_id, "SUCCESS")
            return {"status": 200, "body": {"message": f"Document {doc_id} deleted along with derived chunks and embeddings."}}

        # --- Meetings Ingestion & Intelligence ---
        if path == "/internal/v1/meetings/upload" and method == "POST":
            if "create_meetings" not in ROLE_PERMISSIONS.get(user_role, set()):
                return {"status": 403, "body": {"error": "Permission denied to create meetings"}}

            body = body or {}
            title = body.get("title", "Operations Weekly Meeting")
            raw_audio = body.get("transcript_or_audio", "Manager: After KYC documents are verified, Finance Lead approves invoices.")
            audio_bytes = raw_audio.encode("utf-8")
            participants = body.get("participants", ["Manager", "Finance Lead", "Compliance Officer", "Sales Rep"])

            meeting = meeting_pipeline.process_meeting(
                tenant_id=tenant_id,
                title=title,
                audio_bytes=audio_bytes,
                filename=body.get("filename", "recording.mp3"),
                participants=participants
            )

            # Check for conflicts against existing SOPs
            detected_conflicts = conflict_engine.check_meeting_for_conflicts(tenant_id, meeting)

            db.record_local_audit(tenant_id, user_email, AuditEventType.MEETING_PROCESSED, meeting.meeting_id, "SUCCESS")
            return {
                "status": 201,
                "body": {
                    "meeting": meeting.to_dict(),
                    "conflicts_detected": [c.to_dict() for c in detected_conflicts]
                }
            }

        if path == "/internal/v1/meetings" and method == "GET":
            meetings = db.list_meetings(tenant_id)
            return {"status": 200, "body": {"meetings": [m.to_dict() for m in meetings]}}

        if path.startswith("/internal/v1/meetings/") and path.endswith("/generate-sop") and method == "POST":
            parts = path.strip("/").split("/")
            meeting_id = parts[3]
            meeting = db.get_meeting(tenant_id, meeting_id)
            if not meeting:
                return {"status": 404, "body": {"error": "Meeting not found"}}

            sop = sop_engine.generate_draft_sop_from_meeting(tenant_id, meeting)
            db.record_local_audit(tenant_id, user_email, AuditEventType.SOP_GENERATED, sop.sop_id, "SUCCESS")
            return {"status": 201, "body": {"sop": sop.to_dict(), "status": "DRAFT_REQUIRES_APPROVAL"}}

        if path.startswith("/internal/v1/meetings/") and method == "GET":
            meeting_id = path.split("/")[-1]
            meeting = db.get_meeting(tenant_id, meeting_id)
            if not meeting:
                return {"status": 404, "body": {"error": "Meeting not found"}}
            return {"status": 200, "body": {"meeting": meeting.to_dict()}}

        # --- SOP Management & Approvals ---
        if path == "/internal/v1/sops" and method == "GET":
            sops = db.list_sops(tenant_id)
            return {"status": 200, "body": {"sops": [s.to_dict() for s in sops]}}

        if path.startswith("/internal/v1/sops/") and path.endswith("/approve") and method == "POST":
            if "approve_sops" not in ROLE_PERMISSIONS.get(user_role, set()):
                return {"status": 403, "body": {"error": "Permission denied: Only Manager, Admin, or Knowledge Manager can approve SOPs."}}
            parts = path.strip("/").split("/")
            sop_id = parts[3]
            approved_sop = sop_engine.approve_sop(tenant_id, sop_id, approved_by=user_email)
            if not approved_sop:
                return {"status": 404, "body": {"error": "SOP not found"}}
            db.record_local_audit(tenant_id, user_email, AuditEventType.SOP_APPROVED, sop_id, "APPROVED")
            return {"status": 200, "body": {"sop": approved_sop.to_dict(), "message": "SOP approved successfully."}}

        if path.startswith("/internal/v1/sops/") and path.endswith("/workflow") and method == "GET":
            parts = path.strip("/").split("/")
            sop_id = parts[3]
            sop = db.get_sop(tenant_id, sop_id)
            if not sop:
                return {"status": 404, "body": {"error": "SOP not found"}}
            flow_graph = workflow_generator.generate_flow_graph(sop)
            return {"status": 200, "body": flow_graph}

        if path.startswith("/internal/v1/sops/") and path.endswith("/versions") and method == "GET":
            parts = path.strip("/").split("/")
            sop_id = parts[3]
            versions = db.list_sop_versions(tenant_id, sop_id)
            return {"status": 200, "body": {"versions": versions}}

        if path.startswith("/internal/v1/sops/") and path.endswith("/diff") and method == "GET":
            parts = path.strip("/").split("/")
            sop_id = parts[3]
            # query params or headers
            v_old = headers.get("X-Old-Version", "v1")
            v_new = headers.get("X-New-Version", "v2")
            diff_result = sop_engine.compute_version_diff(tenant_id, sop_id, v_old, v_new)
            return {"status": 200, "body": diff_result}

        if path.startswith("/internal/v1/sops/") and method == "GET":
            sop_id = path.split("/")[-1]
            sop = db.get_sop(tenant_id, sop_id)
            if not sop:
                return {"status": 404, "body": {"error": "SOP not found"}}
            return {"status": 200, "body": {"sop": sop.to_dict()}}

        # --- Conflicts & Knowledge Gaps ---
        if path == "/internal/v1/conflicts" and method == "GET":
            conflicts = db.list_conflicts(tenant_id)
            return {"status": 200, "body": {"conflicts": [c.to_dict() for c in conflicts]}}

        if path.startswith("/internal/v1/conflicts/") and path.endswith("/resolve") and method == "POST":
            parts = path.strip("/").split("/")
            conflict_id = parts[3]
            success = db.resolve_conflict(tenant_id, conflict_id)
            if not success:
                return {"status": 404, "body": {"error": "Conflict not found"}}
            return {"status": 200, "body": {"message": f"Conflict {conflict_id} resolved."}}

        if path == "/internal/v1/knowledge-gaps" and method == "GET":
            gaps = db.list_knowledge_gaps(tenant_id)
            return {"status": 200, "body": {"knowledge_gaps": [g.to_dict() for g in gaps]}}

        # --- Employee Onboarding ---
        if path == "/internal/v1/onboarding" and method == "GET":
            path_data = onboarding_assistant.get_onboarding_path(tenant_id, role=user_role.value, department=user_dept)
            return {"status": 200, "body": path_data}

        # --- Employee AI Q&A with Citations ---
        if path == "/internal/v1/questions" and method == "POST":
            body = body or {}
            question = body.get("question", "").strip()
            if not question:
                return {"status": 400, "body": {"error": "Question is required"}}
            conv_id = body.get("conversation_id")
            answer_result = grounded_qa_engine.answer_question(
                tenant_id=tenant_id,
                question=question,
                department=user_dept,
                user_role=user_role,
                conversation_id=conv_id
            )
            db.record_local_audit(tenant_id, user_email, AuditEventType.AI_QUESTION, question[:50], "SUCCESS")
            return {"status": 200, "body": answer_result}

        # --- Local Audit Trail ---
        if path == "/internal/v1/audit" and method == "GET":
            events = db.list_local_audit_events(tenant_id)
            return {"status": 200, "body": {"audit_events": events}}

        return {"status": 404, "body": {"error": f"Endpoint not found: {method} {path}"}}

private_agent_router = PrivateAgentRouter()
