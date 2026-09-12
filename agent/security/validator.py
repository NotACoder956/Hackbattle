"""
File Security & Path Traversal Validator
Protects against malicious uploads, path traversal attacks, and oversized files.
"""
import os
import re
import uuid
from typing import Tuple

ALLOWED_EXTENSIONS = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain",
    "md": "text/markdown",
    "csv": "text/csv",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "m4a": "audio/mp4",
    "mp4": "video/mp4",
    "webm": "video/webm"
}

def sanitize_filename(filename: str) -> str:
    """
    Cleans filename to prevent path traversal and shell injection.
    """
    # Normalize backslashes from Windows paths
    normalized = filename.replace('\\', '/')
    base = os.path.basename(normalized)
    # Strip any directory traversal dots
    base = base.replace('..', '_')
    clean = re.sub(r'[^a-zA-Z0-9_.-]', '_', base)
    clean = clean.lstrip('._')
    if not clean:
        clean = f"upload_{uuid.uuid4().hex[:8]}"
    return clean

def validate_file_upload(filename: str, file_bytes: bytes, max_size: int) -> Tuple[bool, str, str]:
    """
    Validates file extension, size, and returns (is_valid, sanitized_name, detected_ext).
    """
    if len(file_bytes) > max_size:
        return False, f"File size ({len(file_bytes)} bytes) exceeds maximum limit ({max_size} bytes)", ""

    sanitized = sanitize_filename(filename)
    ext = sanitized.rsplit('.', 1)[-1].lower() if '.' in sanitized else ""

    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file extension: .{ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS.keys())}", ""

    return True, sanitized, ext

def assert_safe_path(base_dir: str, target_path: str) -> bool:
    """
    Ensures target_path does not escape base_dir via directory traversal.
    """
    abs_base = os.path.abspath(base_dir)
    abs_target = os.path.abspath(target_path)
    return os.path.commonpath([abs_base]) == os.path.commonpath([abs_base, abs_target])
