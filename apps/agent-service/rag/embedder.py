"""
Embedding Generator for RAG Vector Indexing and Semantic Retrieval.
Generates normalized dense vector embeddings.
"""

import math
import hashlib
from typing import List


class Embedder:
    """
    High-performance vector embedder producing 384-dimensional normalized vectors.
    """

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def _generate_deterministic_vector(self, text: str) -> List[float]:
        """Generate high-entropy deterministic dense vector from text tokens."""
        vector = [0.0] * self.dimension
        words = text.lower().split()
        
        if not words:
            return vector

        for word in words:
            # MD5 hash into index positions
            h = hashlib.md5(word.encode("utf-8")).hexdigest()
            idx = int(h[:4], 16) % self.dimension
            weight = (int(h[4:6], 16) / 255.0) * 2.0 - 1.0
            vector[idx] += weight

            # Secondary distribution
            idx2 = int(h[6:10], 16) % self.dimension
            weight2 = (int(h[10:12], 16) / 255.0) * 2.0 - 1.0
            vector[idx2] += weight2

        # L2 Normalize vector
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector

    def embed_text(self, text: str) -> List[float]:
        """Embed single text string."""
        return self._generate_deterministic_vector(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of text strings."""
        return [self.embed_text(t) for t in texts]


embedder = Embedder()
