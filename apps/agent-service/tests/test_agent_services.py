"""
Unit tests for Agent Service components (Introspection & Glossary services).
"""

import os
import gc
import tempfile
import pytest
from services.introspection_service import IntrospectionService
from services.glossary_service import GlossaryService, GlossaryTermCreate


@pytest.fixture
def temp_glossary():
    tf = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = tf.name
    tf.close()
    
    service = GlossaryService(db_path=db_path)
    yield service
    
    del service
    gc.collect()
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except PermissionError:
            pass


def test_introspection_formatter():
    service = IntrospectionService(cache_dir=tempfile.gettempdir())
    sample_schema = {
        "database_type": "postgresql",
        "tables": [
            {
                "table_name": "customers",
                "columns": [
                    {"name": "id", "type": "INTEGER"},
                    {"name": "email", "type": "VARCHAR(100)"},
                ],
                "primary_keys": ["id"],
                "foreign_keys": [],
            },
            {
                "table_name": "orders",
                "columns": [
                    {"name": "id", "type": "INTEGER"},
                    {"name": "customer_id", "type": "INTEGER"},
                ],
                "primary_keys": ["id"],
                "foreign_keys": [
                    {
                        "constrained_columns": ["customer_id"],
                        "referred_table": "customers",
                        "referred_columns": ["id"],
                    }
                ],
            },
        ],
    }
    
    formatted = service.format_schema_for_prompt(sample_schema)
    assert "Table: `customers`" in formatted
    assert "- `id` (INTEGER) [PK]" in formatted
    assert "- `email` (VARCHAR(100))" in formatted
    assert "Table: `orders`" in formatted
    assert "- `customer_id` -> `customers(id)`" in formatted


def test_glossary_crud_and_ambiguity_flags(temp_glossary):
    conn_id = "test_conn_ecommerce"
    
    # 1. Create a business term
    t1 = temp_glossary.create_term(
        conn_id,
        GlossaryTermCreate(
            term="churned customer",
            definition="Customer without orders in 180 days.",
            target_table="customers",
            target_column="status",
            business_rule="status = 'churned'",
            is_ambiguous=False,
        ),
    )
    assert t1.id.startswith("term_")
    assert t1.term == "churned customer"
    assert t1.is_ambiguous is False
    
    # 2. Create an ambiguous term
    t2 = temp_glossary.create_term(
        conn_id,
        GlossaryTermCreate(
            term="best employee",
            definition="Ambiguous term.",
            is_ambiguous=True,
            disambiguation_hint="Ask user: sales or support?",
        ),
    )
    assert t2.is_ambiguous is True
    assert "sales or support" in (t2.disambiguation_hint or "")
    
    # 3. List terms
    terms = temp_glossary.list_terms(conn_id)
    assert len(terms) == 2
    
    # 4. Update term
    updated = temp_glossary.update_term(
        t1.id,
        GlossaryTermCreate(
            term="churned customer",
            definition="Customer without orders in 365 days (updated).",
            target_table="customers",
            target_column="status",
            business_rule="status = 'churned'",
            is_ambiguous=False,
        ),
    )
    assert updated is not None
    assert "365 days" in updated.definition
    
    # 5. Delete term
    deleted = temp_glossary.delete_term(t2.id)
    assert deleted is True
    assert len(temp_glossary.list_terms(conn_id)) == 1


def test_heuristic_glossary_drafting(temp_glossary):
    schema_data = {
        "tables": [
            {"table_name": "customers", "columns": [{"name": "id"}, {"name": "status"}]},
            {"table_name": "orders", "columns": [{"name": "id"}, {"name": "total_amount"}]},
        ]
    }
    drafts = temp_glossary.generate_heuristic_draft(schema_data)
    terms_dict = {d.term: d for d in drafts}
    
    assert "churned customer" in terms_dict
    assert "gross revenue" in terms_dict
    assert "best employee" in terms_dict
    assert terms_dict["best employee"].is_ambiguous is True
