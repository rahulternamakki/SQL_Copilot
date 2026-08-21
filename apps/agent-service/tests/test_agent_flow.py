"""
Pytest unit tests for Phase 2 Agent Flow (Read Path).
Covers Planner classification, Clarifier interruption, RAG vector retrieval, SQL synthesis, and LangGraph pipeline.
"""

import pytest
from graph.state import AgentState
from graph.nodes.planner import planner_agent
from graph.nodes.clarifier import clarifier_agent
from graph.nodes.sql_generator import sql_generator_agent
from graph.nodes.safety_critic import safety_critic_agent
from graph.workflow import agent_app
from rag.chunker import chunker
from rag.qdrant_store import qdrant_store


def test_planner_classification():
    # Read query
    p_read = planner_agent.classify_and_plan("Which customers haven't placed an order in 90 days?")
    assert p_read.intent == "read"
    assert len(p_read.steps) > 0

    # Ambiguous query (benchmark test case)
    p_ambig = planner_agent.classify_and_plan("Who is our best employee?")
    assert p_ambig.intent == "ambiguous"
    assert p_ambig.ambiguity_reason is not None

    # Write query
    p_write = planner_agent.classify_and_plan("Delete all inactive customers who registered before 2022.")
    assert p_write.intent == "write"


def test_clarifier_formulation():
    clarification = clarifier_agent.formulate_clarification(
        "Who is our best employee?", "Ambiguous metric"
    )
    assert "question" in clarification
    assert "options" in clarification
    assert len(clarification["options"]) >= 2
    assert any("sales" in opt["label"].lower() for opt in clarification["options"])


def test_rag_chunking_and_store():
    conn_id = "test_conn_rag_flow"
    sample_schema = {
        "database_type": "postgresql",
        "tables": [
            {
                "table_name": "customers",
                "columns": [
                    {"name": "id", "type": "INTEGER"},
                    {"name": "email", "type": "VARCHAR(100)"},
                    {"name": "status", "type": "VARCHAR(20)"},
                ],
                "primary_keys": ["id"],
                "foreign_keys": [],
            }
        ],
    }
    sample_glossary = [
        {
            "id": "term_1",
            "term": "churned customer",
            "definition": "Inactive for 180+ days.",
            "business_rule": "status = 'churned'",
            "is_ambiguous": False,
        }
    ]

    s_chunks = chunker.chunk_schema(conn_id, sample_schema)
    g_chunks = chunker.chunk_glossary(conn_id, sample_glossary)
    assert len(s_chunks) >= 1
    assert len(g_chunks) == 1

    # Upsert and search
    qdrant_store.upsert_chunks(conn_id, s_chunks + g_chunks)
    results = qdrant_store.search(conn_id, "churned customer", limit=2)
    assert len(results) > 0


def test_safety_critic_read_validation():
    # Read query
    critique_read = safety_critic_agent.inspect_sql(
        "SELECT id, email FROM customers WHERE status = 'active';", "SELECT"
    )
    assert critique_read.risk_level == "none"
    assert critique_read.is_safe_to_execute_automatically is True
    assert critique_read.requires_user_confirmation is False

    # Mutating query
    critique_write = safety_critic_agent.inspect_sql(
        "DELETE FROM customers WHERE id = 1;", "DELETE"
    )
    assert critique_write.risk_level == "high"
    assert critique_write.requires_user_confirmation is True


def test_end_to_end_read_graph():
    initial_state: AgentState = {
        "connection_id": "conn_ecommerce_demo",
        "user_query": "Which customers haven't placed an order in the last 90 days?",
        "messages": [{"role": "user", "content": "Which customers haven't placed an order in the last 90 days?"}],
        "intent": None,
        "plan_steps": [],
        "clarification_question": None,
        "user_clarification_response": None,
        "retrieved_chunks": [],
        "generated_sql": None,
        "operation_type": None,
        "tables_touched": [],
        "risk_level": None,
        "requires_confirmation": False,
        "plain_language_preview": None,
        "confirmation_token": None,
        "user_confirmed": None,
        "execution_result": None,
        "retry_count": 0,
        "error_message": None,
        "final_summary": None,
    }

    final_state = agent_app.invoke(initial_state)

    assert final_state["intent"] == "read"
    assert final_state["generated_sql"] is not None
    assert "SELECT" in final_state["generated_sql"].upper()
    assert final_state["risk_level"] == "none"
    assert final_state["execution_result"] is not None
    assert final_state["final_summary"] is not None


def test_ambiguous_query_halts_at_clarifier():
    initial_state: AgentState = {
        "connection_id": "conn_ecommerce_demo",
        "user_query": "Who is our best employee?",
        "messages": [{"role": "user", "content": "Who is our best employee?"}],
        "intent": None,
        "plan_steps": [],
        "clarification_question": None,
        "user_clarification_response": None,
        "retrieved_chunks": [],
        "generated_sql": None,
        "operation_type": None,
        "tables_touched": [],
        "risk_level": None,
        "requires_confirmation": False,
        "plain_language_preview": None,
        "confirmation_token": None,
        "user_confirmed": None,
        "execution_result": None,
        "retry_count": 0,
        "error_message": None,
        "final_summary": None,
    }

    final_state = agent_app.invoke(initial_state)

    assert final_state["intent"] == "ambiguous"
    assert final_state["clarification_question"] is not None
    # Crucial safety check: graph halts before generating SQL
    assert final_state["generated_sql"] is None
    assert final_state["execution_result"] is None
