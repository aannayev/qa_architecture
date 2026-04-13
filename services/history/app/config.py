from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)

    environment: str = Field(default="local", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    service_name: str = Field(default="history-service", alias="OTEL_SERVICE_NAME")

    database_url: str = Field(
        default="postgresql+asyncpg://history:history@postgres:5432/history",
        alias="DATABASE_URL",
    )

    otlp_endpoint: str | None = Field(default=None, alias="OTEL_EXPORTER_OTLP_ENDPOINT")

    unleash_url: str | None = Field(default=None, alias="UNLEASH_URL")
    unleash_api_token: str | None = Field(default=None, alias="UNLEASH_API_TOKEN")
    unleash_app_name: str = Field(default="history-service", alias="UNLEASH_APP_NAME")

    seed_on_startup: bool = Field(default=True, alias="HISTORY_SEED_ON_STARTUP")


@lru_cache
def get_settings() -> Settings:
    return Settings()
