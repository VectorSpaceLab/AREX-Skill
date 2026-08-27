# Testing and quality gates

This reference distills repository-wide testing, linting, formatting, SPDX, pre-commit, and Docker/E2E selection guidance. Use it to choose the smallest effective checks for a change and to explain why broader checks were or were not necessary.

## Default quality rule

Start narrow, then broaden:

1. Run the focused unit or integration-style test that exercises the changed behavior.
2. Run layer-specific static/build checks when the changed layer has them.
3. Run `make lint` and `make test` before PR-ready handoff for most Python/backend/CLI changes.
4. Run `make check` when the diff is ready for review, when hooks/policies/build files changed, or when SPDX/secrets/migration gates are relevant.
5. Use Docker and Playwright only for local stack validation, UI flow/screenshot work, or live integration scripts; do not use them as a substitute for focused hermetic tests.

## Test layout and what Make covers

| Test location | Purpose | Normal command pattern |
| --- | --- | --- |
| `tests/` | Main root test suite covering server, CLI, harness, telemetry, migrations, routes, security, and cross-cutting behavior | `make test`, `make test-v`, or focused `cd observal-server && uv run pytest ../tests/test_name.py -q`. |
| `observal-server/tests/` | Server-package-local tests not covered by the default Make test target | Run directly from `observal-server` when touching those behaviors. |
| `observal_cli/tests/` | CLI-package-local tests not covered by the default Make test target | Run directly when touching CLI command/package behavior. |
| `tests/e2e/` | Playwright browser and live-stack specs | Run through the web package or root pnpm script only when UI/live flows need it. |
| `fuzz/` plus `tests/test_fuzz_targets.py` | Fuzz target smoke tests and seed corpus checks | `make test-fuzz`. |

Important: the default `make test` target runs root `tests/` from inside `observal-server` with pytest-xdist. Package-local tests in `observal-server/tests/` and `observal_cli/tests/` require explicit direct invocation when they are relevant.

## Core commands

### Python tests

```bash
make test
make test-v
make test-adversarial
make test-eval-completeness
make test-fuzz
make test-all
```

Expected signals:

- Exit code 0.
- Pytest reports all selected tests passed.
- For CLI tests, failing exit-code assertions should include `result.output` for diagnostics.
- For fuzz smoke tests, seed corpora are exercised without crashes.

Focused examples:

```bash
cd observal-server
uv run --with pytest --with pytest-asyncio --with pyyaml --with typer --with rich pytest ../tests/test_cmd_auth.py -q
uv run --with pytest --with pytest-asyncio --with pyyaml --with typer --with rich pytest ../observal_cli/tests/test_cmd_scan.py -q
uv run --with pytest --with pytest-asyncio pytest tests/test_jwt.py -q
```

Add extra `--with` packages when the selected test imports them, such as `hypothesis`, `pyarrow`, or `loguru`. For the full root suite, the Make target already includes the common extras used by the current test set.

### Lint and format

```bash
make lint
make format
```

Expected signals:

- `make lint` runs Ruff check and exits 0.
- `make format` runs Ruff format and Ruff auto-fix; inspect the diff afterward.

Ruff configuration highlights:

- Python target version: 3.11.
- Line length: 120.
- Import boundaries recognize first-party packages `observal_cli`, `observal_shared`, `models`, `schemas`, `services`, and `api`.
- Typer-compatible rule relaxations include allowing function calls in argument defaults.
- Test directories have practical per-file ignores for unused mock variables and some import-setup patterns, but new tests should still be clean and focused.

### Full pre-commit

```bash
make check
```

Expected signals:

- All pre-commit hooks pass over all files.
- Hooks include Ruff, formatting, trailing whitespace, EOF, YAML/TOML/JSON syntax, large-file guard, merge-conflict guard, private-key detection, branch guard, secret scanning, Alembic migration chain validation, SPDX copyright update, and Dockerfile linting.

Use `make check` before PR-ready handoff when a change touches policies, headers, migrations, Dockerfiles, generated files, release/compliance scripts, or broad build configuration.

## Test selection by change type

