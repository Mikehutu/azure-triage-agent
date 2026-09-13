"""End-to-end classification test against a real aimock server (offline, keyless)."""

import pytest
from openai import AzureOpenAI

from src.schemas import TicketPayload
from src.services.triage_service import AzureOpenAITriageService, TriageServiceError


def _client(port: int) -> AzureOpenAI:
    return AzureOpenAI(
        azure_endpoint=f"http://127.0.0.1:{port}",
        api_version="2024-12-01-preview",
        azure_deployment="gpt-4o-mini",
        api_key="mock",
        timeout=10.0,
    )


def test_aimock_classification_billing(aimock_port: int) -> None:
    service = AzureOpenAITriageService(_client(aimock_port), "gpt-4o-mini")
    payload = TicketPayload(
        ticket_id="T-8001",
        customer_tier="PREMIUM",
        subject="billing invoice mismatch",
        body="billing invoice is wrong this month",
    )
    result = service.classify(payload)
    assert result.category == "Billing"
    assert result.severity == "P2_HIGH"
    assert result.ticket_id == "T-8001"
    assert result.matched_runbooks == []


def test_aimock_throttling_surfaces_error(aimock_port: int) -> None:
    service = AzureOpenAITriageService(_client(aimock_port), "gpt-4o-mini")
    payload = TicketPayload(
        ticket_id="T-8003",
        customer_tier="ENTERPRISE",
        subject="throttle test please",
        body="throttle test please simulate rate limiting",
    )
    with pytest.raises(TriageServiceError, match="classification request failed"):
        service.classify(payload)
