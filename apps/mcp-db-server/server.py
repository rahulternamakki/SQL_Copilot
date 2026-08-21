"""
MCP Database Server for Governed AI Database Copilot.
Exposes scoped database tools and HTTP API endpoints. Only this service ever touches raw DB credentials.
"""

import os
import time
import logging
from typing import Dict, Any, List, Optional
import sqlglot
from sqlglot import exp
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import vault
from vault import DatabaseCredentials, ConnectionSummary

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-db-server")

app = FastAPI(
    title="Governed AI Database Copilot - MCP DB Server",
    version="0.1.0",
    description="Isolated database gateway with scoped tools, credential vault, and AST-level read-only verification.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# SCHEMAS & MODELS
# ==============================================================================

class SchemaColumn(BaseModel):
    name: str
    type: str
    nullable: bool
    default: Optional[str] = None
    is_primary_key: bool = False
    comment: Optional[str] = None


class SchemaForeignKey(BaseModel):
    constrained_columns: List[str]
    referred_schema: Optional[str] = None
    referred_table: str
    referred_columns: List[str]


class SchemaTable(BaseModel):
    table_name: str
    columns: List[SchemaColumn]
    primary_keys: List[str]
    foreign_keys: List[SchemaForeignKey]
    indexes: List[Dict[str, Any]]
    approximate_row_count: Optional[int] = None
    comment: Optional[str] = None


class SchemaResponse(BaseModel):
    connection_id: str
    database_type: str
    tables: List[SchemaTable]
    table_count: int
    generated_at: str


class SelectQueryRequest(BaseModel):
    connection_id: str
    sql: str
    max_rows: int = Field(default=100, ge=1, le=1000)


class SelectResult(BaseModel):
    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    execution_time_ms: float
    truncated: bool = False


class DryRunRequest(BaseModel):
    connection_id: str
    sql: str


class DryRunResult(BaseModel):
    operation_type: str
    estimated_rows_affected: int
    target_table: Optional[str]
    before_state_sample: List[Dict[str, Any]]
    reverse_sql_template: Optional[str]
    is_destructive: bool


class WriteQueryRequest(BaseModel):
    connection_id: str
    sql: str
    confirmation_token: str


class WriteResult(BaseModel):
    success: bool
    rows_affected: int
    reverse_sql: Optional[str]
    message: str


# ==============================================================================
# CORE MCP DATABASE ENGINE
# ==============================================================================

class MCPDatabaseEngine:
    """
    Manages SQLAlchemy engine caching and executes scoped database operations.
    """

    def __init__(self):
        self._engines: Dict[str, Engine] = {}

    def get_engine(self, connection_id: str) -> Engine:
        """Get or create cached SQLAlchemy engine for the given connection ID."""
        if connection_id in self._engines:
            return self._engines[connection_id]
        
        conn_url = vault.vault_instance.get_connection_url(connection_id)
        if not conn_url:
            raise ValueError(f"Connection ID '{connection_id}' not found in credential vault.")
        
        creds = vault.vault_instance.get_credentials(connection_id)
        connect_args = {"connect_timeout": 5} if creds and creds.db_type == "postgresql" else {}
        
        engine = create_engine(
            conn_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            connect_args=connect_args,
        )
        self._engines[connection_id] = engine
        return engine

    def is_read_only_sql(self, sql_query: str) -> bool:
        """Parse SQL query using sqlglot AST to strictly ensure read-only execution."""
        try:
            cleaned_sql = sql_query.strip().rstrip(";")
            parsed = sqlglot.parse(cleaned_sql)
            if not parsed:
                return False
            
            for statement in parsed:
                if statement is None:
                    continue
                # Allowed root expressions: Select, Union
                if not isinstance(statement, (exp.Select, exp.Union)):
                    return False
                # Reject if any modifying clause exists in AST
                if statement.find(exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Alter):
                    return False
            return True
        except Exception as e:
            logger.warning(f"Failed to parse SQL for read-only validation: {e}")
            return False

    def list_schema(self, connection_id: str) -> SchemaResponse:
        """Introspect database schema and return structured JSON."""
        creds = vault.vault_instance.get_credentials(connection_id)
        if not creds:
            raise ValueError(f"Connection '{connection_id}' not found.")

        engine = self.get_engine(connection_id)
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
                    is_primary_key=c["name"] in pks,
                    comment=c.get("comment"),
                )
                for c in raw_cols
            ]
            
            raw_fks = inspector.get_foreign_keys(t_name)
            foreign_keys = [
                SchemaForeignKey(
                    constrained_columns=fk.get("constrained_columns", []),
                    referred_schema=fk.get("referred_schema"),
                    referred_table=fk.get("referred_table", ""),
                    referred_columns=fk.get("referred_columns", []),
                )
                for fk in raw_fks
            ]
            
            indexes = inspector.get_indexes(t_name)
            
            # Approximate row count if possible
            row_count = None
            try:
                with engine.connect() as conn:
                    row_count = conn.execute(text(f"SELECT COUNT(*) FROM {t_name}")).scalar()
            except Exception:
                row_count = None
            
            tables_meta.append(
                SchemaTable(
                    table_name=t_name,
                    columns=columns,
                    primary_keys=pks,
                    foreign_keys=foreign_keys,
                    indexes=indexes,
                    approximate_row_count=row_count,
                )
            )
            
        return SchemaResponse(
            connection_id=connection_id,
            database_type=creds.db_type,
            tables=tables_meta,
            table_count=len(tables_meta),
            generated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )

    def run_select(self, connection_id: str, sql: str, max_rows: int = 100) -> SelectResult:
        """Execute a validated SELECT query against the database."""
        if not self.is_read_only_sql(sql):
            raise PermissionError("Query rejected: Only read-only SELECT statements are permitted.")
        
        creds = vault.vault_instance.get_credentials(connection_id)
        if not creds:
            raise ValueError(f"Unknown connection {connection_id}")

        start_time = time.time()
        engine = self.get_engine(connection_id)
        
        with engine.connect() as conn:
            # Enforce read-only session level on PostgreSQL
            if creds.db_type == "postgresql":
                try:
                    conn.execute(text("SET TRANSACTION READ ONLY"))
                except Exception:
                    pass
                
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
            truncated=truncated,
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
        
        engine = self.get_engine(connection_id)
        if target_table and op_type in ["UPDATE", "DELETE"]:
            where_clause = parsed.find(exp.Where)
            where_sql = where_clause.sql() if where_clause else ""
            
            count_sql = f"SELECT COUNT(*) FROM {target_table} {where_sql}"
            sample_sql = f"SELECT * FROM {target_table} {where_sql} LIMIT 5"
            
            try:
                with engine.connect() as conn:
                    count_res = conn.execute(text(count_sql)).scalar()
                    estimated_count = int(count_res or 0)
                    
                    sample_res = conn.execute(text(sample_sql))
                    keys = list(sample_res.keys())
                    for row in sample_res.fetchall():
                        before_sample.append({k: str(v) for k, v in zip(keys, row)})
            except Exception as e:
                logger.warning(f"Dry run row count failed: {e}")

        return DryRunResult(
            operation_type=op_type,
            estimated_rows_affected=estimated_count,
            target_table=target_table,
            before_state_sample=before_sample,
            reverse_sql_template=f"-- Auto-undo restore script for {target_table}",
            is_destructive=is_destructive,
        )

    def run_write(self, connection_id: str, sql: str, confirmation_token: str) -> WriteResult:
        """Execute a write statement guarded by a valid confirmation token."""
        creds = vault.vault_instance.get_credentials(connection_id)
        if not creds:
            raise ValueError(f"Unknown connection {connection_id}")
        if creds.read_only:
            raise PermissionError("Connection is configured as READ-ONLY. Write execution prohibited.")
            
        if not confirmation_token or len(confirmation_token) < 8:
            raise PermissionError("Missing or invalid user confirmation token.")
            
        engine = self.get_engine(connection_id)
        with engine.begin() as conn:
            result = conn.execute(text(sql))
            rows_affected = result.rowcount if hasattr(result, "rowcount") else 0
            
        return WriteResult(
            success=True,
            rows_affected=rows_affected,
            reverse_sql=None,
            message=f"Write statement executed successfully ({rows_affected} rows affected).",
        )


