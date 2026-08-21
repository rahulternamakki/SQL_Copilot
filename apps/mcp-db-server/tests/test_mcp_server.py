"""
Unit tests for MCP Database Server & Credential Vault.
"""

import os
import gc
import tempfile
import sqlite3
import pytest
import vault
from vault import CredentialVault, DatabaseCredentials
from server import MCPDatabaseEngine


@pytest.fixture
def temp_vault():
    tf = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = tf.name
    tf.close()
    
    test_vault = CredentialVault(key=None, db_path=db_path)
    yield test_vault
    
    del test_vault
    gc.collect()
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except PermissionError:
            pass


def test_vault_encryption_and_persistence(temp_vault):
    creds = DatabaseCredentials(
        connection_id="test_conn_01",
        display_name="Test Postgres",
        db_type="postgresql",
        host="localhost",
        port=5432,
        database="test_db",
        username="test_user",
        password="super_secret_password_123!",
        ssl_mode="require",
        read_only=True,
    )
    
    # Store credentials
    temp_vault.store_credentials(creds)
    
    # Verify raw SQLite content is encrypted (password not in plaintext in raw DB)
    with sqlite3.connect(temp_vault._db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT encrypted_payload FROM encrypted_vault WHERE connection_id = ?", ("test_conn_01",))
        row = cursor.fetchone()
        assert row is not None
        encrypted_blob = row[0]
        assert b"super_secret_password_123!" not in encrypted_blob

    # Retrieve and decrypt
    retrieved = temp_vault.get_credentials("test_conn_01")
    assert retrieved is not None
    assert retrieved.username == "test_user"
    assert retrieved.password == "super_secret_password_123!"
    assert retrieved.read_only is True

    # List connections (masks password)
    conn_list = temp_vault.list_connections()
    assert len(conn_list) == 1
    assert conn_list[0].connection_id == "test_conn_01"
    assert conn_list[0].display_name == "Test Postgres"

    # Delete connection
    deleted = temp_vault.delete_connection("test_conn_01")
    assert deleted is True
    assert temp_vault.get_credentials("test_conn_01") is None


def test_ast_read_only_validation():
    engine = MCPDatabaseEngine()
    
    # Valid read-only queries
    assert engine.is_read_only_sql("SELECT * FROM customers") is True
    assert engine.is_read_only_sql("SELECT c.id, COUNT(o.id) FROM customers c LEFT JOIN orders o ON c.id = o.customer_id GROUP BY c.id") is True
    assert engine.is_read_only_sql("SELECT * FROM customers WHERE id = 1 UNION SELECT * FROM customers WHERE id = 2;") is True
    
    # Destructive / write queries that MUST be rejected
    assert engine.is_read_only_sql("UPDATE customers SET status = 'active'") is False
    assert engine.is_read_only_sql("DELETE FROM customers WHERE id = 1") is False
    assert engine.is_read_only_sql("INSERT INTO customers (first_name) VALUES ('Hacker')") is False
    assert engine.is_read_only_sql("DROP TABLE customers") is False
    assert engine.is_read_only_sql("ALTER TABLE customers ADD COLUMN balance INT") is False
    assert engine.is_read_only_sql("TRUNCATE TABLE orders") is False
    assert engine.is_read_only_sql("SELECT 1; DROP TABLE customers;") is False


def test_sqlite_schema_introspection(temp_vault):
    tf = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    sqlite_db = tf.name
    tf.close()

    with sqlite3.connect(sqlite_db) as conn:
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT NOT NULL, is_active INTEGER DEFAULT 1)")
        conn.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, amount REAL, FOREIGN KEY(user_id) REFERENCES users(id))")
        conn.execute("INSERT INTO users (email) VALUES ('test@example.com')")
        conn.commit()

    creds = DatabaseCredentials(
        connection_id="sqlite_test",
        display_name="SQLite Demo",
        db_type="sqlite",
        host="localhost",
        port=0,
        database=sqlite_db,
        username="",
        password="",
        read_only=True,
    )
    temp_vault.store_credentials(creds)
    
    old_vault = vault.vault_instance
    vault.vault_instance = temp_vault
    
    try:
        engine = MCPDatabaseEngine()
        schema = engine.list_schema("sqlite_test")
        assert schema.table_count == 2
        tables = {t.table_name: t for t in schema.tables}
        assert "users" in tables
        assert "orders" in tables
        assert any(c.name == "email" for c in tables["users"].columns)
        
        # Test select execution
        res = engine.run_select("sqlite_test", "SELECT id, email FROM users")
        assert res.row_count == 1
        assert res.rows[0][1] == "test@example.com"
        
        # Test write rejection on read-only query endpoint
        with pytest.raises(PermissionError):
            engine.run_select("sqlite_test", "DELETE FROM users WHERE id = 1")
    finally:
        vault.vault_instance = old_vault
        # Dispose engine pool to release file lock on Windows
        if "sqlite_test" in engine._engines:
            engine._engines["sqlite_test"].dispose()
        gc.collect()
        if os.path.exists(sqlite_db):
            try:
                os.remove(sqlite_db)
            except PermissionError:
                pass
