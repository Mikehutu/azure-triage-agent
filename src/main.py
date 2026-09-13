"""FastAPI application for the enterprise ticket triage & enrichment agent.

Slice 03: full pipeline wired — validation (FR-1) → classification (FR-2) →
runbook retrieval (FR-3) → enriched TriageResult. Provider failures surface as
HTTP 502 (fail loud, never a fake/enriched fallback).
"""

from fastapi import Depends, FastAPI, HTTPException

from src.schemas import TicketPayload, TriageResult
from src.services import SearchServiceError, get_search_service, get_triage_service
from src.services.search_service import ISearchService
from src.services.triage_service import ITriageService, TriageServiceError

app = FastAPI(title="azure-triage-agent", version="0.2.0")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.post(
    "/api/v1/triage",
    response_model=TriageResult,
    responses={
        422: {"description": "Validation error"},
        502: {"description": "Triage pipeline provider error (OpenAI/Search)"},
    },
)
def triage(
    payload: TicketPayload,
    triage_svc: ITriageService = Depends(get_triage_service),
    search_svc: ISearchService = Depends(get_search_service),
) -> TriageResult:
    """Validate, classify, and enrich a ticket payload (FR-1 / FR-2 / FR-3)."""
    try:
        result = triage_svc.classify(payload)
        runbooks = search_svc.search_runbooks(f"{payload.subject}\n{payload.body}", top=2)
        return TriageResult(
            **result.model_dump(exclude={"matched_runbooks"}), matched_runbooks=runbooks
        )
    except (TriageServiceError, SearchServiceError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
