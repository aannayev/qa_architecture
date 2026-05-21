# Contributing

Thanks for taking the time to contribute to the AI Quality Architect platform.

## Ground rules

1. **Follow Conventional Commits.** `release-please` drives versioning from your commit messages. Use `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`, `perf:`, `ci:`. Add `!` or `BREAKING CHANGE:` for breaking changes.
2. **Keep PRs small and focused.** A PR touching more than ~400 lines is harder to review than two that each touch 200.
3. **Tests are not optional.** New code requires unit tests; integration or contract tests when behavior crosses a service boundary.
4. **All quality gates must be green.** Coverage ≥ 80%, lint zero warnings, no new security findings, OpenAPI specs lint clean.
5. **Architecture changes need an ADR.** Add a new entry in the *Architectural Decisions* section of [`docs/architecture.md`](docs/architecture.md).
6. **Changes to prompts or AI workflows require CODEOWNERS review.**

## Local development

```bash
cp .env.example .env
make up
make seed
make test
```

## Branch model

- `main` — always deployable. Protected: requires passing CI + 1 review + up-to-date branch.
- `feat/*`, `fix/*`, `docs/*`, `chore/*` — short-lived branches off `main`.
- Release PRs are auto-created by `release-please` on merge to `main`.

## Pull request checklist

- [ ] Conventional Commit title
- [ ] Tests added/updated
- [ ] Docs updated (if specs or architecture are affected)
- [ ] ADR added in `docs/architecture.md` (if architecture changed)
- [ ] All CI checks green
- [ ] Reviewed the AI PR reviewer comments and either addressed them or explained why not

## Where to look

- Architecture & ADRs: [`docs/architecture.md`](docs/architecture.md)
- Test strategy: [`docs/test-strategy.md`](docs/test-strategy.md)
- Release flow: [`docs/release-flow.md`](docs/release-flow.md)
- Demo checklist: [`docs/demo-checklist.md`](docs/demo-checklist.md)
- AI artifacts: [`docs/ai-artifacts/`](docs/ai-artifacts/)
- Full guide (RU): [`docs/full-project-documentation-ru.md`](docs/full-project-documentation-ru.md)
