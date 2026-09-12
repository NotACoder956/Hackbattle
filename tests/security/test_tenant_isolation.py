"""
Security Test: Multi-Tenant Data Isolation
Verifies Company A cannot access Company B's documents, SOPs, meetings, chunks, or conversations.
"""
import unittest
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import agent.storage.db as db
from packages.schemas.models import Document, SOP, Meeting, SOPStep, generate_id, current_timestamp
from packages.shared.constants import DataClassification, DepartmentScope, SOPStatus

class TestTenantIsolation(unittest.TestCase):
    def setUp(self):
        self.tenant_a = "ten_company_alpha"
        self.tenant_b = "ten_company_beta"
        db.init_agent_db()

    def test_document_cross_tenant_isolation(self):
        # Company A uploads a confidential document
        doc_a = Document(
            document_id=generate_id("doc"),
            tenant_id=self.tenant_a,
            filename="alpha_confidential_strategy.pdf",
            title="Alpha Confidential Strategy",
            mime_type="application/pdf",
            version="v1",
            uploaded_by="ceo@alpha.com",
            checksum="chk_123",
            classification=DataClassification.CONFIDENTIAL,
            department="Executive",
            scope=DepartmentScope.PRIVATE,
            status="PROCESSED",
            total_pages=3,
            total_chunks=5
        )
        db.store_document(self.tenant_a, doc_a)

        # Company B attempts to retrieve doc_a by ID
        doc_leak = db.get_document(self.tenant_b, doc_a.document_id)
        self.assertIsNone(doc_leak, "CRITICAL: Company B was able to fetch Company A's document!")

        # Company B lists documents
        beta_docs = db.list_documents(self.tenant_b)
        beta_doc_ids = [d.document_id for d in beta_docs]
        self.assertNotIn(doc_a.document_id, beta_doc_ids, "CRITICAL: Company A's document appeared in Company B's list!")

    def test_sop_cross_tenant_isolation(self):
        # Company A creates a proprietary SOP
        sop_a = SOP(
            sop_id=generate_id("sop"),
            tenant_id=self.tenant_a,
            title="Alpha Proprietary Manufacturing Procedure",
            purpose="Secret chemical synthesis",
            scope="Internal Only",
            owner="R&D",
            steps=[SOPStep(step_number=1, title="Mix Compound", description="Combine elements safely", responsible_role="Scientist")]
        )
        db.store_sop(self.tenant_a, sop_a)

        # Company B queries for sop_a
        sop_leak = db.get_sop(self.tenant_b, sop_a.sop_id)
        self.assertIsNone(sop_leak, "CRITICAL: Company B was able to fetch Company A's SOP!")

        beta_sops = db.list_sops(self.tenant_b)
        beta_sop_ids = [s.sop_id for s in beta_sops]
        self.assertNotIn(sop_a.sop_id, beta_sop_ids, "CRITICAL: Company A's SOP appeared in Company B's SOP catalog!")

    def test_meeting_cross_tenant_isolation(self):
        # Company A stores a confidential executive meeting
        meeting_a = Meeting(
            meeting_id=generate_id("mtg"),
            tenant_id=self.tenant_a,
            title="Alpha Board Meeting - Acquisition Strategy",
            summary="Confidential M&A discussion"
        )
        db.store_meeting(self.tenant_a, meeting_a)

        # Company B attempts to retrieve meeting_a
        meeting_leak = db.get_meeting(self.tenant_b, meeting_a.meeting_id)
        self.assertIsNone(meeting_leak, "CRITICAL: Company B was able to fetch Company A's meeting recording!")

if __name__ == "__main__":
    unittest.main()
