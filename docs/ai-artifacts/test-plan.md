# AI-Focused Test Plan

## AI assistant functional checks

- WebSocket connection can be established.
- Assistant returns responses in mock mode.
- Rate limits are enforced:
  - per-minute limit
  - per-session limit
- Leakage guardrail blocks direct-answer requests.

## AI quality checks

Metrics from `run-llm-eval.sh`:

- accuracy
- relevance
- hallucination_rate

Thresholds:

- accuracy >= 0.70
- relevance >= 0.70
- hallucination_rate <= 0.25
