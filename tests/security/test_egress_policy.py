"""
Security Test: Data Egress Policy Gate
Verifies that company data cannot escape to external endpoints in PRIVATE_ONLY mode.
"""
import unittest
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from packages.shared.constants import DataEgressMode, DataClassification
from agent.egress.policy import DataEgressGate

class TestDataEgressPolicy(unittest.TestCase):
    def test_private_only_blocks_remote_endpoint(self):
        gate = DataEgressGate(mode=DataEgressMode.PRIVATE_ONLY)
        allowed, reason, _ = gate.can_transmit_payload(
            destination_url="https://api.external-cloud.com/v1/inference",
            payload={"text": "Confidential customer process details"},
            classification=DataClassification.INTERNAL
        )
        self.assertFalse(allowed, "Outbound call to external endpoint should be blocked in PRIVATE_ONLY mode!")
        self.assertIn("DATA EGRESS BLOCKED", reason)

    def test_private_only_permits_localhost(self):
        gate = DataEgressGate(mode=DataEgressMode.PRIVATE_ONLY)
        allowed, reason, _ = gate.can_transmit_payload(
            destination_url="http://localhost:11434/api/generate",
            payload={"text": "Local model query"},
            classification=DataClassification.INTERNAL
        )
        self.assertTrue(allowed, "Localhost Ollama/inference server should be allowed in PRIVATE_ONLY mode.")

    def test_highly_confidential_blocked_everywhere(self):
        gate = DataEgressGate(mode=DataEgressMode.REMOTE_PROVIDER)
        allowed, reason, _ = gate.can_transmit_payload(
            destination_url="https://api.partner.com/llm",
            payload={"text": "Secret customer PII and financials"},
            classification=DataClassification.HIGHLY_CONFIDENTIAL
        )
        self.assertFalse(allowed, "HIGHLY_CONFIDENTIAL data must never leave under any policy mode!")
        self.assertIn("HIGHLY_CONFIDENTIAL", reason)

if __name__ == "__main__":
    unittest.main()
