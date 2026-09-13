"""API contract tests — FR-1 (Slice 01).

Covers the validation-facing contract: 422 on malformed payloads with
field-level detail, 200/501 lifecycle until service wiring lands (slice 02+).
"""

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)

VALID = {
    "ticket_id": "T-2002",
    "customer_tier": "ENTERPRISE",
    "subject": "Auth failures after MFA rollout",
    "body": "Users report intermittent failed sign-ins since the MFA change.",
}


def test_healthz_ok() -> None:
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_invalid_tier_returns_422_with_field_detail() -> None:
    resp = client.post("/api/v1/triage", json={**VALID, "customer_tier": "GOLD"})
    assert resp.status_code == 422
    errors = resp.json().get("detail", [])
    assert any(e.get("loc") == ["body", "customer_tier"] for e in errors)


def test_missing_field_returns_422() -> None:
    resp = client.post("/api/v1/triage", json={k: v for k, v in VALID.items() if k != "ticket_id"})
    assert resp.status_code == 422
    errors = resp.json().get("detail", [])
    assert any(e.get("loc") == ["body", "ticket_id"] for e in errors)


def test_extra_field_returns_422() -> None:
    resp = client.post("/api/v1/triage", json={**VALID, "extra": 1})
    assert resp.status_code == 422


def test_valid_payload_interim_501_until_wiring() -> None:
    """Slice 01: valid payloads are accepted by the schema but the triage
    pipeline is not wired yet -> 501 (fail loud, no fake result)."""
    resp = client.post("/api/v1/triage", json=VALID)
    assert resp.status_code == 501
