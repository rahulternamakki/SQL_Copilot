# MCP Database Server (`/apps/mcp-db-server`)

The **MCP Database Server** is an isolated microservice operating on the Model Context Protocol (MCP) tool standard. It acts as the secure execution gateway between AI agents and underlying databases.

## Security Guarantees
1. **Zero Direct DB Access for Agents**: Agents only invoke scoped MCP tools (`list_schema`, `run_select`, `dry_run_preview`, `run_write`).
2. **Encrypted Credential Vault**: Database credentials (passwords/keys) are stored encrypted via Fernet symmetric encryption and never leak into agent contexts or logs.
3. **AST SQL Parser Verification**: Uses `sqlglot` to verify that `run_select` strictly executes read-only `SELECT` / `UNION` queries.
4. **Guarded Writes**: `run_write` requires a valid confirmation token issued only after user approval.

## Tool Surface
- `list_schema(connection_id)`: Structured JSON introspection of tables, types, foreign keys, and indexes.
- `run_select(connection_id, sql, max_rows)`: Enforces read-only execution with pagination limit.
- `dry_run_preview(connection_id, sql)`: Performs pre-execution evaluation, row impact counts, and before-state capture.
- `run_write(connection_id, sql, confirmation_token)`: Executes guarded writes with rollback metadata.
