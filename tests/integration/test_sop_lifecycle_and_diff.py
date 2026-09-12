"""
Integration Test: SOP Lifecycle, Human Approval, Versioning & Diffing
"""
import unittest
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agent.sop.engine import sop_engine
from packages.schemas.models import Meeting, SOPStep, generate_id
from packages.shared.constants import SOPStatus
import agent.storage.db as db

class TestSOPLifecycle(unittest.TestCase):
    def setUp(self):
        self.tenant_id = "ten_sop_lifecycle_test"
        db.init_agent_db()

    def test_sop_draft_approval_and_version_diff(self):
        # 1. Simulate meeting
        meeting = Meeting(
            meeting_id=generate_id("mtg"),
            tenant_id=self.tenant_id,
            title="Customer Operations Planning",
            date="2026-09-12T10:00:00Z"
        )

        # 2. Generate Draft SOP
        sop = sop_engine.generate_draft_sop_from_meeting(self.tenant_id, meeting)
        self.assertEqual(sop.status, SOPStatus.DRAFT, "AI-generated SOP must initially be in DRAFT state!")
        self.assertGreaterEqual(sop.completeness_score, 80, "Completeness score should be at least 80/100")
        self.assertEqual(sop.version, "v1")

        # 3. Manager reviews and approves SOP
        approved = sop_engine.approve_sop(self.tenant_id, sop.sop_id, approved_by="manager@acme.corp")
        self.assertEqual(approved.status, SOPStatus.APPROVED)

        # 4. Process changes in next meeting -> update SOP to v2
        updated_steps = [s.__dict__ if hasattr(s, '__dict__') else s for s in approved.steps]
        # Modify Step 4: Change from Finance Manager to Finance Lead
        for s in updated_steps:
            if s.get("step_number") == 4:
                s["responsible_role"] = "Finance Lead"
                s["description"] = "Finance Lead directly approves setup invoices in ERP."

        sop_v2 = sop_engine.create_new_version(
            tenant_id=self.tenant_id,
            sop_id=approved.sop_id,
            updated_fields={"steps": [SOPStep(**s) for s in updated_steps]},
            created_by="manager@acme.corp",
            change_summary="Reassigned invoice approval authority from Finance Manager to Finance Lead.",
            source_events=["Operations Weekly Meeting - Sep 12"]
        )
        self.assertEqual(sop_v2.version, "v2")

        # 5. Compute Diff between v1 and v2
        diff = sop_engine.compute_version_diff(self.tenant_id, sop.sop_id, "v1", "v2")
        self.assertEqual(diff["old_version"], "v1")
        self.assertEqual(diff["new_version"], "v2")
        self.assertGreaterEqual(len(diff["changes"]), 1)
        self.assertTrue(diff["changes"][0]["responsible_role_changed"])

if __name__ == "__main__":
    unittest.main()
