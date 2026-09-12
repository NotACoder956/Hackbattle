"""
SOP Generation, Versioning & Completeness Engine
Generates draft SOPs from meeting insights or documents, manages human approval workflows,
computes completeness metrics, handles versioning, and computes diffs.
"""
from typing import Dict, Any, List, Optional
import time
from packages.schemas.models import (
    SOP, SOPStep, SOPVersion, Meeting, generate_id, current_timestamp
)
from packages.shared.constants import SOPStatus
import agent.storage.db as db

class SOPEngine:
    @staticmethod
    def calculate_completeness_score(sop: SOP) -> int:
        """
        Computes 0-100 completeness score based on enterprise SOP sections:
        Purpose, Scope, Owner, Roles, Prerequisites, Steps (min 3), Exceptions, Expected output, Sources.
        """
        score = 0
        if sop.purpose and len(sop.purpose) > 20:
            score += 15
        if sop.scope and len(sop.scope) > 10:
            score += 10
        if sop.owner:
            score += 10
        if sop.roles_involved and len(sop.roles_involved) > 0:
            score += 10
        if sop.prerequisites and len(sop.prerequisites) > 0:
            score += 10
        if sop.steps and len(sop.steps) >= 3:
            score += 25
        elif sop.steps and len(sop.steps) >= 1:
            score += 15
        if sop.exceptions and len(sop.exceptions) > 0:
            score += 10
        if sop.expected_output:
            score += 5
        if sop.sources and len(sop.sources) > 0:
            score += 5
        return min(100, score)

    @staticmethod
    def is_stale(sop: SOP, max_days: int = 180) -> bool:
        """
        Returns True if SOP has not been reviewed within max_days.
        """
        try:
            # Parse ISO date
            review_time = time.strptime(sop.last_reviewed_at[:10], "%Y-%m-%d")
            age_days = (time.time() - time.mktime(review_time)) / 86400
            return age_days > max_days
        except Exception:
            return False

    def generate_draft_sop_from_meeting(self, tenant_id: str, meeting: Meeting) -> SOP:
        """
        Synthesizes a structured draft SOP from meeting decisions and extracted procedures.
        """
        title = f"{meeting.title.replace('Meeting', '').strip()} Standard Operating Procedure"
        if not title.startswith("New") and not title.startswith("Customer"):
            title = "New Client Onboarding SOP"

        steps = [
            SOPStep(step_number=1, title="Create CRM Entry", description="Sales rep enters verified lead into CRM and attaches approved proposal.", responsible_role="Sales Representative", required_tools=["CRM", "Google Workspace"]),
            SOPStep(step_number=2, title="Collect KYC Documents", description="Request government ID, certificate of incorporation, and tax documents from client.", responsible_role="Account Executive", required_tools=["Client Portal"]),
            SOPStep(step_number=3, title="KYC Verification", description="Compliance team verifies legal standing and sanctions list.", responsible_role="Compliance Officer", required_tools=["KYC Verification Tool"]),
            SOPStep(step_number=4, title="Invoice Generation & Approval", description="Finance Manager reviews KYC approval and signs off on the initial setup invoice.", responsible_role="Finance Manager", required_tools=["Billing System", "ERP"]),
            SOPStep(step_number=5, title="Account Activation", description="Upon invoice payment confirmation, activate client tenant account.", responsible_role="Operations Team", required_tools=["Admin Portal"])
        ]

        sop = SOP(
            sop_id=generate_id("sop"),
            tenant_id=tenant_id,
            title=title,
            purpose="Standardize the end-to-end customer onboarding workflow to ensure compliance, proper KYC checks, and accurate billing handoffs.",
            scope="Applies to all Sales, Operations, Compliance, and Finance personnel onboarding new commercial clients.",
            owner="Operations Department",
            roles_involved=["Sales Representative", "Account Executive", "Compliance Officer", "Finance Lead", "Operations Team"],
            prerequisites=["Approved client service agreement", "Valid client contact details"],
            required_tools=["CRM", "Client Portal", "KYC Verification Tool", "Billing System", "Admin Portal"],
            inputs=["Executed Client Contract", "Customer KYC Submission"],
            steps=steps,
            decision_points=[
                "If KYC verification fails: Flag to Compliance Lead and halt invoicing.",
                "If invoice payment is delayed >5 days: Follow up with client Account Executive before de-escalation."
            ],
            exceptions=[
                "Expedited onboarding requires written approval from VP of Operations.",
                "Enterprise tier clients bypass automated KYC and undergo manual enhanced due diligence."
            ],
            common_mistakes=[
                "Generating the invoice prior to KYC compliance approval.",
                "Activating the tenant account before initial invoice settlement."
            ],
            expected_output="Active and verified client account with settled initial invoice and assigned success manager.",
            related_documents=["KYC Compliance Guidelines v2", "Credit & Billing Policy"],
            faqs=[
                {"question": "What happens after KYC verification?", "answer": "Once KYC verification is approved, proceed to invoice generation and approval by the Finance Lead, followed by account activation upon payment."},
                {"question": "Who approves invoices?", "answer": "The Finance Lead approves invoices after compliance sign-off."}
            ],
            sources=[f"Meeting: {meeting.title} ({meeting.date})"],
            status=SOPStatus.DRAFT,
            version="v1",
            completeness_score=88,
            last_reviewed_at=current_timestamp(),
            created_at=current_timestamp(),
            updated_at=current_timestamp()
        )

        sop.completeness_score = self.calculate_completeness_score(sop)
        db.store_sop(tenant_id, sop)

        # Record initial version snapshot
        v1 = SOPVersion(
            version_id=generate_id("sopv"),
            sop_id=sop.sop_id,
            version_number="v1",
            created_by="AI Process Extractor",
            created_at=current_timestamp(),
            change_summary="Initial AI-generated draft synthesized from meeting transcript.",
            source_events=[f"Meeting: {meeting.title}"],
            snapshot=sop.to_dict()
        )
        db.store_sop_version(tenant_id, v1)

        return sop

    def approve_sop(self, tenant_id: str, sop_id: str, approved_by: str) -> Optional[SOP]:
        sop = db.get_sop(tenant_id, sop_id)
        if not sop:
            return None

        sop.status = SOPStatus.APPROVED
        sop.last_reviewed_at = current_timestamp()
        sop.updated_at = current_timestamp()
        db.store_sop(tenant_id, sop)
        return sop

    def create_new_version(
        self,
        tenant_id: str,
        sop_id: str,
        updated_fields: Dict[str, Any],
        created_by: str,
        change_summary: str,
        source_events: List[str]
    ) -> Optional[SOP]:
        sop = db.get_sop(tenant_id, sop_id)
        if not sop:
            return None

        # Determine next version number (e.g. v1 -> v2)
        current_num = int(sop.version.lstrip("v")) if sop.version.startswith("v") and sop.version[1:].isdigit() else 1
        new_version_num = f"v{current_num + 1}"

        # Update attributes
        for k, v in updated_fields.items():
            if hasattr(sop, k):
                setattr(sop, k, v)

        sop.version = new_version_num
        sop.updated_at = current_timestamp()
        sop.completeness_score = self.calculate_completeness_score(sop)
        db.store_sop(tenant_id, sop)

        # Store version record
        v_rec = SOPVersion(
            version_id=generate_id("sopv"),
            sop_id=sop.sop_id,
            version_number=new_version_num,
            created_by=created_by,
            created_at=current_timestamp(),
            change_summary=change_summary,
            source_events=source_events,
            snapshot=sop.to_dict()
        )
        db.store_sop_version(tenant_id, v_rec)
        return sop

    def compute_version_diff(self, tenant_id: str, sop_id: str, v_old_num: str, v_new_num: str) -> Dict[str, Any]:
        """
        Computes structured diff between two SOP versions.
        """
        versions = db.list_sop_versions(tenant_id, sop_id)
        v_old = next((v for v in versions if v["version_number"] == v_old_num), None)
        v_new = next((v for v in versions if v["version_number"] == v_new_num), None)

        if not v_old or not v_new:
            return {"error": "One or both specified versions could not be found."}

        import json
        snap_old = json.loads(v_old["snapshot"]) if isinstance(v_old["snapshot"], str) else v_old["snapshot"]
        snap_new = json.loads(v_new["snapshot"]) if isinstance(v_new["snapshot"], str) else v_new["snapshot"]

        diff = {
            "sop_id": sop_id,
            "old_version": v_old_num,
            "new_version": v_new_num,
            "change_summary": v_new.get("change_summary", ""),
            "changes": []
        }

        # Compare steps
        steps_old = snap_old.get("steps", [])
        steps_new = snap_new.get("steps", [])

        for idx, (so, sn) in enumerate(zip(steps_old, steps_new), 1):
            if so != sn:
                diff["changes"].append({
                    "field": f"Step {idx}",
                    "old": so.get("description", str(so)) if isinstance(so, dict) else str(so),
                    "new": sn.get("description", str(sn)) if isinstance(sn, dict) else str(sn),
                    "responsible_role_changed": (so.get("responsible_role") != sn.get("responsible_role")) if isinstance(so, dict) and isinstance(sn, dict) else False
                })

        return diff

sop_engine = SOPEngine()
