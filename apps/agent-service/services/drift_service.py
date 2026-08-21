"""
Schema Drift Detection & Auto-Reindexing Service for Governed AI Database Copilot.
Generates SHA-256 catalog fingerprints, detects out-of-band DDL changes, and triggers incremental Qdrant vector re-indexing.
"""

import os
import json
import hashlib
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from services.introspection_service import introspection_service
from services.glossary_service import glossary_service
from rag.chunker import chunker
from rag.qdrant_store import qdrant_store

logger = logging.getLogger("drift-service")
CACHE_DIR = "schema_cache"


class DriftResult(BaseModel):
    has_drift: bool
    connection_id: str
    previous_hash: Optional[str] = None
    current_hash: str
    added_tables: List[str] = []
    removed_tables: List[str] = []
    modified_tables: List[str] = []
    reindexed_chunks: int = 0
    message: str


class SchemaDriftService:
    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_hash_path(self, connection_id: str) -> str:
        safe_id = "".join(c if c.isalnum() else "_" for c in connection_id)
        return os.path.join(self.cache_dir, f"{safe_id}_hash.txt")

    def compute_schema_hash(self, schema_data: Dict[str, Any]) -> str:
        """Compute deterministic SHA-256 fingerprint from schema structure."""
        simplified_tables = []
        for t in sorted(schema_data.get("tables", []), key=lambda x: x.get("table_name", "")):
            cols = sorted(
                [f"{c.get('name')}:{c.get('type')}:{c.get('nullable')}" for c in t.get("columns", [])]
            )
            pks = sorted(t.get("primary_keys", []))
            fks = sorted([f"{fk.get('referred_table')}:{fk.get('constrained_columns')}" for fk in t.get("foreign_keys", [])])
            simplified_tables.append({
                "table": t.get("table_name"),
                "columns": cols,
                "pks": pks,
                "fks": fks,
            })
        
        serialized = json.dumps(simplified_tables, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    async def check_and_heal_drift(self, connection_id: str, force_reindex: bool = False) -> DriftResult:
        """
        Check for schema drift against cached fingerprint and trigger incremental RAG re-indexing if drifted.
        """
        # 1. Fetch current live schema
        try:
            live_schema = await introspection_service.get_schema(connection_id, force_refresh=True)
        except Exception as e:
            logger.warning(f"Could not introspect live schema for drift check: {e}")
            return DriftResult(
                has_drift=False,
                connection_id=connection_id,
                current_hash="unknown",
                message=f"Introspection failed: {str(e)}",
            )

        current_hash = self.compute_schema_hash(live_schema)
        hash_file = self._get_hash_path(connection_id)

        previous_hash = None
        if os.path.exists(hash_file):
            try:
                with open(hash_file, "r", encoding="utf-8") as f:
                    previous_hash = f.read().strip()
            except Exception:
                pass

        # If no previous hash or hashes match (and not force), schema is in sync
        if previous_hash and previous_hash == current_hash and not force_reindex:
            return DriftResult(
                has_drift=False,
                connection_id=connection_id,
                previous_hash=previous_hash,
                current_hash=current_hash,
                message="Schema is in sync with vector index (zero drift detected).",
            )

        # 2. Schema drift detected: perform incremental re-indexing
        logger.info(f"Schema drift detected for connection '{connection_id}'. Re-indexing vectors in Qdrant.")
        
        glossary_terms = glossary_service.list_terms(connection_id)
        if not glossary_terms:
            glossary_terms = glossary_service.generate_heuristic_draft(live_schema)

        s_chunks = chunker.chunk_schema(connection_id, live_schema)
        g_chunks = chunker.chunk_glossary(connection_id, [t.model_dump() if hasattr(t, "model_dump") else t for t in glossary_terms])
        total_chunks = len(s_chunks) + len(g_chunks)

        # Upsert into Qdrant
        qdrant_store.upsert_chunks(connection_id, s_chunks + g_chunks)

        # Save new hash
        try:
            with open(hash_file, "w", encoding="utf-8") as f:
                f.write(current_hash)
        except Exception as e:
            logger.warning(f"Could not write hash file: {e}")

        diff_msg = (
            f"Schema drift detected! Automatically re-indexed {len(s_chunks)} schema table chunks and {len(g_chunks)} glossary rules into Qdrant."
            if previous_hash
            else f"Initial schema fingerprint captured. Indexed {total_chunks} chunks."
        )

        return DriftResult(
            has_drift=bool(previous_hash and previous_hash != current_hash),
            connection_id=connection_id,
            previous_hash=previous_hash,
            current_hash=current_hash,
            reindexed_chunks=total_chunks,
            message=diff_msg,
        )


drift_service = SchemaDriftService()
