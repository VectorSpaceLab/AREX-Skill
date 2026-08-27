# Self-hosted Mem0 Server Deployment

Use this reference for the `server/` deployment model: a FastAPI REST API plus dashboard, Postgres/pgvector, auth, request logs, API keys, and operational Makefile workflows.

## What the Server Stack Provides

- REST API for memory operations and admin endpoints.
- Dashboard for setup, login, API keys, request audit logs, memories, entities, runtime configuration, and account settings.
- Auth enabled by default with dashboard login and programmatic `X-API-Key` access.
- Docker Compose reference stack with API on port `8888` and dashboard on port `3000`.
- Postgres/pgvector storage and migrations managed on startup.

## First-time Setup

1. Ensure Docker and Docker Compose are available.
2. Copy the server env template and set required secrets:

```bash
cd server
cp .env.example .env
# Edit .env; set POSTGRES_PASSWORD, OPENAI_API_KEY or another configured provider key, and JWT_SECRET.
```

3. Choose one setup path:

```bash
cd server
make bootstrap
```

Use `make bootstrap` for agent-first setup. It starts containers, creates the first admin, and prints the first API key once.

```bash
cd server
make up
```

Use `make up` for browser-first setup. Open the dashboard on port `3000`, complete the setup wizard, and copy the API key immediately.

## Important Environment Variables

| Variable | Purpose | Notes |
| --- | --- | --- |
| `OPENAI_API_KEY` | Default LLM/embedder credential | Required for default memory extraction unless another provider is configured. |
| `JWT_SECRET` | Signs dashboard access/refresh tokens | Required when auth is enabled; generate a long random value. |
| `POSTGRES_PASSWORD` | Postgres password | Required by current Compose setup. |
| `ADMIN_API_KEY` | Legacy shared admin key | Fast compatibility path after old auth-less deployments; prefer per-user keys for new setups. |
| `AUTH_DISABLED` | Local auth bypass | Use only for local development; never production. |
| `DASHBOARD_URL` | CORS origin | Set when dashboard is served from a custom origin. |

Run the bundled validator before proposing a deployment:

```bash
python scripts/check_self_host_env.py --target server --env-file path/to/server.env
```

The script reports missing keys and redacts secret values.

## Auth and API Keys

- Dashboard users authenticate with JWT sessions.
- Programmatic clients use per-user API keys and send `X-API-Key` to the self-hosted API.
- Legacy clients can use `ADMIN_API_KEY` if the deployment intentionally preserves that mode.
- If every protected endpoint returns `401` after an upgrade, check whether auth was enabled and no admin/key path was configured.

## Operational Commands

Use these only in a confirmed self-hosted checkout or deployment runbook:

```bash
cd server && make bootstrap
cd server && make up
cd server && make down
cd server && make reset-admin-password EMAIL=admin@example.com PASSWORD='new-strong-password'
cd server && make prune-logs REQUEST_LOG_RETENTION_DAYS=30
```

Safety notes:

- `reset-admin-password` mutates admin credentials.
- `prune-logs` deletes request log rows older than the retention window.
- Volume resets such as `docker compose down -v` destroy stored memories/users unless a verified backup exists.
- API keys print once; the server stores only prefixes/hashes.

## Migrations and Upgrades

- Current server migrations create users, API keys, request logs, settings, and auth-related indexes.
- Fresh installs can start normally after setting required env vars.
- Upgrades from older pgvector images may require export/import because PostgreSQL major versions cannot share data directories directly.
- Do not start the API against a restored database until the documented migration sequence is clear; otherwise migrations can create empty conflicting tables.

## Request Log Retention

At moderate traffic, request logs can grow quickly. Use the pruning command or schedule it through the host’s cron/systemd. The request log timestamp index is designed for range deletes, but deleting rows still mutates production data and should be scoped deliberately.

## Validation Checklist

- Required env vars set and secrets not empty.
- Ports `3000` and `8888` available or remapped.
- Dashboard origin matches `DASHBOARD_URL` if customized.
- Provider credentials correspond to the configured LLM/embedder.
- Postgres volume state matches the intended fresh/upgrade/restore path.
- Auth mode is explicit: dashboard/API keys, legacy admin key, or local-only disabled auth.
