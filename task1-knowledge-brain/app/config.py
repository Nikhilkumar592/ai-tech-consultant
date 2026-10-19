"""Configuration for Knowledge Brain service."""
from __future__ import annotations

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API
    host: str = Field(default="0.0.0.0", alias="KB_HOST")
    port: int = Field(default=8000, alias="KB_PORT")

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./knowledge_brain.db",
        alias="KB_DATABASE_URL",
    )
    chroma_path: str = Field(default="./chroma_data", alias="KB_CHROMA_PATH")
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2", alias="KB_EMBEDDING_MODEL"
    )

    # Crawler
    crawl_concurrency: int = Field(default=3, alias="KB_CRAWL_CONCURRENCY")
    crawl_delay_seconds: float = Field(default=2.0, alias="KB_CRAWL_DELAY_SECONDS")
    crawl_timeout_seconds: int = Field(default=30, alias="KB_CRAWL_TIMEOUT_SECONDS")
    crawl_max_retries: int = Field(default=3, alias="KB_CRAWL_MAX_RETRIES")
    crawl_batch_size: int = Field(default=10, alias="KB_CRAWL_BATCH_SIZE")

    # Claude
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    claude_default_model: str = Field(
        default="claude-sonnet-4-20250514", alias="CLAUDE_DEFAULT_MODEL"
    )
    claude_complex_model: str = Field(
        default="claude-sonnet-4-20250514", alias="CLAUDE_COMPLEX_MODEL"
    )
    claude_max_tokens: int = Field(default=4096, alias="CLAUDE_MAX_TOKENS")

    # Mode
    mock_mode: bool = Field(default=False, alias="MOCK_MODE")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Paths
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent)

    model_config = {"env_file": ".env", "extra": "ignore", "populate_by_name": True}

    @property
    def images_dir(self) -> Path:
        p = self.base_dir / "data" / "images"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def has_anthropic_key(self) -> bool:
        return bool(self.anthropic_api_key) and self.anthropic_api_key != "your-anthropic-api-key-here"


settings = Settings()
