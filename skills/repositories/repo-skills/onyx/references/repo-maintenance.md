# Repository Maintenance

Read this for cross-cutting Onyx rules before making changes that span backend, web, mobile, CLI, deployment, or Enterprise Edition boundaries.

## Project Shape

- `backend/` contains FastAPI, Celery, SQLAlchemy, migrations, tests, `onyx/` Community Edition source, and `ee/` Enterprise overlays.
- `web/` contains the Next.js web app, Opal design system, shared web/mobile tokens/contracts, Jest tests, and Playwright E2E.
- `mobile/` contains the Expo/React Native app and does not inherit web DOM/Opal rules.
- `cli/` is the user/product `onyx-cli`; `tools/ods/` is the repository developer utility distributed as `onyx-devtools`.
- `deployment/` holds Docker Compose, Helm, Terraform, and cloud deployment assets. Generated Compose outputs are produced from templates; edit the source template/workflow, not generated copies.

## Development Defaults

- Python uses `uv` and Python 3.13. The root `pyproject.toml` sets `tool.uv.package=false`, so backend imports use checkout/PYTHONPATH conventions rather than an installed `onyx` distribution.
- JavaScript package management uses Bun in the relevant package directory. Do not assume Bun is installed on every host.
- Go is needed for `onyx-cli` and `ods` source tests/builds; do not install it without approval.
- Live Onyx calls in this repository should go through the frontend proxy: `http://localhost:3000/api/...`.

## Contribution Quality

- Keep Python and TypeScript strictly typed.
- Prefer integration tests for product behavior; use unit tests for isolated logic and external-dependency unit tests when real services are needed without full app processes.
- Keep comments brief and durable. Do not add change-log-style comments explaining only the current patch.
- Do not add TODOs without an owner or issue number.
- Prefer small, shippable changes behind feature flags for large work. Remove short-lived flags once rolled out.
- Avoid duplicated logic, private attribute access across boundaries, module-level side effects, and long functions that hide multi-step behavior.

## Security and Multi-Tenancy

- Tenant data must use tenant-aware SQLAlchemy sessions; public/shared schema access must use public-schema helpers.
- Celery tasks that touch tenant data must propagate `tenant_id` through tenant-aware task mechanics.
- New FastAPI endpoints that read or mutate user-, chat-, document-, connector-, or tenant-scoped data need the correct auth dependency. Public endpoints must be deliberately public and stateless.
- Admin operations should use admin dependencies rather than ad-hoc in-handler checks.
- Verify resource ownership/tenant access before returning or mutating records by ID.
- Connector credentials must use encrypted credential storage. Never log or store raw API keys, OAuth tokens/codes, service-account JSON, session cookies, or full secret-bearing request/response bodies.
- User-configurable external calls must guard against SSRF, especially connectors, webhooks, OAuth redirect URIs, federated search, and tool/MCP HTTP targets.
- Rich external HTML/Markdown rendered in the web UI must be sanitized.

## Test Secrets and Logs

- Test secrets resolve through Onyx test utilities in priority order: process environment, `.vscode/.env`, then AWS Secrets Manager when configured.
- If a marked secret is required and unavailable, ask the user rather than skipping a required verification silently.
- For live/integration work, inspect service logs under backend log files when available; do not leak secrets from logs into generated artifacts.

## Long-Tail Areas Deferred by This Skill

The first generated graph focuses on common repository work. The following areas are acknowledged but intentionally lower-depth:

- `loadtest/` and `profiling/` performance harnesses.
- `widget/` and browser `extensions/` surfaces.
- Legal/IP assignment artifacts.
- Full model-server local ML runtime and accelerator performance.
- Release-operator workflows that require GitHub/AWS/Docker registry write access.

If a task centers on one of these areas, inspect the current checkout and consider refreshing or extending this repo skill after gathering targeted evidence.
