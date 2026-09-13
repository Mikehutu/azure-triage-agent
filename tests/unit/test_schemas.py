"""Schema validation unit tests — FR-1 contract (Slice 01)."""

import pytest
from pydantic import ValidationError

from src.schemas import TicketPayload

VALID: dict[str, str] = {
    "ticket_id": "T-1001",
    "customer_tier": "PREMIUM",
    "subject": "Billing discrepancy on invoice 4/2026",
    "body": "Invoice total does not match the agreed contract price.",
}


def test_valid_payload_roundtrip() -> None:
    payload = TicketPayload.model_validate(VALID)
    assert payload.ticket_id == "T-1001"
    assert payload.customer_tier == "PREMIUM"


@pytest.mark.parametrize("tier", ["STANDARD", "PREMIUM", "ENTERPRISE"])
def test_all_tiers_accepted(tier: str) -> None:
    assert TicketPayload.model_validate({**VALID, "customer_tier": tier}).customer_tier == tier


def test_unknown_tier_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        TicketPayload.model_validate({**VALID, "customer_tier": "GOLD"})
    assert any("customer_tier" in e["loc"] for e in exc.value.errors())


def test_missing_ticket_id_rejected() -> None:
    with pytest.raises(ValidationError):
        TicketPayload.model_validate({k: v for k, v in VALID.items() if k != "ticket_id"})


def test_empty_body_rejected() -> None:
    with pytest.raises(ValidationError):
        TicketPayload.model_validate({**VALID, "body": ""})


def test_empty_subject_rejected() -> None:
    with pytest.raises(ValidationError):
        TicketPayload.model_validate({**VALID, "subject": ""})


def test_extra_field_rejected() -> None:
    with pytest.raises(ValidationError):
        TicketPayload.model_validate({**VALID, "unexpected": "x"})


def test_whitespace_only_body_rejected() -> None:
    with pytest.raises(ValidationError):
        TicketPayload.model_validate({**VALID, "body": "   \t\n  "})


def test_whitespace_only_subject_rejected() -> None:
    with pytest.raises(ValidationError):
        TicketPayload.model_validate({**VALID, "subject": "   "})
