"""
Security Test: Path Traversal & Malicious File Upload Protection
"""
import unittest
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agent.security.validator import validate_file_upload, sanitize_filename, assert_safe_path

class TestFileSecurity(unittest.TestCase):
    def test_path_traversal_sanitization(self):
        malicious_names = [
            "../../../../etc/passwd",
            "..\\..\\windows\\system32\\cmd.exe",
            "../../../secret.key",
            "/var/root/stolen.pdf"
        ]
        for name in malicious_names:
            sanitized = sanitize_filename(name)
            self.assertNotIn("/", sanitized, f"Sanitized name contains path separator: {sanitized}")
            self.assertNotIn("\\", sanitized, f"Sanitized name contains path separator: {sanitized}")
            self.assertNotIn("..", sanitized, f"Sanitized name contains parent traversal: {sanitized}")

    def test_safe_path_containment(self):
        base_dir = "/tmp/safe_storage"
        safe_child = "/tmp/safe_storage/documents/doc1.pdf"
        escaped_path = "/tmp/safe_storage/../../etc/shadow"

        self.assertTrue(assert_safe_path(base_dir, safe_child))
        self.assertFalse(assert_safe_path(base_dir, escaped_path))

    def test_disallowed_file_types_rejected(self):
        disallowed = [
            ("malware.exe", b"binary"),
            ("exploit.sh", b"#!/bin/bash\nrm -rf /"),
            ("script.py", b"import os; os.system('whoami')"),
            ("payload.bat", b"@echo off")
        ]
        for fname, content in disallowed:
            valid, msg, _ = validate_file_upload(fname, content, max_size=1000000)
            self.assertFalse(valid, f"Executable file should have been rejected: {fname}")
            self.assertIn("Unsupported file extension", msg)

    def test_oversized_file_rejected(self):
        valid, msg, _ = validate_file_upload("large.pdf", b"A" * 105, max_size=100)
        self.assertFalse(valid)
        self.assertIn("exceeds maximum limit", msg)

if __name__ == "__main__":
    unittest.main()
