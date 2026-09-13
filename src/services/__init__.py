"""Service wiring: production (managed identity) + offline mock clients.

Dependency-injection friendly: unit tests inject recording stubs; the API
e2e overrides these via FastAPI dependency_overrides (see test_triage_api.py).
"""

from __future__ import annotations

from functools import lru_cache

from openai import AzureOpenAI

from src.config import Settings, get_settings
from src.services.search_service import (
    AzureAISearchService,
    ISearchService,
    SearchServiceError,
)
from src.services.triage_service import (
    AzureOpenAIClient,
    AzureOpenAITriageService,
    ITriageService,
)

__all__ = [
    "AzureAISearchService",
    "AzureOpenAIClient",
    "AzureOpenAITriageService",
    "ISearchService",
    "ITriageService",
    "SearchServiceError",
    "create_search_service",
    "create_triage_service",
    "get_search_service",
    "get_triage_service",
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


def create_search_service(settings: Settings | None = None) -> ISearchService:
    """Build the Azure AI Search runbook retriever (managed identity auth)."""
    settings = settings or get_settings()
    from azure.identity import DefaultAzureCredential
    from azure.search.documents import SearchClient

    client = SearchClient(
        endpoint=settings.azure_search_service_endpoint,
        index_name=settings.azure_search_index_name,
        credential=DefaultAzureCredential(),
    )
    return AzureAISearchService(client, settings.azure_search_index_name)


@lru_cache
def get_triage_service() -> ITriageService:
    """Cached FastAPI dependency (env changes need restart)."""
    return create_triage_service()


@lru_cache
def get_search_service() -> ISearchService:
    """Cached FastAPI dependency (env changes need restart)."""
    return create_search_service()
