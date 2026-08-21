"""
Cross-Dialect SQL Transpiler Service for Governed AI Database Copilot.
Transpiles SQL queries from Snowflake, MySQL, BigQuery, SQLite, and TSQL into PostgreSQL 16 standard dialect using sqlglot.
"""

import logging
from typing import Dict, Any, Optional
import sqlglot
from pydantic import BaseModel

logger = logging.getLogger("transpiler-service")


class TranspileRequest(BaseModel):
    sql: str
    source_dialect: str = "snowflake"  # snowflake, mysql, bigquery, sqlite, tsql, oracle


class TranspileResponse(BaseModel):
    success: bool
    source_dialect: str
    target_dialect: str = "postgres"
    original_sql: str
    transpiled_sql: str
    notes: Optional[str] = None
    error: Optional[str] = None


class SQLTranspilerService:
    def transpile(self, sql: str, source_dialect: str = "snowflake") -> TranspileResponse:
        """
        Transpile source dialect SQL query into PostgreSQL 16 dialect.
        """
        clean_dialect = source_dialect.lower().strip()
        try:
            transpiled_statements = sqlglot.transpile(
                sql,
                read=clean_dialect,
                write="postgres",
                pretty=True,
            )
            result_sql = ";\n".join(transpiled_statements)
            return TranspileResponse(
                success=True,
                source_dialect=clean_dialect,
                target_dialect="postgres",
                original_sql=sql,
                transpiled_sql=result_sql,
                notes=f"Successfully transpiled from {clean_dialect.capitalize()} to standard PostgreSQL.",
            )
        except Exception as e:
            logger.warning(f"SQL Transpilation failed for dialect {source_dialect}: {e}")
            return TranspileResponse(
                success=False,
                source_dialect=clean_dialect,
                target_dialect="postgres",
                original_sql=sql,
                transpiled_sql=sql,
                error=str(e),
                notes="Transpilation syntax error. Retaining original statement.",
            )


transpiler_service = SQLTranspilerService()
