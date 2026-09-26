from fastapi.testclient import TestClient

import nyayaai.main as main
from nyayaai.main import RateLimiter, app

client = TestClient(app)


def test_security_headers() -> None:
    response = client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]


def test_rate_limiter_blocks_after_limit() -> None:
    limiter = RateLimiter(limit=1, window=60)
    assert limiter.allowed("client") is True
    assert limiter.allowed("client") is False


def test_frontend_does_not_render_model_output_as_html() -> None:
    with open("static/app.js", encoding="utf-8") as file:
        source = file.read()
    assert "innerHTML" not in source


def test_api_rate_limit_returns_429(monkeypatch) -> None:
    limiter = RateLimiter(limit=1, window=60)
    monkeypatch.setattr(main, "rate_limiter", limiter)
    first = client.post(
        "/api/upload",
        files={"file": ("test.exe", b"bad", "application/octet-stream")},
        data={"language": "English"},
    )
    second = client.post(
        "/api/upload",
        files={"file": ("test.exe", b"bad", "application/octet-stream")},
        data={"language": "English"},
    )
    assert first.status_code == 400
    assert second.status_code == 429
