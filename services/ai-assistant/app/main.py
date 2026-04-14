from __future__ import annotations

import logging
import os
import random
import time
from collections import defaultdict

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

app = FastAPI(title="AI Assistant Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

PER_SESSION_LIMIT = int(os.getenv("AI_RATE_LIMIT_PER_SESSION", "20"))
PER_MINUTE_LIMIT = int(os.getenv("AI_RATE_LIMIT_PER_MINUTE", "5"))
PROVIDER = os.getenv("LLM_PROVIDER", "mock").lower()
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "600"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.4"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

session_counter: dict[str, int] = defaultdict(int)
minute_window: dict[str, list[float]] = defaultdict(list)
conversation_history: dict[str, list[dict[str, str]]] = defaultdict(list)

SYSTEM_PROMPT = (
    "You are an AI exam assistant. Your role is to help students during exams by:\n"
    "- Providing helpful hints and explanations\n"
    "- Breaking down complex questions into simpler parts\n"
    "- Explaining underlying concepts and principles\n"
    "- Guiding reasoning without revealing answers directly\n\n"
    "STRICT RULES:\n"
    "- NEVER reveal the correct answer directly\n"
    "- NEVER say which option (A, B, C, D) is correct\n"
    "- Instead, explain the concept so the student can figure it out\n"
    "- Keep responses concise (2-4 sentences)\n"
    "- Be encouraging and supportive\n"
    "- If the student asks for the direct answer, politely refuse and offer to explain the concept instead"
)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
async def readyz() -> dict[str, str]:
    return {"status": "ready"}


def _is_leak_request(message: str) -> bool:
    lowered = message.lower()
    blockers = (
        "correct answer", "just answer", "exact answer", "right option",
        "tell me the answer", "which is correct", "what is the answer",
        "give me answer", "what's the answer", "which option",
    )
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


MOCK_LEAK_RESPONSES = [
    "I can't give you the direct answer, but I can help you think through it. What part of the question is most confusing?",
    "Instead of telling you the answer, let me explain the concept. That way you'll understand *why* it's correct. What topic does this relate to?",
    "I'm here to guide your thinking, not give away answers. Let's break this question down — what do you think it's really asking?",
    "Giving the answer wouldn't help you learn. Tell me what you're stuck on, and I'll explain the underlying idea.",
]

MOCK_GENERAL_HINTS = [
    "Try to recall the key historical period this question refers to. What major events happened around that time?",
    "Think about the fundamental principle behind this question. Which scientific law or formula applies here?",
    "Consider the geographical context. What do you know about the region, climate, or physical features mentioned?",
    "Break this down step by step. What is the question actually asking you to calculate or determine?",
    "Eliminate the options that seem clearly wrong first. What makes the remaining options different from each other?",
    "Think about cause and effect. What would logically lead to the outcome described in the question?",
    "Try to connect this to something you already know well. Is there a similar concept or example you've studied?",
    "Focus on the keywords in the question. They often point directly to the concept being tested.",
    "Consider the time period and context. Historical events don't happen in isolation — what else was going on?",
    "Think about the units and magnitudes. Does your answer make physical sense?",
]


def _mock_response(message: str, session_id: str) -> str:
    if _is_leak_request(message):
        return random.choice(MOCK_LEAK_RESPONSES)

    lowered = message.lower()

    if any(w in lowered for w in ("hello", "hi", "hey", "help me", "help")):
        return (
            "Hi! I'm your exam assistant. I can help you understand questions and "
            "think through the answers. Just describe what you're working on or paste "
            "the question, and I'll give you a helpful hint!"
        )

    if any(w in lowered for w in ("thank", "thanks", "thx")):
        return "You're welcome! Keep going, you're doing great. Ask me if you need more help."

    if any(w in lowered for w in ("history", "ancient", "medieval", "revolution", "war", "century")):
        return (
            "For history questions, try to place the event in its time period first. "
            "Think about what was happening politically and socially at that time. "
            "This context often narrows down the options significantly."
        )

    if any(w in lowered for w in ("math", "calcul", "algebra", "equation", "deriv", "formula", "x =", "solve")):
        return (
            "For math problems, start by identifying what operation or formula is needed. "
            "Write down what you know, then work through it step by step. "
            "Check your answer by substituting it back into the original equation."
        )

    if any(w in lowered for w in ("physics", "force", "energy", "velocity", "newton", "gravity", "wave")):
        return (
            "For physics questions, identify the relevant physical law or principle first. "
            "Think about which quantities are given and which you need to find. "
            "Drawing a quick diagram can often make the solution clearer."
        )

    if any(w in lowered for w in ("geo", "capital", "country", "continent", "river", "mountain", "climate")):
        return (
            "For geography questions, think about the region's location and its characteristics. "
            "Climate, terrain, and proximity to water bodies are often key factors. "
            "Try to visualize the map in your mind."
        )

    if any(w in lowered for w in ("degree", "triangle", "angle")):
        return (
            "Remember the fundamental properties of geometric shapes. "
            "For triangles, there's a well-known rule about the sum of interior angles. "
            "Think about what that total is."
        )

    if any(w in lowered for w in ("pyramid", "egypt", "giza")):
        return (
            "Think about ancient civilizations and where they were located geographically. "
            "The Nile River valley was home to one of the most famous ancient civilizations. "
            "Which modern country occupies that territory today?"
        )

    if any(w in lowered for w in ("derivative", "d/dx", "x^2", "x^3")):
        return (
            "For derivatives, remember the power rule: d/dx(x^n) = n * x^(n-1). "
            "Apply this rule to the expression and simplify. "
            "What power is x raised to in this case?"
        )

    if any(w in lowered for w in ("2x", "equation", "solve for x", "14")):
        return (
            "To solve a linear equation, isolate the variable on one side. "
            "Move constants to the other side by doing the opposite operation. "
            "What happens when you subtract the constant from both sides?"
        )

    msg_idx = hash(message + session_id) % len(MOCK_GENERAL_HINTS)
    return MOCK_GENERAL_HINTS[msg_idx]


async def _call_openai(message: str, session_id: str) -> str:
    history = conversation_history[session_id]
    history.append({"role": "user", "content": message})
    if len(history) > 20:
        history[:] = history[-20:]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": LLM_MODEL,
                    "messages": messages,
                    "max_tokens": LLM_MAX_TOKENS,
                    "temperature": LLM_TEMPERATURE,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            answer = data["choices"][0]["message"]["content"]
            history.append({"role": "assistant", "content": answer})
            return answer
    except Exception as exc:
        logger.error("OpenAI call failed: %s", exc)
        return _mock_response(message, session_id)


async def _call_anthropic(message: str, session_id: str) -> str:
    history = conversation_history[session_id]
    history.append({"role": "user", "content": message})
    if len(history) > 20:
        history[:] = history[-20:]

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": LLM_MODEL,
                    "max_tokens": LLM_MAX_TOKENS,
                    "temperature": LLM_TEMPERATURE,
                    "system": SYSTEM_PROMPT,
                    "messages": history,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            answer = data["content"][0]["text"]
            history.append({"role": "assistant", "content": answer})
            return answer
    except Exception as exc:
        logger.error("Anthropic call failed: %s", exc)
        return _mock_response(message, session_id)


async def _get_response(message: str, session_id: str) -> str:
    if _is_leak_request(message):
        return random.choice(MOCK_LEAK_RESPONSES)

    if PROVIDER == "openai" and OPENAI_API_KEY:
        return await _call_openai(message, session_id)
    if PROVIDER in ("claude", "anthropic") and ANTHROPIC_API_KEY:
        return await _call_anthropic(message, session_id)
    return _mock_response(message, session_id)


async def _handle_assist(websocket: WebSocket) -> None:
    await websocket.accept()
    session_id = websocket.query_params.get("session_id", "anonymous")
    try:
        while True:
            message = await websocket.receive_text()
            rate_error = _rate_limited(session_id)
            if rate_error:
                await websocket.send_json({"role": "assistant", "content": rate_error, "blocked": True})
                continue

            response = await _get_response(message, session_id)
            await websocket.send_json({"role": "assistant", "content": response, "blocked": False})
    except WebSocketDisconnect:
        return


@app.websocket("/v1/assist")
async def assist_stripped(websocket: WebSocket) -> None:
    await _handle_assist(websocket)


@app.websocket("/ai/v1/assist")
async def assist_direct(websocket: WebSocket) -> None:
    await _handle_assist(websocket)
