"""
Auto-Glossary Service for Governed AI Database Copilot.
Uses Groq LLM (llama-3.3-70b-versatile) to automatically draft business definitions and ambiguous concepts from schema JSON.
Persists terms in an editable database store.
"""

import os
import json
import uuid
import sqlite3
import logging
import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from config import settings

logger = logging.getLogger("glossary-service")


class GlossaryTerm(BaseModel):
    id: str
    connection_id: str
    term: str
    definition: str
    target_table: Optional[str] = None
    target_column: Optional[str] = None
    business_rule: Optional[str] = None
    is_ambiguous: bool = False
    disambiguation_hint: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class GlossaryTermCreate(BaseModel):
    term: str
    definition: str
    target_table: Optional[str] = None
    target_column: Optional[str] = None
    business_rule: Optional[str] = None
    is_ambiguous: bool = False
    disambiguation_hint: Optional[str] = None


class LLMGlossaryOutput(BaseModel):
    terms: List[GlossaryTermCreate]


class GlossaryService:
    def __init__(self, db_path: Optional[str] = None):
        if not db_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, "glossary.db")
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS glossary_terms (
                    id TEXT PRIMARY KEY,
                    connection_id TEXT NOT NULL,
                    term TEXT NOT NULL,
                    definition TEXT NOT NULL,
                    target_table TEXT,
                    target_column TEXT,
                    business_rule TEXT,
                    is_ambiguous INTEGER NOT NULL DEFAULT 0,
                    disambiguation_hint TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def list_terms(self, connection_id: str) -> List[GlossaryTerm]:
        """List all terms for a given connection."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM glossary_terms WHERE connection_id = ? ORDER BY term ASC",
                (connection_id,),
            )
            rows = cursor.fetchall()
            return [
                GlossaryTerm(
                    id=row["id"],
                    connection_id=row["connection_id"],
                    term=row["term"],
                    definition=row["definition"],
                    target_table=row["target_table"],
                    target_column=row["target_column"],
                    business_rule=row["business_rule"],
                    is_ambiguous=bool(row["is_ambiguous"]),
                    disambiguation_hint=row["disambiguation_hint"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]

    def create_term(self, connection_id: str, term_data: GlossaryTermCreate) -> GlossaryTerm:
        """Create a new glossary term."""
        term_id = f"term_{uuid.uuid4().hex[:8]}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO glossary_terms (
                    id, connection_id, term, definition, target_table, target_column,
                    business_rule, is_ambiguous, disambiguation_hint, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    term_id,
                    connection_id,
                    term_data.term.strip().lower(),
                    term_data.definition,
                    term_data.target_table,
                    term_data.target_column,
                    term_data.business_rule,
                    1 if term_data.is_ambiguous else 0,
                    term_data.disambiguation_hint,
                    now,
                    now,
                ),
            )
            conn.commit()
            
        return GlossaryTerm(
            id=term_id,
            connection_id=connection_id,
            term=term_data.term.strip().lower(),
            definition=term_data.definition,
            target_table=term_data.target_table,
            target_column=term_data.target_column,
            business_rule=term_data.business_rule,
            is_ambiguous=term_data.is_ambiguous,
            disambiguation_hint=term_data.disambiguation_hint,
            created_at=now,
            updated_at=now,
        )

    def update_term(self, term_id: str, term_data: GlossaryTermCreate) -> Optional[GlossaryTerm]:
        """Update an existing glossary term."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE glossary_terms SET
                    term = ?, definition = ?, target_table = ?, target_column = ?,
                    business_rule = ?, is_ambiguous = ?, disambiguation_hint = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    term_data.term.strip().lower(),
                    term_data.definition,
                    term_data.target_table,
                    term_data.target_column,
                    term_data.business_rule,
                    1 if term_data.is_ambiguous else 0,
                    term_data.disambiguation_hint,
                    now,
                    term_id,
                ),
            )
            conn.commit()
            if cursor.rowcount == 0:
                return None
            
            cursor.execute("SELECT * FROM glossary_terms WHERE id = ?", (term_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return GlossaryTerm(
                id=row["id"],
                connection_id=row["connection_id"],
                term=row["term"],
                definition=row["definition"],
                target_table=row["target_table"],
                target_column=row["target_column"],
                business_rule=row["business_rule"],
                is_ambiguous=bool(row["is_ambiguous"]),
                disambiguation_hint=row["disambiguation_hint"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def delete_term(self, term_id: str) -> bool:
        """Delete term by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM glossary_terms WHERE id = ?", (term_id,))
            conn.commit()
            return cursor.rowcount > 0

    def generate_heuristic_draft(self, schema_data: Dict[str, Any]) -> List[GlossaryTermCreate]:
        """Deterministic fallback glossary drafting based on table & column heuristics."""
        drafts: List[GlossaryTermCreate] = []
        tables = schema_data.get("tables", [])
        
        for tbl in tables:
            t_name = tbl.get("table_name", "").lower()
            cols = [c.get("name", "").lower() for c in tbl.get("columns", [])]
            
            if t_name == "customers":
                drafts.append(
                    GlossaryTermCreate(
                        term="churned customer",
                        definition="A customer who has not placed an order in over 180 days or whose status is marked as churned.",
                        target_table="customers",
                        target_column="status",
                        business_rule="WHERE status = 'churned' OR id NOT IN (SELECT customer_id FROM orders WHERE order_date >= NOW() - INTERVAL '180 days')",
                        is_ambiguous=False,
                    )
                )
                drafts.append(
                    GlossaryTermCreate(
                        term="active customer",
                        definition="A registered customer with status 'active' who has made a purchase.",
                        target_table="customers",
                        target_column="status",
                        business_rule="WHERE status = 'active'",
                        is_ambiguous=False,
                    )
                )
            elif t_name == "orders":
                drafts.append(
                    GlossaryTermCreate(
                        term="gross revenue",
                        definition="Total monetary value of all completed and processing customer orders.",
                        target_table="orders",
                        target_column="total_amount",
                        business_rule="SUM(total_amount) WHERE status IN ('completed', 'processing')",
                        is_ambiguous=False,
                    )
                )
                drafts.append(
                    GlossaryTermCreate(
                        term="net revenue",
                        definition="Gross revenue minus total amount of processed refunds.",
                        target_table="orders",
                        target_column="total_amount",
                        business_rule="SUM(orders.total_amount) - COALESCE(SUM(refunds.amount), 0)",
                        is_ambiguous=False,
                    )
                )
            elif t_name == "products":
                drafts.append(
                    GlossaryTermCreate(
                        term="discontinued items",
                        definition="Products that are permanently discontinued or have 0 stock quantity.",
                        target_table="products",
                        target_column="is_discontinued",
                        business_rule="WHERE is_discontinued = TRUE OR stock_quantity = 0",
                        is_ambiguous=False,
                    )
                )
                
        # Always add standard ambiguous terms benchmark check
        drafts.append(
            GlossaryTermCreate(
                term="best employee",
                definition="Subjective or ambiguous metric. Can refer to highest revenue generated, most orders processed, or highest customer satisfaction score.",
                target_table=None,
                target_column=None,
                business_rule=None,
                is_ambiguous=True,
                disambiguation_hint="Prompt user: 'Do you mean by highest sales volume, total order count, or support resolution speed?'",
            )
        )
        return drafts

    async def auto_draft_with_llm(self, connection_id: str, schema_data: Dict[str, Any]) -> List[GlossaryTerm]:
        """
        Use Groq API (llama-3.3-70b-versatile) to analyze schema and draft plain-language business definitions.
        Falls back gracefully to heuristic drafting if API key is missing or network unavailable.
        """
        draft_terms: List[GlossaryTermCreate] = []

        if settings.groq_api_key:
            try:
                from groq import Groq
                client = Groq(api_key=settings.groq_api_key)
                
                system_prompt = (
                    "You are an expert Data Architect and Business Analyst. "
                    "Given a database schema JSON, draft a set of 5-8 plain-language business terms and definitions. "
                    "Identify:\n"
                    "1. Common business metrics (e.g. churned customer, active order, gross sales).\n"
                    "2. Ambiguous terms that require clarification (mark is_ambiguous = true with a disambiguation_hint, e.g. 'best employee').\n"
                    "3. Filter rules and target table/column mappings.\n"
                    "Respond with a strict JSON object: {\"terms\": [{\"term\": \"...\", \"definition\": \"...\", \"target_table\": \"...\", \"target_column\": \"...\", \"business_rule\": \"...\", \"is_ambiguous\": false, \"disambiguation_hint\": \"...\"}]}"
                )
                
                user_content = f"Database Schema JSON:\n{json.dumps(schema_data, indent=2)}"
                
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    model=settings.groq_model,
                    temperature=0.0,
                    response_format={"type": "json_object"},
                )
                
                raw_response = chat_completion.choices[0].message.content
                parsed = json.loads(raw_response or "{}")
                if "terms" in parsed and isinstance(parsed["terms"], list):
                    for item in parsed["terms"]:
                        draft_terms.append(GlossaryTermCreate(**item))
            except Exception as e:
                logger.warning(f"Groq auto-glossary drafting encountered error: {e}. Falling back to heuristic generator.")
                draft_terms = self.generate_heuristic_draft(schema_data)
        else:
            logger.info("GROQ_API_KEY not configured. Using heuristic glossary generator.")
            draft_terms = self.generate_heuristic_draft(schema_data)

        # Clear old terms and persist new drafts
        saved_terms: List[GlossaryTerm] = []
        for term_create in draft_terms:
            saved = self.create_term(connection_id, term_create)
            saved_terms.append(saved)
            
        return saved_terms


glossary_service = GlossaryService()
