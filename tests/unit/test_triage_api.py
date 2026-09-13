"""Full pipeline API e2e (Slice 03): aimock LLM + fake search, <3s, fail-loud 502."""

import json
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from openai import AzureOpenAI

from src.main import app
from src.schemas import RunbookReference
from src.services import get_search_service, get_triage_service
from src.services.search_service import FakeSearchService, SearchServiceError
from src.services.triage_service import AzureOpenAITriageService

FIXTURES = json.loads(
    (Path(__file__).resolve().parents[1] / "fixtures" / "tickets.json").read_text()
)

RUNBOOKS = [RunbookReference(document_id="rb-1", title="MFA reset runbook", relevance_score=0.87)]


@pytest.fixture()
def client(aimock_port: int) -> Iterator[TestClient]:
    triage = AzureOpenAITriageService(
        AzureOpenAI(
            azure_endpoint=f"http://127.0.0.1:{aimock_port}",
            api_version="2024-12-01-preview",
            azure_deployment="gpt-4o-mini",
            api_key="mock",
            timeout=10.0,
        ),
        "gpt-4o-mini",
    )
    app.dependency_overrides[get_triage_service] = lambda: triage
    app.dependency_overrides[get_search_service] = lambda: FakeSearchService(RUNBOOKS)
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_pipeline_returns_enriched_result_under_3s(client: TestClient) -> None:
    payload = {
        "ticket_id": "T-8001",
        "customer_tier": "PREMIUM",
        "subject": "billing invoice mismatch",
        "body": "billing invoice is wrong this month",
    }
    start = time.perf_counter()
    resp = client.post("/api/v1/triage", json=payload)
    elapsed = time.perf_counter() - start
    assert resp.status_code == 200, resp.text
    assert resp.elapsed.total_seconds() < 3.0, f"took {elapsed:.2f}s"
    body = resp.json()
    assert body["category"] == "Billing"
    assert body["severity"] == "P2_HIGH"
    assert body["ticket_id"] == "T-8001"
    assert body["matched_runbooks"] == [
        {"document_id": "rb-1", "title": "MFA reset runbook", "relevance_score": 0.87}
    ]


def test_pipeline_critical_fixture(client: TestClient) -> None:
    payload = {
        "ticket_id": "T-8002",
        "customer_tier": "ENTERPRISE",
        "subject": "mfa outage",
        "body": "mfa outage blocks sign-in",
    }
    resp = client.post("/api/v1/triage", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["category"] == "Authentication"
    assert body["severity"] == "P1_CRITICAL"


def test_search_failure_returns_502(client: TestClient) -> None:
    class BrokenSearch:
        def search_runbooks(self, query: str, top: int = 2) -> list[RunbookReference]:
            raise SearchServiceError("simulated search outage")

    app.dependency_overrides[get_search_service] = lambda: BrokenSearch()  # type: ignore[arg-type]
    payload = {
        "ticket_id": "T-8001",
        "customer_tier": "PREMIUM",
        "subject": "billing invoice mismatch",
        "body": "billing invoice is wrong this month",
    }
    resp = client.post("/api/v1/triage", json=payload)
    assert resp.status_code == 502
    assert "search outage" in resp.json()["detail"]


def test_oversized_body_returns_422(client: TestClient) -> None:
    payload = {
        "ticket_id": "T-8001",
        "customer_tier": "PREMIUM",
        "subject": "billing invoice mismatch",
        "body": "x" * 20_001,
    }
    resp = client.post("/api/v1/triage", json=payload)
    assert resp.status_code == 422
    errors = resp.json().get("detail", [])
    assert any(e.get("loc") == ["body", "body"] for e in errors)
