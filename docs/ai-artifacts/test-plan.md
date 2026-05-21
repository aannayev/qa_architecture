# AI-Focused Test Plan

## 1. Scope

This plan covers testing of all AI-related components:
- **AI Assistant service** — WebSocket API, guardrails, rate limiting, mock and real LLM modes
- **AI Automation workflow** — PR advisory generation and posting
- **LLM Evaluation** — offline baseline quality metrics

---

## 2. AI Assistant — Functional Tests

### 2.1 WebSocket Connection

| # | Test Case | Input | Expected Result | Priority |
|---|-----------|-------|-----------------|:--------:|
| F1 | Establish connection | `ws://localhost/ai/v1/assist?session_id=test1` | Connection accepted (HTTP 101 → WS open) | Critical |
| F2 | Connection with stripped path | `ws://localhost/v1/assist?session_id=test2` | Connection accepted (direct route) | High |
| F3 | Anonymous session | `ws://localhost/ai/v1/assist` (no session_id) | Connection accepted; uses "anonymous" session | Medium |
| F4 | Send text, receive JSON | Send `"Hello"` | Receive `{"role": "assistant", "content": "...", "blocked": false}` | Critical |

### 2.2 Mock Response Quality

| # | Test Case | Input Message | Expected Behavior | Priority |
|---|-----------|---------------|-------------------|:--------:|
| M1 | Greeting response | `"Hello"` | Returns welcome message with usage guidance | High |
| M2 | History hint | `"Help me with this history question"` | Returns history-related hint (mentions time period, events) | High |
| M3 | Math hint | `"I need help solving this equation"` | Returns math-related hint (mentions step-by-step approach) | High |
| M4 | Physics hint | `"What force applies here?"` | Returns physics-related hint (mentions laws, principles) | High |
| M5 | Geography hint | `"Which country is this?"` | Returns geography-related hint (mentions region, map) | High |
| M6 | Gratitude response | `"Thanks for the help"` | Returns encouraging response | Medium |
| M7 | Generic fallback | `"asdqwezxc"` (no keyword match) | Returns one of 10 general hints (deterministic per session+message hash) | Medium |
| M8 | Deterministic fallback | Same message + session twice | Returns the same hint both times (hash-based selection) | Medium |

### 2.3 Anti-Leak Guardrail

| # | Test Case | Input Message | Expected Behavior | Priority |
|---|-----------|---------------|-------------------|:--------:|
| L1 | "correct answer" | `"What is the correct answer?"` | Refusal response; `blocked` may be false (filter triggers before LLM) | Critical |
| L2 | "just answer" | `"Just answer the question"` | Refusal response | Critical |
| L3 | "exact answer" | `"Give me the exact answer"` | Refusal response | Critical |
| L4 | "right option" | `"Which is the right option?"` | Refusal response | Critical |
| L5 | "tell me the answer" | `"Tell me the answer please"` | Refusal response | Critical |
| L6 | "which is correct" | `"Which is correct, A or B?"` | Refusal response | Critical |
| L7 | "what is the answer" | `"What is the answer to #3?"` | Refusal response | Critical |
| L8 | "give me answer" | `"Give me answer now"` | Refusal response | Critical |
| L9 | "what's the answer" | `"What's the answer?"` | Refusal response | Critical |
| L10 | "which option" | `"Which option should I pick?"` | Refusal response | Critical |
| L11 | Case insensitivity | `"CORRECT ANSWER"` | Refusal response (filter lowercases input) | High |
| L12 | Embedded phrase | `"I don't need the correct answer, just a hint"` | Refusal response (substring match triggers) | High |
| L13 | Safe request (no leak) | `"Can you explain this concept?"` | Normal hint response (not blocked) | High |

### 2.4 Rate Limiting

| # | Test Case | Setup | Expected Behavior | Priority |
|---|-----------|-------|-------------------|:--------:|
| R1 | Per-minute limit | Send 6 messages in < 60s (default limit: 5) | 6th message returns rate limit error with `blocked: true` | Critical |
| R2 | Per-minute recovery | Send 5 messages, wait 61 seconds, send 1 more | 6th message succeeds (window expired) | High |
| R3 | Per-session limit | Send 21 messages (default limit: 20) | 21st message returns session limit error with `blocked: true` | Critical |
| R4 | Different sessions | Session A sends 5/min, Session B sends 1 | Session B succeeds (independent counters) | High |
| R5 | Rate limit message format | Trigger per-minute limit | Response contains "Per-minute limit exceeded" | Medium |
| R6 | Session limit message format | Trigger session limit | Response contains "Session limit exceeded" | Medium |

---

## 3. AI Assistant — Provider Modes

### 3.1 Mock Mode (Default)

| # | Test Case | Config | Expected Behavior |
|---|-----------|--------|-------------------|
| P1 | Default mock | `LLM_PROVIDER=mock` (or unset) | All responses from `_mock_response()` |
| P2 | Mock anti-leak | `LLM_PROVIDER=mock` + leak request | Refusal from `MOCK_LEAK_RESPONSES` |

### 3.2 OpenAI Mode

| # | Test Case | Config | Expected Behavior |
|---|-----------|--------|-------------------|
| P3 | OpenAI call | `LLM_PROVIDER=openai`, `OPENAI_API_KEY=valid` | Response from GPT-4o-mini with system prompt |
| P4 | OpenAI fallback | `LLM_PROVIDER=openai`, `OPENAI_API_KEY=invalid` | Falls back to mock response (logged error) |
| P5 | OpenAI history | Send 3 messages in session | Conversation history maintained (up to 20 messages) |
| P6 | OpenAI leak bypass | `LLM_PROVIDER=openai` + leak phrase | Blocked by keyword filter BEFORE OpenAI call |

