from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    llm_provider: Literal["ollama", "nvidia", "openai", "anthropic"] = Field(
        default="ollama",
        description="LLM provider to use",
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama base URL",
    )
    ollama_model: str = Field(
        default="llama3.2",
        description="Ollama model name",
    )

    nvidia_api_key: str | None = Field(
        default=None,
        description="NVIDIA API key",
    )
    nvidia_base_url: str = Field(
        default="https://integrate.api.nvidia.com/v1",
        description="NVIDIA API base URL",
    )
    nvidia_model: str = Field(
        default="nvidia/nemotron-3-ultra-550b-a55b",
        description="NVIDIA model name",
    )

    openalex_api_key: str | None = Field(
        default=None,
        description="OpenAlex API key (optional)",
    )
    semantic_scholar_api_key: str | None = Field(
        default=None,
        description="Semantic Scholar API key (optional)",
    )

    database_url: str = Field(
        default="sqlite:///data/research.db",
        description="Database connection URL",
    )

    vector_db_path: str = Field(
        default="data/vector_db",
        description="Vector database storage path",
    )

    embedding_model: str = Field(
        default="BAAI/bge-small-en-v1.5",
        description="Embedding model name (sentence-transformers)",
    )

    app_host: str = Field(
        default="0.0.0.0",
        description="Application host",
    )
    app_port: int = Field(
        default=8501,
        description="Application port",
    )

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith(("sqlite:///", "postgresql://", "mysql://")):
            raise ValueError("Database URL must start with sqlite:///, postgresql://, or mysql://")
        return v

    @field_validator("vector_db_path")
    @classmethod
    def validate_vector_db_path(cls, v: str) -> str:
        path = Path(v)
        path.parent.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("ollama_base_url")
    @classmethod
    def validate_ollama_base_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("Ollama base URL must start with http:// or https://")
        return v.rstrip("/")

    @field_validator("nvidia_base_url")
    @classmethod
    def validate_nvidia_base_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("NVIDIA base URL must start with http:// or https://")
        return v.rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()