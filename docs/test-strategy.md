# Test Strategy

## 1. Purpose & Scope

This document defines the testing approach for the QA_architertor exam platform. It covers all test levels, quality gates, risk-based prioritization, tooling, environments, and acceptance criteria.

**Scope:** All 6 deployable services (history, physics, math, geography, ai-assistant, frontend) + infrastructure (gateway, datastores, CI/CD).

---

## 2. Quality Goals

| Goal | Metric | Target |
|------|--------|--------|
| Functional correctness | All unit/integration tests pass | 100% pass rate |
| Code coverage | Python line coverage (history, physics) | ≥ 80% |
| API compatibility | Contract baseline checks across all subjects | All endpoints return 200 |
| User journey | E2E Playwright scenario | Pass |
| Performance | API latency under load | p95 < 500ms (smoke), p95 < 800ms (load) |
| Resilience | Error rate under network degradation | < 20% |
| AI quality | LLM evaluation metrics | accuracy ≥ 0.70, relevance ≥ 0.75, hallucination ≤ 0.15 |
| Security | Vulnerability scans | Zero CRITICAL/HIGH CVEs, zero secrets |

---

## 3. Risk-Based Test Approach

### 3.1 Risk Assessment

| # | Risk Area | Likelihood | Impact | Test Priority | Covered By |
|---|-----------|:----------:|:------:|:-------------:|------------|
| R1 | Answer leakage via AI assistant | High | High | **Critical** | Unit test (anti-leak filter), manual WebSocket test |
| R2 | Answer leakage via API (correct_index exposed) | Medium | High | **Critical** | Unit test (schema hiding), contract test |
| R3 | Service contract divergence across languages | Medium | High | **High** | Contract baseline (`run-contract.sh`) |
| R4 | Database migration failures (history/physics) | Medium | High | **High** | Integration tests with Testcontainers |
| R5 | Frontend state machine errors | Medium | Medium | **High** | E2E Playwright tests |
| R6 | Performance degradation under load | Medium | Medium | **Medium** | k6 smoke + load scenarios |
| R7 | Network resilience failures | Low | Medium | **Medium** | Chaos experiment (`network-latency.sh`) |
| R8 | AI hallucination / low relevance | Medium | Medium | **Medium** | LLM eval baseline metrics |
| R9 | Dependency vulnerabilities | Medium | High | **High** | Trivy in CI |
| R10 | Secrets in codebase | Low | Critical | **Critical** | Gitleaks in CI |

### 3.2 Priority Matrix

```text
                    High Impact              Low Impact
High Likelihood  │ R1, R2 → Critical       │ R8 → Medium
                 │ R3, R4, R9 → High       │
Low Likelihood   │ R10 → Critical          │ R7 → Medium
                 │ R5, R6 → High/Medium    │
```

---

## 4. Test Levels

### Level 1: Unit Tests

| Service | Framework | Command | What Is Tested |
|---------|-----------|---------|----------------|
| history | pytest | `pytest services/history/tests/unit/` | Domain service with fake repository |
| physics | pytest | `pytest services/physics/tests/unit/` | Domain service with fake repository |
| math | go test | `cd services/math && go test ./...` | Question loading, endpoint handlers |
| geography | JUnit/Maven | `cd services/geography && mvn test` | Spring context load, service logic |
| ai-assistant | pytest | `pytest services/ai-assistant/tests/` | Health endpoint |

**Entry criteria:** Code compiles/lints without errors.
**Exit criteria:** All tests pass; Python coverage ≥ 80%.

### Level 2: Integration Tests

| Service | Framework | Command | What Is Tested |
|---------|-----------|---------|----------------|
| history | pytest + Testcontainers | `pytest services/history/tests/integration/` | Full HTTP API against real PostgreSQL |
| physics | pytest + Testcontainers | `pytest services/physics/tests/integration/` | Full HTTP API against real PostgreSQL |

**Entry criteria:** Unit tests pass.
**Exit criteria:** All integration tests pass with real database operations (CRUD, seed verification).

### Level 3: Contract Baseline Tests

| Tool | Command | What Is Tested |
|------|---------|----------------|
| curl-based script | `bash infrastructure/scripts/run-contract.sh` | All 4 subject services respond to `/readyz` (200) and `/v1/questions?limit=1` (200) |

**Entry criteria:** Docker Compose stack is healthy.
**Exit criteria:** All services comply with the unified API contract.

### Level 4: End-to-End Tests (E2E)