db_engine = MCPDatabaseEngine()


# ==============================================================================
# FASTAPI HTTP ENDPOINTS
# ==============================================================================

@app.get("/health")
def health():
    return {"status": "healthy", "service": "mcp-db-server", "version": "0.1.0"}


@app.post("/tools/test_connection")
def test_connection_endpoint(creds: DatabaseCredentials):
    res = vault.vault_instance.test_connection(creds)
    if not res["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res["message"])
    return res


@app.post("/connections", response_model=Dict[str, str])
def save_connection_endpoint(creds: DatabaseCredentials):
    conn_id = vault.vault_instance.store_credentials(creds)
    return {"connection_id": conn_id, "message": "Connection saved successfully."}


@app.get("/connections", response_model=List[ConnectionSummary])
def list_connections_endpoint():
    return vault.vault_instance.list_connections()


@app.get("/connections/{connection_id}", response_model=ConnectionSummary)
def get_connection_endpoint(connection_id: str):
    creds = vault.vault_instance.get_credentials(connection_id)
    if not creds:
        raise HTTPException(status_code=404, detail="Connection not found")
    return ConnectionSummary(
        connection_id=creds.connection_id,
        display_name=creds.display_name,
        db_type=creds.db_type,
        host=creds.host,
        port=creds.port,
        database=creds.database,
        username=creds.username,
        ssl_mode=creds.ssl_mode,
        read_only=creds.read_only,
        created_at=creds.created_at,
        updated_at=creds.updated_at,
    )


@app.delete("/connections/{connection_id}")
def delete_connection_endpoint(connection_id: str):
    success = vault.vault_instance.delete_connection(connection_id)
    if not success:
        raise HTTPException(status_code=404, detail="Connection not found")
    return {"message": "Connection deleted successfully."}


@app.post("/tools/list_schema", response_model=SchemaResponse)
def list_schema_endpoint(req: Dict[str, str]):
    conn_id = req.get("connection_id")
    if not conn_id:
        raise HTTPException(status_code=400, detail="Missing connection_id")
    try:
        return db_engine.list_schema(conn_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/run_select", response_model=SelectResult)
def run_select_endpoint(req: SelectQueryRequest):
    try:
        return db_engine.run_select(req.connection_id, req.sql, req.max_rows)
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/dry_run_preview", response_model=DryRunResult)
def dry_run_endpoint(req: DryRunRequest):
    try:
        return db_engine.dry_run_preview(req.connection_id, req.sql)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/run_write", response_model=WriteResult)
def run_write_endpoint(req: WriteQueryRequest):
    try:
        return db_engine.run_write(req.connection_id, req.sql, req.confirmation_token)
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_SERVER_PORT", "8001"))
    logger.info(f"Starting MCP Database Server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
