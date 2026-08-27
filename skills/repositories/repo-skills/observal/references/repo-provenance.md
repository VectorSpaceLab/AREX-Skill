# Repo provenance

```yaml
schema: disco.repo-provenance.v1
repo_name: Observal
repo_url: https://github.com/Observal/Observal
source_commit: 576522b168ca2db2ca9504f79f7ded9c1065d01b
source_branch: main
source_tag: null
working_tree_state: dirty
package_versions:
  observal-cli: 1.12.1
  observal-server: 1.12.1
  web: 1.12.1
  observal-shared: 1.6.1
generated_skill_id: observal
generated_from_dirty_paths:
  - skills/
```

## Evidence paths used

- `AGENTS.md`, `README.md`, `SETUP.md`, `CONTRIBUTING.md`, `AI_POLICY.md`, `Makefile`, `pyproject.toml`, `package.json`
- `observal_cli/`, especially `main.py`, `cmd_*.py`, `client.py`, `errors.py`, `render.py`, `harness/`, `harness_specs/`, `hooks/`, `sessions/`, and `skills/`
- `observal-server/`, especially `app_factory.py`, `routes.py`, `api/routes/`, `models/`, `schemas/`, `services/`, `jobs/`, `alembic/versions/`, and `clickhouse/migrations/`
- `packages/observal-shared/observal_shared/harness_registry.py`, harness model catalogs, namespace rules, migration helpers, and MCP analysis helpers
- `packages/pi-extension/`
- `web/AGENTS.md`, `web/package.json`, `web/src/routes/`, `web/src/pages/`, `web/src/components/`, `web/src/hooks/`, `web/src/lib/`, `web/src/app.css`, and `web/playwright.config.ts`
- `docs/adding-a-cli-command.md`, `docs/adding-a-harness.md`, `docs/DEVELOPMENT_GUIDE.md`, `docs/cli/`, `docs/reference/`, `docs/self-hosting/`, `docs/testing/`, and selected use-case docs
- `tests/`, `observal_cli/tests/`, `observal-server/tests/`, and `tests/e2e/`
- `scripts/`, `tools/release.py`, `.pre-commit-config.yaml`, `.release.toml`, `REUSE.toml`

## Refresh guidance

Refresh this skill when any of these change materially:

- CLI command hierarchy, flags, output/error behavior, bundled skill sync, or command reference generation.
- Server route organization, auth model, telemetry ingest, ClickHouse/Postgres migration rules, dynamic settings, jobs, insights, or route test layout.
- Shared harness registry, supported harness list, capability gates, hook specs, session parser registration, or telemetry delivery model.
- Frontend framework, route map, query-hook pattern, auth storage model, harness data source, type barrel, design tokens, or Playwright flow.
- Repository-wide policy: Make targets, test layout, AI policy, SPDX/license/pre-commit, release/compliance scripts, or paths that must never be committed.
