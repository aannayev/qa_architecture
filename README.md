# QA_architertor

End-to-end exam platform built with microservice architecture as a test assignment for the **AI Quality Architect** position.

The project demonstrates:
- Polyglot backend (Python + Go + Java)
- Frontend application (React + TypeScript)
- API Gateway and containerized infrastructure
- Quality Engineering approach (unit / integration / contract / e2e / perf / chaos / llm-eval)
- CI/CD and security automation
- AI assistant (WebSocket) integrated into the user scenario

---

## 1. Architecture Overview

### 1.1 System Container Diagram

```mermaid
flowchart TB
    subgraph Client
        Browser["Browser"]
    end

    subgraph Frontend["Frontend :3000"]
        React["React + TypeScript + Vite"]
    end

    subgraph Gateway["API Gateway :80"]
        Traefik["Traefik v3"]
    end

    subgraph SubjectServices["Subject Services :8000 each"]
        History["history\nPython / FastAPI"]
        Physics["physics\nPython / FastAPI"]
        Math["math\nGo / chi"]
        Geo["geography\nJava / Spring Boot"]
    end

    subgraph AI["AI Service"]
        Assistant["ai-assistant\nPython / FastAPI\nWebSocket"]
    end

    subgraph Data["Data Stores"]
        PG[("PostgreSQL 16")]
        Redis[("Redis 7")]
        Unleash[("Unleash 6\nFeature Flags")]
    end

    Browser -->|"HTTP"| React
    React -->|"REST API"| Traefik
    React -.->|"WebSocket"| Traefik

    Traefik -->|"/api/history/*"| History
    Traefik -->|"/api/physics/*"| Physics
    Traefik -->|"/api/math/*"| Math
    Traefik -->|"/api/geography/*"| Geo
    Traefik -.->|"/ai/*"| Assistant

    History --> PG
    Physics --> PG
    History -.->|"flags"| Unleash
    Physics -.->|"flags"| Unleash
    Assistant --> Redis
```

### 1.2 Request Flow (Sequence)

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant G as Traefik
    participant S as Subject Service
    participant DB as PostgreSQL

    U->>F: Opens http://localhost:3000
    U->>F: Selects subject "history"

    F->>G: GET /api/history/v1/questions?limit=10
    G->>S: GET /v1/questions?limit=10
    Note over G: strips /api/history prefix
    S->>DB: SELECT questions
    DB-->>S: rows
    S-->>G: JSON (correct_index hidden)
    G-->>F: JSON
    F->>U: Renders question + options

    U->>F: Clicks answer option
    F->>G: POST /api/history/v1/questions/{id}/submit
    G->>S: POST /v1/questions/{id}/submit
    S->>DB: Lookup correct answer
    S-->>G: {correct, correct_index, explanation}
    G-->>F: result
    F->>U: Shows correct/incorrect + explanation
```

### 1.3 AI Assistant Flow (WebSocket)

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant G as Traefik
    participant AI as AI Assistant

    U->>F: Opens AI Assistant panel
    F->>G: ws://localhost/ai/v1/assist?session_id=xyz
    G->>AI: WS /v1/assist?session_id=xyz

    U->>F: "Help me with this question"
    F->>AI: text message
    AI-->>F: {"content": "Think about events in early 20th century..."}
    F->>U: Shows hint

    U->>F: "Just tell me the correct answer"
    F->>AI: text message
    Note over AI: anti-leak filter triggers
    AI-->>F: {"content": "I cannot provide direct exam answers..."}
    F->>U: Shows refusal (guardrail active)
```

---

## 2. Technology Stack

| Component | Language | Framework | Data Store |
|-----------|----------|-----------|------------|
| history | Python 3.12 | FastAPI | PostgreSQL (SQLAlchemy + Alembic) |
| physics | Python 3.12 | FastAPI | PostgreSQL (SQLAlchemy + Alembic) |
| math | Go 1.22 | chi v5 | In-memory |
| geography | Java 21 | Spring Boot 3 | In-memory |
| ai-assistant | Python 3.12 | FastAPI + WebSocket | Redis |
| frontend | TypeScript | React 18 + Vite 5 | — |
| gateway | — | Traefik v3 | — |

---

## 3. Code Structure & Class Diagrams

### 3.1 Python Service Architecture (history / physics)