| Change | Focused tests | Broader checks |
| --- | --- | --- |
| CLI command syntax, flags, or command tree | `observal_cli/tests/test_cmd_*.py`, root `tests/test_cmd_*.py`, command `--help`, generated skill sync test | `make sync-skill`, `make test`, `make lint`, `make check` if generated files changed. |
| CLI config/auth/session/status behavior | Focused CLI tests with sandboxed HOME/USERPROFILE and temp cwd | `make test`; avoid real home-directory writes. |
| Server route behavior | Small FastAPI route tests with dependency overrides; root route tests or server-local route tests | `make test`, migration checks if schema changes. |
| Database migrations | Migration unit/integration tests plus `python3 scripts/check_migrations.py` or `make check-migrations` | Local stack apply only when manual migration validation is needed. |
| ClickHouse storage/query logic | Focused ClickHouse service/migration tests using mocked boundaries where possible | Live ClickHouse only for manual operational validation. |
| Web components/API hooks | `cd web && pnpm build`; focused component or route checks available in the web layer | Playwright only for affected browser flows/screenshots. |
| Harness adapter/parser/session delivery | Harness adapter/parser/session-delivery tests in root suite | Helper checks and route to `harness-telemetry` for exact coverage. |
| Release/compliance scripts | Script preview/read-only mode, generated diff inspection, policy-specific test if present | `make check`, license/SBOM/VEX checks as applicable. |
| Security fix | Regression test that would fail without the fix | Qualified review and private disclosure handling if vulnerability is not public. |

## Hermetic Python test conventions

New and touched Python tests should move toward these patterns:

- One behavior area per file when practical.
- Plain behavior-focused names such as `test_missing_auth_returns_401` or `test_scan_does_not_modify_ide_files`.
- Arrange, act, assert phases separated by blank lines.
- Assert public result before internal calls.
- Mock boundaries, not the behavior under test: HTTP clients, database session methods, subprocesses, sleeps, auth providers, and external CLIs are good boundaries.
- Use `AsyncMock` for awaited methods and `MagicMock` for sync methods.
- Use local helper factories for setup; use fixtures only when pytest lifecycle or reuse justifies them.
- API route tests should use a small FastAPI app with dependency overrides rather than booting the full app unless the integration boundary itself is under test.
- CLI tests must redirect `HOME`, `USERPROFILE`, and cwd to a temp path and must not touch real user configuration.
- Property-based tests are appropriate for pure logic, serializers, redaction, parsers, and validation invariants; add named regressions for found bugs.
- Fuzz targets are appropriate for untrusted byte inputs where crashes matter more than named invariants.

## Docker and E2E restraint

Use Docker when you need:

- Full local stack startup or manual end-to-end validation.
- API health through the load balancer.
- Browser tests that expect running services in CI mode.
- Live integration scripts that explicitly target the running stack.
- Manual database migration apply or service log inspection.

Avoid Docker when:

- A unit test can mock the database, network, filesystem, or external CLI boundary.
- You are only checking Python syntax, imports, CLI command parsing, or pure service logic.
- You need a fast regression test for PR evidence.

For Playwright:

```bash
cd web
pnpm build
pnpm e2e -- --grep "focused term"
```

Expected signals:

- `pnpm build` passes TypeScript and Vite production build.
- Playwright runs only the affected specs where possible; traces/screenshots are retained on failure.
- Frontend changes still require screenshots of affected screens in the PR body, even if the change is AI-assisted or small.

## SPDX, license, and provenance gates

Every new source file should include SPDX copyright and license headers. Common comment forms:

```python
# SPDX-FileCopyrightText: 2026 Your Name <your@email.example>
# SPDX-License-Identifier: Apache-2.0
```

```typescript
// SPDX-FileCopyrightText: 2026 Your Name <your@email.example>
// SPDX-License-Identifier: Apache-2.0
```

```markdown
<!-- SPDX-FileCopyrightText: 2026 Your Name <your@email.example> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
```

Quality rules:

- Let the pre-commit SPDX hook add the current committer copyright line to staged files that already have headers.
- Use bulk SPDX/header scripts only for deliberate license repair and inspect the diff carefully.
- Do not stage `.env` files, secrets, keys, tokens, credentials, or private local harness/editor configuration.
- Copied or adapted material must be Apache-2.0-compatible or otherwise approved, attributed, and documented.
- New external libraries or assets require license review and PR disclosure.

## Logging and diagnostics quality

Python logging uses Loguru for normal dev logging:

```python
from loguru import logger as optic

optic.debug("user count={}", count)
```

Rules:

- Prefer positional placeholders over f-strings in log messages.
- Do not pass `exc_info=` to Loguru; use `optic.exception(...)` or `optic.opt(exception=True).error(...)`.
- Avoid structlog-style keyword args in new Loguru calls because normal sinks render only the message.
- Never log secrets, tokens, JWT payloads, API keys, bearer tokens, or sensitive telemetry contents.

## Expected final quality evidence

A strong handoff for a repo-development-owned review says:

- Which focused tests were run and why they match the changed behavior.
- Whether default `make test` covers the relevant tests or whether package-local tests were run directly.
- Whether `make lint`, `make format`, or `make check` were run.
- Whether Docker/E2E was intentionally skipped and why.
- Which docs, bundled skills, changelog entries, screenshots, SPDX/license evidence, or release artifacts changed.
- What remains unverified and which reviewer/domain should cover it.
