"""Configuration for Inbox Agent service."""
from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""

    # Server
    host: str = Field(default="0.0.0.0", alias="INBOX_HOST")
    port: int = Field(default=8001, alias="INBOX_PORT")

    # Knowledge Brain Integration
    kb_api_url: str = Field(default="http://localhost:8000", alias="KB_API_URL")

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./inbox.db",
        alias="INBOX_DATABASE_URL",
    )

    # Autonomy & Confidence Rules
    autonomy_approval_threshold: int = Field(default=20, alias="AUTONOMY_APPROVAL_THRESHOLD")
    auto_send_confidence_threshold: float = Field(default=0.85, alias="AUTO_SEND_CONFIDENCE_THRESHOLD")
    escalation_confidence_threshold: float = Field(default=0.40, alias="ESCALATION_CONFIDENCE_THRESHOLD")

    # LLM
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    claude_default_model: str = Field(default="claude-sonnet-4-20250514", alias="CLAUDE_DEFAULT_MODEL")
    mock_mode: bool = Field(default=False, alias="MOCK_MODE")

    base_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent)

    model_config = {"env_file": ".env", "extra": "ignore", "populate_by_name": True}

    @property
    def has_anthropic_key(self) -> bool:
        return bool(self.anthropic_api_key) and self.anthropic_api_key != "your-anthropic-api-key-here"


settings = Settings()
