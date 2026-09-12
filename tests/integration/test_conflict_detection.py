"""
Integration Test: Knowledge Conflict Detection Engine
Detects contradiction between newly spoken meeting statement and existing active SOP.
"""
import unittest
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agent.knowledge.conflicts import conflict_engine
from agent.sop.engine import sop_engine
from packages.schemas.models import SOP, SOPStep, Meeting, generate_id
from packages.shared.constants import SOPStatus
import agent.storage.db as db

class TestConflictDetection(unittest.TestCase):
    def setUp(self):
        self.tenant_id = "ten_conflict_test"
        db.init_agent_db()

    def test_conflict_detection_when_meeting_contradicts_sop(self):
        # 1. Existing approved SOP states Finance Manager approves
        sop = SOP(
            sop_id=generate_id("sop"),
            tenant_id=self.tenant_id,
            title="Invoice Handling SOP",
            purpose="Handling invoices",
            owner="Finance",
            steps=[
                SOPStep(step_number=1, title="Generate Bill", description="Generate customer bill", responsible_role="Billing Specialist"),
                SOPStep(step_number=2, title="Approve Invoice", description="Finance Manager approves customer invoice.", responsible_role="Finance Manager")
            ],
            status=SOPStatus.APPROVED
        )
        db.store_sop(self.tenant_id, sop)

        # 2. New meeting states: "Finance Lead now approves invoices."
        meeting = Meeting(
            meeting_id=generate_id("mtg"),
            tenant_id=self.tenant_id,
            title="Leadership Weekly Alignment",
            extracted_processes=[
                {"statement": "Finance Lead now approves invoices.", "speaker": "CFO", "timestamp": "14:21"}
            ]
        )

        # 3. Conflict engine scans meeting
        conflicts = conflict_engine.check_meeting_for_conflicts(self.tenant_id, meeting)

        self.assertGreaterEqual(len(conflicts), 1, "Conflict engine should flag the approval role change!")
        cnf = conflicts[0]
        self.assertEqual(cnf.sop_id, sop.sop_id)
        self.assertIn("Finance Manager", cnf.existing_statement)
        self.assertIn("Finance Lead now approves", cnf.new_statement)
        self.assertEqual(cnf.status, "PENDING_REVIEW")

if __name__ == "__main__":
    unittest.main()
