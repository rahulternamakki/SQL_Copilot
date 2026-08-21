"""
Retriever Agent Node for Governed AI Database Copilot.
Performs semantic vector search against Qdrant to retrieve grounded schema and glossary context.
"""

import logging
from typing import Dict, Any, List
from graph.state import AgentState
from rag.qdrant_store import qdrant_store

logger = logging.getLogger("retriever-node")


class RetrieverAgent:
    def retrieve_context(self, connection_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Query Qdrant collection for top-k schema and glossary chunks."""
        chunks = qdrant_store.search(connection_id=connection_id, query=query, limit=limit)
        return chunks


retriever_agent = RetrieverAgent()


def retriever_node(state: AgentState) -> Dict[str, Any]:
    """LangGraph node wrapper for Retriever Agent."""
    connection_id = state.get("connection_id", "conn_ecommerce_demo")
    user_query = state.get("user_query", "")
    
    # If user provided a clarification response, augment the search query
    clarification = state.get("user_clarification_response")
    search_query = f"{user_query} ({clarification})" if clarification else user_query

    chunks = retriever_agent.retrieve_context(connection_id, search_query, limit=5)
    logger.info(f"Retriever retrieved {len(chunks)} grounded chunks for query: '{search_query}'")

    return {
        "retrieved_chunks": chunks,
    }
