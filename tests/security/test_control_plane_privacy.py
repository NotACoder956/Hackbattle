"""
Security Test: Cloud Control Plane Zero-Knowledge Privacy Guarantee
Verifies that any request attempting to send company documents, recordings, chunk contents,
or employee company questions to the central cloud is intercepted and rejected with HTTP 422.
"""
import unittest
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from apps.control_api.main import control_plane_app

class TestControlPlanePrivacy(unittest.TestCase):
    def test_rejection_of_raw_document_payload(self):
        malicious_payload = {
            "tenant_id": "ten_test",
            "document_text": "Sensitive internal customer process details..."
        }
        res = control_plane_app.handle_request(
            method="POST",
            path="/api/v1/tenants",
            headers={"Content-Type": "application/json"},
            body=malicious_payload
        )
        self.assertEqual(res["status"], 422, "Control plane must reject any payload containing raw document text!")
        self.assertEqual(res["body"]["error"], "PRIVACY_VIOLATION_BLOCKED")

    def test_rejection_of_chunk_content_payload(self):
        chunk_payload = {
            "agent_id": "agt_test",
            "chunk_content": "Finance Lead approves invoices now."
        }
        res = control_plane_app.handle_request(
            method="POST",
            path="/api/v1/agents/heartbeat",
            headers={"Content-Type": "application/json"},
            body=chunk_payload
        )
        self.assertEqual(res["status"], 422, "Control plane must reject any chunk content payload!")

if __name__ == "__main__":
    unittest.main()
