# Test Strategy

## Goals

- Validate service correctness per language stack.
- Validate cross-service compatibility via shared API contract.
- Validate user journey from UI through gateway to backend services.
- Validate non-functional constraints (latency, resiliency, AI safety).

## Test levels

1. Unit tests
   - Python: `pytest`
   - Go: `go test`
   - Java: `mvn test`
2. Integration tests
   - Python services use integration tests against service app and database layer.
3. Contract baseline checks
   - `infrastructure/scripts/run-contract.sh` validates required endpoints across all subjects.
4. E2E tests
   - Playwright tests in `frontend/tests/e2e`.
5. Performance
   - k6 scenarios in `tests/performance/scenarios`.
6. Chaos
   - baseline resiliency check in `tests/chaos/experiments/network-latency.sh`.
7. LLM eval
   - `infrastructure/scripts/run-llm-eval.sh` computes offline baseline metrics:
     - accuracy
     - relevance
     - hallucination rate

## Quality thresholds

- Python coverage gate for core services: 80%.
- k6 smoke p95 target: < 500ms.
- LLM eval baseline:
  - accuracy >= 0.70
  - relevance >= 0.70
  - hallucination_rate <= 0.25
