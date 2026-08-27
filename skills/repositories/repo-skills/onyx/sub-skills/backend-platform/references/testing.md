# Testing

This reference covers the backend test ladder, environment expectations, secrets, and log locations.

## Test ladder

| Test type | Environment | When to use it | Typical command |
| --- | --- | --- | --- |
| Unit | No external services | Isolated logic with mocked I/O. | `uv run --frozen --no-default-groups --group backend --group dev pytest -xv backend/tests/unit` |
| External-dependency unit | Real Postgres, Redis, MinIO, and related external services; Onyx app processes are not running | Real dependency behavior with direct function calls and selective mocking. | `uv run --frozen --no-default-groups --group backend --group dev --env-file .vscode/.env pytest backend/tests/external_dependency_unit` |
| Integration | Full Onyx deployment running | Real API flows with no mocking. Prefer this when the behavior crosses process boundaries. | `uv run --frozen --no-default-groups --group backend --group dev --env-file .vscode/.env pytest backend/tests/integration` |
| Playwright / E2E | Full stack including the web server | Frontend and backend coordination, browser behavior, or flows that need the running UI. | `cd web && bun run playwright <TEST_NAME>` |

## How to choose

- Prefer integration tests over unit tests when the behavior crosses processes or needs real deployment state.
- Use external-dependency unit tests when you need real infrastructure but want direct control over the function under test.
- Use Playwright only when the browser and backend must cooperate.
- Keep tests focused on one flow when possible.

## Fixtures and style

- Integration tests should use the existing manager and expected-state pattern when one exists.
- Check the shared fixtures and local test utilities before creating new helpers.
- Prefer fixtures over hand-built state when the suite already provides them.
- Use the smallest test type that proves the behavior.

## Secrets and logs

- Secret lookup order is: environment variables, then the gitignored local env file, then AWS Secrets Manager.
- Tests that require secrets should declare them explicitly.
- Some integration and end-to-end scenarios assume `AUTH_TYPE=basic` and `ENABLE_PAID_ENTERPRISE_EDITION_FEATURES=true` on the running API server.
- When debugging integration or live flows, inspect the service log files under `backend/log/`.
- For browser-based flows, log in through the UI with the shared admin test user unless the test scenario says otherwise.
- The shared admin browser account is `admin_user@example.com` with password `TestPassword123!`.

## Practical note

- The `uv` workflow is the normal way to run backend Python tests and it will use the lockfile-pinned environment.
- The example commands select the backend and dev groups so they stay focused on backend tooling.
- Add `--group ee` to the `uv run` command when the scenario exercises EE-only dependencies.
