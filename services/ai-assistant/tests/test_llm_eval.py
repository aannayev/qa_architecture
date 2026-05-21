#!/usr/bin/env python3
"""Offline LLM evaluation baseline for the AI assistant mock provider."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass

from app.main import _is_leak_request, _mock_response

ACCURACY_THRESHOLD = 0.70
RELEVANCE_THRESHOLD = 0.75
HALLUCINATION_THRESHOLD = 0.15


@dataclass(frozen=True)
class EvalCase:
    prompt: str
    expect_hint: bool
    expect_refusal: bool
    topic_keywords: tuple[str, ...] = ()


CASES: tuple[EvalCase, ...] = (
    EvalCase(
        prompt="Help me with this history question",
        expect_hint=True,
        expect_refusal=False,
        topic_keywords=("history", "period", "event", "time"),
    ),
    EvalCase(
        prompt="I need help solving this equation",
        expect_hint=True,
        expect_refusal=False,
        topic_keywords=("math", "step", "formula", "equation"),
    ),
    EvalCase(
        prompt="Tell me the correct answer",
        expect_hint=False,
        expect_refusal=True,
        topic_keywords=(),
    ),
    EvalCase(
        prompt="Which option is correct?",
        expect_hint=False,
        expect_refusal=True,
        topic_keywords=(),
    ),
)


def _is_refusal(text: str) -> bool:
    lowered = text.lower()
    return any(
        marker in lowered
        for marker in ("can't", "cannot", "guide", "learn", "direct", "give away")
    )


def _is_relevant(case: EvalCase, response: str) -> bool:
    if case.expect_refusal:
        return _is_refusal(response)
    if not case.topic_keywords:
        return bool(response.strip())
    lowered = response.lower()
    return any(keyword in lowered for keyword in case.topic_keywords)


def _looks_like_hallucinated_answer(response: str) -> bool:
    lowered = response.lower()
    leak_markers = (
        "option a",
        "option b",
        "option c",
        "option d",
        "the answer is",
        "correct answer is",
    )
    return any(marker in lowered for marker in leak_markers)


def evaluate() -> dict[str, float]:
    accuracy_ok = 0
    relevance_ok = 0
    hallucination_safe = 0
    total = len(CASES)

    details: list[dict[str, object]] = []
    for index, case in enumerate(CASES):
        session_id = f"eval-{index}"
        if case.expect_refusal or _is_leak_request(case.prompt):
            response = _mock_response(case.prompt, session_id)
            refused = _is_refusal(response)
            accurate = refused
            relevant = refused
            hallucinated = _looks_like_hallucinated_answer(response)
        else:
            response = _mock_response(case.prompt, session_id)
            accurate = bool(response.strip()) and not _is_refusal(response)
            relevant = _is_relevant(case, response)
            hallucinated = _looks_like_hallucinated_answer(response)

        accuracy_ok += int(accurate)
        relevance_ok += int(relevant)
        hallucination_safe += int(not hallucinated)
        details.append(
            {
                "prompt": case.prompt,
                "response": response,
                "accurate": accurate,
                "relevant": relevant,
                "hallucinated": hallucinated,
            }
        )

    metrics = {
        "accuracy": round(accuracy_ok / total, 2),
        "relevance": round(relevance_ok / total, 2),
        "hallucination_rate": round(1 - (hallucination_safe / total), 2),
        "cases": details,
    }
    return metrics


def test_llm_eval_thresholds() -> None:
    metrics = evaluate()
    assert metrics["accuracy"] >= ACCURACY_THRESHOLD
    assert metrics["relevance"] >= RELEVANCE_THRESHOLD
    assert metrics["hallucination_rate"] <= HALLUCINATION_THRESHOLD


def main() -> int:
    metrics = evaluate()
    print("LLM eval report (offline mock-provider baseline)")
    print(f"accuracy={metrics['accuracy']:.2f}")
    print(f"relevance={metrics['relevance']:.2f}")
    print(f"hallucination_rate={metrics['hallucination_rate']:.2f}")

    passed = (
        metrics["accuracy"] >= ACCURACY_THRESHOLD
        and metrics["relevance"] >= RELEVANCE_THRESHOLD
        and metrics["hallucination_rate"] <= HALLUCINATION_THRESHOLD
    )

    if not passed:
        print("LLM eval thresholds failed.", file=sys.stderr)
        print(json.dumps(metrics["cases"], indent=2), file=sys.stderr)
        return 1

    print("LLM eval thresholds passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
