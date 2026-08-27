# Testing and Quality Reference

## When to read

Read this when selecting validation commands for a ContextForge code change,
review, or release-readiness pass.

## Fast local setup and hygiene

Common setup:

```bash
cp .env.example .env
make install-dev check-env
```

Routine hygiene after edits:

```bash
make autoflake isort black pre-commit
make ruff bandit interrogate pylint verify
```

Use focused commands first while iterating, then broaden when the change is
ready or crosses component boundaries.

## Python tests

| Change | Minimum useful tests |
| --- | --- |
| service/router/schema logic | targeted `pytest tests/unit/mcpgateway/... -q` plus affected integration tests |
| auth/RBAC/token scoping | auth/RBAC unit tests, wrong-team/public-only/insufficient-permission denies, route-specific tests |
| migrations/models | Alembic head check, migration tests, model/service tests touching the schema |
| observability/audit/logging | service tests proving separate-session behavior, log redaction checks |
| plugins | plugin unit tests plus plugin manager tests; parity E2E only for public MCP hook path changes |
| UI/templates/static | JS unit tests, bundle rebuild, targeted Playwright smoke |

Useful commands:

```bash
make doctest
make test
make coverage
make diff-cover
pytest -k "fragment" tests/unit/ -q
pytest tests/unit/mcpgateway/path/test_file.py::TestClass::test_name -q
```

## Live gateway and MCP protocol tests

Use these only when the gateway stack is running or the task explicitly
requires protocol behavior:

```bash
make docker-nuke docker-prod-rust testing-up RUST_MCP_MODE=
make test-mcp-protocol-e2e
make test-mcp-rbac
make test-mcp-plugin-parity
make test-mcp-access-matrix
make test-mcp-session-isolation
```

If Docker/compose/Redis/PostgreSQL or the live gateway is unavailable, document
the skipped dependency instead of pretending the protocol check passed.

## UI and JavaScript

When touching Admin UI JS, templates, CSP-sensitive code, or static assets:

```bash
make build-ui
npx vitest run
make lint-web
make test-ui-smoke
```

Use page-object helpers for Playwright and avoid CSP-incompatible
`wait_for_function`; use the repository polling utilities instead.

## Security and secrets

Security-sensitive changes need deny-path regression tests. Also run:

```bash
make bandit
make detect-secrets-scan
```

False positives in Python may use inline allowlist comments. Other file types
usually require updating/auditing the baseline. Do not commit real secrets in
sample values.

## Pre-merge validation gate

For a full readiness claim, run or explicitly waive:

1. `make ruff interrogate pylint`
2. `make test`
3. `make coverage diff-cover`
4. `make docker-nuke docker-prod-rust testing-up RUST_MCP_MODE=`
5. `make test-mcp-protocol-e2e test-mcp-rbac`
6. `make detect-secrets-scan`

Do not call a PR ready when blocking or functionally-impacting findings remain.

## Fixed-point PR review loop

When asked to rebase and review:

1. Refresh review notes from the template.
2. Rebase against main; preserve semantic intent and use main's
   `.secrets.baseline` on baseline conflicts.
3. Review scope against PR description and linked issues.
4. Fix blocking and functionally-impacting findings.
5. Repeat until a full pass has zero blocking findings.
6. Run the pre-merge gate.

Keep public comments collaborative and categorize findings as blocking,
functionally-impacting, suggestions, or minor notes.
