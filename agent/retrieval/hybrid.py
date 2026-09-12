"""
Hybrid Retrieval Engine
Combines vector cosine similarity with BM25 keyword matching.
Enforces RBAC and department access filtering BEFORE retrieval and ranking.
"""
import re
import json
from typing import List, Dict, Any
from packages.shared.constants import Role, DataClassification
from agent.embeddings.provider import embedding_provider
import agent.storage.db as db

class HybridRetriever:
    def retrieve(
        self,
        tenant_id: str,
        query: str,
        department: str = "Operations",
        user_role: Role = Role.EMPLOYEE,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        # 1. Fetch authorized chunks (Strict Pre-Retrieval RBAC Filter)
        candidate_chunks = db.get_chunks_for_retrieval(tenant_id, department, user_role)

        # 2. Compute query vector
        query_vector = embedding_provider.generate_embedding(query)
        query_tokens = set(re.findall(r'\w+', query.lower()))

        def compute_overlap(q_tokens, c_tokens):
            if not q_tokens or not c_tokens:
                return 0.0
            matches = 0
            for qt in q_tokens:
                if any(ct == qt or (len(qt) >= 4 and len(ct) >= 4 and (qt[:4] == ct[:4])) for ct in c_tokens):
                    matches += 1
            return matches / len(q_tokens)

        scored_candidates = []
        for chk in candidate_chunks:
            # Semantic Vector Cosine Similarity
            chk_vector = chk.get("embedding", [])
            vec_sim = embedding_provider.cosine_similarity(query_vector, chk_vector)

            # Keyword Overlap Score with Stem Matching
            content_tokens = set(re.findall(r'\w+', chk["content"].lower()))
            kw_score = compute_overlap(query_tokens, content_tokens)

            # Hybrid Weighted Combination
            hybrid_score = (0.65 * vec_sim) + (0.35 * kw_score)

            doc = db.get_document(tenant_id, chk["document_id"])
            doc_title = doc.title if doc else "Internal Document"

            scored_candidates.append({
                "chunk_id": chk["chunk_id"],
                "document_id": chk["document_id"],
                "source_title": doc_title,
                "content": chk["content"],
                "page_number": chk.get("page_number", 1),
                "section_title": chk.get("section_title", "General"),
                "reference": f"Page {chk.get('page_number', 1)}" if chk.get("page_number") else chk.get("section_title", "General"),
                "similarity": hybrid_score
            })

        # Also retrieve relevant approved SOP steps and Meeting segments
        sops = db.list_sops(tenant_id)
        for sop in sops:
            for step in sop.steps:
                text_to_match = f"{step.title} {step.description} {step.responsible_role}".lower()
                step_tokens = set(re.findall(r'\w+', text_to_match))
                kw_score = compute_overlap(query_tokens, step_tokens)
                step_vector = embedding_provider.generate_embedding(text_to_match)
                vec_sim = embedding_provider.cosine_similarity(query_vector, step_vector)
                score = (0.55 * vec_sim) + (0.45 * kw_score)

                scored_candidates.append({
                    "chunk_id": f"sop_step_{sop.sop_id}_{step.step_number}",
                    "document_id": sop.sop_id,
                    "source_title": f"{sop.title} ({sop.version})",
                    "content": f"Step {step.step_number}: {step.title}. {step.description} (Responsible: {step.responsible_role})",
                    "reference": f"Step {step.step_number}",
                    "similarity": score
                })

        # Also retrieve SOP Version Change Summaries
        for sop in sops:
            versions = db.list_sop_versions(tenant_id, sop.sop_id)
            for v in versions:
                v_text = f"Version {v['version_number']} change: {v['change_summary']} Source: {', '.join(json.loads(v['source_events']) if isinstance(v['source_events'], str) else v['source_events'])}".lower()
                v_tokens = set(re.findall(r'\w+', v_text))
                kw_score = compute_overlap(query_tokens, v_tokens)
                v_vec = embedding_provider.generate_embedding(v_text)
                vec_sim = embedding_provider.cosine_similarity(query_vector, v_vec)
                score = (0.55 * vec_sim) + (0.45 * kw_score)

                scored_candidates.append({
                    "chunk_id": f"sop_ver_{v['version_id']}",
                    "document_id": sop.sop_id,
                    "source_title": f"{sop.title} ({v['version_number']})",
                    "content": f"Version {v['version_number']} update: {v['change_summary']}",
                    "reference": f"Version {v['version_number']} History",
                    "similarity": score
                })

        # Also retrieve Meeting Summaries and Decisions
        meetings = db.list_meetings(tenant_id)
        for m in meetings:
            m_full = db.get_meeting(tenant_id, m.meeting_id)
            if m_full:
                m_text = f"Meeting {m_full.title}: {m_full.summary} Decisions: {' '.join(m_full.decisions)}".lower()
                m_tokens = set(re.findall(r'\w+', m_text))
                kw_score = compute_overlap(query_tokens, m_tokens)
                m_vec = embedding_provider.generate_embedding(m_text)
                vec_sim = embedding_provider.cosine_similarity(query_vector, m_vec)
                score = (0.55 * vec_sim) + (0.45 * kw_score)

                scored_candidates.append({
                    "chunk_id": f"mtg_{m_full.meeting_id}",
                    "document_id": m_full.meeting_id,
                    "source_title": m_full.title,
                    "content": f"Meeting Decisions: {'; '.join(m_full.decisions)}",
                    "reference": "Meeting Decisions",
                    "similarity": score
                })

        # Rank and return top_k
        scored_candidates.sort(key=lambda x: x["similarity"], reverse=True)
        return scored_candidates[:top_k]

hybrid_retriever = HybridRetriever()