### 3.3 Anthropic Mode

| # | Test Case | Config | Expected Behavior |
|---|-----------|--------|-------------------|
| P7 | Anthropic call | `LLM_PROVIDER=claude`, `ANTHROPIC_API_KEY=valid` | Response from Anthropic API with system prompt |
| P8 | Anthropic fallback | `LLM_PROVIDER=claude`, `ANTHROPIC_API_KEY=invalid` | Falls back to mock response |

---

## 4. AI Quality Metrics (LLM Evaluation)

### 4.1 Baseline Metrics

Evaluated by `infrastructure/scripts/run-llm-eval.sh` using fixed offline fixtures.

| Metric | Definition | Threshold | Current Baseline |
|--------|-----------|-----------|:----------------:|
| **accuracy** | Factual correctness of hints | ≥ 0.70 | 0.75 (3/4 fixtures) |
| **relevance** | Pertinence to the question topic | ≥ 0.75 | 0.75 (3/4 fixtures) |
| **hallucination_rate** | Rate of fabricated information | ≤ 0.15 | 0.00 (4/4 safe) |

### 4.2 Evaluation Methodology

**Current approach (offline baseline):**
- 4 fixed test fixtures with pre-judged labels
- Script computes ratios: `metric = count_pass / total`
- Deterministic — always produces the same result in CI
- Validates the *framework* works, not real LLM quality

**Future approach (real LLM evaluation):**
- Human-labeled test dataset (50+ question-answer pairs)
- Run against real LLM provider
- Compute metrics using DeepEval or similar framework
- Track metrics over time in CI artifacts

### 4.3 Test Cases for Evaluation Script

| # | Test Case | Expected |
|---|-----------|----------|
| E1 | Script runs successfully | Exit code 0, prints all 3 metrics |
| E2 | Accuracy ≥ 0.70 | Prints "accuracy=0.75" |
| E3 | Relevance ≥ 0.75 | Prints "relevance=0.75" |
| E4 | Hallucination ≤ 0.15 | Prints "hallucination_rate=0.00" |
| E5 | All thresholds pass | Prints "LLM eval thresholds passed." |
| E6 | Threshold failure (synthetic) | If fixtures changed to fail, exit code 1 + "failed" message |

---

## 5. AI Automation (PR Advisory) — Test Plan

### 5.1 Workflow Execution

| # | Test Case | Trigger | Expected |
|---|-----------|---------|----------|
| A1 | Workflow triggers on PR | Open a PR | `ai-doc-and-test-advisor` job starts |
| A2 | Diff collection | PR with code changes | `pr_context.txt` contains changed files + unified diff |
| A3 | Diff truncation | PR with > 1200 lines diff | Diff truncated to 1200 lines in context |

### 5.2 With API Key

| # | Test Case | Config | Expected |
|---|-----------|--------|----------|
| A4 | Advisory generated | `OPENAI_API_KEY` secret set | `ai_advisory.md` contains 5 sections (Docs, Tests, Quality, Security, Checklist) |
| A5 | PR comment posted | PR event | Bot comment with `<!-- ai-automation-advisory -->` marker |
| A6 | Comment updated on re-push | Push to existing PR | Existing bot comment updated (not duplicated) |
| A7 | Artifact uploaded | Any run | `ai-advisory-report` artifact available for download |

### 5.3 Without API Key (Fallback)

| # | Test Case | Config | Expected |
|---|-----------|--------|----------|
| A8 | Fallback checklist | `OPENAI_API_KEY` not set | Static fallback checklist posted (docs, tests, security reminders) |
| A9 | No error on missing key | `OPENAI_API_KEY` empty | Workflow exits 0, posts fallback content |

---

## 6. Edge Cases & Negative Tests

| # | Test Case | Scenario | Expected |
|---|-----------|----------|----------|
| N1 | Empty message | Send `""` via WebSocket | Returns a hint (treated as generic message) |
| N2 | Very long message | Send 10,000-character message | Handled without crash; response generated normally |
| N3 | Unicode/emoji | Send `"🤔 помогите"` | Handled without crash; subject detection may not match (falls back to generic) |
| N4 | Rapid reconnection | Disconnect and reconnect quickly | New connection accepted; session counter preserved for same session_id |
| N5 | Concurrent sessions | 10 WebSocket connections with different session_ids | All handled independently; no cross-session data leakage |
| N6 | XSS in message | Send `<script>alert('xss')</script>` | Message processed as text; no execution on server side |
| N7 | SQL injection in session_id | `session_id='; DROP TABLE--` | No database involved; session_id used as dict key only |

---

## 7. Risk Matrix for AI Components

| Risk | Likelihood | Impact | Test Coverage |
|------|:----------:|:------:|---------------|
| Answer leakage via AI | High | High | L1-L13 (keyword filter), P6 (provider bypass), system prompt |
| Rate limit bypass | Low | Medium | R1-R6 |
| LLM API failure | Medium | Low | P4, P8 (fallback to mock) |
| Hallucination in real mode | Medium | Medium | E1-E6 (baseline), system prompt constraint |
| Conversation history leak | Low | High | N5 (cross-session isolation) |
| Workflow failure on PR | Low | Low | A1-A9 (fallback mode) |
