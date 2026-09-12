"""
Document Chunking Engine with Provenance Tracking
Chunks parsed document sections into overlapping windows while preserving
page numbers, section titles, character offsets, and classification scopes.
Applies secret detection & redaction automatically.
"""
from typing import List, Optional
from packages.schemas.models import DocumentChunk, generate_id, current_timestamp
from packages.shared.constants import DataClassification, DepartmentScope
from agent.security.secret_detector import scan_and_redact_secrets

class Chunker:
    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_section(
        self,
        document_id: str,
        version_id: str,
        tenant_id: str,
        content: str,
        section_title: str,
        page_number: Optional[int] = 1,
        classification: DataClassification = DataClassification.INTERNAL,
        department_scope: DepartmentScope = DepartmentScope.DEPARTMENT,
        department: str = "Operations"
    ) -> List[DocumentChunk]:
        # Redact any embedded API keys, passwords, or secrets prior to chunk creation
        sanitized_content, _ = scan_and_redact_secrets(content)

        chunks = []
        text_length = len(sanitized_content)

        if text_length <= self.chunk_size:
            chunk = DocumentChunk(
                chunk_id=generate_id("chk"),
                document_id=document_id,
                tenant_id=tenant_id,
                version_id=version_id,
                content=sanitized_content.strip(),
                page_number=page_number,
                section_title=section_title,
                char_start=0,
                char_end=text_length,
                classification=classification,
                department_scope=department_scope,
                department=department,
                created_at=current_timestamp()
            )
            return [chunk]

        start = 0
        while start < text_length:
            end = min(start + self.chunk_size, text_length)
            # Find closest sentence/paragraph boundary if possible
            if end < text_length:
                boundary = sanitized_content.rfind("\n", start, end)
                if boundary == -1:
                    boundary = sanitized_content.rfind(". ", start, end)
                if boundary != -1 and boundary > start + (self.chunk_size // 2):
                    end = boundary + 1

            chunk_text = sanitized_content[start:end].strip()
            if chunk_text:
                chunk = DocumentChunk(
                    chunk_id=generate_id("chk"),
                    document_id=document_id,
                    tenant_id=tenant_id,
                    version_id=version_id,
                    content=chunk_text,
                    page_number=page_number,
                    section_title=section_title,
                    char_start=start,
                    char_end=end,
                    classification=classification,
                    department_scope=department_scope,
                    department=department,
                    created_at=current_timestamp()
                )
                chunks.append(chunk)

            if end >= text_length:
                break
            start = end - self.chunk_overlap

        return chunks

default_chunker = Chunker()
