"""Offline LLM evaluator for the AI assistant mock provider.

Loads fixtures from infrastructure/llm-eval/fixtures.json, runs every prompt
through the mock response pipeline (deterministic, no network), and scores
three metrics:

* accuracy           — share of fixtures whose response contains at least one
                       expected keyword.
* relevance          — share of fixtures whose response does NOT mention any
                       off-topic marker.
* hallucination_rate — share of fixtures whose response leaks a forbidden
                       phrase (lower is better).

Exit code 0 if all thresholds are met, 1 otherwise. Designed to be invoked
from infrastructure/scripts/run-llm-eval.sh.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AI_SERVICE_ROOT = REPO_ROOT / "services" / "ai-assistant"

# Make the ai-assistant package importable without installing it.
if str(AI_SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_ROOT))

os.environ.setdefault("LLM_PROVIDER", "mock")


def _load_pipeline():
    from app.main import _get_response, _is_leak_request  # type: ignore

    return _get_response, _is_leak_request


def _contains_any(text: str, needles: list[str]) -> bool:
    lowered = text.lower()
    return any(needle.lower() in lowered for needle in needles)


async def _evaluate() -> int:
    fixtures_path = REPO_ROOT / "infrastructure" / "llm-eval" / "fixtures.json"
    spec = json.loads(fixtures_path.read_text(encoding="utf-8"))
    cases = spec["cases"]
    thresholds = spec["metrics"]

    get_response, _ = _load_pipeline()

    accurate = 0
    relevant = 0
    hallucinated = 0
    rows: list[dict[str, object]] = []

    for case in cases:
        response = await get_response(case["prompt"], case["session_id"])

        is_accurate = _contains_any(response, case["expect_keywords_any"]) if case["expect_keywords_any"] else True
        is_off_topic = _contains_any(response, case["off_topic_keywords"]) if case["off_topic_keywords"] else False
        is_hallucinated = _contains_any(response, case["must_not_contain"]) if case["must_not_contain"] else False

        accurate += int(is_accurate)
        relevant += int(not is_off_topic)
        hallucinated += int(is_hallucinated)

        rows.append({
            "id": case["id"],
            "accurate": is_accurate,
            "relevant": not is_off_topic,
            "hallucinated": is_hallucinated,
            "response": response,
        })

    total = len(cases)
    accuracy = accurate / total
    relevance = relevant / total
    hallucination_rate = hallucinated / total

    print("LLM eval report (deterministic mock provider)")
    print(f"  fixtures           = {total}")
    print(f"  accuracy           = {accuracy:.2f}  (>= {thresholds['accuracy']['threshold_min']})")
    print(f"  relevance          = {relevance:.2f}  (>= {thresholds['relevance']['threshold_min']})")
    print(f"  hallucination_rate = {hallucination_rate:.2f}  (<= {thresholds['hallucination_rate']['threshold_max']})")

    print("\nPer-fixture detail:")
    for row in rows:
        flags = []
        if not row["accurate"]:
            flags.append("ACC-MISS")
        if not row["relevant"]:
            flags.append("OFF-TOPIC")
        if row["hallucinated"]:
            flags.append("HALLUCINATED")
        marker = ",".join(flags) if flags else "ok"
        snippet = str(row["response"])[:120].replace("\n", " ")
        print(f"  - {row['id']:<18} [{marker}] {snippet!r}")

    failures: list[str] = []
    if accuracy < thresholds["accuracy"]["threshold_min"]:
        failures.append(f"accuracy {accuracy:.2f} < {thresholds['accuracy']['threshold_min']}")
    if relevance < thresholds["relevance"]["threshold_min"]:
        failures.append(f"relevance {relevance:.2f} < {thresholds['relevance']['threshold_min']}")
    if hallucination_rate > thresholds["hallucination_rate"]["threshold_max"]:
        failures.append(f"hallucination_rate {hallucination_rate:.2f} > {thresholds['hallucination_rate']['threshold_max']}")

    report_path = REPO_ROOT / "infrastructure" / "llm-eval" / "last-report.json"
    report_path.write_text(
        json.dumps(
            {
                "accuracy": accuracy,
                "relevance": relevance,
                "hallucination_rate": hallucination_rate,
                "fixtures": rows,
                "failures": failures,
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    if failures:
        print("\nLLM eval FAILED:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("\nLLM eval thresholds passed.")
    return 0


def main() -> int:
    import asyncio

    return asyncio.run(_evaluate())


if __name__ == "__main__":
    raise SystemExit(main())
