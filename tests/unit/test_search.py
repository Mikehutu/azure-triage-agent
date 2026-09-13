"""Search service unit tests (Slice 03) — mocked SDK client + fake adapter."""

from typing import Any

import pytest

from src.schemas import RunbookReference
from src.services.search_service import (
    AzureAISearchService,
    FakeSearchService,
    SearchServiceError,
)

RESULTS = [
    {"document_id": "rb-1", "title": "Password reset runbook", "@search.score": 0.87},
    {"document_id": "rb-2", "title": "MFA rollout runbook", "@search.score": 0.72},
]


class RecordingClient:
    def __init__(self, results: list[dict[str, Any]], error: Exception | None = None) -> None:
        self.results = results
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def search(
        self,
        search_text: str,
        *,
        top: int = 2,
        search_mode: str = "all",
        select: list[str] | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        self.calls.append({"text": search_text, "top": top, "mode": search_mode, "select": select})
        if self.error is not None:
            raise self.error
        return self.results


def test_maps_documents_and_scores() -> None:
    client = RecordingClient(RESULTS)
    refs = AzureAISearchService(client, "kb-runbooks-index").search_runbooks(
        "password reset", top=2
    )
    assert refs == [
        RunbookReference(document_id="rb-1", title="Password reset runbook", relevance_score=0.87),
        RunbookReference(document_id="rb-2", title="MFA rollout runbook", relevance_score=0.72),
    ]
    call = client.calls[-1]
    assert call["text"] == "password reset"
    assert call["top"] == 2
    assert call["mode"] == "all"  # hybrid semantics
    assert call["select"] == ["document_id", "title"]


def test_duplicate_document_ids_deduped() -> None:
    client = RecordingClient(
        [
            {"document_id": "rb-1", "title": "First", "@search.score": 0.9},
            {"document_id": "rb-1", "title": "Duplicate chunk", "@search.score": 0.5},
            {"document_id": "rb-2", "title": "Second", "@search.score": 0.4},
        ]
    )
    refs = AzureAISearchService(client, "idx").search_runbooks("q")
    assert [r.document_id for r in refs] == ["rb-1", "rb-2"]


def test_no_matches_returns_empty() -> None:
    refs = AzureAISearchService(RecordingClient([]), "idx").search_runbooks("nonsense query")
    assert refs == []


def test_index_missing_score_defaults_zero() -> None:
    client = RecordingClient([{"document_id": "rb-9", "title": "Sparse runbook"}])
    refs = AzureAISearchService(client, "idx").search_runbooks("q", top=1)
    assert refs[0].relevance_score == 0.0


def test_provider_error_raises_search_error() -> None:
    client = RecordingClient([], error=RuntimeError("search service down"))
    with pytest.raises(SearchServiceError, match="runbook search failed"):
        AzureAISearchService(client, "idx").search_runbooks("q")


def test_empty_query_raises() -> None:
    with pytest.raises(SearchServiceError, match="non-empty"):
        AzureAISearchService(RecordingClient([]), "idx").search_runbooks("   ")


def test_non_positive_top_raises() -> None:
    with pytest.raises(SearchServiceError, match="positive"):
        AzureAISearchService(RecordingClient([]), "idx").search_runbooks("q", top=0)


def test_fake_search_service_deterministic() -> None:
    fake = FakeSearchService(
        [
            RunbookReference(document_id="a", title="A", relevance_score=1.0),
            RunbookReference(document_id="b", title="B", relevance_score=0.5),
        ]
    )
    assert [r.document_id for r in fake.search_runbooks("anything", top=1)] == ["a"]
    assert fake.search_runbooks("anything", top=2) is not fake.search_runbooks(
        "anything", top=2
    )  # fresh slice
    assert FakeSearchService().search_runbooks("q") == []


def test_fake_non_positive_top_raises() -> None:
    with pytest.raises(SearchServiceError):
        FakeSearchService().search_runbooks("q", top=-1)
