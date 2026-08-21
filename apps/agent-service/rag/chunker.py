"""
Schema & Business Glossary Chunker for RAG Ingestion Pipeline.
Decomposes database catalog and glossary definitions into semantically coherent chunks.
"""

from typing import List, Dict, Any
from pydantic import BaseModel


class RAGChunk(BaseModel):
    chunk_id: str
    connection_id: str
    chunk_type: str  # "table", "column_group", "glossary_term"
    title: str
    content: str
    metadata: Dict[str, Any]


class Chunker:
    """
    Chunks structured schema JSON and glossary terms into retrieval units.
    """

    def chunk_schema(self, connection_id: str, schema_data: Dict[str, Any]) -> List[RAGChunk]:
        chunks: List[RAGChunk] = []
        tables = schema_data.get("tables", [])
        db_type = schema_data.get("database_type", "postgresql")

        for tbl in tables:
            t_name = tbl.get("table_name", "")
            cols = tbl.get("columns", [])
            pks = tbl.get("primary_keys", [])
            fks = tbl.get("foreign_keys", [])
            row_count = tbl.get("approximate_row_count")
            comment = tbl.get("comment", "")

            # 1. Main Table Chunk
            col_lines = []
            for col in cols:
                c_name = col.get("name", "")
                c_type = col.get("type", "")
                is_pk = " [PRIMARY KEY]" if c_name in pks else ""
                nullable = "" if col.get("nullable", True) else " NOT NULL"
                default = f" DEFAULT {col.get('default')}" if col.get("default") else ""
                col_lines.append(f"  - {c_name} ({c_type}){is_pk}{nullable}{default}")

            fk_lines = []
            for fk in fks:
                c_cols = ", ".join(fk.get("constrained_columns", []))
                r_tbl = fk.get("referred_table", "")
                r_cols = ", ".join(fk.get("referred_columns", []))
                fk_lines.append(f"  - Foreign Key: ({c_cols}) references {r_tbl}({r_cols})")

            content = (
                f"Table: {t_name}\n"
                f"Database Type: {db_type}\n"
                f"Description: {comment or 'Database table in catalog'}\n"
                f"Estimated Rows: {row_count if row_count is not None else 'unknown'}\n"
                f"Columns:\n" + "\n".join(col_lines) + "\n"
            )
            if fk_lines:
                content += "Relationships:\n" + "\n".join(fk_lines) + "\n"

            chunks.append(
                RAGChunk(
                    chunk_id=f"table_{connection_id}_{t_name}",
                    connection_id=connection_id,
                    chunk_type="table",
                    title=f"Table: {t_name}",
                    content=content.strip(),
                    metadata={
                        "table_name": t_name,
                        "columns": [c.get("name") for c in cols],
                        "primary_keys": pks,
                        "foreign_keys": fks,
                    },
                )
            )

            # 2. Wide Table Column Group Chunk (if > 5 columns)
            if len(cols) > 5:
                half = len(cols) // 2
                col_group_content = f"Table {t_name} Column Details:\n" + "\n".join(col_lines[:half])
                chunks.append(
                    RAGChunk(
                        chunk_id=f"colgroup_{connection_id}_{t_name}_1",
                        connection_id=connection_id,
                        chunk_type="column_group",
                        title=f"Columns Group 1 for {t_name}",
                        content=col_group_content,
                        metadata={"table_name": t_name},
                    )
                )

        return chunks

    def chunk_glossary(self, connection_id: str, glossary_terms: List[Dict[str, Any]]) -> List[RAGChunk]:
        chunks: List[RAGChunk] = []
        for term in glossary_terms:
            t_id = term.get("id", "")
            t_name = term.get("term", "")
            definition = term.get("definition", "")
            target_table = term.get("target_table", "")
            target_col = term.get("target_column", "")
            rule = term.get("business_rule", "")
            is_ambiguous = term.get("is_ambiguous", False)
            hint = term.get("disambiguation_hint", "")

            content = (
                f"Business Concept / Glossary Term: '{t_name}'\n"
                f"Definition: {definition}\n"
            )
            if target_table:
                content += f"Target Table: {target_table}\n"
            if target_col:
                content += f"Target Column: {target_col}\n"
            if rule:
                content += f"SQL Filter / Calculation Rule: {rule}\n"
            if is_ambiguous:
                content += f"⚠️ AMBIGUITY NOTICE: This term has multiple definitions. Disambiguation hint: {hint}\n"

            chunks.append(
                RAGChunk(
                    chunk_id=f"glossary_{connection_id}_{t_id or t_name.replace(' ', '_')}",
                    connection_id=connection_id,
                    chunk_type="glossary_term",
                    title=f"Glossary: {t_name}",
                    content=content.strip(),
                    metadata={
                        "term": t_name,
                        "target_table": target_table,
                        "is_ambiguous": is_ambiguous,
                        "business_rule": rule,
                    },
                )
            )

        return chunks


chunker = Chunker()