| Tool | Command | What Is Tested |
|------|---------|----------------|
| Playwright (Chromium) | `make e2e` | Subject selection screen renders; exam flow for history |

**Entry criteria:** Full compose stack running and healthy.
**Exit criteria:** All Playwright scenarios pass.

**Known gap:** Only the `history` subject has full E2E coverage. `physics`, `math`, and `geography` are covered by contract tests but not browser-level E2E.

### Level 5: Performance Tests

| Scenario | Tool | Command | Parameters | Thresholds |
|----------|------|---------|------------|------------|
| Smoke | k6 | `make perf-smoke` | 1 VU, 10 iterations | p95 < 500ms, error rate < 5% |
| Load | k6 | `make perf-load` | 50 VUs, 5 minutes | p95 < 800ms, error rate < 5% |

**Entry criteria:** Stack healthy, contract tests pass.
**Exit criteria:** All k6 thresholds met.

### Level 6: Chaos Tests

| Experiment | Tool | Command | Threshold |
|------------|------|---------|-----------|
| Network resilience | Shell script | `make chaos` | Failure rate < 20% |

**Entry criteria:** Stack healthy under normal conditions.
**Exit criteria:** Services remain functional (< 20% errors) under network degradation.

### Level 7: LLM Evaluation

| Metric | Tool | Command | Threshold |
|--------|------|---------|-----------|
| accuracy | `run-llm-eval.sh` | `make llm-eval` | ≥ 0.70 |
| relevance | `run-llm-eval.sh` | `make llm-eval` | ≥ 0.75 |
| hallucination_rate | `run-llm-eval.sh` | `make llm-eval` | ≤ 0.15 |

**Entry criteria:** AI assistant is running (mock or real provider).
**Exit criteria:** All three metrics within thresholds.

---

## 5. Quality Gates

### 5.1 PR Merge Gates (CI — Blocks Merge)

