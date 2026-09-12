"""
Security Test: Agent Enrollment, Registration, Heartbeat, and Immediate Revocation
"""
import unittest
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from apps.control_api.main import control_plane_app

class TestAgentRevocation(unittest.TestCase):
    def test_enroll_register_and_revoke_lifecycle(self):
        tenant_id = "ten_acme_lifecycle_test"

        # 1. Admin enrolls a new private agent
        enroll_res = control_plane_app.handle_request(
            method="POST",
            path="/api/v1/agents/enroll",
            headers={"Content-Type": "application/json"},
            body={"tenant_id": tenant_id, "name": "Acme-OnPrem-01"}
        )
        self.assertEqual(enroll_res["status"], 201)
        enrollment_token = enroll_res["body"]["enrollment_token"]
        agent_id = enroll_res["body"]["agent_id"]

        # 2. Private agent starts up inside customer network and registers
        reg_res = control_plane_app.handle_request(
            method="POST",
            path="/api/v1/agents/register",
            headers={"Content-Type": "application/json"},
            body={"enrollment_token": enrollment_token, "version": "1.0.4"}
        )
        self.assertEqual(reg_res["status"], 200)
        auth_token = reg_res["body"]["auth_token"]

        # 3. Agent sends successful heartbeat
        hb_res = control_plane_app.handle_request(
            method="POST",
            path="/api/v1/agents/heartbeat",
            headers={"Content-Type": "application/json"},
            body={"agent_id": agent_id, "auth_token": auth_token, "version": "1.0.4"}
        )
        self.assertEqual(hb_res["status"], 200)
        self.assertEqual(hb_res["body"]["status"], "ACK")

        # 4. Security Admin detects compromise and immediately revokes the agent
        revoke_res = control_plane_app.handle_request(
            method="POST",
            path=f"/api/v1/agents/{agent_id}/revoke",
            headers={"Content-Type": "application/json"},
            body={"tenant_id": tenant_id}
        )
        self.assertEqual(revoke_res["status"], 200)

        # 5. Revoked agent attempts subsequent heartbeat -> Must be rejected with 403 Forbidden!
        hb_revoked_res = control_plane_app.handle_request(
            method="POST",
            path="/api/v1/agents/heartbeat",
            headers={"Content-Type": "application/json"},
            body={"agent_id": agent_id, "auth_token": auth_token, "version": "1.0.4"}
        )
        self.assertEqual(hb_revoked_res["status"], 403, "Revoked agent must immediately fail heartbeat!")

if __name__ == "__main__":
    unittest.main()
