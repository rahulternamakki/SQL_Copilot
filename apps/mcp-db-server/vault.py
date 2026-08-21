"""
Credential Vault Module for Governed AI Database Copilot.
Handles secure symmetric encryption (Fernet) and retrieval of database connection parameters.
"""

import os
import json
import base64
from typing import Dict, Optional
from cryptography.fernet import Fernet
from pydantic import BaseModel, Field


class DatabaseCredentials(BaseModel):
    connection_id: str
    db_type: str = "postgresql"  # postgresql, mysql, etc.
    host: str
    port: int = 5432
    database: str
    username: str
    password: str
    ssl_mode: str = "prefer"
    read_only: bool = True
    display_name: Optional[str] = None


class CredentialVault:
    """
    Encrypts database credentials at rest and resolves connection strings on-demand.
    Database credentials are never exposed to LLMs or public logs.
    """

    def __init__(self, key: Optional[str] = None):
        if not key:
            key = os.getenv("VAULT_ENCRYPTION_KEY")
        if not key:
            # Generate temporary fallback key for local dev if not supplied
            key = Fernet.generate_key().decode()
        
        # Ensure key is properly formatted base64 url-safe
        if isinstance(key, str):
            key_bytes = key.encode()
        else:
            key_bytes = key
            
        self._cipher = Fernet(key_bytes)
        self._storage: Dict[str, bytes] = {}

    def store_credentials(self, creds: DatabaseCredentials) -> str:
        """Encrypt and store credentials under connection_id."""
        raw_json = creds.model_dump_json()
        encrypted = self._cipher.encrypt(raw_json.encode())
        self._storage[creds.connection_id] = encrypted
        return creds.connection_id

    def get_credentials(self, connection_id: str) -> Optional[DatabaseCredentials]:
        """Retrieve and decrypt credentials for a given connection_id."""
        encrypted = self._storage.get(connection_id)
        if not encrypted:
            return None
        decrypted = self._cipher.decrypt(encrypted).decode()
        return DatabaseCredentials.model_validate_json(decrypted)

    def get_connection_url(self, connection_id: str) -> Optional[str]:
        """Build SQLAlchemy connection string for the specified connection_id."""
        creds = self.get_credentials(connection_id)
        if not creds:
            return None
        
        if creds.db_type == "postgresql":
            return f"postgresql+psycopg2://{creds.username}:{creds.password}@{creds.host}:{creds.port}/{creds.database}?sslmode={creds.ssl_mode}"
        elif creds.db_type == "mysql":
            return f"mysql+pymysql://{creds.username}:{creds.password}@{creds.host}:{creds.port}/{creds.database}"
        else:
            raise ValueError(f"Unsupported database type: {creds.db_type}")


# Global vault singleton instance
vault_instance = CredentialVault()
