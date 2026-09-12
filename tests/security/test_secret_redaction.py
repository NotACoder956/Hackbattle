"""
Security Test: Automated Secret Detection and Redaction
Ensures credentials never leak into embeddings or AI prompts.
"""
import unittest
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agent.security.secret_detector import scan_and_redact_secrets

class TestSecretDetection(unittest.TestCase):
    def test_aws_key_redaction(self):
        text = "Deploying production assets with AKIAIOSFODNN7EXAMPLE to S3 bucket."
        redacted, findings = scan_and_redact_secrets(text)
        self.assertNotIn("AKIAIOSFODNN7EXAMPLE", redacted)
        self.assertIn("[REDACTED_AWS_ACCESS_KEY]", redacted)
        self.assertGreaterEqual(len(findings), 1)

    def test_openai_and_github_token_redaction(self):
        text = "Connect with sk-abcdef1234567890abcdef1234567890 and repo token ghp_111122223333444455556666777788889999"
        redacted, findings = scan_and_redact_secrets(text)
        self.assertNotIn("sk-abcdef1234567890abcdef1234567890", redacted)
        self.assertNotIn("ghp_111122223333444455556666777788889999", redacted)
        self.assertIn("[REDACTED_OPENAI_KEY]", redacted)
        self.assertIn("[REDACTED_GITHUB_TOKEN]", redacted)

    def test_database_url_and_password_redaction(self):
        text = "Connect to database postgres://postgres:SuperSecretP@ss123@prod-db.internal:5432/acme_db"
        redacted, findings = scan_and_redact_secrets(text)
        self.assertNotIn("SuperSecretP@ss123", redacted)
        self.assertIn("[REDACTED_DATABASE_URL]", redacted)

if __name__ == "__main__":
    unittest.main()
