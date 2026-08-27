# Development Commands

Use this reference to choose the smallest safe command for Transformer Lab repository work. Prefer focused checks over whole stacks unless the change actually crosses that boundary.

## Environment Prerequisites

| Surface | Requirement | Notes |
| --- | --- | --- |
| Frontend | Node v22 | Avoid Node v23+ unless maintainers update support. `npm install` supplies webpack, dotenv, concurrently, Playwright packages, and frontend tooling. |
| Backend/API | Python managed by Transformer Lab install | Normal developer flow uses the API environment prepared by `cd api && ./install.sh`. The backend code runs from `api/`, not as `transformerlab.api`. |
| CLI | Python package under `cli/` | The console entry point is `lab`, built with Typer. |
| SDK | Python package under `lab-sdk/` | Distribution name is `transformerlab`, import root is `lab`, and entry point includes `tfl-remote-trap`. |

## Setup and Run

```bash
# frontend dependencies
npm install

# backend/API dependencies; mutates the Transformer Lab API env
cd api && ./install.sh

# start API only
cd api && ./run.sh

# start frontend only
npm start

# run frontend and API side by side, after API deps are installed
python scripts/dev.py
```

`python scripts/dev.py` checks ports `8338` (API) and `1212` (frontend) before launching. It is long-running and prompts before killing port blockers, so do not run it in unattended automation unless the user expects an app session.

## Lint and Format

```bash
# frontend formatting
npm run format
npm run format:check

# Python lint from the API environment
cd api && ruff check
cd api && ruff format <changed-python-files>
```

Always run `npm run format` on changed frontend files before commit. For backend Python, run Ruff check and format the changed files. Keep Python type hints on function arguments and return values.

## Tests

```bash
# backend all tests
cd api && pytest

# backend focused test
cd api && pytest test/<file>::<test>

# CLI full suite after cli/src changes
cd cli && python -m pytest tests/ -v

# CLI focused example
cd cli && python -m pytest tests/commands/test_status.py -v

# SDK tests
cd lab-sdk && python -m pytest tests/ -v
```

Frontend has no unit test framework. E2E tests live under the Playwright suite and require a running app. Do not write or run Playwright tests for routine visual checks unless the user asks for E2E work or the change touches the E2E suite.

```bash
# self-contained E2E stack; starts and tears down docker test app
npm run docker-test:playwright

# manual cycle when debugging E2E
npm run docker-test:up
npx playwright test <spec-or-filter>
npm run docker-test:down
```

Default dev/test login is `admin@example.com` / `admin123` after the test app seeds its initial user.

## API Curl Authentication

Most protected API endpoints require auth plus team context.

```bash
TOKEN=$(curl -s -X POST http://localhost:8338/auth/jwt/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123" | jq -r .access_token)

curl -H "Authorization: Bearer $TOKEN" http://localhost:8338/users/me/teams

curl -H "Authorization: Bearer $TOKEN" \
  -H "X-Team-Id: <team-id>" \
  http://localhost:8338/server/announcements
```

Use API keys for CLI flows; use JWT cookies/Bearer tokens for app/API debugging. Protected endpoints may reject requests without `X-Team-Id` or an equivalent team cookie.

## Change-Type Command Matrix

| Change type | Minimum likely checks |
| --- | --- |
| Pure frontend component/style | `npm run format` and browser visual verification of changed screen; optionally `npm run format:check`. |
| Frontend data fetching/API client | Frontend format plus a curl/API check or browser verification through authenticated app state. |
| Backend service/router/schema | Focused `cd api && pytest ...`; Ruff check/format; curl check if endpoint behavior changes. |
| Auth/team/permission logic | Service/API tests covering owner/member/no-header cases; curl with and without `X-Team-Id`. |
| DB model/migration | Alembic migration review/upgrade in safe env; no foreign keys; tests on SQLite-compatible behavior. |
| Task/job/provider dispatch | Focused provider/task/job tests; inspect task/job lifecycle reference; avoid real cloud launches unless requested. |
| CLI command | Focused CLI command tests with `CliRunner`; full CLI suite after `cli/src/` changes. |
| SDK helper/resource | SDK tests; reinstall SDK into the backend runtime when API imports SDK changes. |
| App-wide visual behavior | Run app stack, use browser visual verification, and only run Playwright when E2E is requested or touched. |

## Safe Readiness Helper

The bundled script is read-only and can be run from any directory:

```bash
python <this-skill>/scripts/check_transformerlab_dev_readiness.py --repo-root <checkout>
python <this-skill>/scripts/check_transformerlab_dev_readiness.py --repo-root <checkout> --check-url http://localhost:8338/server/health
```

It reports expected files, package versions, Node/Python/tool versions, port occupancy, and optional HTTP reachability. It does not install packages, start services, kill processes, log in, run tests, or call cloud providers.
