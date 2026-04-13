from __future__ import annotations

import os
import time
from collections import defaultdict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI(title="AI Assistant Service", version="0.1.0")

PER_SESSION_LIMIT = int(os.getenv("AI_RATE_LIMIT_PER_SESSION", "20"))
PER_MINUTE_LIMIT = int(os.getenv("AI_RATE_LIMIT_PER_MINUTE", "5"))
PROVIDER = os.getenv("LLM_PROVIDER", "mock").lower()

session_counter: dict[str, int] = defaultdict(int)
minute_window: dict[str, list[float]] = defaultdict(list)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
async def readyz() -> dict[str, str]:
    return {"status": "ready"}


def _is_leak_request(message: str) -> bool:
    lowered = message.lower()
    blockers = ("correct answer", "just answer", "exact answer", "right option")
    return any(marker in lowered for marker in blockers)


def _rate_limited(session_id: str) -> str | None:
    now = time.time()
    minute_window[session_id] = [t for t in minute_window[session_id] if now - t <= 60]
    if len(minute_window[session_id]) >= PER_MINUTE_LIMIT:
        return "Per-minute limit exceeded. Please wait before asking another question."
    if session_counter[session_id] >= PER_SESSION_LIMIT:
        return "Session limit exceeded. Start a new exam session."
    minute_window[session_id].append(now)
    session_counter[session_id] += 1
    return None


def _mock_response(message: str) -> str:
    if _is_leak_request(message):
        return "I cannot provide direct exam answers. I can explain the concept and guide your reasoning."
    return (
        "Hint: break the question into key facts, eliminate unlikely options, "
        "and justify your final choice with one principle."
    )


@app.websocket("/ai/v1/assist")
async def assist(websocket: WebSocket) -> None:
    await websocket.accept()
    session_id = websocket.query_params.get("session_id", "anonymous")
    try:
        while True:
            message = await websocket.receive_text()
            rate_error = _rate_limited(session_id)
            if rate_error:
                await websocket.send_json({"role": "assistant", "content": rate_error, "blocked": True})
                continue

            if PROVIDER == "mock":
                response = _mock_response(message)
            else:
                response = (
                    "Real provider mode is configured, but external inference is not wired in this repository yet. "
                    "Using safe fallback hint mode."
                )

            await websocket.send_json({"role": "assistant", "content": response, "blocked": False})
    except WebSocketDisconnect:
        return
