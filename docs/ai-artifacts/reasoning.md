# Architecture Reasoning

## Why a shared subject API

The frontend can be implementation-agnostic and treat all subjects uniformly.
This also enables one reusable contract check script.

## Why mock-first AI provider

The assignment requires AI integration, but reviewers must run locally without external credentials.
Mock-first guarantees deterministic behavior and stable CI.

## Why gateway path routing

Path routing (`/api/<subject>`, `/ai`) keeps browser and tests stable while service internals evolve.