| Gate | Tool | Threshold | Required? |
|------|------|-----------|:---------:|
| Python linting | ruff | Zero warnings | Soft (logged, doesn't block) |
| Python unit + integration | pytest | 100% pass, coverage ≥ 80% | **Yes** |
| Go tests | `go test` | 100% pass | **Yes** |
| Java tests | `mvn test` | 100% pass | **Yes** |
| Frontend build | `npm run build` | Successful compilation | **Yes** |
| E2E tests | Playwright | 100% pass | **Yes** |
| Docker image build | `docker build` | All images build successfully | **Yes** |
| Compose validation | `docker compose config` | Valid configuration | **Yes** |
| Dependency scan | Trivy | Zero CRITICAL/HIGH | **Yes** |
| Secrets scan | Gitleaks | Clean (no findings) | **Yes** |
| SAST | CodeQL | Clean (no findings) | **Yes** |
| AI PR review | OpenAI (GPT-4o-mini) | Advisory only | No |

### 5.2 Release Gates

| Gate | Description | How Verified |
|------|-------------|--------------|
| All CI gates green | No exceptions; all checks above must pass | GitHub branch protection |
| PR approved | At least 1 code review approval | GitHub branch protection |
| Branch up-to-date | PR branch rebased on latest `main` | GitHub branch protection |
| Conventional Commit | Commit message follows `feat:` / `fix:` / etc. | Enforced by `release-please` |
| Semver tag | Tag follows `vX.Y.Z` pattern | `release.yml` trigger condition |

### 5.3 Deployment Gates

| Gate | Description | How Verified |
|------|-------------|--------------|
| Smoke test | All services respond 200 on `/readyz` | `smoke.sh` post-deploy |
| Contract baseline | All endpoints return expected status codes | `run-contract.sh` |
| Canary observation | 10% traffic to new version shows no error spike | Manual observation + `make canary` |

---

## 6. Test Environments

| Environment | Setup | Data | Purpose |
|-------------|-------|------|---------|
| **Unit test (local)** | pytest / go test / mvn test | Mocks, fakes, fixtures | Fast feedback during development |
| **Integration test** | Testcontainers (ephemeral Postgres) | Auto-seeded | Verify DB interactions |
| **Full stack (local)** | `docker compose --profile services up` | Seed data from `seed.py` / hardcoded | Manual testing, E2E, perf, chaos |
| **CI (GitHub Actions)** | Docker-in-Docker compose | Same seed data | Automated regression on every PR |

---

## 7. Test Data Management

| Data Type | Source | Lifecycle |
|-----------|--------|-----------|
| History questions | `services/history/app/domain/seed.py` | Seeded on first startup via Alembic + application |
| Physics questions | `services/physics/app/domain/seed.py` | Seeded on first startup via Alembic + application |
| Math questions | Hardcoded in `services/math/main.go` | Available immediately (in-memory) |
| Geography questions | Hardcoded in `services/geography/.../QuestionService.java` | Available immediately (in-memory) |
| Integration test data | `conftest.py` fixtures + Testcontainers Postgres | Created/destroyed per test session |
| E2E test data | Relies on seed data from compose stack | Persistent during test run |

---

## 8. Test Coverage Matrix

| Service | Unit | Integration | Contract | E2E | Perf | Chaos | LLM Eval |
|---------|:----:|:-----------:|:--------:|:---:|:----:|:-----:|:--------:|
| history | ✅ | ✅ (Testcontainers) | ✅ | ✅ | ✅ | ✅ | — |
| physics | ✅ | ✅ (Testcontainers) | ✅ | — | ✅ | — | — |
| math | ✅ | — | ✅ | — | — | — | — |
| geography | ✅ | — | ✅ | — | — | — | — |
| ai-assistant | ✅ | — | — | — | — | — | ✅ |
| frontend | — | — | — | ✅ (Playwright) | — | — | — |

### Coverage Gaps & Mitigation

| Gap | Risk Level | Mitigation Plan |
|-----|:----------:|----------------|
| No E2E for physics/math/geography | Medium | Contract tests validate API; extend Playwright when resources allow |
| No integration tests for math/geography | Low | Services are stateless with hardcoded data; unit + contract tests sufficient |
| No performance tests for math/geography | Low | Share same gateway; history perf tests cover gateway path |
| No chaos tests for physics | Medium | Same architecture as history; extend chaos script to cover all Python services |
| Limited AI functional testing | Medium | Expand to test all anti-leak patterns and rate-limit edge cases |

---

## 9. Tools & Frameworks

| Category | Tool | Version | Purpose |
|----------|------|---------|---------|
| Unit (Python) | pytest | 7.x+ | Test runner + assertions |
| Coverage (Python) | pytest-cov | Latest | Line coverage reporting |
| Unit (Go) | go test | 1.22 | Built-in test framework |
| Unit (Java) | JUnit + Maven Surefire | 5.x / 3.x | Test runner for Spring Boot |
| Integration | Testcontainers (Python) | Latest | Ephemeral PostgreSQL for integration tests |
| E2E | Playwright | 1.x | Browser automation (Chromium) |
| Performance | k6 | Latest | Load testing with JavaScript scenarios |
| Chaos | Shell scripts | — | Network degradation simulation |
| LLM Eval | Shell script (`run-llm-eval.sh`) | — | Offline baseline metrics |
| Linting (Python) | ruff | Latest | Fast Python linter + formatter |
| Linting (Go) | gofmt | 1.22 | Standard Go formatter |
| Linting (Java) | Spotless (Maven) | — | Java code formatting |
| Linting (Frontend) | Prettier | — | TypeScript/CSS formatting |
| SAST | CodeQL | — | Multi-language static analysis |
| Dependency scan | Trivy | Latest | CVE scanning |
| Secrets | Gitleaks | Latest | Secret detection |
| AI review | GPT-4o-mini (via GitHub Actions) | — | PR advisory comments |

---

## 10. Defect Classification

| Severity | Definition | SLA (Test Assignment Context) |
|----------|------------|-------------------------------|
| **Blocker** | System cannot start, core user flow broken | Fix before demo |
| **Critical** | Answer leakage, data loss, security vulnerability | Fix before merge |
| **Major** | Feature works incorrectly, wrong results | Fix in current sprint |
| **Minor** | UI cosmetic issues, non-critical edge cases | Backlog |
| **Trivial** | Typos, logging noise | Backlog |

---

## 11. Reporting

| Report | Frequency | Audience | Location |
|--------|-----------|----------|----------|
| CI test results | Every push/PR | Developers | GitHub Actions UI |
| Coverage report | Every push/PR | Developers, Reviewers | CI logs (pytest-cov output) |
| Security scan results | Every push/PR | Developers, Security | GitHub Security tab (CodeQL), CI logs (Trivy, Gitleaks) |
| LLM eval metrics | On demand (`make llm-eval`) | QA, AI team | Terminal output |
| AI PR advisory | Every PR | Developers, Reviewers | PR comment (by ai-automation workflow) |
