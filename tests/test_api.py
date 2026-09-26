from fastapi.testclient import TestClient

import nyayaai.main as main
from nyayaai.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["version"] == app.version


def test_rejects_invalid_file() -> None:
    response = client.post(
        "/api/upload",
        files={"file": ("test.exe", b"bad", "application/octet-stream")},
        data={"language": "English"},
    )
    assert response.status_code == 400


def test_uploads_text_document() -> None:
    main.DOCUMENTS.clear()
    response = client.post(
        "/api/upload",
        files={
            "file": (
                "agreement.txt",
                b"1. Payment\nPayment is due monthly.\n2. Termination\nThirty days notice.",
                "text/plain",
            )
        },
        data={"language": "English"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["clause_count"] == 2
    assert body["document_id"] in main.DOCUMENTS


def test_unknown_document_returns_404() -> None:
    response = client.post(
        "/api/ask",
        json={"document_id": "missing", "question": "What is the term?"},
    )
    assert response.status_code == 404


def test_question_without_matching_clause_returns_grounded_fallback() -> None:
    main.DOCUMENTS.clear()
    upload = client.post(
        "/api/upload",
        files={"file": ("agreement.txt", b"1. Payment\nPayment is due monthly.", "text/plain")},
        data={"language": "English"},
    )
    document_id = upload.json()["document_id"]
    response = client.post(
        "/api/ask",
        json={"document_id": document_id, "question": "What is the weather today?"},
    )
    assert response.status_code == 200
    assert response.json()["citations"] == []


def test_ask_uses_retrieved_context(monkeypatch) -> None:
    main.DOCUMENTS.clear()
    upload = client.post(
        "/api/upload",
        files={"file": ("agreement.txt", b"1. Payment\nPayment is due monthly.", "text/plain")},
        data={"language": "English"},
    )
    document_id = upload.json()["document_id"]
    captured = {}

    def fake_ask(system: str, user: str) -> str:
        captured["system"] = system
        captured["user"] = user
        return "Payment is due monthly. C1"

    monkeypatch.setattr(main, "ask_llm", fake_ask)
    response = client.post(
        "/api/ask",
        json={"document_id": document_id, "question": "When is payment due?"},
    )
    assert response.status_code == 200
    assert "Payment is due monthly." in captured["user"]
    assert response.json()["citations"] == ["Clause C1"]


def test_analyze_sanitizes_model_result(monkeypatch) -> None:
    main.DOCUMENTS.clear()
    upload = client.post(
        "/api/upload",
        files={"file": ("agreement.txt", b"1. Payment\nPayment is due monthly.", "text/plain")},
        data={"language": "English"},
    )
    document_id = upload.json()["document_id"]
    monkeypatch.setattr(
        main,
        "summarize",
        lambda clauses: {
            "summary": "Payment is due monthly.",
            "risks": [{"text": "Review payment", "citation": "C1"}],
        },
    )
    response = client.post(f"/api/analyze/{document_id}")
    assert response.status_code == 200
    assert response.json()["risks"][0]["citation"] == "C1"


def test_upload_rejects_invalid_language() -> None:
    response = client.post(
        "/api/upload",
        files={"file": ("agreement.txt", b"Payment is due monthly.", "text/plain")},
        data={"language": "x" * 31},
    )
    assert response.status_code == 400


def test_upload_rejects_file_above_configured_limit(monkeypatch) -> None:
    from types import SimpleNamespace

    monkeypatch.setattr(main, "settings", SimpleNamespace(max_upload_bytes=2, max_upload_mb=1))
    response = client.post(
        "/api/upload",
        files={"file": ("agreement.txt", b"123", "text/plain")},
        data={"language": "English"},
    )
    assert response.status_code == 413


def test_analyze_missing_document_returns_404() -> None:
    response = client.post("/api/analyze/missing")
    assert response.status_code == 404
