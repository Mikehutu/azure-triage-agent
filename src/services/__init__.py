"""Service wiring: production (managed identity) and mock (aimock) clients."""

from __future__ import annotations

from openai import AzureOpenAI

from src.config import Settings, get_settings
from src.services.triage_service import (
    AzureOpenAIClient,
    AzureOpenAITriageService,
    ITriageService,
)

__all__ = [
    "AzureOpenAIClient",
    "AzureOpenAITriageService",
    "ITriageService",
    "create_triage_service",
]


def _build_managed_identity_client(settings: Settings) -> AzureOpenAI:
    """Production client: DefaultAzureCredential (user-assigned managed identity).

    No secrets anywhere — the SDK retrieves the token from the identity.
    """
    from azure.identity import DefaultAzureCredential

    credential = DefaultAzureCredential()
    return AzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_version=settings.azure_openai_api_version,
        azure_deployment=settings.azure_openai_chat_deployment,
        azure_ad_token_provider=lambda: (
            credential.get_token("https://cognitiveservices.azure.com/.default").token
        ),
        timeout=settings.request_timeout_seconds,
    )


def _build_mock_client(settings: Settings) -> AzureOpenAI:
    """Offline client for aimock (dummy key, local endpoint)."""
    return AzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_version=settings.azure_openai_api_version,
        azure_deployment=settings.azure_openai_chat_deployment,
        api_key="mock",
        timeout=settings.request_timeout_seconds,
    )


def create_triage_service(settings: Settings | None = None) -> ITriageService:
    """Build a triage service honoring AZURE_TRIAGE_MOCK (see INFRASTRUCTURE.md)."""
    settings = settings or get_settings()
    client: AzureOpenAI = (
        _build_mock_client(settings) if settings.mock else _build_managed_identity_client(settings)
    )
    return AzureOpenAITriageService(client, settings.azure_openai_chat_deployment)
