"""
Pytest unit tests for Phase 4 Hardening, Observability, Schema Drift, and SQL Transpiler.
"""

import pytest
from observability.tracer import tracer, AgentTracer
from services.drift_service import drift_service, SchemaDriftService
from services.transpiler_service import transpiler_service


def test_tracer_telemetry():
    timings = {
        "Planner": 42.5,
        "Retriever": 18.2,
        "SQL Generator": 180.4,
        "Safety Critic": 12.1,
    }
    prompt = "Which customers haven't placed an order in the last 90 days?"
    output = "Found 4 matching customer records."

    telemetry = tracer.create_trace(timings, prompt, output)

    assert telemetry.total_latency_ms > 200.0
    assert telemetry.total_tokens > 0
    assert telemetry.estimated_cost_usd >= 0.0
    assert len(telemetry.spans) == 4
    assert telemetry.spans[0].node_name == "Planner"


def test_schema_drift_hashing():
    service = SchemaDriftService()
    schema_v1 = {
        "tables": [
            {
                "table_name": "customers",
                "columns": [{"name": "id", "type": "INT", "nullable": False}],
                "primary_keys": ["id"],
                "foreign_keys": [],
            }
        ]
    }
    schema_v2 = {
        "tables": [
            {
                "table_name": "customers",
                "columns": [
                    {"name": "id", "type": "INT", "nullable": False},
                    {"name": "phone_number", "type": "VARCHAR(20)", "nullable": True},
                ],
                "primary_keys": ["id"],
                "foreign_keys": [],
            }
        ]
    }

    hash_v1 = service.compute_schema_hash(schema_v1)
    hash_v2 = service.compute_schema_hash(schema_v2)

    assert hash_v1 != hash_v2
    assert len(hash_v1) == 64  # SHA-256 length


def test_sql_transpiler_dialects():
    # 1. Snowflake Dialect
    snowflake_sql = "SELECT * FROM orders WHERE DATEADD('day', -30, CURRENT_TIMESTAMP()) < order_date;"
    res_sf = transpiler_service.transpile(snowflake_sql, "snowflake")
    assert res_sf.success is True
    assert res_sf.target_dialect == "postgres"

    # 2. MySQL Dialect
    mysql_sql = "SELECT IFNULL(discount_percent, 0) FROM order_items;"
    res_my = transpiler_service.transpile(mysql_sql, "mysql")
    assert res_my.success is True
    assert "COALESCE" in res_my.transpiled_sql.upper() or "IFNULL" in res_my.transpiled_sql.upper()

    # 3. BigQuery Dialect
    bq_sql = "SELECT TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY);"
    res_bq = transpiler_service.transpile(bq_sql, "bigquery")
    assert res_bq.success is True
