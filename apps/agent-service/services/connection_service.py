"""
Connection Service for Agent Service.
Orchestrates communication with the MCP DB Server for database connection management.
"""

import httpx
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from config import settings

logger = logging.getLogger("connection-service")


class DatabaseConnectionPayload(BaseModel):
    connection_id: str
    display_name: str
    db_type: str = "postgresql"
    host: str
    port: int = 5432
    database: str
    username: str
    password: str
    ssl_mode: str = "prefer"
    read_only: bool = True


class ConnectionService:
    def __init__(self, mcp_url: Optional[str] = None):
        self.mcp_url = mcp_url or settings.mcp_server_url

    async def test_connection(self, payload: DatabaseConnectionPayload) -> Dict[str, Any]:
        """Test database connection via MCP DB Server."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                res = await client.post(
                    f"{self.mcp_url}/tools/test_connection",
                    json=payload.model_dump(),
                )
                if res.status_code == 404:
                    res = await client.post(
                        f"{self.mcp_url}/connections/test",
                        json=payload.model_dump(),
                    )
                if res.status_code == 200:
                    data = res.json()
                    if isinstance(data, dict) and data.get("success") is False:
                        return data
                    return {"success": True, "message": data.get("message", "Connection successful!")}
                else:
                    detail = res.json().get("detail", res.text)
                    return {"success": False, "message": detail}
            except Exception as e:
                logger.error(f"Failed to test connection: {e}")
                return {"success": False, "message": f"Connection failed: {str(e)}"}

    async def save_connection(self, payload: DatabaseConnectionPayload) -> Dict[str, Any]:
        """Save encrypted connection in vault via MCP DB Server."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                f"{self.mcp_url}/connections",
                json=payload.model_dump(),
            )
            if res.status_code != 200:
                raise ValueError(res.json().get("detail", "Failed to save connection"))
            return res.json()

    async def list_connections(self) -> List[Dict[str, Any]]:
        """List stored database connections."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                res = await client.get(f"{self.mcp_url}/connections")
                if res.status_code == 200:
                    return res.json()
                return []
            except Exception as e:
                logger.warning(f"Could not connect to MCP server: {e}")
                return []

    async def get_connection(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get connection details."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(f"{self.mcp_url}/connections/{connection_id}")
            if res.status_code == 200:
                return res.json()
            return None

    async def delete_connection(self, connection_id: str) -> bool:
        """Delete connection from vault."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.delete(f"{self.mcp_url}/connections/{connection_id}")
            return res.status_code == 200


connection_service = ConnectionService()
