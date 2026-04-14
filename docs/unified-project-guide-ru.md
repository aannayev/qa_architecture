# QA_architertor: Единый документ проекта (RU)

## 1. Назначение документа

Этот документ объединяет в одном месте:
- описание проекта и архитектуры;
- схему "как все работает";
- инструкции по запуску с нуля;
- тестирование и quality gates;
- CI/CD, security и release процесс;
- AI automation и AI assistant;
- чеклист готовности перед сдачей.

Документ рассчитан на человека, который открывает репозиторий впервые.

---

## 2. Что это за проект

`QA_architertor` — это микросервисная экзаменационная платформа для демонстрации навыков уровня Senior/Architect в областях:
- software architecture;
- quality engineering;
- CI/CD и security;
- AI integration.

### Технологический стек

- Backend:
  - `history` (Python/FastAPI)
  - `physics` (Python/FastAPI)
  - `math` (Go/chi)
  - `geography` (Java/Spring Boot)
  - `ai-assistant` (Python/FastAPI, WebSocket)
- Frontend: React + TypeScript + Vite
- Gateway: Traefik
- Infra: Docker Compose, Postgres, Redis, Unleash
- QA/Security: Playwright, k6, CodeQL, Trivy, Gitleaks

---

## 3. Схема: как система работает

### 3.1 Контейнерная схема (упрощенно)

```text
[Browser]
    |
    v
[Frontend :3000]
    |
    v
[Traefik Gateway :80]
    |------------------> [history service] ----\
    |------------------> [physics service] -----+--> [Postgres]
    |------------------> [math service] --------/
    |------------------> [geography service] ---/
    |
    +------------------> [ai-assistant] --------> [Redis]

[history/physics] ---> [Unleash]
```

### 3.2 Поток обычного запроса пользователя

1. Пользователь открывает UI (`http://localhost:3000`).
2. Frontend запрашивает вопросы через gateway:
   - `GET /api/<subject>/v1/questions`
3. Traefik направляет запрос в нужный предметный сервис.
4. Сервис возвращает вопросы/результат ответа.
5. Frontend отображает прогресс экзамена и итоговый score.

### 3.3 Поток AI запроса

1. Frontend открывает WebSocket:
   - `ws://localhost/ai/v1/assist`
2. Пользователь запрашивает подсказку.
3. AI assistant возвращает помощь/объяснение.
4. Guardrails предотвращают прямую выдачу "правильного ответа" и ограничивают rate.

### 3.4 Единый API-контракт предметных сервисов

Каждый предметный сервис поддерживает:
- `GET /healthz`
- `GET /readyz`
- `GET /v1/topics`
- `GET /v1/questions`
- `GET /v1/questions/{id}`
- `POST /v1/questions/{id}/submit`

---

## 4. Что уже реализовано

### 4.1 Продуктовая часть

- 4 предметных микросервиса на требуемых языках.
- Frontend с пользовательским сценарием:
  - выбор предмета;
  - прохождение вопросов;
  - показ результата.
- AI assistant как отдельный сервис с WebSocket интеграцией.
- API Gateway (Traefik) для единой точки входа.

### 4.2 Quality Engineering

- Unit/integration тесты по языковым стекам.
- Contract baseline checks.
- E2E на Playwright.
- Performance baseline (k6 smoke/load).
- Chaos baseline сценарий.
- LLM-eval baseline метрики:
  - accuracy;
  - relevance;
  - hallucination_rate.

### 4.3 CI/CD и Security

- CI workflow:
  - quality jobs (Python/Go/Java/Frontend);
  - e2e job с подъемом compose-стека;
  - docker image build;
  - compose validation;
  - dependency scan (Trivy);
  - secrets scan (Gitleaks).
- CodeQL workflow (SAST).
- Release workflow:
  - trigger по semver-tag `vX.Y.Z`;
  - push образов в GHCR;
  - GitHub Release.

### 4.4 AI Automation

- Workflow `.github/workflows/ai-automation.yml`:
  - анализ diff в PR;
  - AI advisory по документации/тестам/рискам;
  - публикация комментария в PR;
  - сохранение advisory как artifact.
- При отсутствии `OPENAI_API_KEY` workflow работает в fallback режиме.

---

## 5. Структура репозитория

