"""Classification engine unit tests (Slice 02) — mocked client via dependency injection."""

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from src.config import Settings
from src.schemas import TicketPayload
from src.services import create_triage_service
from src.services.triage_service import AzureOpenAITriageService, TriageServiceError

FIXTURES = json.loads(
    (Path(__file__).resolve().parents[1] / "fixtures" / "tickets.json").read_text()
)

PAYLOAD = TicketPayload(**FIXTURES["critical"])
VALID_JSON = json.dumps(
    {
        "ticket_id": PAYLOAD.ticket_id,
        "category": "Infrastructure",
        "severity": "P1_CRITICAL",
        "summary": "Billing portal outage",
        "suggested_action": "Escalate to infra on-call, verify origin status",
        "matched_runbooks": [],
    }
)


def _recording_client(
    content: str | None = None, *, error: Exception | None = None
) -> tuple[Any, dict[str, Any]]:
    seen: dict[str, Any] = {}

    def _create(**kwargs: Any) -> Any:
        seen.update(kwargs)
        if error is not None:
            raise error
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=_create)))
    return client, seen


def test_classify_builds_correct_request() -> None:
    client, seen = _recording_client(VALID_JSON)
    service = AzureOpenAITriageService(client, "gpt-4o-mini")
    result = service.classify(PAYLOAD)

    assert result.category == "Infrastructure"
    assert result.severity == "P1_CRITICAL"
    assert seen["model"] == "gpt-4o-mini"
    assert seen["temperature"] == 0.0
    fmt = seen["response_format"]
    assert fmt["type"] == "json_schema"
    assert fmt["json_schema"]["strict"] is True
    schema = fmt["json_schema"]["schema"]
    assert schema.get("additionalProperties") is False
    assert schema["properties"]["matched_runbooks"]["items"]["additionalProperties"] is False


@pytest.mark.parametrize("fixture_key", ["standard", "critical"])
def test_fixtures_classify_within_schema(fixture_key: str) -> None:
    payload = TicketPayload(**FIXTURES[fixture_key])
    expected = FIXTURES["expected"][fixture_key]
    resp = json.dumps(
        {
            "ticket_id": payload.ticket_id,
            "category": expected["category"],
            "severity": expected["severity"],
            "summary": "fixture",
            "suggested_action": "fixture",
            "matched_runbooks": [],
        }
    )
    client, _ = _recording_client(resp)
    result = AzureOpenAITriageService(client, "gpt-4o-mini").classify(payload)
    assert result.category == expected["category"]
    assert result.severity == expected["severity"]


def test_malformed_json_raises() -> None:
    client, _ = _recording_client('{"category": "Billing"')  # truncated
    with pytest.raises(TriageServiceError):
        AzureOpenAITriageService(client, "gpt-4o-mini").classify(PAYLOAD)


def test_out_of_enum_value_raises() -> None:
    bad = json.dumps(
        {
            "ticket_id": PAYLOAD.ticket_id,
            "category": "Magic",
            "severity": "P1_CRITICAL",
            "summary": "x",
            "suggested_action": "y",
            "matched_runbooks": [],
        }
    )
    client, _ = _recording_client(bad)
    with pytest.raises(TriageServiceError):
        AzureOpenAITriageService(client, "gpt-4o-mini").classify(PAYLOAD)


def test_empty_content_raises() -> None:
    client, _ = _recording_client(None)
    with pytest.raises(TriageServiceError):
        AzureOpenAITriageService(client, "gpt-4o-mini").classify(PAYLOAD)


def test_provider_error_raises_triage_error() -> None:
    client, _ = _recording_client(error=RuntimeError("429 rate limit"))
    with pytest.raises(TriageServiceError, match="classification request failed"):
        AzureOpenAITriageService(client, "gpt-4o-mini").classify(PAYLOAD)


def test_mismatched_ticket_id_raises() -> None:
    mismatched = json.dumps(
        {
            "ticket_id": "DIFFERENT",
            "category": "Billing",
            "severity": "P4_LOW",
            "summary": "x",
            "suggested_action": "y",
            "matched_runbooks": [],
        }
    )
    client, _ = _recording_client(mismatched)
    with pytest.raises(TriageServiceError, match="mismatched ticket_id"):
        AzureOpenAITriageService(client, "gpt-4o-mini").classify(PAYLOAD)


def test_create_service_mock_branch(monkeypatch: Any) -> None:
    captured: dict[str, Any] = {}

    class FakeAzureOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            captured.update(kwargs)

    import src.services as services

    monkeypatch.setattr(services, "AzureOpenAI", FakeAzureOpenAI)
    service = create_triage_service(
        Settings(mock=True, azure_openai_endpoint="http://127.0.0.1:4010")
    )
    assert isinstance(service, AzureOpenAITriageService)
    assert captured["api_key"] == "mock"
    assert captured["azure_endpoint"] == "http://127.0.0.1:4010"


def test_create_service_managed_identity_branch(monkeypatch: Any) -> None:
    captured: dict[str, Any] = {}

    class FakeAzureOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            captured.update(kwargs)

    import src.services as services

    monkeypatch.setattr(services, "AzureOpenAI", FakeAzureOpenAI)
    create_triage_service(Settings())
    assert captured["azure_endpoint"].startswith("https://placeholder")
    assert callable(captured["azure_ad_token_provider"])
    assert "api_key" not in captured
