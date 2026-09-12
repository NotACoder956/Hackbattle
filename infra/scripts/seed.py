"""
SOPIQ Production-Grade Seed Data Script
Initializes demo tenants, users, documents, meeting transcripts,
SOPs with version history, detected knowledge conflicts, and knowledge gaps.
"""
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from packages.schemas.models import (
    Tenant, User, Agent, Document, Meeting, SOP, SOPStep,
    KnowledgeConflict, KnowledgeGap, generate_id, current_timestamp
)
from packages.shared.constants import (
    Role, DepartmentScope, DataClassification, SOPStatus, AgentStatus
)
import apps.control_api.db as control_db
from agent.api.routes import private_agent_router
import agent.storage.db as agent_db
from agent.sop.engine import sop_engine

def seed_database():
    print("[SOPIQ Seed] Initializing Control Plane and Private Agent databases...")
    control_db.init_db()
    agent_db.init_agent_db()

    # 1. Create Acme Technologies Tenant in Control Plane
    acme_tenant = control_db.create_tenant(name="Acme Technologies", domain="acme.corp", plan="ENTERPRISE")
    tenant_id = acme_tenant.tenant_id
    print(f"[SOPIQ Seed] Created Tenant: Acme Technologies ({tenant_id})")

    # 2. Create Users
    users = [
        ("admin@acme.corp", "Administrator", "AcmePass123!", Role.ADMIN, "Executive"),
        ("sarah.manager@acme.corp", "Sarah Jenkins", "AcmePass123!", Role.MANAGER, "Operations"),
        ("david.km@acme.corp", "David Miller", "AcmePass123!", Role.KNOWLEDGE_MANAGER, "Operations"),
        ("yash@acme.corp", "Yash Aggarwal", "AcmePass123!", Role.EMPLOYEE, "Sales Operations"),
        ("elena.finance@acme.corp", "Elena Rostova", "AcmePass123!", Role.MANAGER, "Finance"),
    ]

    for email, name, pwd, role, dept in users:
        u = control_db.create_user(tenant_id, email, name, pwd, role=role, department=dept)
        print(f"[SOPIQ Seed] Created User: {name} ({email}) - {role.value}")

    # 3. Enroll & Register Private Agent
    enrollment = control_db.create_agent_enrollment(tenant_id, name="Acme-HQ-Agent-01")
    reg = control_db.register_agent(enrollment["enrollment_token"], version="1.0.4")
    agent_id = reg["agent_id"]
    agent_token = reg["auth_token"]
    print(f"[SOPIQ Seed] Enrolled & Registered Private Agent: {agent_id} (ONLINE)")

    # 4. Ingest Documents into Customer Private Agent
    docs = [
        {
            "filename": "Client_Onboarding_Guide.pdf",
            "title": "Client Onboarding Guide",
            "department": "Operations",
            "classification": DataClassification.INTERNAL.value,
            "content": """# CLIENT ONBOARDING GUIDE
Section 1: Workflow Overview
The customer onboarding journey transitions verified commercial prospects into active production clients.

Section 2: CRM & Documentation Setup
The assigned Sales Representative initiates a client profile in the enterprise CRM, uploading signed MSA contracts and contact matrices.

Section 3: KYC Verification Requirements
Before billing or provisioning, the Compliance Officer must execute mandatory identity verification. Ensure corporate certificate and tax IDs are verified.

Section 4: Invoicing Sign-off
After KYC verification is approved by compliance, the setup invoice is generated. The Finance Lead signs off on payment terms.

Section 5: Tenant Activation
Upon invoice settlement notification, Operations provisions account credentials and schedules kickoff."""
        },
        {
            "filename": "KYC_Compliance_Guidelines.pdf",
            "title": "KYC Compliance Guidelines",
            "department": "Operations",
            "classification": DataClassification.INTERNAL.value,
            "content": """# KYC COMPLIANCE GUIDELINES
Section 1: Mandatory Legal Verifications
All corporate accounts must provide Articles of Incorporation, proof of business address, and beneficiary disclosures.

Section 2: Escalations and Failure Handlers
If a prospective client fails KYC screening or appears on sanctions registries, immediately halt the onboarding process. Notify the Compliance Lead. Invoicing is strictly prohibited for unverified prospects."""
        },
        {
            "filename": "Invoice_Approval_Policy.docx",
            "title": "Invoice Approval Policy",
            "department": "Finance",
            "classification": DataClassification.INTERNAL.value,
            "content": """# INVOICE APPROVAL POLICY
Section 1: Hierarchy and Thresholds
All initial setup invoices must receive explicit review prior to ledger posting.

Section 2: Authorized Approvers
As established in recent operational updates, the Finance Lead holds direct signing authority for customer onboarding invoices."""
        }
    ]

    for d in docs:
        res = private_agent_router.handle_request(
            method="POST",
            path="/internal/v1/documents/upload",
            headers={"X-Tenant-ID": tenant_id, "X-User-Role": Role.ADMIN.value, "X-User-Email": "admin@acme.corp"},
            body=d
        )
        print(f"[SOPIQ Seed] Ingested document: {d['title']} ({res['body']['total_chunks_indexed']} chunks indexed)")

    # 5. Ingest Meeting Recording & Transcript
    meeting_transcript = """Manager: Good morning team. Today we are aligning on the New Customer Onboarding workflow.
Manager: Yash, you're handling CRM entries for new leads this quarter.
Yash: Confirmed. Once the client agreement is signed, I create the CRM profile and collect KYC paperwork.
Sarah: From now on, once KYC is submitted, compliance verifies it within 24 hours.
Elena: Regarding invoices: we decided that the Finance Lead now approves invoices instead of the Finance Manager. This avoids bottlenecks before weekend activations.
Sarah: Perfect. So the flow is CRM entry -> KYC collection -> Compliance verification -> Finance Lead invoice approval -> Operations account activation.
Manager: Action item for Sarah to approve the updated SOP in SOPIQ today."""

    m_res = private_agent_router.handle_request(
        method="POST",
        path="/internal/v1/meetings/upload",
        headers={"X-Tenant-ID": tenant_id, "X-User-Role": Role.MANAGER.value, "X-User-Email": "sarah.manager@acme.corp"},
        body={
            "title": "Operations Weekly Sync - Process Updates",
            "transcript_or_audio": meeting_transcript,
            "participants": ["Sarah Jenkins", "Elena Rostova", "Yash Aggarwal", "Manager"],
            "filename": "ops_weekly_sync_sep12.mp3"
        }
    )
    meeting_obj = m_res["body"]["meeting"]
    meeting_id = meeting_obj["meeting_id"]
    print(f"[SOPIQ Seed] Processed meeting: {meeting_obj['title']} ({len(meeting_obj['segments'])} segments)")

    # 6. Generate SOP from Meeting
    sop_res = private_agent_router.handle_request(
        method="POST",
        path=f"/internal/v1/meetings/{meeting_id}/generate-sop",
        headers={"X-Tenant-ID": tenant_id, "X-User-Role": Role.MANAGER.value, "X-User-Email": "sarah.manager@acme.corp"}
    )
    sop_data = sop_res["body"]["sop"]
    sop_id = sop_data["sop_id"]
    print(f"[SOPIQ Seed] AI generated draft SOP: '{sop_data['title']}' (Score: {sop_data['completeness_score']}/100)")

    # 7. Approve SOP v1
    app_res = private_agent_router.handle_request(
        method="POST",
        path=f"/internal/v1/sops/{sop_id}/approve",
        headers={"X-Tenant-ID": tenant_id, "X-User-Role": Role.MANAGER.value, "X-User-Email": "sarah.manager@acme.corp"}
    )
    print(f"[SOPIQ Seed] Manager approved SOP: {sop_id} (Status: APPROVED)")

    # 8. Create SOP v2 (Reflecting the Finance Lead change)
    sop = agent_db.get_sop(tenant_id, sop_id)
    updated_steps = [s.__dict__ if hasattr(s, '__dict__') else s for s in sop.steps]
    for s in updated_steps:
        if s.get("step_number") == 4:
            s["responsible_role"] = "Finance Lead"
            s["description"] = "Finance Lead reviews KYC approval and signs off on the initial setup invoice."

    sop_v2 = sop_engine.create_new_version(
        tenant_id=tenant_id,
        sop_id=sop_id,
        updated_fields={"steps": [SOPStep(**s) for s in updated_steps]},
        created_by="sarah.manager@acme.corp",
        change_summary="Reassigned Step 4 invoice signoff from Finance Manager to Finance Lead as decided in Operations Weekly Sync.",
        source_events=["Meeting: Operations Weekly Sync - Process Updates"]
    )
    print(f"[SOPIQ Seed] Created SOP Version 2: {sop_v2.version} with change diff history")

    # 9. Seed Knowledge Gaps (Repeated unanswered questions)
    agent_db.record_knowledge_gap(tenant_id, "How do I request a developer laptop?", "IT & Operations")
    for _ in range(13):
        agent_db.record_knowledge_gap(tenant_id, "How do I request a developer laptop?", "IT & Operations")

    agent_db.record_knowledge_gap(tenant_id, "Where do I submit international travel expense receipts?", "Finance")
    for _ in range(7):
        agent_db.record_knowledge_gap(tenant_id, "Where do I submit international travel expense receipts?", "Finance")

    print("[SOPIQ Seed] Seeded Knowledge Gaps: Developer Laptop (14 requests), Travel Expense Receipts (8 requests)")
    print("[SOPIQ Seed] Seeding complete! Acme Technologies is ready for the demo.")

if __name__ == "__main__":
    seed_database()