```mermaid
classDiagram
    class FastAPI {
        +include_router()
        +add_middleware()
    }

    class APIRouter {
        +GET /v1/topics
        +GET /v1/questions
        +GET /v1/questions/id
        +POST /v1/questions/id/submit
    }

    class QuestionService {
        -repo: QuestionRepository
        +topics() list
        +list_questions(topic, difficulty, limit) list
        +get_question(id) Question
        +submit(id, selected_index) SubmitResult
    }

    class QuestionRepository {
        -session: AsyncSession
        +find_all(topic, difficulty, limit) list
        +find_by_id(id) Question
        +count() int
        +upsert_many(questions) void
    }

    class Question {
        +id: UUID
        +external_id: str
        +topic: str
        +difficulty: Difficulty
        +prompt: str
        +options: list~str~
        +correct_index: int
        +explanation: str
        +created_at: datetime
        +updated_at: datetime
    }

    class QuestionPublic {
        +id: UUID
        +external_id: str
        +topic: str
        +difficulty: str
        +prompt: str
        +options: list~str~
        Note: correct_index HIDDEN
    }

    class SubmitResult {
        +question_id: UUID
        +correct: bool
        +correct_index: int
        +explanation: str
    }

    FastAPI --> APIRouter
    APIRouter --> QuestionService
    QuestionService --> QuestionRepository
    QuestionRepository --> Question
    APIRouter ..> QuestionPublic : response
    APIRouter ..> SubmitResult : response
```

### 3.2 Go Service Architecture (math)

```mermaid
classDiagram
    class main_go {
        +main()
        +liveness() handler
        +readiness() handler
        +listTopics() handler
        +listQuestions() handler
        +getQuestion() handler
        +submitAnswer() handler
        -publicQuestion(q) question
        -writeJSON(w, status, payload)
    }

    class question {
        +ID: string
        +ExternalID: string
        +Topic: string
        +Difficulty: string
        +Prompt: string
        +Options: []string
        -CorrectIndex: int
        -Explanation: string
    }

    class submitResult {
        +QuestionID: string
        +Correct: bool
        +CorrectIndex: int
        +Explanation: string
    }

    main_go --> question : in-memory slice
    main_go ..> submitResult : response
```

### 3.3 Java Service Architecture (geography)

```mermaid
classDiagram
    class GeographyApplication {
        +main(args)
    }

    class QuestionController {
        +topics() List~TopicInfo~
        +listQuestions(topic, difficulty, limit) List~Question~
        +getQuestion(questionId) Question
        +submit(questionId, request) SubmitResult
    }

    class HealthController {
        +healthz() Map
        +readyz() Map
    }

    class QuestionService {
        -questions: List~Question~
        +topics() List~TopicInfo~
        +listQuestions(topic, difficulty, limit) List~Question~
        +getQuestion(id) Optional~Question~
        +findOriginal(id) Optional~Question~
    }

    class Question {
        +id: UUID
        +externalId: String
        +topic: String
        +difficulty: String
        +prompt: String
        +options: List~String~
        +correctIndex: int
        +explanation: String
    }

    GeographyApplication --> QuestionController
    GeographyApplication --> HealthController
    QuestionController --> QuestionService
    QuestionService --> Question
```

### 3.4 Frontend State Machine

```mermaid
stateDiagram-v2
    [*] --> pick: App loads

    pick --> loading: User selects subject
    loading --> answering: Questions fetched
    loading --> pick: Fetch error

    answering --> answering: Submit answer\n(next question)
    answering --> result: Last question answered

    result --> pick: "Start new exam"

    state answering {
        [*] --> ShowQuestion
        ShowQuestion --> WaitSubmit: User clicks option
        WaitSubmit --> ShowQuestion: More questions
        WaitSubmit --> [*]: No more questions
    }
```

### 3.5 Database Schema (history / physics)

```mermaid
erDiagram
    QUESTIONS {
        uuid id PK
        varchar(64) external_id UK
        varchar(64) topic
        enum difficulty "easy | medium | hard"
        text prompt
        jsonb options "string array"
        int correct_index
        text explanation
        timestamptz created_at
        timestamptz updated_at
    }
```

---

## 4. Gateway Routing

Traefik receives all external requests and routes them to the correct service:

