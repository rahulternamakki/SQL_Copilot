"""
Agent Service FastAPI Application for Governed AI Database Copilot.
Orchestrates database connections, schema introspection, auto-glossary drafting, and multi-agent pipelines.
"""

import os
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent-service")

app = FastAPI(
    title="Governed AI Database Copilot - Agent Service",
    version="0.2.0",
    description="Multi-agent orchestrator with RAG grounding, safety critic, and MCP isolation.",
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
    version: str = "0.2.0"


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check verifying configuration readiness."""
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
    """Test connection reachability via MCP DB Server before saving."""
    res = await connection_service.test_connection(payload)
    if not res.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("message", "Connection failed"))
    return res


@app.post("/api/connections")
async def save_database_connection(payload: DatabaseConnectionPayload):
    """Save encrypted database credentials in vault and trigger RAG ingestion."""
    try:
        res = await connection_service.save_connection(payload)
        # Background RAG ingestion
        try:
            schema_data = await introspection_service.get_schema(payload.connection_id, force_refresh=True)
            glossary_terms = glossary_service.list_terms(payload.connection_id)
            if not glossary_terms:
                glossary_terms = await glossary_service.auto_draft_with_llm(payload.connection_id, schema_data)
            
            s_chunks = chunker.chunk_schema(payload.connection_id, schema_data)
            g_chunks = chunker.chunk_glossary(payload.connection_id, [t.model_dump() for t in glossary_terms])
            qdrant_store.upsert_chunks(payload.connection_id, s_chunks + g_chunks)
        except Exception as rag_err:
            logger.warning(f"Initial RAG ingestion warning: {rag_err}")
            
        return res
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/connections")
async def list_database_connections():
    """List all registered database connections with passwords masked."""
    return await connection_service.list_connections()


@app.get("/api/connections/{connection_id}")
async def get_database_connection(connection_id: str):
    """Get single connection metadata."""
    conn = await connection_service.get_connection(connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    return conn


@app.delete("/api/connections/{connection_id}")
async def delete_database_connection(connection_id: str):
    """Delete connection from vault."""
    success = await connection_service.delete_connection(connection_id)
    if not success:
        raise HTTPException(status_code=404, detail="Connection not found")
    return {"message": "Connection deleted successfully"}


# ==============================================================================
# SCHEMA INTROSPECTION & SAMPLE DATA ENDPOINTS
# ==============================================================================

@app.get("/api/connections/{connection_id}/schema")
async def get_connection_schema(connection_id: str):
    """Retrieve structured database schema JSON (cached or live)."""
    try:
        return await introspection_service.get_schema(connection_id, force_refresh=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/connections/{connection_id}/schema/refresh")
async def refresh_connection_schema(connection_id: str):
    """Force re-introspection of live database schema and re-index RAG."""
    try:
        schema_data = await introspection_service.get_schema(connection_id, force_refresh=True)
        glossary_terms = glossary_service.list_terms(connection_id)
        s_chunks = chunker.chunk_schema(connection_id, schema_data)
        g_chunks = chunker.chunk_glossary(connection_id, [t.model_dump() for t in glossary_terms])
        qdrant_store.upsert_chunks(connection_id, s_chunks + g_chunks)
        return schema_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/connections/{connection_id}/tables/{table_name}/sample")
async def get_table_sample(connection_id: str, table_name: str, limit: int = Query(default=5, ge=1, le=50)):
    """Fetch sample rows from a table using AST-verified read-only select."""
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
# RAG INDEXING ENDPOINT
# ==============================================================================

@app.post("/api/connections/{connection_id}/rag/ingest")
async def ingest_connection_rag(connection_id: str):
    """Manually trigger RAG chunking and Qdrant vector indexing."""
    try:
        schema_data = await introspection_service.get_schema(connection_id, force_refresh=False)
        glossary_terms = glossary_service.list_terms(connection_id)
        if not glossary_terms:
            glossary_terms = await glossary_service.auto_draft_with_llm(connection_id, schema_data)
        
        s_chunks = chunker.chunk_schema(connection_id, schema_data)
        g_chunks = chunker.chunk_glossary(connection_id, [t.model_dump() for t in glossary_terms])
        qdrant_store.upsert_chunks(connection_id, s_chunks + g_chunks)
        return {
            "success": True,
            "schema_chunks_indexed": len(s_chunks),
            "glossary_chunks_indexed": len(g_chunks),
            "total_chunks": len(s_chunks) + len(g_chunks),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# BUSINESS GLOSSARY ENDPOINTS
# ==============================================================================

@app.get("/api/connections/{connection_id}/glossary", response_model=List[GlossaryTerm])
def list_glossary_terms(connection_id: str):
    """List all glossary terms configured for a connection."""
    return glossary_service.list_terms(connection_id)


@app.post("/api/connections/{connection_id}/glossary/generate", response_model=List[GlossaryTerm])
async def generate_glossary_draft(connection_id: str):
    """Trigger Groq LLM to analyze schema and draft business definitions and ambiguous terms."""
    try:
        schema_data = await introspection_service.get_schema(connection_id, force_refresh=False)
        terms = await glossary_service.auto_draft_with_llm(connection_id, schema_data)
        # Update RAG store
        s_chunks = chunker.chunk_schema(connection_id, schema_data)
        g_chunks = chunker.chunk_glossary(connection_id, [t.model_dump() for t in terms])
        qdrant_store.upsert_chunks(connection_id, s_chunks + g_chunks)
        return terms
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to auto-draft glossary: {str(e)}")


@app.post("/api/connections/{connection_id}/glossary", response_model=GlossaryTerm)
def create_glossary_term(connection_id: str, term: GlossaryTermCreate):
    """Create a new manual glossary term."""
    return glossary_service.create_term(connection_id, term)


@app.put("/api/connections/{connection_id}/glossary/{term_id}", response_model=GlossaryTerm)
def update_glossary_term(connection_id: str, term_id: str, term: GlossaryTermCreate):
    """Update an existing glossary term."""
    updated = glossary_service.update_term(term_id, term)
    if not updated:
        raise HTTPException(status_code=404, detail="Glossary term not found")
    return updated


@app.delete("/api/connections/{connection_id}/glossary/{term_id}")
def delete_glossary_term(connection_id: str, term_id: str):
    """Delete a glossary term."""
    success = glossary_service.delete_term(term_id)
    if not success:
        raise HTTPException(status_code=404, detail="Glossary term not found")
    return {"message": "Glossary term deleted successfully"}


# ==============================================================================
# CHAT & MULTI-AGENT EXECUTION ENDPOINTS
# ==============================================================================

class ChatRequest(BaseModel):
    connection_id: str
    query: str
    session_id: Optional[str] = None


class ClarifyRequest(BaseModel):
    connection_id: str
    original_query: str
    selected_option: str
    session_id: Optional[str] = None


@app.post("/api/chat")
async def execute_chat(req: ChatRequest):
    """
    Execute natural language query through the LangGraph multi-agent pipeline.
    """
    session_id = req.session_id or str(uuid.uuid4())
    logger.info(f"Executing chat workflow for connection '{req.connection_id}', query: '{req.query}'")

    # Ensure schema & glossary are indexed in RAG
    try:
        if not qdrant_store.search(req.connection_id, "test", limit=1):
            schema_data = await introspection_service.get_schema(req.connection_id, force_refresh=False)
            glossary_terms = glossary_service.list_terms(req.connection_id)
            if not glossary_terms:
                glossary_terms = glossary_service.generate_heuristic_draft(schema_data)
            s_chunks = chunker.chunk_schema(req.connection_id, schema_data)
            g_chunks = chunker.chunk_glossary(req.connection_id, [t.model_dump() if hasattr(t, "model_dump") else t for t in glossary_terms])
            qdrant_store.upsert_chunks(req.connection_id, s_chunks + g_chunks)
    except Exception as e:
        logger.warning(f"RAG pre-check warning: {e}")

    # Build initial AgentState
    initial_state: AgentState = {
        "connection_id": req.connection_id,
        "user_query": req.query,
        "messages": [{"role": "user", "content": req.query}],
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

    # Execute LangGraph
    try:
        final_state = agent_app.invoke(initial_state)
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
            "execution_result": final_state.get("execution_result"),
            "final_summary": final_state.get("final_summary"),
            "retry_count": final_state.get("retry_count", 0),
        }
    except Exception as e:
        logger.error(f"LangGraph execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/clarify")
async def clarify_and_resume_chat(req: ClarifyRequest):
    """
    Resume agent workflow following user clarification response.
    """
    session_id = req.session_id or str(uuid.uuid4())
    logger.info(f"Resuming query '{req.original_query}' with user clarification '{req.selected_option}'")

    initial_state: AgentState = {
        "connection_id": req.connection_id,
        "user_query": req.original_query,
        "messages": [
            {"role": "user", "content": req.original_query},
            {"role": "assistant", "content": "Please clarify your criteria."},
            {"role": "user", "content": f"Clarification: {req.selected_option}"},
        ],
        "intent": "read",  # Resolved to read intent
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
        }
    except Exception as e:
        logger.error(f"Clarified execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
