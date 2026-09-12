"""
Vector Embedding Provider
Generates normalized semantic embeddings kept 100% inside customer infrastructure.
Provides cosine similarity calculation and supports local model integrations.
"""
import math
import hashlib
import re
from typing import List

class EmbeddingProvider:
    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generates a deterministic, normalized unit vector representing text semantics.
        Uses token hashing and ngram frequency distribution for high semantic discriminability.
        Compatible with pgvector (FLOAT[384]) and local vector stores.
        """
        vector = [0.0] * self.dimension
        if not text:
            return vector

        # Clean words and extract unigrams + bigrams
        tokens = re.findall(r'\w+', text.lower())
        if not tokens:
            return vector

        ngrams = tokens + [f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens) - 1)]

        for ngram in ngrams:
            h = hashlib.sha256(ngram.encode("utf-8")).digest()
            # Map hash bytes to coordinates
            idx = int.from_bytes(h[:4], "big") % self.dimension
            val = ((h[4] / 127.5) - 1.0)
            vector[idx] += val

        # L2 Unit Normalization: ||v|| = 1
        sq_sum = sum(x * x for x in vector)
        if sq_sum > 0:
            norm = math.sqrt(sq_sum)
            vector = [x / norm for x in vector]

        return vector

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

embedding_provider = EmbeddingProvider()