```mermaid
flowchart LR
    subgraph Incoming["Incoming Request"]
        R1["/api/history/v1/questions"]
        R2["/api/physics/v1/topics"]
        R3["/api/math/v1/questions/5"]
        R4["/api/geography/v1/topics"]
        R5["/ai/v1/assist (WS)"]
    end

    subgraph MW["Middleware"]
        AS["api-strip\nremoves /api/{subject}"]
        AIS["ai-strip\nremoves /ai"]
    end

    subgraph Services["Backend Receives"]
        S1["/v1/questions"]
        S2["/v1/topics"]
        S3["/v1/questions/5"]
        S4["/v1/topics"]
        S5["/v1/assist"]
    end

    R1 --> AS --> S1
    R2 --> AS --> S2
    R3 --> AS --> S3
    R4 --> AS --> S4
    R5 --> AIS --> S5
```

### Unified API Contract

Every subject service implements the same endpoints:

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/healthz` | Liveness check |
| `GET` | `/readyz` | Readiness check (DB connectivity) |
| `GET` | `/v1/topics` | List available topics with question counts |
| `GET` | `/v1/questions` | List questions (filters: `topic`, `difficulty`, `limit`) |
| `GET` | `/v1/questions/{id}` | Get single question (correct answer hidden) |
| `POST` | `/v1/questions/{id}/submit` | Submit answer, get result with explanation |

---

## 5. Getting Started

### Prerequisites

- Docker Desktop (with Docker Compose v2)
- Git
- Bash-compatible shell (`Git Bash` or `WSL`) for `.sh` scripts
- (optional) `make`

```bash
docker --version          # 24.x+
docker compose version    # v2.x+
```

### Step-by-Step Launch

```bash
# 1. Clone the repository
git clone <repository-url>
cd QA_architertor

# 2. Create environment file
cp .env.example .env
# PowerShell: Copy-Item .env.example .env

# 3. Build and start all services
docker compose --profile services up -d --build

# 4. Wait for services to become healthy
bash ./infrastructure/scripts/wait-for-healthy.sh

# 5. Run smoke check
bash ./infrastructure/scripts/smoke.sh

# 6. Run contract baseline checks
bash ./infrastructure/scripts/run-contract.sh
```

Or with Makefile:

```bash
make up      # builds, starts, waits, prints URLs
```

### URLs After Launch

| Resource | URL |
|----------|-----|
| Frontend | http://localhost:3000 |
| Gateway API | http://localhost/api |
| AI WebSocket | ws://localhost/ai/v1/assist |
| Traefik Dashboard | http://localhost:8080 |

---

## 6. Makefile Commands

### Lifecycle

| Command | Description |
|---------|-------------|
| `make up` | Build and start the full stack, wait for healthy, print URLs |
| `make down` | Stop all containers and remove volumes |
| `make ps` | List running containers |
| `make logs` | Tail logs for all services |
| `make seed` | Verify seed data is present |

### Quality

| Command | Description |
|---------|-------------|
| `make lint` | Run linters (ruff for Python) |
| `make fmt` | Auto-format code (ruff / gofmt / spotless / prettier) |
| `make test` | Run unit + integration tests for all services |
| `make coverage` | Run tests with coverage enforcement (80% threshold) |

### Testing

| Command | Description |
|---------|-------------|
| `make contract` | Baseline API contract checks |
| `make e2e` | Playwright E2E tests |
| `make perf-smoke` | k6 smoke test (1 VU, 10 iterations, p95 < 500ms) |
| `make perf-load` | k6 load test (50 VUs, 5 minutes, p95 < 800ms) |
| `make chaos` | Chaos baseline (network resilience check) |
| `make llm-eval` | LLM evaluation (accuracy, relevance, hallucination rate) |
| `make smoke` | Post-deploy health check for all services |

### Deployment

| Command | Description |
|---------|-------------|
| `make canary` | Route 10% traffic to green, 90% to blue |
| `make deploy-green` | Route 100% traffic to green (new version) |
| `make deploy-blue` | Route 100% traffic to blue (rollback) |

### Codegen

| Command | Description |
|---------|-------------|
| `make gen` | Run all code generators |
| `make gen-types` | Generate frontend TS types from OpenAPI |
| `make gen-proto` | Generate gRPC stubs (Go + Python) |

---

## 7. Testing Pyramid

```mermaid
graph TB
    subgraph Pyramid["Testing Levels"]
        direction TB
        L1["Unit Tests\nPython: pytest, Go: go test, Java: JUnit\nFastest, most numerous"]
        L2["Integration Tests\nPython: pytest + Testcontainers Postgres\nReal DB, HTTP client"]
        L3["Contract Tests\ncurl-based API contract baseline\nAll services implement same endpoints"]
        L4["E2E Tests\nPlaywright (Chromium)\nFull compose stack"]
        L5["Performance Tests\nk6 smoke (1 VU) + load (50 VU)\nLatency and error thresholds"]
        L6["Chaos Tests\nNetwork resilience checks\nFailure rate threshold 20%"]
        L7["LLM Evaluation\naccuracy >= 0.70, relevance >= 0.75\nhallucination_rate <= 0.15"]
    end

    L1 --> L2 --> L3 --> L4 --> L5 --> L6 --> L7
