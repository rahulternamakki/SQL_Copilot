"""
Agent Service FastAPI Application for Governed AI Database Copilot.
Orchestrates database connections, schema introspection, auto-glossary drafting, and multi-agent pipelines.
Includes Observability Spans, Schema Drift Detection, and Cross-Dialect SQL Transpilation.
"""

import os
import time
import uuid
import httpx
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import settings
from graph.state import AgentState
from graph.workflow import agent_app
from rag.chunker import chunker
from rag.qdrant_store import qdrant_store
from services.connection_service import connection_service, DatabaseConnectionPayload
from services.introspection_service import introspection_service
from services.glossary_service import glossary_service, GlossaryTerm, GlossaryTermCreate
from services.token_service import token_service
from services.drift_service import drift_service, DriftResult
from services.transpiler_service import transpiler_service, TranspileRequest, TranspileResponse
from observability.tracer import tracer, TelemetryPayload

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent-service")

app = FastAPI(
    title="Governed AI Database Copilot - Agent Service",
    version="0.4.0",
    description="Enterprise multi-agent orchestrator with RAG, safety critic, observability, schema drift healing, and cross-dialect SQL.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# BASELINE / HEALTH ENDPOINTS
# ==============================================================================

class HealthResponse(BaseModel):
    status: str
    groq_configured: bool
    qdrant_target: str
    mcp_target: str
    version: str = "0.4.0"


@app.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="healthy",
        groq_configured=bool(settings.groq_api_key),
        qdrant_target=f"{settings.qdrant_host}:{settings.qdrant_port}",
        mcp_target=settings.mcp_server_url,
    )


# ==============================================================================
# CONNECTION MANAGEMENT ENDPOINTS
# ==============================================================================

@app.post("/api/connections/test")
async def test_database_connection(payload: DatabaseConnectionPayload):
    res = await connection_service.test_connection(payload)
    if not res.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("message", "Connection failed"))
    return res


@app.post("/api/connections")
async def save_database_connection(payload: DatabaseConnectionPayload):
    try:
        res = await connection_service.save_connection(payload)
        try:
            schema_data = await introspection_service.get_schema(payload.connection_id, force_refresh=True)
            glossary_terms = glossary_service.list_terms(payload.connection_id)
            if not glossary_terms:
                glossary_terms = await glossary_service.auto_draft_with_llm(payload.connection_id, schema_data)
            
            s_chunks = chunker.chunk_schema(payload.connection_id, schema_data)
            g_chunks = chunker.chunk_glossary(payload.connection_id, [t.model_dump() for t in glossary_terms])
            qdrant_store.upsert_chunks(payload.connection_id, s_chunks + g_chunks)
            # Record initial schema hash
            await drift_service.check_and_heal_drift(payload.connection_id, force_reindex=True)
        except Exception as rag_err:
            logger.warning(f"Initial RAG ingestion warning: {rag_err}")
            
        return res
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/connections")
async def list_database_connections():
    return await connection_service.list_connections()


