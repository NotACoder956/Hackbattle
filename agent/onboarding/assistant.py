"""
Personalized Employee Onboarding Engine
Generates tailored "First Week" knowledge paths and process checklists
based on the employee's role, department, and security clearances.
"""
from typing import Dict, Any, List
from packages.schemas.models import SOP
import agent.storage.db as db

class OnboardingAssistant:
    def get_onboarding_path(self, tenant_id: str, role: str, department: str = "Operations") -> Dict[str, Any]:
        sops = db.list_sops(tenant_id)
        docs = db.list_documents(tenant_id, department=department)

        recommended_sops = []
        for s in sops:
            # Check if this SOP relates to user's department or role
            if department.lower() in s.owner.lower() or any(role.lower() in r.lower() for r in s.roles_involved):
                recommended_sops.append({
                    "sop_id": s.sop_id,
                    "title": s.title,
                    "version": s.version,
                    "owner": s.owner,
                    "completeness_score": s.completeness_score,
                    "summary": s.purpose
                })

        return {
            "department": department,
            "role": role,
            "welcome_message": f"Welcome to {department}! Here is your curated Day 1-7 onboarding curriculum.",
            "core_systems": [
                {"name": "Customer CRM", "purpose": "Lead pipeline and commercial records"},
                {"name": "Compliance Verification Portal", "purpose": "KYC review and identity validation"},
                {"name": "Billing ERP", "purpose": "Invoicing, purchase orders, and payment approvals"},
                {"name": "Internal Knowledge Base (SOPIQ)", "purpose": "Searchable company SOPs and meeting records"}
            ],
            "first_week_checklist": [
                {"day": 1, "task": "Review Company Code of Conduct & Information Security Guidelines", "completed": False},
                {"day": 2, "task": "Read 'New Client Onboarding SOP' (v2) and understand KYC handoff steps", "completed": False},
                {"day": 3, "task": "Request CRM & Compliance portal sandbox credentials", "completed": False},
                {"day": 4, "task": "Shadow senior team member through one complete invoice approval cycle", "completed": False},
                {"day": 5, "task": "Complete initial onboarding check-in with your Department Lead", "completed": False}
            ],
            "essential_sops": recommended_sops,
            "key_contacts": [
                {"role": "Department Lead", "contact": "sarah.manager@acme.corp", "scope": "Process escalations and team approvals"},
                {"role": "Finance Lead", "contact": "elena.finance@acme.corp", "scope": "Invoice sign-offs and billing inquiries"},
                {"role": "Knowledge Manager", "contact": "david.km@acme.corp", "scope": "SOP updates and documentation"}
            ],
            "common_mistakes_to_avoid": [
                "Never issue an initial invoice before KYC documents have received formal compliance clearance.",
                "Do not activate client accounts manually without confirmed accounting settlement."
            ]
        }

onboarding_assistant = OnboardingAssistant()
