# Prompts Used

## Architecture

Prompt focus:

- define service boundaries for exam domain
- maintain a shared API contract across language stacks
- enforce gateway-first traffic model

## AI assistant

Prompt focus:

- provide hints, not direct answers
- reject requests that ask for explicit answer leakage
- keep deterministic fallback behavior for local and CI runs

## Test generation

Prompt focus:

- produce endpoint-level contract checks for each subject service
- ensure tests assert both success and failure behavior
