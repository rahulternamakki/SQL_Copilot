"""
Credential Vault Module for Governed AI Database Copilot.
Handles secure symmetric encryption (Fernet) and SQLite persistence of database connection parameters.
Database credentials are encrypted at rest and never exposed to LLMs or public logs.
"""

import os
import json
import sqlite3
import datetime
from typing import Dict, Any, List, Optional
from cryptography.fernet import Fernet
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Auto-discover and load .env
current_dir = os.path.dirname(os.path.abspath(__file__))
possible_env_paths = [
    os.path.join(current_dir, ".env"),
    os.path.join(os.path.dirname(current_dir), ".env"),
    os.path.join(os.path.dirname(os.path.dirname(current_dir)), ".env"),
    ".env",
    "../.env",
]
for p in possible_env_paths:
    if os.path.exists(p):
        load_dotenv(p, override=False)


class DatabaseCredentials(BaseModel):
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
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ConnectionSummary(BaseModel):
    connection_id: str
    display_name: str
    db_type: str
    host: str
    port: int
    database: str
    username: str
    ssl_mode: str
    read_only: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


ConnectionRecord = ConnectionSummary


class CredentialVault:
    """
    Encrypts database credentials at rest in a local SQLite vault database.
    Provides methods to store, retrieve, list, test, and delete connections.
    """

    def __init__(self, key: Optional[str] = None, db_path: Optional[str] = None):
        if not key:
            key = os.getenv("VAULT_ENCRYPTION_KEY")
        if not key or key == "generate_fernet_key_and_paste_here":
            key = Fernet.generate_key().decode()
            os.environ["VAULT_ENCRYPTION_KEY"] = key
        
        if isinstance(key, str):
            key_bytes = key.encode()
        else:
            key_bytes = key
            
        self._cipher = Fernet(key_bytes)
        
        if not db_path:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(base_dir, "vault.db")
        self._db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize the encrypted vault table."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS encrypted_vault (
                    connection_id TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL,
                    db_type TEXT NOT NULL,
                    host TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    database TEXT NOT NULL,
                    username TEXT NOT NULL,
                    ssl_mode TEXT NOT NULL,
                    read_only INTEGER NOT NULL DEFAULT 1,
                    encrypted_payload BLOB NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def store_credentials(self, creds: DatabaseCredentials) -> str:
        """Encrypt sensitive parameters and save/update the connection."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if not creds.created_at:
            creds.created_at = now
        creds.updated_at = now

        raw_json = creds.model_dump_json()
        encrypted = self._cipher.encrypt(raw_json.encode())

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO encrypted_vault (
                    connection_id, display_name, db_type, host, port,
                    database, username, ssl_mode, read_only,
                    encrypted_payload, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(connection_id) DO UPDATE SET
                    display_name=excluded.display_name,
                    db_type=excluded.db_type,
                    host=excluded.host,
                    port=excluded.port,
                    database=excluded.database,
                    username=excluded.username,
                    ssl_mode=excluded.ssl_mode,
                    read_only=excluded.read_only,
                    encrypted_payload=excluded.encrypted_payload,
                    updated_at=excluded.updated_at
                """,
                (
                    creds.connection_id,
                    creds.display_name,
                    creds.db_type,
                    creds.host,
                    creds.port,
                    creds.database,
                    creds.username,
                    creds.ssl_mode,
                    1 if creds.read_only else 0,
                    encrypted,
                    creds.created_at,
                    creds.updated_at,
                ),
            )
            conn.commit()
        return creds.connection_id

    def save_connection(self, data: Dict[str, Any]) -> ConnectionSummary:
        """Save connection from dict and return summary."""
        creds = DatabaseCredentials(**data)
        self.store_credentials(creds)
        return ConnectionSummary(**creds.model_dump())

    def get_credentials(self, connection_id: str) -> Optional[DatabaseCredentials]:
        """Retrieve and decrypt credentials for a given connection_id."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT encrypted_payload FROM encrypted_vault WHERE connection_id = ?",
                (connection_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            
            encrypted = row["encrypted_payload"]
            try:
                decrypted = self._cipher.decrypt(encrypted).decode()
                return DatabaseCredentials.model_validate_json(decrypted)
            except Exception as e:
                raise ValueError(f"Failed to decrypt credentials for connection {connection_id}: {e}")

    def get_connection(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve credentials as a dict."""
        creds = self.get_credentials(connection_id)
        if not creds:
            return None
        return creds.model_dump()

    def get_connection_record(self, connection_id: str) -> Optional[ConnectionSummary]:
        """Retrieve connection summary record."""
        creds = self.get_credentials(connection_id)
        if not creds:
            return None
        return ConnectionSummary(**creds.model_dump())

    def list_connections(self) -> List[ConnectionSummary]:
        """List all stored connections without exposing plaintext passwords."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT connection_id, display_name, db_type, host, port, database, username, ssl_mode, read_only, created_at, updated_at
                FROM encrypted_vault
                ORDER BY updated_at DESC
                """
            )
            rows = cursor.fetchall()
            return [
                ConnectionSummary(
                    connection_id=row["connection_id"],
                    display_name=row["display_name"],
                    db_type=row["db_type"],
                    host=row["host"],
                    port=row["port"],
                    database=row["database"],
                    username=row["username"],
                    ssl_mode=row["ssl_mode"],
                    read_only=bool(row["read_only"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]

    def delete_connection(self, connection_id: str) -> bool:
        """Delete connection from vault."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM encrypted_vault WHERE connection_id = ?", (connection_id,))
            conn.commit()
            return cursor.rowcount > 0

    def build_connection_url(self, creds: DatabaseCredentials) -> str:
        """Build SQLAlchemy connection string from DatabaseCredentials with URL-encoded credentials."""
        import urllib.parse
        safe_user = urllib.parse.quote_plus(creds.username) if creds.username else ""
        safe_pass = urllib.parse.quote_plus(creds.password) if creds.password else ""
        auth_part = f"{safe_user}:{safe_pass}@" if safe_user or safe_pass else ""

        if creds.db_type == "postgresql":
            ssl_arg = f"?sslmode={creds.ssl_mode}" if creds.ssl_mode else ""
            return f"postgresql+psycopg2://{auth_part}{creds.host}:{creds.port}/{creds.database}{ssl_arg}"
        elif creds.db_type == "mysql":
            return f"mysql+pymysql://{auth_part}{creds.host}:{creds.port}/{creds.database}"
        elif creds.db_type == "sqlite":
            return f"sqlite:///{creds.database}"
        else:
            raise ValueError(f"Unsupported database type: {creds.db_type}")

    def get_connection_url(self, connection_id: str) -> Optional[str]:
        creds = self.get_credentials(connection_id)
        if not creds:
            return None
        return self.build_connection_url(creds)

    def test_connection(self, creds: DatabaseCredentials) -> Dict[str, Any]:
        url = self.build_connection_url(creds)
        try:
            engine = create_engine(url, connect_args={"connect_timeout": 5} if creds.db_type == "postgresql" else {})
            with engine.connect() as conn:
                res = conn.execute(text("SELECT 1 AS ping")).scalar()
                if res == 1:
                    return {"success": True, "message": "Connection test successful!"}
                else:
                    return {"success": False, "message": f"Unexpected ping result: {res}"}
        except Exception as e:
            return {"success": False, "message": f"Connection failed: {str(e)}"}


# Global vault singleton instances
vault_instance = CredentialVault()
credential_vault = vault_instance
