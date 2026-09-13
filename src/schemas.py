"""Pydantic schemas for the enterprise ticket triage API.

Enterprise rails: Literal-constrained enums, no secrets, extra fields forbidden,
non-blank text fields (agy F-02).
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

CustomerTier = Literal["STANDARD", "PREMIUM", "ENTERPRISE"]
Category = Literal["Billing", "Authentication", "Infrastructure", "Product Defect"]
Severity = Literal["P1_CRITICAL", "P2_HIGH", "P3_MEDIUM", "P4_LOW"]


class TicketPayload(BaseModel):
    """Inbound ticket payload from the caller.

    Rejects unknown fields (extra=forbid) so a misshapen upstream payload fails
    loud instead of being silently ignored.
    """

    model_config = {"extra": "forbid"}

    ticket_id: str = Field(min_length=1)
    customer_tier: CustomerTier = Field(description="STANDARD, PREMIUM, or ENTERPRISE")
    subject: str = Field(min_length=1)
    body: str = Field(min_length=1)

    @field_validator("subject", "body")
    @classmethod
    def _reject_blank(cls, value: str) -> str:
        """Reject whitespace-only strings (agy F-02, 2026-09-13)."""
        if not value.strip():
            raise ValueError("must contain non-whitespace characters")
        return value


class RunbookReference(BaseModel):
    """A single runbook hit returned by the search service."""

    document_id: str
    title: str
    relevance_score: float


class TriageResult(BaseModel):
    """Enriched ticket payload returned to the human support agent."""

    ticket_id: str
    category: Category
    severity: Severity
    summary: str
    suggested_action: str
    matched_runbooks: list[RunbookReference]
