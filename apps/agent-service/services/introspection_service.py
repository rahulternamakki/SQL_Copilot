"""
Schema Introspection Service for Agent Service.
Fetches, caches, and formats structured database schemas from the MCP server.
"""

import os
import json
import httpx
import logging
from typing import Dict, Any, Optional
from config import settings

logger = logging.getLogger("introspection-service")


class IntrospectionService:
    def __init__(self, cache_dir: Optional[str] = None):
        if not cache_dir:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cache_dir = os.path.join(base_dir, "schema_cache")
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, connection_id: str) -> str:
        return os.path.join(self.cache_dir, f"{connection_id}.json")

    async def get_schema(self, connection_id: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Fetch schema from MCP DB Server or return cached JSON."""
        cache_path = self._get_cache_path(connection_id)
        
        if not force_refresh and os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error reading schema cache: {e}")

        # Fetch live from MCP server
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(
                f"{settings.mcp_server_url}/tools/list_schema",
                json={"connection_id": connection_id},
            )
            if res.status_code != 200:
                raise ValueError(res.json().get("detail", "Failed to introspect schema from MCP server"))
            
            schema_data = res.json()
            
            # Save to disk cache
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(schema_data, f, indent=2)
                
            return schema_data

    def format_schema_for_prompt(self, schema_data: Dict[str, Any]) -> str:
        """Format structured schema JSON into concise markdown for LLM prompt context."""
        tables = schema_data.get("tables", [])
        lines = [f"### Database Schema ({schema_data.get('database_type', 'SQL')})"]
        
        for tbl in tables:
            tbl_name = tbl.get("table_name", "")
            cols = tbl.get("columns", [])
            pks = tbl.get("primary_keys", [])
            fks = tbl.get("foreign_keys", [])
            
            lines.append(f"\n#### Table: `{tbl_name}`")
            col_strs = []
            for col in cols:
                c_name = col.get("name", "")
                c_type = col.get("type", "")
                is_pk = " [PK]" if c_name in pks else ""
                col_strs.append(f"- `{c_name}` ({c_type}){is_pk}")
            lines.extend(col_strs)
            
            if fks:
                lines.append("  Foreign Keys:")
                for fk in fks:
                    c_cols = ", ".join(fk.get("constrained_columns", []))
                    r_tbl = fk.get("referred_table", "")
                    r_cols = ", ".join(fk.get("referred_columns", []))
                    lines.append(f"  - `{c_cols}` -> `{r_tbl}({r_cols})`")
                    
        return "\n".join(lines)


introspection_service = IntrospectionService()
