from nyayaai.models import Clause
from nyayaai.services import llm_service


def test_make_context_contains_clause_citations() -> None:
    context = llm_service.make_context([Clause("C1", "Payment is due monthly.", 3)])
    assert "[C1, page 3]" in context
    assert "Payment is due monthly." in context


def test_summarize_sanitizes_unknown_risk_citations(monkeypatch) -> None:
    monkeypatch.setattr(
        llm_service,
        "ask_llm",
        lambda system, user: (
            '{"summary":"Payment is monthly.",'
            '"risks":[{"text":"Review payment","citation":"C1, page 2"},'
            '{"text":"Invented","citation":"C99, page 9"}]}'
        ),
    )
    result = llm_service.summarize([Clause("C1", "Payment is monthly.", 2)])
    assert result["summary"] == "Payment is monthly."
    assert len(result["risks"]) == 1
    assert result["risks"][0]["citation"] == "C1, page 2"


def test_summarize_handles_non_json_model_output(monkeypatch) -> None:
    monkeypatch.setattr(llm_service, "ask_llm", lambda system, user: "plain answer")
    result = llm_service.summarize([Clause("C1", "Payment is monthly.")])
    assert result == {"summary": "plain answer", "risks": []}


def test_get_llm_requires_api_key(monkeypatch) -> None:
    from types import SimpleNamespace

    from fastapi import HTTPException

    monkeypatch.setattr(llm_service, "settings", SimpleNamespace(groq_api_key=""))
    try:
        llm_service.get_llm()
    except HTTPException as exc:
        assert exc.status_code == 503
    else:
        raise AssertionError("Expected missing-key error")


def test_ask_llm_returns_model_content(monkeypatch) -> None:
    from types import SimpleNamespace

    class FakeCompletions:
        def create(self, **kwargs):
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="answer"))])

    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    monkeypatch.setattr(llm_service, "get_llm", lambda: fake_client)
    assert llm_service.ask_llm("system", "user") == "answer"


def test_ask_llm_rejects_empty_model_response(monkeypatch) -> None:
    from types import SimpleNamespace

    from fastapi import HTTPException

    class FakeCompletions:
        def create(self, **kwargs):
            return SimpleNamespace(choices=[])

    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    monkeypatch.setattr(llm_service, "get_llm", lambda: fake_client)
    try:
        llm_service.ask_llm("system", "user")
    except HTTPException as exc:
        assert exc.status_code == 502
    else:
        raise AssertionError("Expected empty-response error")