```text
services/                  предметные сервисы + ai-assistant
frontend/                  React клиент
gateway/                   конфигурация Traefik
infrastructure/scripts/    скрипты запуска/проверок/quality
tests/                     performance + chaos
.github/workflows/         CI, CodeQL, Release, AI automation
docs/                      документация и артефакты
tools/                     вспомогательные scripts
```

---

## 6. Пошаговый запуск проекта с нуля

## Шаг 1. Требования

Нужно установить:
- Docker Desktop (с Docker Compose v2);
- Git;
- Bash shell (`Git Bash` или `WSL`) для запуска `.sh`;
- опционально `make`.

Проверка:

```bash
docker --version
docker compose version
```

## Шаг 2. Подготовка окружения

В корне репозитория:

```bash
cp .env.example .env
```

Для PowerShell:

```powershell
Copy-Item .env.example .env
```

## Шаг 3. Поднять сервисы

```bash
docker compose --profile services up -d --build
```

## Шаг 4. Дождаться ready/healthy

```bash
bash ./infrastructure/scripts/wait-for-healthy.sh
```

## Шаг 5. Прогнать базовые проверки

```bash
bash ./infrastructure/scripts/smoke.sh
bash ./infrastructure/scripts/run-contract.sh
```

## Шаг 6. Открыть приложение

- Frontend: `http://localhost:3000`
- API base: `http://localhost/api`
- AI WS: `ws://localhost/ai/v1/assist`
- Traefik dashboard: `http://localhost:8080`

---

## 7. Как проверить функциональность вручную

1. Открыть frontend.
2. Выбрать любой предмет.
3. Ответить на несколько вопросов.
4. Убедиться, что отображается итоговый результат.
5. Открыть AI assistant:
   - попросить hint;
   - затем попросить прямой ответ;
   - убедиться, что anti-leak защита работает.

---

## 8. Команды для разработки и проверки

```bash
make up
make down
make ps
make logs
make lint
make fmt
make test
make coverage
make contract
make e2e
make perf-smoke
make perf-load
make chaos
make llm-eval
```

Кратко:
- `make test` — unit/integration + frontend build.
- `make contract` — проверка базового API-контракта.
- `make e2e` — Playwright сценарии.
- `make llm-eval` — offline baseline AI метрики.

---

## 9. CI/CD: путь от коммита до релиза

1. Разработчик создает commit/push.
2. На PR запускаются CI + security workflows.
3. Quality gates должны пройти успешно.
4. После merge создается tag `vX.Y.Z`.
5. Release workflow:
   - собирает и публикует образы в GHCR;
   - создает GitHub Release.

---

## 10. Security подход

- SAST: `CodeQL`.
- Dependency vulnerabilities: `Trivy`.
- Secrets scanning: `Gitleaks`.
- Базовая защита AI assistant:
  - anti-leak правилa;
  - rate limiting.

---

## 11. Частые проблемы и решения

### 11.1 Локальные запросы дают 503 в Windows

Причина: прокси.

Решение:

```bash
curl --noproxy "*" http://localhost/api/history/readyz
```

### 11.2 `.sh` не запускается в PowerShell

Запускать через bash:

```bash
bash ./infrastructure/scripts/smoke.sh
```

### 11.3 Сервисы не выходят в healthy

Проверить:

```bash
docker compose ps
docker compose logs -f --tail=100
```

---

## 12. Чеклист "проект готов к демонстрации"

- [ ] `docker compose --profile services up -d --build` выполнился успешно.
- [ ] `smoke.sh` зеленый.
- [ ] `run-contract.sh` зеленый.
- [ ] UI открывается и проходит экзаменационный flow.
- [ ] AI assistant отвечает и не раскрывает прямой ответ.
- [ ] `make test` и `make e2e` проходят локально.
- [ ] Документация актуальна.

---

## 13. Что именно сдавать

1. Репозиторий с кодом, workflow и документацией.
2. Видео-демо (по задаче: на английском, 10-20 минут).
3. AI artifacts:
   - prompts;
   - reasoning;
   - test-plan.

---

## 14. Полезные ссылки внутри репозитория

- `README.md`
- `docs/architecture.md`
- `docs/release-flow.md`
- `docs/test-strategy.md`
- `docs/demo-checklist.md`
- `docs/ai-artifacts/README.md`
- `docs/unified-project-guide-ru.docx`
- `docs/unified-project-guide-ru.md`

