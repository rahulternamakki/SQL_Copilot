"""
Qdrant Vector Store Management for Governed AI Database Copilot.
Enforces per-tenant isolation by creating dedicated collections per connection_id.
Includes seamless in-memory fallback for local environments where Qdrant container is offline.
"""

import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from config import settings
from rag.chunker import RAGChunk
from rag.embedder import embedder

logger = logging.getLogger("qdrant-store")


class QdrantStore:
    def __init__(self):
        self.host = settings.qdrant_host
        self.port = settings.qdrant_port
        self.prefix = settings.qdrant_collection_prefix
        self._client: Optional[QdrantClient] = None
        self._fallback_memory_store: Dict[str, List[Dict[str, Any]]] = {}

    def _get_client(self) -> Optional[QdrantClient]:
        if self._client is not None:
            return self._client
        try:
            if getattr(settings, "qdrant_url", None):
                self._client = QdrantClient(
                    url=settings.qdrant_url,
                    api_key=settings.qdrant_api_key,
                    timeout=5.0,
                )
            else:
                self._client = QdrantClient(host=self.host, port=self.port, timeout=3.0)
            return self._client
        except Exception as e:
            logger.warning(f"Could not connect to Qdrant: {e}. Using fallback memory store.")
            return None

    def get_collection_name(self, connection_id: str) -> str:
        safe_id = "".join(c if c.isalnum() else "_" for c in connection_id)
        return f"{self.prefix}{safe_id}"

    def ensure_collection(self, connection_id: str):
        col_name = self.get_collection_name(connection_id)
        client = self._get_client()
        if client:
            try:
                collections = client.get_collections().collections
                exists = any(c.name == col_name for c in collections)
                if not exists:
                    client.create_collection(
                        collection_name=col_name,
                        vectors_config=VectorParams(size=embedder.dimension, distance=Distance.COSINE),
                    )
            except Exception as e:
                logger.warning(f"Qdrant ensure_collection error: {e}")
                self._fallback_memory_store.setdefault(col_name, [])
        else:
            self._fallback_memory_store.setdefault(col_name, [])

    def upsert_chunks(self, connection_id: str, chunks: List[RAGChunk]):
        self.ensure_collection(connection_id)
        col_name = self.get_collection_name(connection_id)
        
        # Prepare vectors
        contents = [c.content for c in chunks]
        vectors = embedder.embed_batch(contents)

        client = self._get_client()
        if client:
            try:
                points = [
                    PointStruct(
                        id=idx + 1,
                        vector=vec,
                        payload={
                            "chunk_id": chunk.chunk_id,
                            "chunk_type": chunk.chunk_type,
                            "title": chunk.title,
                            "content": chunk.content,
                            "metadata": chunk.metadata,
                        },
                    )
                    for idx, (chunk, vec) in enumerate(zip(chunks, vectors))
                ]
                client.upsert(collection_name=col_name, points=points)
                logger.info(f"Successfully upserted {len(points)} chunks into Qdrant collection '{col_name}'")
                return
            except Exception as e:
                logger.warning(f"Qdrant upsert failed: {e}. Storing in memory fallback.")

        # Fallback memory store
        self._fallback_memory_store[col_name] = [
            {
                "chunk_id": chunk.chunk_id,
                "chunk_type": chunk.chunk_type,
                "title": chunk.title,
                "content": chunk.content,
                "vector": vec,
                "metadata": chunk.metadata,
            }
            for chunk, vec in zip(chunks, vectors)
        ]

    def search(self, connection_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        self.ensure_collection(connection_id)
        col_name = self.get_collection_name(connection_id)
        query_vec = embedder.embed_text(query)

        client = self._get_client()
        if client:
            try:
                search_results = client.search(
                    collection_name=col_name,
                    query_vector=query_vec,
                    limit=limit,
                )
                if search_results:
                    return [
                        {
                            "chunk_id": hit.payload.get("chunk_id"),
                            "chunk_type": hit.payload.get("chunk_type"),
                            "title": hit.payload.get("title"),
                            "content": hit.payload.get("content"),
                            "score": hit.score,
                            "metadata": hit.payload.get("metadata", {}),
                        }
                        for hit in search_results
                    ]
            except Exception as e:
                logger.warning(f"Qdrant search failed: {e}. Falling back to memory cosine search.")

        # Fallback memory search
        stored = self._fallback_memory_store.get(col_name, [])
        if not stored:
            return []

        def cosine_similarity(v1: List[float], v2: List[float]) -> float:
            return sum(a * b for a, b in zip(v1, v2))

        scored = []
        for item in stored:
            score = cosine_similarity(query_vec, item["vector"])
            scored.append(
                {
                    "chunk_id": item["chunk_id"],
                    "chunk_type": item["chunk_type"],
                    "title": item["title"],
                    "content": item["content"],
                    "score": round(score, 4),
                    "metadata": item["metadata"],
                }
            )

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]


qdrant_store = QdrantStore()
