"""
Kenya Legal AI — Configuration & Settings
==========================================
Centralized configuration using pydantic-settings with .env support.
"""

from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Application ──────────────────────────────────────────────────────
    app_name: str = "Kenya Legal AI"
    app_env: str = Field(default="development", pattern="^(development|staging|production)$")
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR)$")

    # ── LLM Provider ─────────────────────────────────────────────────────
    llm_provider: str = Field(default="mistral", pattern="^(openai|anthropic|ollama|google|groq|mistral)$")
    llm_model: str = "mistral-large-latest"
    llm_temperature: float = 0.4
    drafting_temperature: float = 0.2
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    groq_api_key: str = ""
    mistral_api_key: str = ""

    # ── Embeddings ───────────────────────────────────────────────────────
    embedding_provider: str = Field(default="cohere", pattern="^(openai|google|cohere|huggingface)$")
    embedding_model: str = "embed-english-v3.0"
    embedding_dimension: int = 1024
    cohere_api_key: str = ""

    # ── Data Sources ─────────────────────────────────────────────────────
    laws_africa_api_key: str = ""
    laws_africa_base_url: str = "https://api.laws.africa/v3"

    # ── Vector Database (Qdrant) ─────────────────────────────────────────
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "kenya_legal_docs"
    qdrant_api_key: str = ""
    qdrant_cloud_host: str = ""
    qdrant_cloud_api_key: str = ""

    # ── PostgreSQL ───────────────────────────────────────────────────────
    database_url: str = "postgresql://user:password@localhost:5432/kenya_legal_ai"

    # ── Security ─────────────────────────────────────────────────────────
    secret_key: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    cors_origins: str = "*"

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v, info):
        app_env = info.data.get("app_env", "development")
        if app_env in ["staging", "production"] and v in ["change-this-in-production", "0ed5da20db593231594d6806aaa6961c"]:
            raise ValueError(
                f"SECRET_KEY must be set to a secure random value in {app_env} environment. "
                "Generate one with: openssl rand -hex 32"
            )
        return v

    # ── Data Paths ───────────────────────────────────────────────────────
    raw_data_dir: str = "data/raw"
    processed_data_dir: str = "data/processed"
    metadata_dir: str = "data/metadata"
    models_dir: str = "data/models"
    python_version: str = "3.11.0"

    # ── RAG Configuration ────────────────────────────────────────────────
    chunk_size: int = 1000          # characters per chunk
    chunk_overlap: int = 200        # overlap between chunks
    retrieval_top_k: int = 10       # number of chunks to retrieve
    rerank_top_k: int = 5           # number of chunks after re-ranking
    retrieval_threshold: float = 0.35 # minimum score to consider a chunk relevant

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def raw_data_path(self) -> Path:
        return Path(self.raw_data_dir)

    @property
    def processed_data_path(self) -> Path:
        return Path(self.processed_data_dir)

    @property
    def metadata_path(self) -> Path:
        return Path(self.metadata_dir)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
