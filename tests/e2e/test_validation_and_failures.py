"""Practical end-to-end tests for validation, edge cases, and provider failure handling.

Validates that malformed inputs trigger HTTP 422 with field locations and that upstream
provider errors (such as AI rate limiting) fail loud with HTTP 502 rather than returning
fabricated or degraded results.
"""

import httpx


def test_upstream_throttling_surfaces_502(api_client: httpx.Client) -> None:
    """Validate that upstream AI rate limiting (HTTP 429) fails loud as HTTP 502."""
    payload = {
        "ticket_id": "T-8003",
        "customer_tier": "ENTERPRISE",
        "subject": "trigger throttle test please",
        "body": "throttle test simulation to test rate limit error handling.",
    }

    resp = api_client.post("/api/v1/triage", json=payload)
    assert resp.status_code == 502, f"Expected 502, got {resp.status_code}: {resp.text}"

    detail = resp.json().get("detail", "")
    assert "classification request failed" in detail or "Rate limit" in detail


def test_invalid_customer_tier_returns_422(api_client: httpx.Client) -> None:
    """Validate that unapproved customer tiers are rejected with 422."""
    payload = {
        "ticket_id": "T-8001",
        "customer_tier": "GOLD",  # Only STANDARD, PREMIUM, ENTERPRISE allowed
        "subject": "billing invoice issue",
        "body": "billing invoice is incorrect.",
    }

    resp = api_client.post("/api/v1/triage", json=payload)
    assert resp.status_code == 422
    errors = resp.json().get("detail", [])
    assert any(e.get("loc") == ["body", "customer_tier"] for e in errors)


def test_whitespace_only_subject_returns_422(api_client: httpx.Client) -> None:
    """Validate rejection of whitespace-only subject strings."""
    payload = {
        "ticket_id": "T-8001",
        "customer_tier": "STANDARD",
        "subject": "    \t\n   ",
        "body": "Valid body text describing a legitimate problem.",
    }

    resp = api_client.post("/api/v1/triage", json=payload)
    assert resp.status_code == 422
    errors = resp.json().get("detail", [])
    assert any(e.get("loc") == ["body", "subject"] for e in errors)


def test_whitespace_only_body_returns_422(api_client: httpx.Client) -> None:
    """Validate rejection of whitespace-only body strings."""
    payload = {
        "ticket_id": "T-8001",
        "customer_tier": "STANDARD",
        "subject": "Legitimate Subject",
        "body": "    ",
    }

    resp = api_client.post("/api/v1/triage", json=payload)
    assert resp.status_code == 422
    errors = resp.json().get("detail", [])
    assert any(e.get("loc") == ["body", "body"] for e in errors)


def test_missing_mandatory_field_returns_422(api_client: httpx.Client) -> None:
    """Validate that missing required fields trigger 422 with field pointer."""
    payload = {
        # ticket_id intentionally omitted
        "customer_tier": "PREMIUM",
        "subject": "billing invoice question",
        "body": "billing invoice detail.",
    }

    resp = api_client.post("/api/v1/triage", json=payload)
    assert resp.status_code == 422
    errors = resp.json().get("detail", [])
    assert any(e.get("loc") == ["body", "ticket_id"] for e in errors)


def test_extra_injected_fields_rejected_422(api_client: httpx.Client) -> None:
    """Validate strict schema enforcement (extra='forbid') against unknown fields."""
    payload = {
        "ticket_id": "T-8001",
        "customer_tier": "PREMIUM",
        "subject": "billing invoice issue",
        "body": "billing invoice detail.",
        "injected_field": "unauthorized_metadata",
    }

    resp = api_client.post("/api/v1/triage", json=payload)
    assert resp.status_code == 422
    errors = resp.json().get("detail", [])
    assert any(e.get("loc") == ["body", "injected_field"] for e in errors)


def test_oversized_body_returns_422(api_client: httpx.Client) -> None:
    """Validate that payloads exceeding 20,000 characters are rejected with 422."""
    payload = {
        "ticket_id": "T-8001",
        "customer_tier": "PREMIUM",
        "subject": "billing invoice oversized",
        "body": "A" * 20_001,
    }

    resp = api_client.post("/api/v1/triage", json=payload)
    assert resp.status_code == 422
    errors = resp.json().get("detail", [])
    assert any(e.get("loc") == ["body", "body"] for e in errors)


def test_invalid_json_payload_returns_422(api_client: httpx.Client) -> None:
    """Validate that non-JSON request bodies return 422."""
    resp = api_client.post(
        "/api/v1/triage",
        content="this is not valid json",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 422
