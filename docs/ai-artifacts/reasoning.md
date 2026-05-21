# Architecture Reasoning

This document records the key decisions made during the design and implementation of the QA_architertor platform, including the alternatives considered and the rationale for each choice.

---

## Decision 1: Unified Subject Service API Contract

### Context

Four services in four different language stacks (Python, Go, Java) need to serve the same frontend and pass the same contract tests. Without a shared interface, the frontend would need per-service adapters and contract testing would be impossible.

### Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| **Unified REST contract** (chosen) | One frontend client, one contract test, easy to add subjects | Limits per-service flexibility |
| GraphQL | Flexible queries, single endpoint | Requires schema stitching or federation; overkill for fixed question domain |
| gRPC | Strong typing, efficient binary protocol | Not browser-native without transcoding gateway; adds build complexity |
| Per-service custom API | Maximum flexibility | Frontend needs N adapters; N separate contract tests; no consistency guarantee |

### Decision

All subject services implement identical endpoints: `/v1/topics`, `/v1/questions`, `/v1/questions/{id}`, `/v1/questions/{id}/submit`, plus health probes `/healthz` and `/readyz`.

### Consequences

- `run-contract.sh` validates all services in a single pass.
- Frontend `api.ts` is completely subject-agnostic — it substitutes the subject name in the URL path.
- Adding a new subject (e.g., "literature") requires only implementing the same interface in any language.
- Trade-off: all services must return the same response schema, which limits service-specific extensions.

---

## Decision 2: Gateway-First Traffic Model (Traefik)

### Context

The frontend and E2E tests need stable URLs. Internal service topology (port numbers, container names) should be hidden from clients.

### Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| **Traefik** (chosen) | Native Docker provider, dynamic config, path routing, middleware pipeline, blue/green support | More complex config than simple reverse proxy |
| Nginx | Widely known, simple config | Static config; no native Docker service discovery; reload on topology change |
| Envoy / Istio | Full service mesh, advanced traffic management | Massive operational overhead for a test assignment |
| No gateway (direct ports) | Simplest setup | Frontend must know all service ports; changes break tests |

### Decision

Traefik v3 with path-prefix routing (`/api/<subject>` → subject service, `/ai` → AI assistant). Strip-prefix middleware removes routing prefixes before forwarding.

### Consequences

- All external traffic goes through `localhost:80` — one URL to remember.
- Blue/green deployment is a Traefik config change (weighted routing), not infrastructure change.
- Services can be scaled, replaced, or reorganized without changing frontend URLs.
- Dashboard at `:8080` provides runtime visibility into routes and middleware.

---

## Decision 3: Mock-First AI Provider

### Context

The assignment requires AI integration, but reviewers must be able to run the project locally and in CI without external API keys or costs.

### Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| **Mock-first with opt-in real LLM** (chosen) | Deterministic, zero-cost, works offline | Mock responses are static; doesn't test real LLM behavior |
| Always require API key | Tests real LLM behavior | Blocks reviewers without keys; costs money in CI; non-deterministic |
| Local model (Ollama, llama.cpp) | Real LLM without external API | Heavy resource requirements (GPU/RAM); slow on CI runners |
| Embedding-based responses | Semantic understanding without full LLM | Complex setup; still needs model download |

### Decision

`LLM_PROVIDER=mock` is the default. Mock mode uses pattern-matched keyword responses with deterministic hash-based fallback. Real providers (OpenAI, Anthropic) are opt-in via environment variables.

### Consequences

- CI always passes regardless of API key availability.
- Reviewers get the full user experience without any setup beyond `docker compose up`.
- LLM eval script (`run-llm-eval.sh`) establishes baseline metrics against mock behavior — provides a reference point for real LLM comparison.
- Anti-leak filter works identically in mock and real mode (runs before provider dispatch).

---

## Decision 4: PostgreSQL for Stateful, In-Memory for Stateless

### Context

The assignment requires data storage. Python services (history, physics) have enough questions to justify a real database and demonstrate ORM + migration skills. Go and Java services have small, static question sets.

### Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| **PostgreSQL + in-memory mix** (chosen) | Demonstrates full ORM lifecycle for Python; lightweight for Go/Java | Inconsistent storage model across services |
| All services use PostgreSQL | Consistent architecture | Unnecessary complexity for 5-10 static questions in Go/Java |
| All services use in-memory | Simplest | Doesn't demonstrate ORM, migrations, or database testing |
| SQLite per service | Persistent, lightweight | Not production-representative; no async driver for Python |
| MongoDB | Schema-flexible | Different paradigm; less standard for this domain |

