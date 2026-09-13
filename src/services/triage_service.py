"""Triage service (Slice 02): Azure OpenAI structured-output classification.

Fail-fast on every failure path: no degraded/fallback classifications, no bare
excepts. Production auth via DefaultAzureCredential (managed identity); mock
mode for offline aimock tests.
"""

from __future__ import annotations

import json
from typing import Any, Protocol, get_args, runtime_checkable

from pydantic import ValidationError

from src.schemas import Category, Severity, TicketPayload, TriageResult

SYSTEM_PROMPT = (
    "You are an enterprise support ticket triage specialist. Classify each ticket into "
    "exactly one category (Billing, Authentication, Infrastructure, Product Defect) and one "
    "severity (P1_CRITICAL, P2_HIGH, P3_MEDIUM, P4_LOW). Return STRICT JSON matching the "
    "provided schema. Never invent runbook data; matched_runbooks may be empty."
)


class TriageServiceError(RuntimeError):
    """Raised when classification cannot be completed. Fail loud, never silent."""


@runtime_checkable
class ITriageService(Protocol):
    """Contract implemented by every triage service (PRD Interface Definitions)."""

    def classify(self, payload: TicketPayload) -> TriageResult:
        """Classify category/severity and enrich with runbooks.

        Raises on missing config or failed classification; no bare except.
        """
        ...


class _Completions(Protocol):
    def create(self, **kwargs: Any) -> Any: ...


class _Chat(Protocol):
    completions: _Completions


class AzureOpenAIClient(Protocol):
    """Minimal Azure OpenAI client surface (mock-friendly)."""

    @property
    def chat(self) -> Any:
        """Provider for chat.completions (the SDK's `chat` property)."""
        ...


def _strict_schema() -> dict[str, Any]:
    """Flat, strict JSON schema for the structured output (Azure-safe).

    No $defs/$ref (Azure json_schema mode prefers fully inlined schemas), and
    every object gets additionalProperties: false — required by strict mode.
    """
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "ticket_id": {"type": "string"},
            "category": {"type": "string", "enum": list(get_args(Category))},
            "severity": {"type": "string", "enum": list(get_args(Severity))},
            "summary": {"type": "string"},
            "suggested_action": {"type": "string"},
            "matched_runbooks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "document_id": {"type": "string"},
                        "title": {"type": "string"},
                        "relevance_score": {"type": "number"},
                    },
                    "required": ["document_id", "title", "relevance_score"],
                },
            },
        },
        "required": [
            "ticket_id",
            "category",
            "severity",
            "summary",
            "suggested_action",
            "matched_runbooks",
        ],
    }


class AzureOpenAITriageService:
    """Classification engine backed by Azure OpenAI structured outputs."""

    def __init__(self, client: AzureOpenAIClient, deployment: str) -> None:
        self._client = client
        self._deployment = deployment

    def classify(self, payload: TicketPayload) -> TriageResult:
        try:
            completion = self._client.chat.completions.create(
                model=self._deployment,
                temperature=0.0,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            f"ticket_id: {payload.ticket_id}\n"
                            f"customer_tier: {payload.customer_tier}\n"
                            f"subject: {payload.subject}\n"
                            f"body: {payload.body}"
                        ),
                    },
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "triage_result",
                        "schema": _strict_schema(),
                        "strict": True,
                    },
                },
            )
        except Exception as exc:
            raise TriageServiceError(f"classification request failed: {exc}") from exc

        if not completion.choices:
            raise TriageServiceError("classification returned no choices")
        content = completion.choices[0].message.content
        if not content:
            raise TriageServiceError("classification returned empty content")

        try:
            result = TriageResult.model_validate(json.loads(content))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise TriageServiceError(f"classification returned invalid payload: {exc}") from exc

        if result.ticket_id != payload.ticket_id:
            raise TriageServiceError("classification returned mismatched ticket_id")

        return result
