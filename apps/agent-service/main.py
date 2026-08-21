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
from services.connection_service import connection_service, DatabaseConnectionPayload
from services.introspection_service import introspection_service
from services.glossary_service import glossary_service, GlossaryTerm, GlossaryTermCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent-service")

app = FastAPI(
    title="Governed AI Database Copilot - Agent Service",
    version="0.1.0",
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
    version: str = "0.1.0"


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
    """Save encrypted database credentials in vault via MCP DB Server."""
    try:
        res = await connection_service.save_connection(payload)
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
    """Force re-introspection of live database schema."""
    try:
        return await introspection_service.get_schema(connection_id, force_refresh=True)
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
        return await glossary_service.auto_draft_with_llm(connection_id, schema_data)
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
# CHAT / AGENT ENDPOINTS (PREVIEW / FOUNDATION)
# ==============================================================================

class ChatRequest(BaseModel):
    connection_id: str
    query: str
    session_id: Optional[str] = None


@app.post("/api/chat")
async def start_chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())
    logger.info(f"Received chat query for connection '{req.connection_id}', session '{session_id}'")
    return {
        "session_id": session_id,
        "status": "ready_for_phase_2",
        "query": req.query,
        "connection_id": req.connection_id,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
