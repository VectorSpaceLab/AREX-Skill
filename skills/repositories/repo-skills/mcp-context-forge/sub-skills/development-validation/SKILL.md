---
name: development-validation
description: "Maintain and validate ContextForge code changes across Python,
  auth, MCP transports, Rust runtime, plugins, migrations, docs, UI, Helm, and
  security gates."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Development and Validation

Use this sub-skill when the user is editing, reviewing, testing, packaging, or
validating a ContextForge checkout rather than only operating an installed
gateway.

## Route here for

- choosing Makefile targets, pytest subsets, coverage, lint, security, or
  pre-merge validation gates.
- adding or reviewing Alembic migrations.
- touching auth/RBAC-sensitive code and needing deny-path test coverage.
- editing Admin UI JS/templates/CSP behavior.
- changing plugin framework integration or plugin examples.
- working on Rust MCP runtime modes and live compose-backed validation.
- editing Helm charts, docs/ADRs, release metadata, or secret baselines.
- running a fixed-point PR review loop.

## Reroute

- End-user install/config/startup: [`../runtime-configuration/SKILL.md`](../runtime-configuration/SKILL.md).
- Detailed auth/token-scoping policy: [`../auth-rbac-security/SKILL.md`](../auth-rbac-security/SKILL.md).
- MCP transport runtime semantics: [`../mcp-transports-federation/SKILL.md`](../mcp-transports-federation/SKILL.md).
- Plugin configuration and observability behavior: [`../plugins-observability/SKILL.md`](../plugins-observability/SKILL.md).
- Registry API payload details: [`../registry-admin-api/SKILL.md`](../registry-admin-api/SKILL.md).

## Read first

- [`references/testing-and-quality.md`](references/testing-and-quality.md) for command selection and test layers.
- [`references/migrations-docs-charts-rust.md`](references/migrations-docs-charts-rust.md) for Alembic, docs, Helm, and Rust rules.
- [`references/troubleshooting.md`](references/troubleshooting.md) for common validation failures.
- [`scripts/contextforge_validation_plan.py`](scripts/contextforge_validation_plan.py) for a no-execute command planner.

## Fast validation planner

Use the bundled planner to choose commands without executing them:

```bash
python scripts/contextforge_validation_plan.py --areas auth transport rust
python scripts/contextforge_validation_plan.py --areas migration docs ui --format markdown
```

Then run the selected commands from the target checkout, not from the generated
skill directory.

## General edit checklist

1. Identify the affected surface: Python service/router, auth/RBAC, transport,
   Rust, plugin, UI, docs, Helm, migration, or packaging.
2. Read the nearest subarea guidance before editing.
3. Prefer focused tests during iteration; broaden only when the change crosses
   boundaries or before readiness.
4. For security-sensitive changes, add deny-path tests before relying on happy
   paths.
5. For migrations, check the current Alembic head before writing `down_revision`.
6. For UI/static changes, rebuild the Admin UI bundle and run JS/Playwright
   checks matching the affected page.
7. For Rust public MCP path changes, validate mode headers and live gateway MCP
   E2E in the intended runtime mode.
8. Never push or commit unless the user explicitly asks.

## Repo-wide quality gate

Use broad gates only when the task calls for readiness or the change spans
multiple areas:

```bash
make autoflake isort black pre-commit
make ruff bandit interrogate pylint verify
make doctest test htmlcov
```

For pre-merge review readiness, add coverage/diff-cover, compose-backed gateway
startup, MCP protocol/RBAC E2E, and secret scanning as described in the
validation reference.

## Maintainer invariants

- Synchronous SQLAlchemy usage inside async handlers is intentional here; do not
  refactor one call site to async without a broader migration plan.
- Audit trail and observability writes use separate-session patterns; do not
  pass request-scoped DB sessions back into existing audit call sites.
- Accepted ADRs are historical records. Supersede them with new ADRs instead of
  rewriting the original decision body.
- `.secrets.baseline` conflict resolution should preserve the main-branch
  baseline unless there is a deliberate audited change.
- Keep generated/review artifacts outside runtime skill directories and outside
  production code unless explicitly requested.

## Output style

When answering maintainer tasks, name the smallest adequate validation set, then
state what additional gates are needed before merge. If a command needs Docker,
Redis, PostgreSQL, Keycloak, Helm, Kubernetes, browsers, or Rust toolchains,
call that dependency out before recommending it.
