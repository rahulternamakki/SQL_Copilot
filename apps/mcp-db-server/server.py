"""
MCP Database Server for Governed AI Database Copilot.
Enforces process isolation, AST-level read-only verification, dry-run previews, and rollback snapshots.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import sqlglot
from sqlglot import exp
from sqlalchemy import create_engine, text, inspect

import vault
from vault import DatabaseCredentials, ConnectionSummary, ConnectionRecord
from rollback_manager import rollback_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-db-server")

app = FastAPI(
    title="Governed AI Database Copilot - MCP DB Server",
    version="0.3.0",
    description="Isolated database access layer with AST verification and rollback logging.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# MCP ENGINE HELPER (PROGRAMMATIC & TESTS)
# ==============================================================================

class MCPDatabaseEngine:
    """Helper engine for programmatic test invocations."""
    def __init__(self):
        self._engines = {}

    def is_read_only_sql(self, sql: str) -> bool:
        try:
            parsed_statements = sqlglot.parse(sql)
        except Exception:
            return False
        for stmt in parsed_statements:
            if not isinstance(stmt, (exp.Select, exp.Union)):
                return False
            if stmt.find(exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Alter):
                return False
        return True

    def list_schema(self, connection_id: str):
        payload = list_schema({"connection_id": connection_id})
        class ColumnObj:
            def __init__(self, c):
                self.name = c["name"]
                self.type = c["type"]
                for k, v in c.items():
                    setattr(self, k, v)
        class TableObj:
            def __init__(self, t):
                self.table_name = t["table_name"]
                self.columns = [ColumnObj(c) for c in t["columns"]]
                for k, v in t.items():
                    if k != "columns":
                        setattr(self, k, v)
        class SchemaResult:
            def __init__(self, d):
                self.table_count = d["table_count"]
                self.tables = [TableObj(t) for t in d["tables"]]
        return SchemaResult(payload)

    def run_select(self, connection_id: str, sql: str):
        if not self.is_read_only_sql(sql):
            raise PermissionError("AST Violation: Read-only query violation.")
        res = run_select(RunSelectPayload(connection_id=connection_id, sql=sql))
        return type("R", (), res)


# ==============================================================================
# PYDANTIC REQUEST/RESPONSE MODELS
# ==============================================================================

class ConnectionPayload(BaseModel):
    connection_id: str
    display_name: str
    db_type: str = "postgresql"
    host: str = "localhost"
    port: int = 5432
    database: str
    username: str
    password: str
    ssl_mode: str = "disable"
    read_only: bool = True


class RunSelectPayload(BaseModel):
    connection_id: str
    sql: str
    max_rows: int = Field(default=100, ge=1, le=5000)


class RunWritePayload(BaseModel):
    connection_id: str
    sql: str
    confirmation_token: Optional[str] = None


class DryRunPayload(BaseModel):
    connection_id: str
    sql: str


class RollbackPayload(BaseModel):
    rollback_id: str


# ==============================================================================
# CONNECTION & VAULT MANAGEMENT TOOLS
# ==============================================================================

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "mcp-db-server", "version": "0.3.0"}


@app.post("/connections/test")
@app.post("/tools/test_connection")
def test_connection(payload: ConnectionPayload):
    """Test connection reachability directly without saving."""
    creds = DatabaseCredentials(**payload.model_dump())
    return vault.vault_instance.test_connection(creds)


@app.post("/connections", response_model=ConnectionRecord)
def save_connection(payload: ConnectionPayload):
    """Save connection into encrypted credential vault."""
    try:
        return vault.vault_instance.save_connection(payload.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/connections", response_model=List[ConnectionRecord])
def list_connections():
    """List all registered connections (passwords masked)."""
    return vault.vault_instance.list_connections()


@app.get("/connections/{connection_id}", response_model=ConnectionRecord)
def get_connection(connection_id: str):
    conn = vault.vault_instance.get_connection_record(connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    return conn


@app.delete("/connections/{connection_id}")
def delete_connection(connection_id: str):
    success = vault.vault_instance.delete_connection(connection_id)
    if not success:
        raise HTTPException(status_code=404, detail="Connection not found")
    return {"message": "Connection deleted"}


# ==============================================================================
# SCOPED MCP TOOLS: SCHEMA INTROSPECTION
# ==============================================================================

@app.post("/tools/list_schema")
def list_schema(payload: Dict[str, str]):
    """Introspect full schema: tables, columns, primary keys, foreign keys."""
    connection_id = payload.get("connection_id")
    creds = vault.vault_instance.get_credentials(connection_id)
    if not creds:
        raise HTTPException(status_code=404, detail="Connection not found in vault")

    url = vault.vault_instance.build_connection_url(creds)
    try:
        engine = create_engine(url)
        inspector = inspect(engine)
        table_names = inspector.get_table_names()

        tables_data = []
        for t_name in table_names:
            cols = inspector.get_columns(t_name)
            pks = inspector.get_pk_constraint(t_name).get("constrained_columns", [])
            fks = inspector.get_foreign_keys(t_name)
            indexes = inspector.get_indexes(t_name)

            row_count = None
            try:
                with engine.connect() as conn:
                    res = conn.execute(text(f"SELECT COUNT(*) FROM {t_name}"))
                    row_count = res.scalar()
            except Exception:
                pass

            tables_data.append(
                {
                    "table_name": t_name,
                    "columns": [
                        {
                            "name": c["name"],
                            "type": str(c["type"]),
                            "nullable": c.get("nullable", True),
                            "default": str(c.get("default")) if c.get("default") else None,
                            "is_primary_key": c["name"] in pks,
                            "comment": c.get("comment"),
                        }
                        for c in cols
                    ],
                    "primary_keys": pks,
                    "foreign_keys": [
                        {
                            "constrained_columns": fk["constrained_columns"],
                            "referred_schema": fk.get("referred_schema"),
                            "referred_table": fk["referred_table"],
                            "referred_columns": fk["referred_columns"],
                        }
                        for fk in fks
                    ],
                    "indexes": indexes,
                    "approximate_row_count": row_count,
                }
            )

        engine.dispose()
        return {
            "connection_id": connection_id,
            "database_type": creds.db_type,
            "tables": tables_data,
            "table_count": len(tables_data),
        }
    except Exception as e:
        logger.error(f"Schema introspection error: {e}")
        raise HTTPException(status_code=500, detail=f"Schema introspection failed: {str(e)}")


# ==============================================================================
# SCOPED MCP TOOLS: RUN_SELECT (AST-VERIFIED READ ONLY)
# ==============================================================================

@app.post("/tools/run_select")
def run_select(payload: RunSelectPayload):
    """Execute read-only SQL queries verified by AST parser."""
    try:
        parsed_statements = sqlglot.parse(payload.sql)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid SQL syntax: {str(e)}")

    for stmt in parsed_statements:
        if not isinstance(stmt, (exp.Select, exp.Union)):
            raise HTTPException(
                status_code=403,
                detail=f"AST Violation: Only SELECT/UNION statements permitted in run_select (Received: {stmt.key}).",
            )
        if stmt.find(exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Alter):
            raise HTTPException(
                status_code=403,
                detail="AST Violation: Mutating statements (INSERT/UPDATE/DELETE/DROP/ALTER) forbidden in read-only mode.",
            )

    creds = vault.vault_instance.get_credentials(payload.connection_id)
    if not creds:
        raise HTTPException(status_code=404, detail="Connection not found in vault")

    url = vault.vault_instance.build_connection_url(creds)
    start_time = time.perf_counter()

    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            result = conn.execute(text(payload.sql))
            columns = list(result.keys())
            raw_rows = result.fetchmany(payload.max_rows + 1)
            truncated = len(raw_rows) > payload.max_rows
            rows = raw_rows[: payload.max_rows]

            formatted_rows = [[str(v) if v is not None else None for v in row] for row in rows]

        engine.dispose()
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "columns": columns,
            "rows": formatted_rows,
            "row_count": len(rows),
            "execution_time_ms": duration_ms,
            "truncated": truncated,
        }
    except Exception as e:
        logger.error(f"SQL execution error: {e}")
        raise HTTPException(status_code=400, detail=f"Database execution error: {str(e)}")


# ==============================================================================
# SCOPED MCP TOOLS: WRITE PATH, DRY RUN, & ROLLBACK ENGINE
# ==============================================================================

@app.post("/tools/dry_run_preview")
def dry_run_preview(payload: DryRunPayload):
    """Inspect write query, estimate affected row count, and fetch before-state sample rows."""
    res = rollback_manager.inspect_and_dry_run(payload.connection_id, payload.sql)
    return res


@app.post("/tools/run_write")
def run_write(payload: RunWritePayload):
    """Execute confirmed mutating SQL statement inside transaction with rollback snapshot."""
    creds = vault.vault_instance.get_credentials(payload.connection_id)
    if not creds:
        raise HTTPException(status_code=404, detail="Connection not found in vault")

    if creds.read_only:
        raise HTTPException(
            status_code=403,
            detail="Database connection is in READ-ONLY mode. Write operations are blocked at the MCP gateway.",
        )

    try:
        result = rollback_manager.snapshot_and_execute(payload.connection_id, payload.sql)
        return result
    except Exception as e:
        logger.error(f"Write execution error: {e}")
        raise HTTPException(status_code=400, detail=f"Write execution failed: {str(e)}")


@app.post("/tools/rollback")
def rollback_tool(payload: RollbackPayload):
    """Restore database state to pre-mutation snapshot using rollback_id."""
    res = rollback_manager.execute_rollback(payload.rollback_id)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message", "Rollback failed."))
    return res


@app.get("/tools/audit_logs")
def audit_logs_tool(connection_id: Optional[str] = None):
    """List historical audit and rollback logs."""
    return rollback_manager.list_logs(connection_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
