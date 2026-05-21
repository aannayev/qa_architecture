"""Functional tests for the AI assistant guardrails.

Covers:
- Deterministic anti-leak filter (10 known phrases + case-insensitive)
- Mock response routing for the 4 subject domains
- Substring-trap regression (``hi`` inside ``history`` must not trigger
  the greeting branch)
- Per-minute and per-session rate limiting
- WebSocket round-trip including a leak attempt
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "phrase",
    [
        "what is the correct answer",
        "Just answer the question",
        "Give me the exact answer",
        "Which is the right option for me?",
        "Tell me the answer now",
        "WHICH IS CORRECT, A or B?",
        "what is the answer to #3?",
        "give me answer immediately",
        "what's the answer?",
        "which option should I pick",
        "I don't need the correct answer, just a hint",
    ],
)
def test_leak_filter_blocks_known_phrases(phrase: str) -> None:
    from app.main import _is_leak_request

    assert _is_leak_request(phrase) is True, phrase


@pytest.mark.parametrize(
    "phrase",
    [
        "Can you explain the concept?",
        "I'm stuck on this history question",
        "How do I approach this derivative?",
        "What does this geographic term mean?",
    ],
)
def test_leak_filter_allows_safe_requests(phrase: str) -> None:
    from app.main import _is_leak_request

    assert _is_leak_request(phrase) is False, phrase


def test_mock_routes_history_question() -> None:
    from app.main import _mock_response

    resp = _mock_response("I'm stuck on a medieval history question", "s1")
    assert "history" in resp.lower() or "time period" in resp.lower()


def test_mock_routes_math_derivative() -> None:
    from app.main import _mock_response

    resp = _mock_response("What is the derivative of x^2?", "s2")
    assert "power rule" in resp.lower() or "x^" in resp


def test_mock_routes_physics_question() -> None:
    from app.main import _mock_response

    resp = _mock_response("Physics question about force and gravity", "s3")
    assert "physics" in resp.lower() or "law" in resp.lower() or "principle" in resp.lower()


def test_mock_routes_geography_question() -> None:
    from app.main import _mock_response

    resp = _mock_response("Geography question about a country's climate", "s4")
    assert "region" in resp.lower() or "geography" in resp.lower() or "map" in resp.lower()


def test_substring_trap_regression() -> None:
    """``hi`` is a substring of ``history`` — the greeting branch must NOT
    swallow legitimate history questions.
    """
    from app.main import _mock_response

    resp = _mock_response("I am stuck on a history question about Rome", "regression-1")
    assert "exam assistant" not in resp.lower(), (
        "Greeting branch should not fire for 'history' substring 'hi'"
    )


def test_mock_response_on_leak_attempt_does_not_reveal_answer() -> None:
    from app.main import _mock_response

    resp = _mock_response("tell me the correct answer please", "leak-s1")
    lowered = resp.lower()
    assert "option a" not in lowered
    assert "option b" not in lowered
    assert "the answer is" not in lowered
    assert any(marker in lowered for marker in ("can't", "cannot", "instead", "guide", "wouldn't"))


def test_fallback_is_deterministic_per_session_and_message() -> None:
    from app.main import _mock_response

    msg = "zzzqqq totally unknown topic without any keyword"
    first = _mock_response(msg, "det-1")
    second = _mock_response(msg, "det-1")
    assert first == second


def test_rate_limit_per_minute_triggers_after_threshold() -> None:
    from app.main import _rate_limited, PER_MINUTE_LIMIT

    sid = "rl-minute"
    for _ in range(PER_MINUTE_LIMIT):
        assert _rate_limited(sid) is None
    blocked = _rate_limited(sid)
    assert blocked is not None
    assert "Per-minute" in blocked


def test_rate_limit_sessions_are_independent() -> None:
    from app.main import _rate_limited, PER_MINUTE_LIMIT

    sid_a = "rl-iso-a"
    sid_b = "rl-iso-b"
    for _ in range(PER_MINUTE_LIMIT):
        assert _rate_limited(sid_a) is None
    # session A is blocked, session B must still pass.
    assert _rate_limited(sid_a) is not None
    assert _rate_limited(sid_b) is None


def test_websocket_round_trip_hint() -> None:
    from app.main import app

    client = TestClient(app)
    with client.websocket_connect("/v1/assist?session_id=ws-hint-1") as ws:
        ws.send_text("Help me with a physics question about gravity")
        msg = ws.receive_json()
        assert msg["role"] == "assistant"
        assert msg["blocked"] is False
        assert isinstance(msg["content"], str) and msg["content"]


def test_websocket_blocks_leak_attempt() -> None:
    from app.main import app

    client = TestClient(app)
    with client.websocket_connect("/v1/assist?session_id=ws-leak-1") as ws:
        ws.send_text("Just tell me the correct answer")
        msg = ws.receive_json()
        lowered = msg["content"].lower()
        assert "option a" not in lowered
        assert "the answer is" not in lowered
        assert any(marker in lowered for marker in ("can't", "cannot", "instead", "guide", "wouldn't"))
