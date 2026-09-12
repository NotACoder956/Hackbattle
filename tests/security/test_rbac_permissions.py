"""
Security Test: Server-Side RBAC Enforcement
Validates that permissions are enforced strictly on the server/agent side.
"""
import unittest
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from packages.shared.constants import Role, ROLE_PERMISSIONS
from agent.api.routes import private_agent_router

class TestRBACPermissions(unittest.TestCase):
    def test_employee_cannot_approve_sop(self):
        headers = {
            "X-Tenant-ID": "ten_rbac_test",
            "X-User-Role": Role.EMPLOYEE.value,
            "X-User-Email": "employee@acme.corp"
        }
        res = private_agent_router.handle_request(
            method="POST",
            path="/internal/v1/sops/sop_sample_123/approve",
            headers=headers
        )
        self.assertEqual(res["status"], 403, "EMPLOYEE should be blocked from approving SOPs with 403 Forbidden")
        self.assertIn("Permission denied", res["body"]["error"])

    def test_viewer_cannot_upload_document(self):
        headers = {
            "X-Tenant-ID": "ten_rbac_test",
            "X-User-Role": Role.VIEWER.value,
            "X-User-Email": "viewer@acme.corp"
        }
        res = private_agent_router.handle_request(
            method="POST",
            path="/internal/v1/documents/upload",
            headers=headers,
            body={"filename": "test.txt", "content": "Sample"}
        )
        self.assertEqual(res["status"], 403, "VIEWER should be blocked from uploading documents with 403 Forbidden")

    def test_employee_cannot_delete_document(self):
        headers = {
            "X-Tenant-ID": "ten_rbac_test",
            "X-User-Role": Role.EMPLOYEE.value,
            "X-User-Email": "employee@acme.corp"
        }
        res = private_agent_router.handle_request(
            method="DELETE",
            path="/internal/v1/documents/doc_sample_999",
            headers=headers
        )
        self.assertEqual(res["status"], 403, "EMPLOYEE should be blocked from deleting documents with 403 Forbidden")

    def test_manager_can_upload_document(self):
        headers = {
            "X-Tenant-ID": "ten_rbac_test",
            "X-User-Role": Role.MANAGER.value,
            "X-User-Email": "manager@acme.corp"
        }
        res = private_agent_router.handle_request(
            method="POST",
            path="/internal/v1/documents/upload",
            headers=headers,
            body={"filename": "operations_memo.txt", "content": "Memo content for operations."}
        )
        self.assertEqual(res["status"], 201, "MANAGER must be permitted to upload operational documents")

if __name__ == "__main__":
    unittest.main()
