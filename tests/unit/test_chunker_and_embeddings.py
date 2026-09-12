"""
Unit Test: Chunker & Vector Embeddings
Verifies sliding window chunking, provenance retention, L2 unit normalization, and cosine similarity.
"""
import unittest
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agent.chunking.chunker import default_chunker
from agent.embeddings.provider import embedding_provider
from packages.shared.constants import DataClassification, DepartmentScope

class TestChunkerAndEmbeddings(unittest.TestCase):
    def test_chunking_provenance(self):
        content = "Line 1.\nLine 2.\nLine 3.\nLine 4.\nLine 5."
        chunks = default_chunker.chunk_section(
            document_id="doc_100",
            version_id="v1",
            tenant_id="ten_test",
            content=content,
            section_title="Guidelines",
            page_number=4,
            classification=DataClassification.INTERNAL,
            department_scope=DepartmentScope.DEPARTMENT,
            department="Operations"
        )
        self.assertGreaterEqual(len(chunks), 1)
        chk = chunks[0]
        self.assertEqual(chk.document_id, "doc_100")
        self.assertEqual(chk.page_number, 4)
        self.assertEqual(chk.section_title, "Guidelines")
        self.assertEqual(chk.classification, DataClassification.INTERNAL)

    def test_embedding_normalization_and_similarity(self):
        text_a = "New client customer onboarding and invoice approval workflow."
        text_b = "Customer onboarding procedure and billing signoff process."
        text_unrelated = "Astronomical exploration of Jupiter planetary moons."

        vec_a = embedding_provider.generate_embedding(text_a)
        vec_b = embedding_provider.generate_embedding(text_b)
        vec_c = embedding_provider.generate_embedding(text_unrelated)

        self.assertEqual(len(vec_a), 384)

        # L2 norm check
        norm_a = sum(x * x for x in vec_a)
        self.assertAlmostEqual(norm_a, 1.0, places=3)

        sim_related = embedding_provider.cosine_similarity(vec_a, vec_b)
        sim_unrelated = embedding_provider.cosine_similarity(vec_a, vec_c)

        self.assertGreater(sim_related, sim_unrelated, "Related onboarding texts must have higher semantic similarity than unrelated texts!")

if __name__ == "__main__":
    unittest.main()
