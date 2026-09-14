"""Practical end-to-end tests for core API lifecycles over live HTTP.

Validates the full request-response lifecycle across live TCP sockets, verifying
classification, SLA severity assignment, runbook enrichment, and latency budgets.
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx

from src.schemas import TriageResult


def test_health_check_live(api_client: httpx.Client) -> None:
    """Validate GET /healthz liveness probe on live server."""
    resp = api_client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    assert resp.elapsed.total_seconds() < 0.5


def test_triage_standard_billing_flow(api_client: httpx.Client) -> None:
    """Validate full end-to-end triage of a standard billing inquiry."""
    payload = {
        "ticket_id": "T-8001",
        "customer_tier": "PREMIUM",
        "subject": "billing invoice mismatch for current month",
        "body": "billing invoice shows discrepancies in enterprise line items.",
    }

    start = time.perf_counter()
    resp = api_client.post("/api/v1/triage", json=payload)
    elapsed = time.perf_counter() - start

    assert resp.status_code == 200, resp.text
    data = resp.json()

    # Validate schema compliance using Pydantic
    result = TriageResult.model_validate(data)
    assert result.ticket_id == "T-8001"
    assert result.category == "Billing"
    assert result.severity == "P2_HIGH"
    assert len(result.summary) > 0
    assert len(result.suggested_action) > 0
    assert len(result.matched_runbooks) > 0

    # Ensure runbook metadata is well-formed
    first_runbook = result.matched_runbooks[0]
    assert first_runbook.document_id.startswith("rb-")
    assert len(first_runbook.title) > 0
    assert 0.0 <= first_runbook.relevance_score <= 1.0

    # SLA latency constraint (< 3.0 seconds)
    assert elapsed < 3.0, f"Request exceeded 3s SLA budget: {elapsed:.3f}s"


def test_triage_critical_mfa_incident_flow(api_client: httpx.Client) -> None:
    """Validate critical incident escalation with P1 severity."""
    payload = {
        "ticket_id": "T-8002",
        "customer_tier": "ENTERPRISE",
        "subject": "critical mfa outage affecting all logins",
        "body": "mfa outage blocks user sign-in across all European tenants.",
    }

    resp = api_client.post("/api/v1/triage", json=payload)
    assert resp.status_code == 200, resp.text

    result = TriageResult.model_validate(resp.json())
    assert result.ticket_id == "T-8002"
    assert result.category == "Authentication"
    assert result.severity == "P1_CRITICAL"
    assert len(result.matched_runbooks) > 0


def test_triage_latency_budget(api_client: httpx.Client) -> None:
    """Verify that average round-trip latency easily satisfies the <3s SLA budget."""
    payload = {
        "ticket_id": "T-8001",
        "customer_tier": "STANDARD",
        "subject": "billing invoice correction needed",
        "body": "billing invoice requires adjustment for prorated subscription.",
    }

    durations: list[float] = []
    for _ in range(5):
        t0 = time.perf_counter()
        resp = api_client.post("/api/v1/triage", json=payload)
        durations.append(time.perf_counter() - t0)
        assert resp.status_code == 200

    avg_duration = sum(durations) / len(durations)
    # Even across multiple iterations, local pipeline should respond well under 500ms
    assert avg_duration < 1.0, f"Average latency too high: {avg_duration:.3f}s"


def test_concurrent_triage_requests(api_client: httpx.Client) -> None:
    """Verify statelessness and lack of race conditions under concurrent client requests."""
    payloads = [
        {
            "ticket_id": "T-8001",
            "customer_tier": "PREMIUM",
            "subject": f"billing invoice query {i}",
            "body": f"billing invoice query body content number {i}",
        }
        for i in range(10)
    ]

    def send(item: dict[str, str]) -> tuple[int, dict[str, str]]:
        r = api_client.post("/api/v1/triage", json=item)
        return r.status_code, r.json()

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(send, p) for p in payloads]
        for f in as_completed(futures):
            code, json_data = f.result()
            assert code == 200
            assert json_data["category"] == "Billing"
            assert json_data["severity"] == "P2_HIGH"
