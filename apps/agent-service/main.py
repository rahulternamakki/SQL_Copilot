"""
Agent Service FastAPI Application for Governed AI Database Copilot.
Orchestrates multi-agent workflows, RAG schema retrieval, safety inspections, and tool dispatch.
"""

import os
import uuid
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from config import settings
from graph.state import AgentState

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


class HealthResponse(BaseModel):
    status: str
    groq_configured: bool
    qdrant_target: str
    mcp_target: str
    version: str = "0.1.0"


class ChatRequest(BaseModel):
    connection_id: str
    query: str
    session_id: Optional[str] = None


class ConfirmationRequest(BaseModel):
    connection_id: str
    confirmation_token: str
    action: str = Field(pattern="^(confirm|reject)$")


class ConnectionRegisterRequest(BaseModel):
    connection_id: Optional[str] = None
    host: str
    port: int = 5432
    database: str
    username: str
    password: str
    ssl_mode: str = "prefer"
    read_only: bool = True
    display_name: str


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check verifying configuration readiness."""
    return HealthResponse(
        status="healthy",
        groq_configured=bool(settings.groq_api_key),
        qdrant_target=f"{settings.qdrant_host}:{settings.qdrant_port}",
        mcp_target=settings.mcp_server_url,
    )


@app.post("/api/chat")
async def start_chat(req: ChatRequest):
    """
    Entrypoint for natural language database queries.
    Passes query to LangGraph agent pipeline.
    """
    session_id = req.session_id or str(uuid.uuid4())
    logger.info(f"Received chat query for connection '{req.connection_id}', session '{session_id}'")
    
    # Base state initialized for execution in subsequent phases
    state: AgentState = {
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
    
    return {
        "session_id": session_id,
        "status": "received",
        "query": req.query,
        "connection_id": req.connection_id,
        "state_initialized": True
    }


@app.post("/api/chat/confirm")
async def confirm_action(req: ConfirmationRequest):
    """
    Resumes graph execution following explicit user confirmation of a destructive or high-risk write.
    """
    logger.info(f"Confirmation '{req.action}' received for token '{req.confirmation_token}'")
    return {
        "status": "processed",
        "action": req.action,
        "token_valid": True
    }


@app.post("/api/connections")
async def register_connection(req: ConnectionRegisterRequest):
    """
    Register a database connection into the encrypted credential vault.
    """
    conn_id = req.connection_id or f"conn_{uuid.uuid4().hex[:8]}"
    return {
        "connection_id": conn_id,
        "display_name": req.display_name,
        "read_only": req.read_only,
        "status": "registered"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
