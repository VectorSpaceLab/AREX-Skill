# Migrations, Docs, Helm, and Rust Runtime

## Alembic migrations

Before adding a migration:

```bash
cd mcpgateway
alembic heads
```

Rules:

- `down_revision` must point to the current head. Never guess from an older
  migration.
- Keep migrations idempotent: inspect tables/columns before adding or dropping.
- Fresh databases may be built from models directly; skip schema mutation when
  the target table is absent.
- After writing a migration, verify there is still exactly one head.
- Add migration tests when behavior or downgrade logic is non-trivial.

Hermetic downgrade rule:

- If `downgrade()` depends on runtime settings, snapshot those values into
  `migration_metadata` during `upgrade()` and read the snapshot during
  `downgrade()`.
- Do not let current environment variables change historical downgrade
  behavior.

## Docs and ADRs

Docs are MkDocs-based. Use the docs subarea for architecture, deployment,
development, manage, using, testing, best practices, tutorials, overview, FAQ,
and coverage content.

Commands:

```bash
cd docs
make build
make serve
```

ADR rules:

- Accepted/Implemented ADRs are historical records. Do not rewrite their body
  to reflect new behavior.
- To reverse or replace a decision, write a new ADR, mark the old one
  superseded, and update the ADR index/navigation.
- Add new pages to MkDocs navigation.

## Admin UI assets

Admin UI uses bundled static assets, HTMX/Alpine patterns, templates, and JS
unit tests. When touching UI or CSP-sensitive behavior:

```bash
make build-ui
npx vitest run
make lint-web
make test-ui-smoke
```

Do not leave the built bundle stale after changing source JS/CSS/templates.

## Helm chart work

Chart work is under the Helm chart directory. Useful chart commands:

```bash
make -C charts/mcp-stack lint
make -C charts/mcp-stack lint-values
make -C charts/mcp-stack validate-all
make -C charts/mcp-stack test-template
make -C charts/mcp-stack test-dry-run
```

Helm/Kubernetes installs require cluster context and should not be run without
explicit deployment target confirmation.

## Rust MCP runtime work

For pure Rust changes:

```bash
make -C crates/mcp_runtime fmt-check
make -C crates/mcp_runtime clippy-all
make -C crates/mcp_runtime test
make -C crates/mcp_runtime test-rmcp
```

For Rust + Python MCP integration changes, add Python/backend checks and live
MCP validation. Verify what is actually mounted:

```bash
curl -sD - http://localhost:8080/health -o /dev/null | rg 'x-contextforge-mcp-'
```

Expected mode/header combinations:

- Python baseline: runtime `python`, transport `python`.
- Rust shadow: runtime `rust-managed`, public transport `python`.
- Rust edge/full: runtime `rust-managed`, public transport `rust`.

Use the MCP transport sub-skill for deeper runtime semantics.

## Secret baseline conflicts

When conflict resolution touches `.secrets.baseline`, prefer the main-branch
baseline unless the change deliberately adds audited false positives. For Python
false positives, inline allowlist comments are often preferred; for other file
types, regenerate/audit the baseline.

## Transaction invariants

- Existing audit call sites should not pass a request-scoped session into audit
  logging just to share a transaction.
- Observability write methods open independent sessions and commit best-effort.
- Synchronous SQLAlchemy sessions inside async handlers are an intentional
  project design choice; do not flag or locally convert them without a broader
  migration plan.
