"""
Configuration settings for Governed AI Database Copilot Agent Service.
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    # Groq LLM Settings
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL")
    groq_temperature: float = Field(default=0.0, alias="GROQ_TEMPERATURE")

    # Qdrant Vector DB Settings
    qdrant_host: str = Field(default="localhost", alias="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, alias="QDRANT_PORT")
    qdrant_collection_prefix: str = Field(default="db_copilot_", alias="QDRANT_COLLECTION_PREFIX")

    # MCP Server Connection
    mcp_server_url: str = Field(default="http://localhost:8001", alias="NEXT_PUBLIC_MCP_URL")

    # Security & Tokens
    jwt_secret: str = Field(default="governed-copilot-default-secret-key-32b", alias="JWT_SECRET")
    confirmation_token_expiry_seconds: int = Field(default=300, alias="CONFIRMATION_TOKEN_EXPIRY_SECONDS")

    # Service Binding
    host: str = Field(default="0.0.0.0", alias="AGENT_SERVICE_HOST")
    port: int = Field(default=8000, alias="AGENT_SERVICE_PORT")

    # Safety & Limits
    max_rows_default: int = Field(default=100, alias="DEFAULT_MAX_ROWS_PER_QUERY")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
