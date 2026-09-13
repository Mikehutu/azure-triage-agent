"""Settings unit tests — env-name-only config contract (Slice 01)."""

from _pytest.monkeypatch import MonkeyPatch

from src.config import Settings, get_settings


def test_defaults() -> None:
    s = get_settings()
    assert s.azure_openai_chat_deployment == "gpt-4o-mini"
    assert s.azure_search_index_name == "kb-runbooks-index"
    assert s.mock is False


def test_env_override(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("AZURE_TRIAGE_MOCK", "true")
    assert Settings().mock is True
