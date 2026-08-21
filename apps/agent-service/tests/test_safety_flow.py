"""
Pytest unit tests for Phase 3 Safety Critic, HMAC Confirmation Tokens, and Write Halt.
"""

import time
import pytest
from services.token_service import TokenService
from graph.nodes.safety_critic import safety_critic_agent
from graph.workflow import agent_app
from graph.state import AgentState


def test_token_service_lifecycle():
    service = TokenService(secret="test-secret-key-123", ttl_seconds=2)
    conn_id = "conn_ecommerce_demo"
    sql = "DELETE FROM customers WHERE id = 5;"

    # Issue token
    token = service.issue_token(conn_id, sql)
    assert token is not None
    assert len(token.split(".")) == 3

    # Verify valid token
    valid, err = service.verify_token(token, conn_id, sql)
    assert valid is True
    assert err is None

    # Mismatched SQL or connection_id fails
    valid_mismatch, err_mismatch = service.verify_token(token, conn_id, "DELETE FROM orders;")
    assert valid_mismatch is False

    # Expired token fails
    time.sleep(2.1)
    valid_expired, err_expired = service.verify_token(token, conn_id, sql)
    assert valid_expired is False
    assert "expired" in err_expired.lower()


def test_safety_critic_destructive_inspection():
    conn_id = "conn_ecommerce_demo"
    sql = "DELETE FROM customers WHERE status = 'inactive' AND created_at < '2022-01-01';"
    
    critique = safety_critic_agent.inspect_sql(conn_id, sql, "DELETE")

    assert critique["risk_level"] == "high"
    assert critique["requires_user_confirmation"] is True
    assert critique["confirmation_token"] is not None
    assert "DELETE" in critique["plain_language_preview"]


def test_destructive_write_halts_in_langgraph():
    initial_state: AgentState = {
        "connection_id": "conn_ecommerce_demo",
        "user_query": "Delete all inactive customer accounts who registered before 2022.",
        "messages": [{"role": "user", "content": "Delete all inactive customer accounts who registered before 2022."}],
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

    assert final_state["intent"] == "write"
    assert final_state["requires_confirmation"] is True
    assert final_state["confirmation_token"] is not None
    assert final_state["risk_level"] == "high"
    # Essential safety guarantee: execution_result is None until human confirmed
    assert final_state["execution_result"] is None
