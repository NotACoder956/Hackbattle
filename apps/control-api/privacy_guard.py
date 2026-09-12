"""
Control Plane Privacy Guard
Enforces that raw documents, recordings, chunk texts, employee questions,
and company embeddings never reach or get stored in the cloud control plane.
"""
import re
from typing import Dict, Any

FORBIDDEN_CONTENT_KEYS = {
    "raw_text", "raw_content", "document_text", "transcript_text",
    "audio_bytes", "recording_file", "embedding_vector", "vector",
    "chunks", "chunk_content", "question_content", "sop_steps_raw"
}

def inspect_payload_for_company_content(data: Any) -> bool:
    """
    Returns True if data contains forbidden company content keys or patterns,
    violating the control plane zero-knowledge privacy architecture.
    """
    if isinstance(data, dict):
        for k, v in data.items():
            if k.lower() in FORBIDDEN_CONTENT_KEYS:
                return True
            if inspect_payload_for_company_content(v):
                return True
    elif isinstance(data, list):
        for item in data:
            if inspect_payload_for_company_content(item):
                return True
    return False
