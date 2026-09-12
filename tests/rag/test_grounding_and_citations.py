"""
RAG & Grounding Test: Citations & Safe Uncertainty Fallbacks
Verifies that all company answers are grounded with verifiable citations,
and ungrounded questions return standard uncertainty fallback and trigger Knowledge Gap tracking.
"""
import unittest
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agent.rag.grounded_qa import grounded_qa_engine
from agent.sop.engine import sop_engine
from packages.schemas.models import Meeting, SOPStep, generate_id
from packages.shared.constants import Role
import agent.storage.db as db

class TestRAGGroundingAndCitations(unittest.TestCase):
    def setUp(self):
        self.tenant_id = "ten_rag_test"
        db.init_agent_db()

        # Seed an approved onboarding SOP
        meeting = Meeting(
            meeting_id=generate_id("mtg"),
            tenant_id=self.tenant_id,
            title="Operations Onboarding Meeting",
            date="2026-09-12"
        )
        sop = sop_engine.generate_draft_sop_from_meeting(self.tenant_id, meeting)
        sop_engine.approve_sop(self.tenant_id, sop.sop_id, "manager@acme.corp")

    def test_grounded_answer_with_citations_after_kyc(self):
        res = grounded_qa_engine.answer_question(
            tenant_id=self.tenant_id,
            question="What should I do after KYC verification?",
            department="Operations",
            user_role=Role.EMPLOYEE
        )
        self.assertEqual(res["status"], "SUCCESS")
        msg = res["message"]
        self.assertIn("Invoice Generation", msg["content"])
        self.assertIn("Finance Lead", msg["content"])
        self.assertGreaterEqual(len(msg["citations"]), 1)

        first_citation = msg["citations"][0]
        self.assertTrue("SOP" in first_citation["source_title"] or "Onboarding" in first_citation["source_title"])
        self.assertTrue("Step" in first_citation["reference"] or "Page" in first_citation["reference"])

    def test_who_approves_invoices(self):
        res = grounded_qa_engine.answer_question(
            tenant_id=self.tenant_id,
            question="Who approves invoices?",
            department="Operations",
            user_role=Role.EMPLOYEE
        )
        self.assertEqual(res["status"], "SUCCESS")
        msg = res["message"]
        self.assertIn("Finance Lead", msg["content"])
        self.assertGreaterEqual(len(msg["citations"]), 1)

    def test_insufficient_evidence_safely_falls_back_and_records_gap(self):
        unknown_q = "How do I launch a lunar satellite from the rooftop parking?"
        res = grounded_qa_engine.answer_question(
            tenant_id=self.tenant_id,
            question=unknown_q,
            department="Operations",
            user_role=Role.EMPLOYEE
        )
        self.assertEqual(res["status"], "UNANSWERED_GAP_RECORDED")
        msg = res["message"]
        self.assertEqual(
            msg["content"],
            "I couldn't find enough information in the company's knowledge base to answer this confidently."
        )
        self.assertEqual(len(msg["citations"]), 0)

        # Check knowledge gap in database
        gaps = db.list_knowledge_gaps(self.tenant_id)
        gap_questions = [g.question for g in gaps]
        self.assertIn(unknown_q, gap_questions, "Unanswered query must be registered as a Knowledge Gap!")

if __name__ == "__main__":
    unittest.main()
