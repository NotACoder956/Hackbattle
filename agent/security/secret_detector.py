"""
Secret Detection & Redaction Engine
Detects API keys, database credentials, passwords, tokens, and private keys.
Redacts them before chunking and embedding so company secrets never get exposed to AI models.
"""
import re
from typing import Tuple, List, Dict

SECRET_PATTERNS = [
    # AWS Access Key ID
    (re.compile(r'(?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}'), "[REDACTED_AWS_ACCESS_KEY]"),
    # AWS Secret Key
    (re.compile(r'(?i)aws_secret_access_key\s*=\s*[0-9a-zA-Z/+]{40}'), "aws_secret_access_key=[REDACTED_AWS_SECRET]"),
    # Generic API Keys / Tokens (e.g. sk-..., ghp_..., xoxb-...)
    (re.compile(r'sk-[a-zA-Z0-9]{20,64}'), "[REDACTED_OPENAI_KEY]"),
    (re.compile(r'ghp_[a-zA-Z0-9]{36}'), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r'xox[baprs]-[0-9a-zA-Z-]{10,48}'), "[REDACTED_SLACK_TOKEN]"),
    # Database URLs
    (re.compile(r'(postgres|mysql|mongodb)://[^:]+:[^/\s]+@[a-zA-Z0-9.-]+:[0-9]+/[a-zA-Z0-9_]+'), "[REDACTED_DATABASE_URL]"),
    # Generic Password Assignments
    (re.compile(r'(?i)(password|passwd|secret|auth_token)\s*[:=]\s*["\']?[a-zA-Z0-9!@#$%^&*()_+=-]{8,}["\']?'), r'\1=[REDACTED_CREDENTIAL]'),
    # RSA / EC Private Keys
    (re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----'), "[REDACTED_PRIVATE_KEY]"),
    # Bearer Tokens
    (re.compile(r'(?i)Bearer\s+[a-zA-Z0-9_.-]{24,}'), "Bearer [REDACTED_TOKEN]")
]

def scan_and_redact_secrets(text: str) -> Tuple[str, List[Dict[str, str]]]:
    """
    Scans input text for sensitive credentials.
    Returns:
        sanitized_text: string with secrets replaced by [REDACTED_...]
        findings: list of detected secret types
    """
    if not text:
        return "", []

    sanitized = text
    findings = []

    for pattern, replacement in SECRET_PATTERNS:
        matches = pattern.findall(sanitized)
        if matches:
            findings.append({
                "rule": replacement,
                "count": len(matches)
            })
            sanitized = pattern.sub(replacement, sanitized)

    return sanitized, findings