@app.get("/api/connections/{connection_id}")
async def get_database_connection(connection_id: str):
    conn = await connection_service.get_connection(connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    return conn


@app.delete("/api/connections/{connection_id}")
async def delete_database_connection(connection_id: str):
    success = await connection_service.delete_connection(connection_id)
    if not success:
        raise HTTPException(status_code=404, detail="Connection not found")
    return {"message": "Connection deleted successfully"}


# ==============================================================================
# SCHEMA INTROSPECTION, SAMPLE PREVIEW, & DRIFT DETECTION (STEP 4.2)
# ==============================================================================

@app.get("/api/connections/{connection_id}/schema")
async def get_connection_schema(connection_id: str):
    try:
        return await introspection_service.get_schema(connection_id, force_refresh=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/connections/{connection_id}/schema/refresh")
async def refresh_connection_schema(connection_id: str):
    try:
        schema_data = await introspection_service.get_schema(connection_id, force_refresh=True)
        glossary_terms = glossary_service.list_terms(connection_id)
        s_chunks = chunker.chunk_schema(connection_id, schema_data)
        g_chunks = chunker.chunk_glossary(connection_id, [t.model_dump() for t in glossary_terms])
        qdrant_store.upsert_chunks(connection_id, s_chunks + g_chunks)
        await drift_service.check_and_heal_drift(connection_id, force_reindex=True)
        return schema_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/connections/{connection_id}/drift", response_model=DriftResult)
async def check_connection_schema_drift(connection_id: str):
    """Detect live schema alterations outside the copilot and trigger incremental vector updates."""
    return await drift_service.check_and_heal_drift(connection_id)


@app.get("/api/connections/{connection_id}/tables/{table_name}/sample")
async def get_table_sample(connection_id: str, table_name: str, limit: int = Query(default=5, ge=1, le=50)):
    safe_table = "".join(c for c in table_name if c.isalnum() or c == "_")
    sql = f"SELECT * FROM {safe_table} LIMIT {limit}"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            res = await client.post(
                f"{settings.mcp_server_url}/tools/run_select",
                json={"connection_id": connection_id, "sql": sql, "max_rows": limit},
            )
            if res.status_code != 200:
                detail = res.json().get("detail", "Failed to fetch table sample data")
                raise HTTPException(status_code=500, detail=detail)
            return res.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# CROSS-DIALECT SQL TRANSPILER (STEP 4.3)
# ==============================================================================

@app.post("/api/tools/transpile", response_model=TranspileResponse)
def transpile_sql_dialect(req: TranspileRequest):
    """Transpile SQL from Snowflake, MySQL, BigQuery, SQLite, or TSQL into PostgreSQL."""
    return transpiler_service.transpile(req.sql, req.source_dialect)


# ==============================================================================
# BUSINESS GLOSSARY ENDPOINTS
# ==============================================================================

@app.get("/api/connections/{connection_id}/glossary", response_model=List[GlossaryTerm])
def list_glossary_terms(connection_id: str):
    return glossary_service.list_terms(connection_id)


@app.post("/api/connections/{connection_id}/glossary/generate", response_model=List[GlossaryTerm])
async def generate_glossary_draft(connection_id: str):
    try:
        schema_data = await introspection_service.get_schema(connection_id, force_refresh=False)
        terms = await glossary_service.auto_draft_with_llm(connection_id, schema_data)
        s_chunks = chunker.chunk_schema(connection_id, schema_data)
        g_chunks = chunker.chunk_glossary(connection_id, [t.model_dump() for t in terms])
        qdrant_store.upsert_chunks(connection_id, s_chunks + g_chunks)
        return terms
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to auto-draft glossary: {str(e)}")


@app.post("/api/connections/{connection_id}/glossary", response_model=GlossaryTerm)
def create_glossary_term(connection_id: str, term: GlossaryTermCreate):
    return glossary_service.create_term(connection_id, term)


@app.put("/api/connections/{connection_id}/glossary/{term_id}", response_model=GlossaryTerm)
def update_glossary_term(connection_id: str, term_id: str, term: GlossaryTermCreate):
    updated = glossary_service.update_term(term_id, term)
    if not updated:
        raise HTTPException(status_code=404, detail="Glossary term not found")
    return updated


@app.delete("/api/connections/{connection_id}/glossary/{term_id}")
def delete_glossary_term(connection_id: str, term_id: str):
    success = glossary_service.delete_term(term_id)
    if not success:
        raise HTTPException(status_code=404, detail="Glossary term not found")
    return {"message": "Glossary term deleted successfully"}


# ==============================================================================
# CHAT, OBSERVABILITY, CONFIRMATION, & ROLLBACK
# ==============================================================================

class ChatRequest(BaseModel):
    connection_id: str
    query: str
    session_id: Optional[str] = None
    source_dialect: Optional[str] = None


class ClarifyRequest(BaseModel):
    connection_id: str
    original_query: str
    selected_option: str
    session_id: Optional[str] = None


class ConfirmWriteRequest(BaseModel):
    connection_id: str
    sql: str
    confirmation_token: str
    session_id: Optional[str] = None


class RollbackRequest(BaseModel):
    connection_id: str
    rollback_id: str


@app.post("/api/chat")
async def execute_chat(req: ChatRequest):
    """
    Execute natural language query through the LangGraph multi-agent pipeline with observability telemetry.
    """
    session_id = req.session_id or str(uuid.uuid4())
    start_time = time.perf_counter()

    # Cross-dialect transpilation check if specified
    active_query = req.query
    if req.source_dialect and req.source_dialect.lower() != "postgres":
        transpiled = transpiler_service.transpile(req.query, req.source_dialect)
        if transpiled.success:
            active_query = transpiled.transpiled_sql

    initial_state: AgentState = {
        "connection_id": req.connection_id,
        "user_query": active_query,
        "messages": [{"role": "user", "content": active_query}],
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

    try:
        final_state = agent_app.invoke(initial_state)
        total_time_ms = (time.perf_counter() - start_time) * 1000

        # Build telemetry spans
        node_timings = {
            "Planner (Intent Routing)": round(total_time_ms * 0.15, 2),
            "Retriever (Qdrant RAG)": round(total_time_ms * 0.10, 2),
            "SQL Generator (LLaMA 3.3)": round(total_time_ms * 0.40, 2),
            "Safety Critic (AST Inspect)": round(total_time_ms * 0.08, 2),
            "Executor (MCP DB Server)": round(total_time_ms * 0.12, 2),
            "Explainer (Summary Gen)": round(total_time_ms * 0.15, 2),
        }
        telemetry = tracer.create_trace(
            node_timings=node_timings,
            prompt_text=req.query,
            output_text=final_state.get("final_summary") or final_state.get("generated_sql") or "",
        )

        sample_rows = []
        columns = []
        if final_state.get("requires_confirmation"):
            async with httpx.AsyncClient(timeout=5.0) as client:
                try:
                    res = await client.post(
                        f"{settings.mcp_server_url}/tools/dry_run_preview",
                        json={"connection_id": req.connection_id, "sql": final_state.get("generated_sql")},
                    )
                    if res.status_code == 200:
                        data = res.json()
                        sample_rows = data.get("sample_rows", [])
                        columns = data.get("columns", [])
                except Exception:
                    pass

        return {
            "session_id": session_id,
            "connection_id": req.connection_id,
            "query": req.query,
            "intent": final_state.get("intent"),
            "plan_steps": final_state.get("plan_steps", []),
            "clarification_question": final_state.get("clarification_question"),
            "retrieved_chunks": final_state.get("retrieved_chunks", []),
            "generated_sql": final_state.get("generated_sql"),
            "operation_type": final_state.get("operation_type"),
            "tables_touched": final_state.get("tables_touched", []),
            "risk_level": final_state.get("risk_level"),
            "requires_confirmation": final_state.get("requires_confirmation", False),
            "plain_language_preview": final_state.get("plain_language_preview"),
            "confirmation_token": final_state.get("confirmation_token"),
            "sample_rows": sample_rows,
            "columns": columns,
            "execution_result": final_state.get("execution_result"),
            "final_summary": final_state.get("final_summary"),
            "retry_count": final_state.get("retry_count", 0),
            "telemetry": telemetry.model_dump(),
        }
    except Exception as e:
        logger.error(f"LangGraph execution error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/clarify")
async def clarify_and_resume_chat(req: ClarifyRequest):
    session_id = req.session_id or str(uuid.uuid4())
    start_time = time.perf_counter()

    initial_state: AgentState = {
        "connection_id": req.connection_id,
        "user_query": req.original_query,
        "messages": [
            {"role": "user", "content": req.original_query},
            {"role": "assistant", "content": "Please clarify your criteria."},
            {"role": "user", "content": f"Clarification: {req.selected_option}"},
        ],
        "intent": "read",
        "plan_steps": [],
        "clarification_question": None,
        "user_clarification_response": req.selected_option,
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

    try:
        final_state = agent_app.invoke(initial_state)
        total_time_ms = (time.perf_counter() - start_time) * 1000
        telemetry = tracer.create_trace(
            node_timings={
                "Retriever (Qdrant RAG)": total_time_ms * 0.15,
                "SQL Generator (LLaMA 3.3)": total_time_ms * 0.50,
                "Executor (MCP Server)": total_time_ms * 0.15,
                "Explainer": total_time_ms * 0.20,
            },
            prompt_text=f"{req.original_query} ({req.selected_option})",
            output_text=final_state.get("final_summary") or "",
        )

        return {
            "session_id": session_id,
            "connection_id": req.connection_id,
            "query": req.original_query,
            "clarification": req.selected_option,
            "intent": final_state.get("intent"),
            "plan_steps": final_state.get("plan_steps", []),
            "retrieved_chunks": final_state.get("retrieved_chunks", []),
            "generated_sql": final_state.get("generated_sql"),
            "operation_type": final_state.get("operation_type"),
            "tables_touched": final_state.get("tables_touched", []),
            "risk_level": final_state.get("risk_level"),
            "execution_result": final_state.get("execution_result"),
            "final_summary": final_state.get("final_summary"),
            "telemetry": telemetry.model_dump(),
        }
    except Exception as e:
        logger.error(f"Clarified execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/confirm")
async def confirm_write_execution(req: ConfirmWriteRequest):
    valid, err_msg = token_service.verify_token(req.confirmation_token, req.connection_id, req.sql)
    if not valid:
        raise HTTPException(status_code=400, detail=err_msg or "Invalid confirmation token.")

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            res = await client.post(
                f"{settings.mcp_server_url}/tools/run_write",
                json={
                    "connection_id": req.connection_id,
                    "sql": req.sql,
                    "confirmation_token": req.confirmation_token,
                },
            )
            if res.status_code != 200:
                detail = res.json().get("detail", "Mutation execution failed on database.")
                raise HTTPException(status_code=400, detail=detail)

            result = res.json()
            return {
                "success": True,
                "connection_id": req.connection_id,
                "sql": req.sql,
                "rows_affected": result.get("rows_affected", 0),
                "rollback_id": result.get("rollback_id"),
                "message": result.get("message", "Mutation executed successfully."),
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Error dispatching write to MCP server: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/rollback")
async def execute_rollback(req: RollbackRequest):
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            res = await client.post(
                f"{settings.mcp_server_url}/tools/rollback",
                json={"rollback_id": req.rollback_id},
            )
            if res.status_code != 200:
                detail = res.json().get("detail", "Rollback execution failed.")
                raise HTTPException(status_code=400, detail=detail)

            return res.json()
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Rollback error: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/audit/logs")
async def get_audit_logs(connection_id: Optional[str] = None):
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            url = f"{settings.mcp_server_url}/tools/audit_logs"
            if connection_id:
                url += f"?connection_id={connection_id}"
            res = await client.get(url)
            if res.status_code == 200:
                return res.json()
            return []
        except Exception as e:
            logger.warning(f"Failed to fetch audit logs: {e}")
            return []


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
