# AI Quality Architect - Exam Platform

Polyglot microservices exam platform that demonstrates architecture, quality engineering, CI/CD, and AI integration.

## Current implementation

- Subject services:
  - `history` (Python/FastAPI)
  - `physics` (Python/FastAPI)
  - `math` (Go/chi)
  - `geography` (Java/Spring Boot)
- `ai-assistant` service (Python/FastAPI + WebSocket `/ai/v1/assist`)
- Frontend (`React + TypeScript + Vite`)
- Gateway (`Traefik`) and shared infra (`Postgres`, `Redis`, `Unleash`)
- CI workflows for quality, security scans, CodeQL, and release-to-GHCR

## Quick start

```bash
cp .env.example .env
docker compose --profile services up -d --build
./infrastructure/scripts/wait-for-healthy.sh
./infrastructure/scripts/smoke.sh
```

Main URLs:

- Frontend: `http://localhost:3000`
- Gateway API base: `http://localhost/api`
- AI WebSocket: `ws://localhost/ai/v1/assist`
- Traefik dashboard: `http://localhost:8080`

## Make targets

```bash
make up
make down
make test
make lint
make fmt
make e2e
make contract
make perf-smoke
make perf-load
make chaos
make llm-eval
```

## Architecture and QA docs

- [Architecture overview](docs/architecture.md)
- [Release flow](docs/release-flow.md)
- [Test strategy](docs/test-strategy.md)
- [AI artifacts](docs/ai-artifacts/README.md)

## Repository layout

```text
services/        Subject services + AI assistant
frontend/        React web client
gateway/         Traefik static/dynamic config
infrastructure/  Compose helpers and scripts
tests/           Performance and chaos suites
tools/           Auxiliary scripts (codegen and helpers)
.github/         CI/security/release workflows
docs/            Architecture, QA, and AI artifacts
```

## License

MIT (see `LICENSE`).
