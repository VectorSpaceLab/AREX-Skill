# Testing and Verification Overview

Use this reference to choose a verification layer before running broad test
suites. LangBot has many optional services; the correct check depends on the
change surface.

## Layered Commands

| Layer | Command | Use when |
|---|---|---|
| Quick self-test | `bash scripts/test-quick.sh` or `make test-quick` | General backend changes; runs ruff, unit tests, and smoke tests. |
| Fast integration | `bash scripts/test-integration-fast.sh` or `make test-integration-fast` | API, SQLite persistence, and pipeline interactions without external services. |
| Focused pytest | `uv run pytest <files> -q --tb=short` | Most changes; choose the smallest files tied to the modified subsystem. |
| Backend startup E2E | `uv run --python 3.12 pytest tests/e2e -q --tb=short` | Boot/config/HTTP startup changes. |
| Box integration | `uv run --python 3.12 pytest tests/integration_tests -q --tb=short` | Real Box runtime/container behavior; requires Docker or Podman. |
| Frontend lint/e2e | `cd web && pnpm lint` / `pnpm test:e2e` | Web UI changes. |
| Skills QA assets | `cd skills && bin/lbs validate && bin/lbs index` | In-repo skill/case/troubleshooting asset edits. |

The bundled helper [../scripts/select_langbot_checks.py](../scripts/select_langbot_checks.py)
prints these command groups and can optionally execute one group from a checkout.

## Focused Native Candidates

- Message flow and fake providers: `tests/smoke/test_fake_message_flow.py`.
- Pipeline stage-chain behavior: `tests/integration/pipeline/test_full_flow.py`.
- API/MCP/auth: MCP controller/mount/service tests plus API-key/authz unit tests.
- Plugin Runtime and Box unit behavior: plugin connector/handler tests and Box
  service/connector/workspace tests.
- Persistence: SQLite migration integration tests for general schema flow;
  Postgres/pgvector tests require a service DSN.
- Vector/RAG: vector manager/filter unit tests first; service-backed vector
  tests only when the corresponding service exists.
- Frontend: `pnpm lint` for static confidence, Playwright e2e when user-path
  behavior changes.

## Verification Principles

1. Run the narrowest test that can fail for the change you made.
2. Expand only when the change crosses boundaries or the narrow test is too
   synthetic.
3. Do not require provider API keys or IM platform credentials for wiring tests;
   use fakes/mocks unless the task is explicitly live-integration.
4. Service-backed and browser-backed gates are optional unless the selected task
   changes that service or user path.
5. A skipped optional backend is not a pass; record it as skipped/unverified.
6. When changing API endpoints that should be agent-accessible, verify the HTTP
   route/service behavior, MCP tool surface, and skill/testing documentation in
   the same pass.
