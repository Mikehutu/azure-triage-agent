"""Runbook retrieval (Slice 03): Azure AI Search hybrid retrieval.

Fail-loud on every failure path (no silent fallback). Offline runs use
FakeSearchService — the deterministic dev/test adapter.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from src.schemas import RunbookReference


class SearchServiceError(RuntimeError):
    """Raised when runbook retrieval cannot be completed."""


@runtime_checkable
class ISearchService(Protocol):
    """Contract (PRD Interface Definitions): top-N hybrid runbook lookups."""

    def search_runbooks(self, query: str, top: int = 2) -> list[RunbookReference]:
        """Hybrid-search the kb-runbooks-index for the top-N matching runbooks."""
        ...


class SearchClientLike(Protocol):
    """Azure AI Search SDK surface needed by AzureAISearchService (mock-friendly)."""

    def search(
        self,
        search_text: str,
        *,
        top: int = 2,
        search_mode: str = "all",
        select: list[str] | None = None,
        **kwargs: Any,
    ) -> Any: ...


class AzureAISearchService:
    """Hybrid search against kb-runbooks-index via the Azure AI Search SDK."""

    def __init__(self, client: SearchClientLike, index_name: str) -> None:
        self._client = client
        self._index_name = index_name

    def search_runbooks(self, query: str, top: int = 2) -> list[RunbookReference]:
        if top <= 0:
            raise SearchServiceError("top must be a positive integer")
        if not query.strip():
            raise SearchServiceError("search query must be non-empty")
        try:
            results = self._client.search(
                query,
                top=top,
                search_mode="all",  # hybrid: text + vector when embeddings are wired
                select=["document_id", "title"],
            )
            refs: list[RunbookReference] = []
            seen: set[str] = set()
            for item in results:
                document_id = str(item["document_id"])
                if document_id in seen:
                    continue  # chunked indexes can emit duplicates (agy F-01)
                seen.add(document_id)
                refs.append(
                    RunbookReference(
                        document_id=document_id,
                        title=str(item["title"]),
                        relevance_score=float(item.get("@search.score", 0.0)),
                    )
                )
            return refs
        except Exception as exc:
            raise SearchServiceError(f"runbook search failed: {exc}") from exc


class FakeSearchService:
    """In-process dev/test adapter — deterministic, offline. Never ships to prod."""

    def __init__(self, runbooks: list[RunbookReference] | None = None) -> None:
        self._runbooks = list(runbooks or [])

    def search_runbooks(self, query: str, top: int = 2) -> list[RunbookReference]:
        if top <= 0:
            raise SearchServiceError("top must be a positive integer")
        return self._runbooks[:top]
