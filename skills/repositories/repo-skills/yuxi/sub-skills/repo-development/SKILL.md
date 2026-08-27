---
name: repo-development
description: "Maintain the Yuxi monorepo: Docker Compose workflows,
  backend/frontend/CLI checks, formatting, release versioning, and contribution
  docs."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Repo Development

Use this sub-skill when the task is about keeping the Yuxi repository healthy: editing code, choosing the smallest valid check set, formatting, versioning, release prep, or updating maintainer docs.

## Owns
- Monorepo boundaries for `backend/`, `web/`, `packages/yuxi-cli/`, `docs/`, `scripts/`, and Docker Compose.
- Hot-reload development in the Compose stack.
- Safe backend import, CLI pytest, frontend unit, and frontend lint checks.
- Service-required backend integration/e2e checks when the stack is already running.
- Format, version bump, changelog, and contribution workflow.

## Does not own
- Product runtime behavior, agent logic, KB/OCR internals, or external-provider troubleshooting except where they affect maintainer checks.
- Starting or stopping Docker Compose services from the bundled check script.

## Read first
- `references/development-workflows.md`
- `references/testing-and-release.md`
- `references/troubleshooting.md`

## Safe working rules
- Treat Docker Compose as the canonical development runtime.
- Prefer no-write checks when you only need verification.
- The frontend lint path can rewrite files; use the bundled check-only command unless you explicitly want auto-fix.
- Keep service-required tests opt-in; the bundled script never starts or stops services for you.
- Update changelog and docs navigation when the change is user-visible or adds formal docs.
- Avoid unrelated refactors, broad formatting, and secret leakage.

## Recommended command path
- Backend package import: `./scripts/run-selected-checks.sh backend-import --run`
- CLI pytest: `./scripts/run-selected-checks.sh cli-pytest --run`
- Frontend unit: `./scripts/run-selected-checks.sh frontend-unit --run`
- Frontend lint check: `./scripts/run-selected-checks.sh frontend-lint --run`
- Service-required backend checks: `./scripts/run-selected-checks.sh backend-integration backend-e2e --with-services --run`
- Mutating repo-wide cleanup: `make format`
- Release/version policy: read `references/testing-and-release.md`; only use the repo-owned version-bump helper inside a checkout after an explicit release task and diff review.

## If the command choice is unclear
Use the bundled references to decide the smallest safe command set. If a check depends on running services or external credentials, surface that requirement before claiming success.
