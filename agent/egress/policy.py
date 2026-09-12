"""
Data Egress Policy Gate
Enforces the core privacy guarantee: company data cannot exit the local environment
unless explicitly authorized through a validated outbound egress mode.
"""
from typing import Dict, Any, Tuple
from packages.shared.constants import DataEgressMode, DataClassification
from agent.security.secret_detector import scan_and_redact_secrets

class EgressPolicyViolation(Exception):
    pass

class DataEgressGate:
    def __init__(self, mode: DataEgressMode = DataEgressMode.PRIVATE_ONLY):
        self.mode = mode

    def can_transmit_payload(
        self,
        destination_url: str,
        payload: Dict[str, Any],
        classification: DataClassification = DataClassification.INTERNAL
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Executes egress pipeline:
        Classification -> SecretDetection -> PolicyCheck -> DestinationApproval
        """
        # 1. Check Default Mode: PRIVATE_ONLY
        if self.mode == DataEgressMode.PRIVATE_ONLY:
            # Allow loopback/internal addresses only
            is_local = any(destination_url.startswith(prefix) for prefix in [
                "http://localhost", "http://127.0.0.1", "http://0.0.0.0", "http://host.docker.internal"
            ])
            if not is_local:
                return False, f"DATA EGRESS BLOCKED: Mode is PRIVATE_ONLY. Outbound transmission to {destination_url} is strictly prohibited.", {}

        # 2. Strict Confidentiality Gate
        if classification == DataClassification.HIGHLY_CONFIDENTIAL:
            return False, "DATA EGRESS BLOCKED: HIGHLY_CONFIDENTIAL knowledge can never leave local infrastructure under any policy.", {}

        # 3. Secret Inspection and Redaction
        sanitized_payload = {}
        detected_secrets = []
        for k, v in payload.items():
            if isinstance(v, str):
                cleaned, findings = scan_and_redact_secrets(v)
                sanitized_payload[k] = cleaned
                if findings:
                    detected_secrets.extend(findings)
            else:
                sanitized_payload[k] = v

        if detected_secrets and self.mode != DataEgressMode.SANITIZED:
            return False, f"DATA EGRESS BLOCKED: Payload contains unredacted credentials: {detected_secrets}", {}

        # 4. Mode-based Destination Authorization
        if self.mode == DataEgressMode.CUSTOMER_PROVIDER:
            # Requires explicit approval in configuration
            return True, "Approved for Customer-Configured Provider", sanitized_payload

        if self.mode == DataEgressMode.REMOTE_PROVIDER:
            return True, "Approved for Remote Provider with Sanitization", sanitized_payload

        # Default local transmission
        return True, "Local processing approved", sanitized_payload

egress_gate = DataEgressGate()
