SHELL := /usr/bin/env bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help

COMPOSE        := docker compose
COMPOSE_OBS    := docker compose -f docker-compose.yml -f docker-compose.observability.yml
COMPOSE_CHAOS  := docker compose -f docker-compose.yml -f docker-compose.chaos.yml
COMPOSE_PROJECT:= qa-architect

# ──────────────────────────────────────────────────────────────
# Help
# ──────────────────────────────────────────────────────────────
.PHONY: help
help: ## Show this help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ──────────────────────────────────────────────────────────────
# Lifecycle
# ──────────────────────────────────────────────────────────────
.PHONY: up
up: ## Start the core stack (gateway + DB + services + frontend)
	$(COMPOSE) --profile services up -d --build
	@./infrastructure/scripts/wait-for-healthy.sh || true
	@echo ""
	@echo "  Frontend:   http://localhost:3000"
	@echo "  Traefik:    http://localhost:8080"
	@echo ""

.PHONY: up-observability
up-observability: ## Start the core stack + observability (Prom/Grafana/Tempo/Loki)
	$(COMPOSE_OBS) up -d --build
	@./infrastructure/scripts/wait-for-healthy.sh || true
	@echo ""
	@echo "  Grafana:    http://localhost:3001 (admin/admin)"
	@echo "  Prometheus: http://localhost:9090"
	@echo ""

.PHONY: up-chaos
up-chaos: ## Start the core stack + Toxiproxy and Pumba
	$(COMPOSE_CHAOS) up -d --build

.PHONY: down
down: ## Stop and remove all containers + volumes
	$(COMPOSE) --profile services down -v --remove-orphans

.PHONY: logs
logs: ## Tail logs for all services
	$(COMPOSE) logs -f --tail=100

.PHONY: ps
ps: ## List running containers
	$(COMPOSE) ps

.PHONY: seed
seed: ## Seed exam questions into every subject service
	@./infrastructure/scripts/seed-data.sh

# ──────────────────────────────────────────────────────────────
# Quality
# ──────────────────────────────────────────────────────────────
.PHONY: lint
lint: ## Run every linter across the monorepo
	@./infrastructure/scripts/run-lint.sh

.PHONY: fmt
fmt: ## Auto-format everything (ruff / gofmt / spotless / prettier)
	@./infrastructure/scripts/run-format.sh

.PHONY: test
test: ## Run unit + integration tests for every service
	@./infrastructure/scripts/run-tests.sh

.PHONY: coverage
coverage: ## Run tests with coverage and enforce thresholds
	@COVERAGE=1 ./infrastructure/scripts/run-tests.sh

# ──────────────────────────────────────────────────────────────
# End-to-end / cross-service testing
# ──────────────────────────────────────────────────────────────
.PHONY: e2e
e2e: ## Playwright E2E against the compose stack
	@if [[ -d frontend ]]; then \
		cd frontend && npm run test:e2e; \
	else \
		echo "frontend is not implemented yet; skipping e2e."; \
	fi

.PHONY: contract
contract: ## Pact consumer + provider verification
	@./infrastructure/scripts/run-contract.sh

.PHONY: perf-smoke
perf-smoke: ## k6 smoke (PR gate: p95 < 500ms)
	docker run --rm -i --network $(COMPOSE_PROJECT)_qa-net \
	    -v "$$PWD/tests/performance:/scripts" grafana/k6 run /scripts/scenarios/smoke.js

.PHONY: perf-load
perf-load: ## k6 load (50 VU / 5 min)
	docker run --rm -i --network $(COMPOSE_PROJECT)_qa-net \
	    -v "$$PWD/tests/performance:/scripts" grafana/k6 run /scripts/scenarios/load.js

.PHONY: chaos
chaos: up-chaos ## Run one chaos experiment (network latency)
	@./tests/chaos/experiments/network-latency.sh

.PHONY: llm-eval
llm-eval: ## Run the DeepEval suite against the AI assistant
	@./infrastructure/scripts/run-llm-eval.sh

.PHONY: smoke
smoke: ## Post-start smoke test (health + one Playwright spec)
	@./infrastructure/scripts/smoke.sh

# ──────────────────────────────────────────────────────────────
# Blue / Green
# ──────────────────────────────────────────────────────────────
.PHONY: canary
canary: ## Shift 10% of traffic to the green variant
	@BLUE_WEIGHT=90 GREEN_WEIGHT=10 ./infrastructure/scripts/bluegreen-apply.sh
	@echo "Canary: blue=90 / green=10"

.PHONY: deploy-green
deploy-green: ## Flip 100% of traffic to green
	@BLUE_WEIGHT=0 GREEN_WEIGHT=100 ./infrastructure/scripts/bluegreen-apply.sh
	@echo "Fully on green"

.PHONY: deploy-blue
deploy-blue: ## Flip 100% of traffic back to blue
	@BLUE_WEIGHT=100 GREEN_WEIGHT=0 ./infrastructure/scripts/bluegreen-apply.sh
	@echo "Fully on blue"

# ──────────────────────────────────────────────────────────────
# Codegen
# ──────────────────────────────────────────────────────────────
.PHONY: gen
gen: gen-types gen-proto ## Run all codegen

.PHONY: gen-types
gen-types: ## Generate frontend TS types from OpenAPI
	@./tools/scripts/gen-types-frontend.sh

.PHONY: gen-proto
gen-proto: ## Generate gRPC stubs (Go + Python)
	@./tools/scripts/gen-proto.sh

# ──────────────────────────────────────────────────────────────
# Clean
# ──────────────────────────────────────────────────────────────
.PHONY: clean
clean: ## Remove build artifacts and caches
	@find . -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -prune -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -prune -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -prune -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "node_modules" -prune -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "dist" -prune -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "build" -prune -exec rm -rf {} + 2>/dev/null || true
