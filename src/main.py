"""FastAPI application for the enterprise ticket triage & enrichment agent.

Slice 01: API surface shell + validation contract. Service wiring lands in
slice 02 (Azure OpenAI classification) and slice 03 (Azure AI Search runbook
retrieval). Until then, valid payloads respond 501 (fail loud, never fake a
triage result).
"""

from fastapi import FastAPI, HTTPException

from src.schemas import TicketPayload, TriageResult

app = FastAPI(title="azure-triage-agent", version="0.1.0")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.post(
    "/api/v1/triage",
    response_model=TriageResult,
    responses={
        422: {"description": "Validation error"},
        501: {"description": "Triage pipeline not wired (slice 02+)"},
    },
)
def triage(payload: TicketPayload) -> TriageResult:
    """Validate a ticket payload (FR-1).

    Returns HTTP 422 with field-level detail on invalid payloads. Validation is
    schema-enforced before any service code runs.
    """
    raise HTTPException(status_code=501, detail="triage pipeline not wired yet (slice 02)")
