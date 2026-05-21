# Prompts & Prompt Engineering

## 1. AI Exam Assistant — System Prompt

Used in `services/ai-assistant/app/main.py` as the `SYSTEM_PROMPT` constant. Sent as the `system` message in every LLM conversation.

```text
You are an AI exam assistant. Your role is to help students during exams by:
- Providing helpful hints and explanations
- Breaking down complex questions into simpler parts
- Explaining underlying concepts and principles
- Guiding reasoning without revealing answers directly

STRICT RULES:
- NEVER reveal the correct answer directly
- NEVER say which option (A, B, C, D) is correct
- Instead, explain the concept so the student can figure it out
- Keep responses concise (2-4 sentences)
- Be encouraging and supportive
- If the student asks for the direct answer, politely refuse and offer to
  explain the concept instead
```

### Design Decisions

- **"NEVER" in caps** — hard emphasis reduces compliance drift in both OpenAI and Anthropic models.
- **Concise length constraint (2-4 sentences)** — prevents cost inflation and keeps UI responsive.
- **No domain-specific knowledge injected** — the assistant is generic across all 4 subjects; domain context comes from user messages.
- **Encouraging tone** — assignment targets an exam environment where student anxiety is a factor.

### Limitations

- Prompt alone is not sufficient to prevent answer leakage — a determined adversary can rephrase. This is why a **deterministic keyword filter** (`_is_leak_request`) acts as the first layer before the prompt even reaches the LLM.

---

## 2. Anti-Leak Keyword Filter

Not a prompt per se, but a deterministic pre-filter that runs **before** any LLM call. Defined in `_is_leak_request()`.

**Blocked phrases:**

```text
"correct answer", "just answer", "exact answer", "right option",
"tell me the answer", "which is correct", "what is the answer",
"give me answer", "what's the answer", "which option"
```

**Response when triggered** (one of 4 mock responses, randomly selected):

```text
1. "I can't give you the direct answer, but I can help you think through it.
    What part of the question is most confusing?"
2. "Instead of telling you the answer, let me explain the concept.
    That way you'll understand *why* it's correct. What topic does this relate to?"
3. "I'm here to guide your thinking, not give away answers.
    Let's break this question down — what do you think it's really asking?"
4. "Giving the answer wouldn't help you learn.
    Tell me what you're stuck on, and I'll explain the underlying idea."
```

### Why a Keyword Filter Instead of Pure Prompt Engineering

| Approach | Determinism | Bypass Risk | Latency | Cost |
|----------|:-----------:|:-----------:|:-------:|:----:|
| Keyword filter only | ✅ 100% | Medium (rephrase) | ~0ms | $0 |
| Prompt engineering only | ❌ Non-deterministic | High (jailbreak) | LLM latency | LLM cost |
| **Both (current approach)** | ✅ Filter catches known patterns | Low | Filter: ~0ms, LLM: normal | Normal |

---

## 3. Mock Response Strategy

In default `LLM_PROVIDER=mock` mode, the assistant uses pattern-matched responses instead of calling an LLM.

**Subject detection keywords → tailored hints:**

| Pattern | Example Keywords | Response Type |
|---------|-----------------|---------------|
| Greeting | `hello`, `hi`, `help me` | Welcome message + usage guidance |
| Gratitude | `thank`, `thanks` | Encouragement to continue |
| History | `history`, `ancient`, `revolution`, `war` | Historical context hint |
| Math | `math`, `equation`, `solve`, `formula` | Step-by-step problem approach |
| Physics | `physics`, `force`, `energy`, `velocity` | Identify-the-law approach |
| Geography | `geo`, `capital`, `country`, `river` | Spatial reasoning hint |
| Derivative | `derivative`, `d/dx`, `x^2` | Power rule explanation |
| Linear equation | `2x`, `solve for x` | Isolate-the-variable approach |
| Fallback | (anything else) | Deterministic selection from 10 general hints (hash-based) |

**Fallback selection:** `hash(message + session_id) % len(hints)` — ensures the same question from the same session always gets the same hint (deterministic for testing).

---

## 4. AI PR Advisory Prompt

Used in `.github/workflows/ai-automation.yml`. Sent to GPT-4o-mini when a PR is opened or updated.

```text
System: "Be strict, concrete, and actionable."

User: "You are a senior QA architect assistant. Analyze this PR context and
produce concise recommendations in Markdown with sections:
1) Documentation updates needed
2) Test additions needed
3) Code quality risks
4) Security concerns
5) Suggested follow-up checklist

{PR diff context — changed files list + unified diff, truncated to 1200 lines}
```

### Design Decisions

- **Low temperature (0.1)** — minimizes hallucination in code review, favors deterministic and factual output.
- **Model: GPT-4o-mini** — cost-effective for advisory tasks; full GPT-4o unnecessary for diff analysis.
- **Diff truncation (1200 lines)** — prevents token limit issues on large PRs while capturing enough context.
- **Fallback mode** — when `OPENAI_API_KEY` is not configured, posts a static checklist instead of failing silently.

### Fallback Checklist (No API Key)

```text
- Ensure docs are updated when API/contracts change.
- Ensure tests are added/updated for changed logic.
- Ensure security-sensitive changes include threat notes.
```

---

## 5. Test Generation Prompts (Architecture-Level)

These prompts guided the design of the test strategy rather than generating individual test code:

### Contract Test Design

```text
Given a microservice architecture with N services implementing the same REST API
contract, design a minimal validation script that:
- Checks each service responds to health endpoints
- Verifies the query interface returns valid data
- Runs in under 30 seconds with curl only (no test framework dependency)
```

### Unit Test Architecture

```text
For a Python/FastAPI service with repository pattern:
- Unit tests should use a FakeRepository (in-memory) to isolate domain logic
- Integration tests should use Testcontainers with a real PostgreSQL instance
- Schema tests should verify that QuestionPublic hides correct_index
```

### LLM Evaluation Design

```text
Design an offline evaluation script for an AI exam assistant that measures:
1. Accuracy — does the assistant provide factually correct guidance?
2. Relevance — is the response relevant to the question asked?
3. Hallucination rate — does the assistant invent information?

Use fixed test fixtures for deterministic CI; real LLM eval requires human-labeled data.
```

---

## 6. Configuration Parameters

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `LLM_PROVIDER` | `mock` | Provider selection: `mock`, `openai`, `claude`/`anthropic` |
| `LLM_MODEL` | `gpt-4o-mini` | Model name for OpenAI/Anthropic API calls |
| `LLM_MAX_TOKENS` | `600` | Max response tokens |
| `LLM_TEMPERATURE` | `0.4` | Creativity vs. determinism balance |
| `AI_RATE_LIMIT_PER_SESSION` | `20` | Max messages per WebSocket session |
| `AI_RATE_LIMIT_PER_MINUTE` | `5` | Max messages per minute per session |
| `OPENAI_API_KEY` | *(empty)* | OpenAI API key (enables `openai` provider) |
| `ANTHROPIC_API_KEY` | *(empty)* | Anthropic API key (enables `claude` provider) |
