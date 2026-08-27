# Observal repository overview

## Product model

Observal is a control plane and system of record for AI-agent components. It packages MCP servers, skills, hooks, prompts, and sandboxes into versioned Agents, resolves those packages for multiple coding-agent harnesses, and records session telemetry for debugging, review, audits, insights, and recommendations.

Primary user surfaces:

| Surface | Main role |
| --- | --- |
| CLI `observal` | Local auth/config, scan/doctor, component registry, agent authoring/pull, teams, ops/admin, server lifecycle, reconciliation, support bundles |
| FastAPI server | REST/GraphQL registry API, auth/JWT/device flow/SSO/SCIM, review/admin, ingest, telemetry storage, insights, jobs, settings |
| Web UI | Registry browsing, agent builder, component details, traces, admin dashboards, settings, insight reports, teamspaces, account flows |
| Bundled Observal skills | Agent-facing command guidance installed by the CLI so LLMs can drive Observal safely |
| Harness adapters | Per-harness scan/install/config/hook/session handling for supported coding agents |

## Repository shape

| Area | What it owns | Route to |
| --- | --- | --- |
| `observal_cli/` | Typer CLI, command modules, config, client/error contracts, harness scanning, local session push hooks, bundled skills, server lifecycle helpers | `cli` or `harness-telemetry` |
| `observal-server/` | FastAPI app, route registration, models, schemas, services, jobs, migrations, GraphQL, health/metrics, dynamic settings | `server` |
| `web/` | Vite 6 SPA, React 19, TanStack Router, query hooks, shared UI, theme tokens, Playwright config | `web` |
| `packages/observal-shared/` | Shared harness registry/model catalogs, namespace rules, MCP analysis, migration helpers, secrets helpers | `harness-telemetry` or `server` |
| `packages/pi-extension/` | Pi telemetry extension package and tests | `harness-telemetry` |
| `docs/` | CLI, harness, self-hosting, reference, testing, and use-case documentation | owning sub-skill plus `repo-development` |
| `tests/` | Primary pytest suite and Playwright specs; root pytest mocks externals by default | owning sub-skill plus `repo-development` |
| `observal_cli/skills/` | Bundled CLI skills installed/synced by the CLI | `cli` |
| `scripts/`, `tools/`, `Makefile` | Maintenance, compliance, skill sync, migration, release, and developer commands | `repo-development` |

## Data and telemetry architecture

- PostgreSQL stores relational registry/auth/team/component/agent/settings data through SQLAlchemy async models and Alembic migrations.
- ClickHouse stores session events, aggregates, audit/security events, and webhook deliveries through SQL migrations and `services/clickhouse/*` helpers.
- Redis supports auth revocation, pub/sub, arq jobs, and dynamic settings cache; auth fails closed if Redis is down.
- Session telemetry flows from harness hooks to local session push, to `POST /api/v1/ingest/session`, then into ClickHouse. `observal reconcile` backfills missed local sessions.

## Harness support model

Harness support is capability-based, not a single tier. The shared registry names capabilities such as `hooks`, `mcp_servers`, `skills`, and `prompts`, along with config paths, skill paths, event maps, parser ids, scopes, and model catalogs. CLI adapters scan and patch local harnesses; server adapters generate install files; session parser modules normalize raw traces.

Only Kiro has broad harness-specific Playwright coverage in this snapshot. Cursor and Pi have no dedicated hook-spec files; Pi uses a bundled extension path.

## Development mental model

1. Identify the owning surface before editing.
2. Preserve adapter/factory patterns instead of adding broad conditionals.
3. Keep public command/API/UI behavior synchronized with docs, tests, and bundled skills.
4. Prefer focused hermetic tests before broad `make test`; use Docker/E2E only when the changed behavior needs a live stack or browser.
5. Record skipped heavy checks and why.
