"""
Knowledge Conflict Detection Engine
Detects contradictions between newly extracted statements from meetings/documents
and existing active SOPs, preventing silent overwrites and surfacing human review items.
"""
import re
from typing import List, Optional
from packages.schemas.models import (
    KnowledgeConflict, Meeting, SOP, generate_id, current_timestamp
)
import agent.storage.db as db

class KnowledgeConflictEngine:
    def check_meeting_for_conflicts(self, tenant_id: str, meeting: Meeting) -> List[KnowledgeConflict]:
        conflicts = []
        active_sops = db.list_sops(tenant_id)
        if not active_sops:
            return conflicts

        for proc in meeting.extracted_processes:
            stmt = proc.get("statement", "")
            lower_stmt = stmt.lower()

            for sop in active_sops:
                # Check for approval role changes
                if "approv" in lower_stmt:
                    for step in sop.steps:
                        desc_lower = step.description.lower()
                        role_lower = step.responsible_role.lower()

                        # Detect if a different role is assigned to approval
                        if "approv" in desc_lower and "now" in lower_stmt:
                            # Extract potential new role
                            conflict_detected = False
                            if "finance lead" in lower_stmt and "manager" in (desc_lower + role_lower):
                                conflict_detected = True
                            elif "compliance" in lower_stmt and "legal" in desc_lower:
                                conflict_detected = True

                            if conflict_detected:
                                cnf = KnowledgeConflict(
                                    conflict_id=generate_id("cnf"),
                                    tenant_id=tenant_id,
                                    sop_id=sop.sop_id,
                                    sop_title=sop.title,
                                    existing_statement=f"Step {step.step_number}: {step.description} (Responsible: {step.responsible_role})",
                                    new_source_type="MEETING",
                                    new_source_title=meeting.title,
                                    new_source_reference=f"Timestamp {proc.get('timestamp', '00:00')}",
                                    new_statement=stmt,
                                    recommended_action=f"Update SOP Step {step.step_number} to reflect: {stmt}",
                                    status="PENDING_REVIEW",
                                    created_at=current_timestamp()
                                )
                                db.store_conflict(tenant_id, cnf)
                                conflicts.append(cnf)

        return conflicts

conflict_engine = KnowledgeConflictEngine()
