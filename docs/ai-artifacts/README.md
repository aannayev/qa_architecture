# AI Artifacts

This folder collects all AI-related deliverables as requested by the assignment.

## Contents

| File | Description |
|------|-------------|
| [`prompts.md`](prompts.md) | All prompts used in the project: AI assistant system prompt, anti-leak filter, mock response strategy, AI PR advisory prompt, configuration parameters |
| [`reasoning.md`](reasoning.md) | 7 architectural decisions with alternatives considered, trade-off analysis, and consequences (ADR-style) |
| [`test-plan.md`](test-plan.md) | Comprehensive AI test plan: 50+ test cases covering WebSocket, guardrails, rate limiting, provider modes, LLM evaluation, edge cases, and risk matrix |

## Relationship to Other Docs

- **Architecture decisions** are also summarized in [`docs/architecture.md`](../architecture.md) Section 8.
- **LLM quality thresholds** are defined canonically in [`docs/architecture.md`](../architecture.md) Section 6 (Quality Attributes). All other documents reference these values.
- **AI automation workflow** details are in [`.github/workflows/ai-automation.yml`](../../.github/workflows/ai-automation.yml).
