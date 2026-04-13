# Release Flow

## Commit to production path

```mermaid
flowchart LR
  Dev[Developer push]
  PR[Pull Request]
  CI[CI workflow]
  Security[Security workflows]
  Merge[Merge to main]
  Tag[Create semver tag]
  Release[release workflow]
  GHCR[GHCR images]
  GHRelease[GitHub release]

  Dev --> PR
  PR --> CI
  PR --> Security
  CI --> Merge
  Security --> Merge
  Merge --> Tag
  Tag --> Release
  Release --> GHCR
  Release --> GHRelease
```

## CI gates

- Python quality (history, physics, ai-assistant)
- Go tests (math)
- Java tests (geography)
- Frontend build
- Docker builds for all deployable units
- Compose validation
- Dependency scan (Trivy)
- Secrets scan (Gitleaks)
- SAST (CodeQL in dedicated workflow)

## Versioning

- Release trigger: push tag `vX.Y.Z`
- Artifacts:
  - GHCR images per service, tagged with release version
  - GitHub Release entry with generated notes
