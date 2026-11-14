"""Application settings for CheckStock (TASK_04)."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Pydantic settings loaded from environment/.env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://checkstock:checkstock@localhost:5432/checkstock"
    postgres_user: str = "checkstock"
    postgres_password: str = "checkstock"
    postgres_db: str = "checkstock"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    environment: str = "local"


settings = Settings()