```

### Test Coverage by Service

| Service | Unit | Integration | Contract | E2E | Perf | Chaos | LLM Eval |
|---------|:----:|:-----------:|:--------:|:---:|:----:|:-----:|:--------:|
| history | yes | yes (Testcontainers) | yes | yes | yes | yes | — |
| physics | yes | yes (Testcontainers) | yes | — | yes | — | — |
| math | yes | — | yes | — | — | — | — |
| geography | yes | — | yes | — | — | — | — |
| ai-assistant | yes | — | — | — | — | — | yes |
| frontend | — | — | — | yes (Playwright) | — | — | — |

---

## 8. CI/CD Pipeline

```mermaid
flowchart TD
    subgraph Trigger["Trigger"]
        PUSH["Push / Pull Request"]
        TAG["Tag v*.*.*"]
    end

    subgraph CI["CI Pipeline — ci.yml"]
        QP["quality-python\nruff + pytest\ncoverage >= 80%\n(history, physics, ai-assistant)"]
        QG["quality-go\ngo test\n(math)"]
        QJ["quality-java\nmvn test\n(geography)"]
        QF["quality-frontend\nnpm build"]
        E2E["e2e-frontend\ncompose up + Playwright"]
        DB["docker-build\nAll service images"]
        CV["compose-validate\ndocker compose config"]
        DS["dependency-scan\nTrivy (CRITICAL/HIGH)"]
        SS["secrets-scan\nGitleaks"]
    end

    subgraph Security["Security — codeql.yml"]
        CQL["CodeQL SAST\nPython, JS/TS, Java, Go"]
    end

    subgraph AIAuto["AI — ai-automation.yml"]
        AIA["AI PR Advisory\nOpenAI analysis of diff\ndocs + tests + risks"]
    end

    subgraph Release["Release — release.yml"]
        IMG["Build & push images to GHCR"]
        GHR["Create GitHub Release"]
    end

    PUSH --> CI
    PUSH --> Security
    PUSH --> AIAuto

    QP & QG & QJ & QF --> E2E

    TAG --> IMG --> GHR
```

### Quality Gates Summary

| Gate | Tool | Threshold | Blocks Merge? |
|------|------|-----------|:-------------:|
| Python linting | ruff | — | No (soft) |
| Python tests + coverage | pytest | >= 80% (history, physics) | Yes |
| Go tests | go test | pass | Yes |
| Java tests | mvn test | pass | Yes |
| Frontend build | npm build | pass | Yes |
| E2E | Playwright | pass | Yes |
| Docker build | docker build | pass | Yes |
| Compose validation | docker compose config | pass | Yes |
| Dependency scan | Trivy | no CRITICAL/HIGH | Yes |
| Secrets scan | Gitleaks | clean | Yes |
| SAST | CodeQL | clean | Yes |
| AI PR review | OpenAI | advisory | No |

### Release Process

```
1. Developer creates a semver tag:
   git tag v1.0.0 && git push origin v1.0.0

2. release.yml automatically:
   a) Logs into GitHub Container Registry (GHCR)
   b) Builds Docker images for all services
   c) Pushes to ghcr.io/<owner>/qa-architect-<service>:<tag>
   d) Creates GitHub Release with changelog
