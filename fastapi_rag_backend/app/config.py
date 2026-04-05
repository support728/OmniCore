from pydantic import Field
import os
import re
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Core ---
    app_name: str = "RAG Clarity Backend"
    environment: str = "dev"
    debug: bool = True

    # --- API ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    web_concurrency: int = 2
    log_level: str = "info"

    # --- Security ---
    cors_allowed_origins: str = ""
    trusted_hosts: str = ""

    # --- Database ---
    database_url: Optional[str] = None
    postgres_dsn: str = "postgresql+asyncpg://rag:rag@localhost:5432/ragdb"
    sqlite_fallback_dsn: str = "sqlite+aiosqlite:///./fastapi_rag_backend/dev.db"
    use_sqlite_fallback: bool = True
    redis_url: str = "redis://localhost:6379/0"

    # --- Storage (Optional S3 / MinIO) ---
    storage_enabled: bool = False  # master switch

    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str = "us-east-1"

    s3_bucket: str | None = None
    s3_endpoint_url: str | None = None  # for MinIO or custom endpoints

    # --- AI ---
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    ai_endpoint_url: Optional[str] = None  # ✅ FIXED
    embedding_model: str = "text-3-small"
    openai_model: str = "gpt-4o-mini"

    system_prompt: str = "You are Nova, a smart AI assistant. Answer the user's question based on your knowledge and any provided context."
    # --- RAG ---
    vector_dim: int = 1536
    chunk_size: int = 1000
    chunk_overlap: int = 150

    # --- Proactive AI ---
    proactive_enabled: bool = True
    proactive_interval_seconds: int = 180
    proactive_confidence_threshold: float = 0.72
    proactive_dedupe_minutes: int = 240
    proactive_threshold_min: float = 0.45
    proactive_threshold_max: float = 0.95
    proactive_adjust_accept: float = -0.03
    proactive_adjust_ignore: float = 0.02
    proactive_adjust_dismiss: float = 0.05

    # --- Auth ---
    auth_session_ttl_hours: int = 720
    auth_min_password_length: int = 8

    # --- Startup ---
    startup_require_dependencies: bool = False

    # --- Config ---
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("openai_api_key", mode="before")
    @classmethod
    def normalize_openai_key(cls, value):
        if value is None:
            return None
        return str(value).strip().strip('"').strip("'") or None


# --- Validation Helper ---


# --- Singleton ---
settings = Settings()