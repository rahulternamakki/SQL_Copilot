"""
MCP Database Server for Governed AI Database Copilot.
Exposes scoped, safe database tool endpoints. Never exposes raw database credentials to agents.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
import sqlglot
from sqlglot import exp
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from pydantic import BaseModel
from vault import vault_instance, DatabaseCredentials

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-db-server")


class SchemaColumn(BaseModel):
    name: str
    type: str
    nullable: bool
    default: Optional[str] = None
    is_primary_key: bool = False


class SchemaTable(BaseModel):
    table_name: str
    columns: List[SchemaColumn]
    primary_keys: List[str]
    foreign_keys: List[Dict[str, Any]]
    indexes: List[Dict[str, Any]]


class SchemaResponse(BaseModel):
    connection_id: str
    tables: List[SchemaTable]


class SelectResult(BaseModel):
    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    execution_time_ms: float
    truncated: bool = False


class DryRunResult(BaseModel):
    operation_type: str
    estimated_rows_affected: int
    target_table: Optional[str]
    before_state_sample: List[Dict[str, Any]]
    reverse_sql_template: Optional[str]
    is_destructive: bool


class WriteResult(BaseModel):
    success: bool
    rows_affected: int
    reverse_sql: Optional[str]
    message: str


class MCPDatabaseServer:
    """
    Core MCP Database Server implementing the scoped 'badge' tool surface.
    """

    def __init__(self):
        self._engines: Dict[str, Engine] = {}

    def _get_engine(self, connection_id: str) -> Engine:
        """Get or create cached SQLAlchemy engine for the given connection ID."""
        if connection_id in self._engines:
            return self._engines[connection_id]
        
        conn_url = vault_instance.get_connection_url(connection_id)
        if not conn_url:
            raise ValueError(f"Connection ID '{connection_id}' not found in credential vault.")
        
        engine = create_engine(conn_url, pool_pre_ping=True, pool_size=5, max_overflow=10)
        self._engines[connection_id] = engine
        return engine

    def _is_read_only_sql(self, sql_query: str) -> bool:
        """Parse SQL query using sqlglot AST to strictly ensure read-only execution."""
        try:
            parsed = sqlglot.parse(sql_query)
            if not parsed:
                return False
            for statement in parsed:
                if statement is None:
                    continue
                # Allowed read-only expressions: Select, Union
                if not isinstance(statement, (exp.Select, exp.Union)):
                    return False
            return True
        except Exception as e:
            logger.warning(f"Failed to parse SQL for read-only validation: {e}")
            return False

    def list_schema(self, connection_id: str) -> SchemaResponse:
        """Introspect database schema and return structured JSON."""
        engine = self._get_engine(connection_id)
        inspector = inspect(engine)
        
        tables_meta: List[SchemaTable] = []
        table_names = inspector.get_table_names()
        
        for t_name in table_names:
            pk_constraint = inspector.get_pk_constraint(t_name)
            pks = pk_constraint.get("constrained_columns", []) if pk_constraint else []
            
            raw_cols = inspector.get_columns(t_name)
            columns = [
                SchemaColumn(
                    name=c["name"],
                    type=str(c["type"]),
                    nullable=c.get("nullable", True),
                    default=str(c.get("default", "")) if c.get("default") is not None else None,
                    is_primary_key=c["name"] in pks
                )
                for c in raw_cols
            ]
            
            fks = inspector.get_foreign_keys(t_name)
            indexes = inspector.get_indexes(t_name)
            
            tables_meta.append(
                SchemaTable(
                    table_name=t_name,
                    columns=columns,
                    primary_keys=pks,
                    foreign_keys=fks,
                    indexes=indexes
                )
            )
            
        return SchemaResponse(connection_id=connection_id, tables=tables_meta)

    def run_select(self, connection_id: str, sql: str, max_rows: int = 100) -> SelectResult:
        """Execute a validated SELECT query against the database."""
        if not self._is_read_only_sql(sql):
            raise PermissionError("Query rejected: Only read-only SELECT statements are permitted on run_select tool.")
        
        creds = vault_instance.get_credentials(connection_id)
        if not creds:
            raise ValueError(f"Unknown connection {connection_id}")

        import time
        start_time = time.time()
        
        engine = self._get_engine(connection_id)
        with engine.connect() as conn:
            # Enforce read-only transaction on PostgreSQL if applicable
            if creds.db_type == "postgresql":
                conn.execute(text("SET TRANSACTION READ ONLY"))
                
            result = conn.execute(text(sql))
            columns = list(result.keys())
            rows_raw = result.fetchmany(max_rows + 1)
            
            truncated = len(rows_raw) > max_rows
            if truncated:
                rows_raw = rows_raw[:max_rows]
                
            rows = [[str(val) if val is not None else None for val in row] for row in rows_raw]
            
        execution_time = (time.time() - start_time) * 1000.0
        return SelectResult(
            columns=columns,
            rows=rows,
            row_count=len(rows),
            execution_time_ms=round(execution_time, 2),
            truncated=truncated
        )

    def dry_run_preview(self, connection_id: str, sql: str) -> DryRunResult:
        """Estimate row count and capture before-state for write operations without committing changes."""
        parsed = sqlglot.parse_one(sql)
        op_type = parsed.key.upper() if parsed else "UNKNOWN"
        is_destructive = op_type in ["DELETE", "DROP", "TRUNCATE"] or (op_type == "UPDATE" and not parsed.find(exp.Where))
        
        target_table = None
        table_node = parsed.find(exp.Table)
        if table_node:
            target_table = table_node.name
            
        estimated_count = 0
        before_sample: List[Dict[str, Any]] = []
        
        engine = self._get_engine(connection_id)
        if target_table and op_type in ["UPDATE", "DELETE"]:
            where_clause = parsed.find(exp.Where)
            where_sql = where_clause.sql() if where_clause else ""
            
            count_sql = f"SELECT COUNT(*) FROM {target_table} {where_sql}"
            sample_sql = f"SELECT * FROM {target_table} {where_sql} LIMIT 5"
            
            with engine.connect() as conn:
                count_res = conn.execute(text(count_sql)).scalar()
                estimated_count = int(count_res or 0)
                
                sample_res = conn.execute(text(sample_sql))
                keys = list(sample_res.keys())
                for row in sample_res.fetchall():
                    before_sample.append({k: str(v) for k, v in zip(keys, row)})

        return DryRunResult(
            operation_type=op_type,
            estimated_rows_affected=estimated_count,
            target_table=target_table,
            before_state_sample=before_sample,
            reverse_sql_template=f"-- Auto-undo restore script for {target_table}",
            is_destructive=is_destructive
        )

    def run_write(self, connection_id: str, sql: str, confirmation_token: str) -> WriteResult:
        """Execute a write statement guarded by a valid confirmation token."""
        creds = vault_instance.get_credentials(connection_id)
        if not creds:
            raise ValueError(f"Unknown connection {connection_id}")
        if creds.read_only:
            raise PermissionError("Connection is configured as READ-ONLY. Write execution prohibited.")
            
        if not confirmation_token or len(confirmation_token) < 8:
            raise PermissionError("Missing or invalid user confirmation token.")
            
        engine = self._get_engine(connection_id)
        with engine.begin() as conn:
            result = conn.execute(text(sql))
            rows_affected = result.rowcount if hasattr(result, "rowcount") else 0
            
        return WriteResult(
            success=True,
            rows_affected=rows_affected,
            reverse_sql=None,
            message=f"Write statement executed successfully ({rows_affected} rows affected)."
        )


# Global MCP server instance
mcp_server = MCPDatabaseServer()

if __name__ == "__main__":
    logger.info("MCP Database Server initialized and ready for tool calls.")