```

---

## 9. Security

| Tool | Purpose | Where |
|------|---------|-------|
| **CodeQL** | SAST — finds vulnerabilities in source code | Separate workflow, runs on push/PR + weekly cron |
| **Trivy** | Scans dependencies for known CVEs | CI job, fails on CRITICAL/HIGH |
| **Gitleaks** | Detects leaked secrets in code | CI job |

### AI Assistant Guardrails

| Mechanism | How It Works |
|-----------|-------------|
| Anti-leak filter | Detects phrases like "correct answer", "just answer", "right option" and refuses |
| Per-session rate limit | Max `AI_RATE_LIMIT_PER_SESSION` requests per session |
| Per-minute rate limit | Max `AI_RATE_LIMIT_PER_MINUTE` requests per minute |

---

## 10. Repository Structure

```text
services/
  history/              Python/FastAPI — history questions
    app/
      main.py           FastAPI application factory
      api/routes.py     HTTP endpoints (/v1/...)
      domain/
        models.py       SQLAlchemy ORM model (Question)
        schemas.py      Pydantic DTOs (hides correct_index)
        service.py      Business logic
        repository.py   Database queries
        seed.py         Seed data
      config.py         Settings from env vars
      db.py             PostgreSQL connection
      health.py         /healthz, /readyz
      feature_flags.py  Unleash client
      telemetry.py      OpenTelemetry
    alembic/            Database migrations
    tests/
      unit/             Unit tests (fake repo)
      integration/      Integration tests (Testcontainers)

  physics/              Same structure as history

  math/                 Go/chi — math questions
    main.go             Entire service (routes + data + logic)
    main_test.go        Unit test

  geography/            Java/Spring Boot — geography questions
    src/main/java/.../
      controller/       REST controllers
      service/          Business logic + in-memory data
      model/            Data models (records)

  ai-assistant/         Python/FastAPI — AI helper
    app/main.py         WebSocket + guardrails + rate limiting

frontend/               React + TypeScript + Vite
  src/
    App.tsx             Main component (quiz UI + AI chat)
    api.ts              HTTP client (fetchQuestions, submitAnswer)
    types.ts            TypeScript types
  tests/e2e/            Playwright tests

gateway/                Traefik configuration
  traefik.yml           Static config (entrypoints, providers)
  dynamic/
    middlewares.yml      Strip-prefix, security headers, rate limit
    blue-green.yml       Blue/green weighted routing

infrastructure/
  docker/postgres/init/  DB initialization script
  scripts/
    wait-for-healthy.sh  Wait for all containers
    smoke.sh             Health check all services
    run-tests.sh         Run all test suites
    run-contract.sh      API contract baseline
    run-lint.sh          Linting
    run-format.sh        Auto-formatting
    run-llm-eval.sh      LLM evaluation metrics
    bluegreen-apply.sh   Blue/green traffic switch
    seed-data.sh         Verify seed data

tests/
  performance/scenarios/
    smoke.js             k6 smoke (1 VU, p95 < 500ms)
    load.js              k6 load (50 VU, p95 < 800ms)
  chaos/experiments/
    network-latency.sh   Network resilience check

.github/workflows/
  ci.yml                 Main CI pipeline
  release.yml            Release on tag
  codeql.yml             SAST (CodeQL)
  ai-automation.yml      AI PR advisory

docs/
  architecture.md        System architecture
  test-strategy.md       Testing strategy
  release-flow.md        Release flow
  demo-checklist.md      Demo checklist
  full-project-documentation-ru.md  Full documentation (RU)
  ai-artifacts/          AI artifacts (prompts, reasoning, test-plan)

docker-compose.yml              Main compose (all services)
docker-compose.observability.yml  Prometheus, Grafana, Tempo, Loki
docker-compose.chaos.yml         Chaos tools
Makefile                         Developer shortcuts
.env.example                     Environment template
```

---

## 11. How to Verify the Product Works

1. Open `http://localhost:3000`
2. Select any subject (history, physics, math, geography)
3. Answer several questions
4. Verify the result screen shows score
5. Open AI Assistant panel:
   - Send a hint request (e.g., "help me with this question")
   - Send a leak attempt (e.g., "give me correct answer")
6. Verify the assistant provides hints but refuses to reveal answers

---

## 12. Troubleshooting (Windows / WSL / Proxy)

### `503` or unstable responses from localhost

Cause: Windows system proxy may intercept local requests.

```bash
curl --noproxy "*" http://localhost/api/history/readyz
```

### `.sh` scripts don't run in PowerShell

```bash
bash ./infrastructure/scripts/smoke.sh
```

### Services take long to start

```bash
docker compose ps
docker compose logs -f --tail=100
```

### Port already in use

Edit `.env`:
```
FRONTEND_PORT=3001
TRAEFIK_HTTP_PORT=8081
```

---

## 13. Documentation Index

| Document | Path |
|----------|------|
| Architecture | `docs/architecture.md` |
| Test Strategy | `docs/test-strategy.md` |
| Release Flow | `docs/release-flow.md` |
| Demo Checklist | `docs/demo-checklist.md` |
| Full Guide (RU) | `docs/full-project-documentation-ru.md` |
| AI Artifacts | `docs/ai-artifacts/README.md` |

---

## 14. License

MIT — see `LICENSE`.
