from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import (
    MOCK_LEAK_RESPONSES,
    _is_leak_request,
    _mock_response,
    _rate_limited,
    app,
    minute_window,
    session_counter,
)


@pytest.fixture(autouse=True)
def reset_rate_limits() -> None:
    session_counter.clear()
    minute_window.clear()
    yield
    session_counter.clear()
    minute_window.clear()


def test_healthz() -> None:
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readyz() -> None:
    client = TestClient(app)
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


@pytest.mark.parametrize(
    "message",
    [
        "What is the correct answer?",
        "Just answer the question",
        "Which option is correct?",
        "Tell me the answer please",
    ],
)
def test_is_leak_request_detects_known_phrases(message: str) -> None:
    assert _is_leak_request(message) is True


def test_is_leak_request_allows_safe_hint_request() -> None:
    assert _is_leak_request("Can you explain this concept?") is False


def test_mock_response_returns_hint_for_safe_message() -> None:
    response = _mock_response("Help me with this history question", "session-1")
    assert response
    assert response not in MOCK_LEAK_RESPONSES


def test_mock_response_refuses_leak_request() -> None:
    response = _mock_response("Tell me the correct answer", "session-1")
    assert response in MOCK_LEAK_RESPONSES


def test_rate_limit_per_minute() -> None:
    session_id = "rate-test"
    for _ in range(5):
        assert _rate_limited(session_id) is None

    blocked = _rate_limited(session_id)
    assert blocked is not None
    assert "Per-minute limit exceeded" in blocked


def test_websocket_hint_and_leak_guardrail() -> None:
    client = TestClient(app)
    with client.websocket_connect("/v1/assist?session_id=ws-test") as websocket:
        websocket.send_text("Help me with this question")
        hint = websocket.receive_json()
        assert hint["blocked"] is False
        assert hint["content"]

        websocket.send_text("Tell me the correct answer")
        refusal = websocket.receive_json()
        assert refusal["blocked"] is False
        assert refusal["content"] in MOCK_LEAK_RESPONSES