### Decision

- `history` and `physics`: PostgreSQL via SQLAlchemy (async) + Alembic migrations. Questions seeded on startup.
- `math` and `geography`: Questions hardcoded in source code (in-memory). No database dependency.

### Consequences

- Python services showcase: async ORM, migration lifecycle, Testcontainers integration tests, seed data management.
- Go/Java services stay lightweight and fast to start.
- Trade-off: in-memory services lose data on restart (acceptable — data is static and rebuilt from code).
- Trade-off: no integration tests needed for Go/Java (no DB to test against).

---

## Decision 5: Anti-Leak Guardrails — Deterministic Filter + LLM Prompt

### Context

The AI assistant must provide hints without revealing correct answers. Pure prompt engineering is non-deterministic and can be bypassed via adversarial prompting.

### Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| **Keyword filter + system prompt** (chosen) | Deterministic for known patterns; LLM prompt handles novel phrasings | Keyword filter can be bypassed by paraphrase |
| System prompt only | Handles novel phrasings naturally | Non-deterministic; can be jailbroken |
| Keyword filter only | 100% deterministic | Doesn't handle rephrased requests |
| Embedding similarity filter | Semantic understanding of intent | Requires embedding model; adds latency; complex setup |
| Output validation (post-processing) | Catches leaks in LLM response | Additional latency; must define "what is an answer" |

### Decision

Two-layer defense:
1. **Layer 1 (deterministic):** `_is_leak_request()` checks for 10 known leak phrases. Triggers before any LLM call. Returns a randomized refusal response.
2. **Layer 2 (probabilistic):** System prompt instructs LLM to never reveal answers. Handles novel phrasings that bypass keyword filter.

### Consequences

- 100% catch rate for known leak patterns (testable, deterministic).
- Graceful handling of novel leak attempts via LLM instruction.
- Rate limiting (5/min, 20/session) provides a third defense layer — limits brute-force attempts.
- Mock mode uses the same anti-leak filter, ensuring consistent behavior across providers.

---

## Decision 6: Conventional Commits + Tag-Based Releases

### Context

The project needs automated versioning, changelog generation, and release artifact creation.

### Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| **Conventional Commits + semver tags** (chosen) | Industry standard; machine-readable; drives automated releases | Requires commit discipline |
| Manual versioning | Full control | Human error; no automation |
| `release-please` auto-PRs | Fully automated version bumps | Additional complexity; may conflict with manual tags |
| CalVer (date-based) | Simple, no decision needed | Less semantic; harder to communicate breaking changes |

### Decision

Developers write Conventional Commit messages (`feat:`, `fix:`, etc.). Releases are triggered by pushing a semver tag (`vX.Y.Z`). `release.yml` builds Docker images, pushes to GHCR, and creates a GitHub Release.

### Consequences

- Clear commit history — anyone can scan commits and understand what changed.
- Automated Docker image tagging matches git tags.
- GitHub Release page serves as changelog.

---

## Decision 7: Multi-Language Stack (Polyglot)

### Context

The assignment explicitly requires implementing services in Python, Go, and Java to demonstrate polyglot capability.

### Why These Specific Frameworks

| Service | Language | Framework | Why This Framework |
|---------|----------|-----------|-------------------|
| history, physics | Python 3.12 | FastAPI | Async-native, auto-generated OpenAPI docs, Pydantic validation, strong ecosystem |
| math | Go 1.22 | chi v5 | Idiomatic Go HTTP routing, minimal dependencies, fast compilation |
| geography | Java 21 | Spring Boot 3 | Enterprise standard, extensive ecosystem, demonstrates JVM competence |
| ai-assistant | Python 3.12 | FastAPI | WebSocket support, same stack as subject services for knowledge reuse |
| frontend | TypeScript | React 18 + Vite 5 | Modern SPA standard, strong typing, fast development with HMR |

### Trade-offs

- **Operational cost:** Three different build systems (pip, go, maven), three different test runners (pytest, go test, JUnit).
- **Benefit:** Demonstrates real-world polyglot competence; shows that the unified API contract works across any language stack.
