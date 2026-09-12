"""
Prompt Injection Defense & Untrusted Content Framing
Isolates retrieved documents and transcripts from system instructions.
Prevents prompt injection attacks embedded inside uploaded files or transcripts.
"""
import re

INJECTION_TRIGGER_PATTERNS = [
    re.compile(r'(?i)ignore\s+(all\s+)?(previous|prior|above)\s+instructions'),
    re.compile(r'(?i)system\s+prompt\s+override'),
    re.compile(r'(?i)reveal\s+(all\s+)?(secrets|passwords|keys|confidential)'),
    re.compile(r'(?i)you\s+are\s+now\s+(DAN|unrestricted|in\s+developer\s+mode)')
]

def sanitize_untrusted_content(text: str) -> str:
    """
    Escapes tag breakouts and neutralizes direct injection commands in retrieved context.
    """
    if not text:
        return ""

    # Prevent premature closing of untrusted container tags
    sanitized = text.replace("</untrusted_company_content>", "&lt;/untrusted_company_content&gt;")
    sanitized = sanitized.replace("<untrusted_company_content>", "&lt;untrusted_company_content&gt;")

    # Wrap any detected adversarial triggers with advisory warnings
    for pattern in INJECTION_TRIGGER_PATTERNS:
        if pattern.search(sanitized):
            sanitized = pattern.sub(r"[UNTRUSTED ADVERSARIAL PHRASE SUPPRESSED: '\g<0>']", sanitized)

    return sanitized

def frame_grounded_context(chunks: list) -> str:
    """
    Wraps retrieved knowledge chunks inside safe boundaries.
    """
    formatted_chunks = []
    for idx, c in enumerate(chunks, 1):
        content = sanitize_untrusted_content(c.get("content", ""))
        source_title = c.get("source_title", "Document")
        ref = c.get("reference", f"Chunk {idx}")
        formatted_chunks.append(
            f"--- SOURCE [{idx}]: {source_title} ({ref}) ---\n{content}\n"
        )
    return "\n".join(formatted_chunks)
