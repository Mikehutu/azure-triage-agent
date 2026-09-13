"""Pydantic-settings configuration.

Env var NAMES only — never values. No secrets in code, docs, or commits.
All cloud endpoints are optional-sensible placeholders; real deployments set
the env vars. See INFRASTRUCTURE.md for the full list.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, sourced from AZURE_TRIAGE_* environment variables."""

    model_config = SettingsConfigDict(env_prefix="AZURE_TRIAGE_", extra="forbid")

    azure_openai_endpoint: str = Field(
        default="https://placeholder.openai.azure.com/",
        description="Azure OpenAI resource endpoint (https://<account>.openai.azure.com/)",
    )
    azure_openai_api_version: str = Field(default="2024-12-01-preview")
    azure_openai_chat_deployment: str = Field(default="gpt-4o-mini")
    azure_search_service_endpoint: str = Field(
        default="https://placeholder.search.windows.net",
        description="Azure AI Search service endpoint",
    )
    azure_search_index_name: str = Field(default="kb-runbooks-index")
    request_timeout_seconds: float = Field(default=5.0, gt=0.0)
    mock: bool = Field(default=False, description="Use local mocks (aimock) instead of real Azure")


@lru_cache
def get_settings() -> Settings:
    """Process-wide cached settings (constructed once; env changes need restart)."""
    return Settings()
