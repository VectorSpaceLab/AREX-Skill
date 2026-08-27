# Server Operations

Use this reference for self-hosted Prefect server startup, status checks, database commands, background services, scaling, logging, and maintenance. Prefer read-only commands until the user explicitly approves a long-running service or database mutation.

## Local Server Basics

A local self-hosted server can be started with:

```bash
prefect server start
```

This is a long-running process. Confirm the user wants a service started, clarify the terminal/background plan, and know how it will be stopped before running it. The default UI is typically `http://127.0.0.1:4200`; the corresponding API URL is typically `http://127.0.0.1:4200/api`.

Configure a profile to use that server:

```bash
prefect config set PREFECT_API_URL=http://127.0.0.1:4200/api
prefect server status --wait --timeout 30 --output json
```

`prefect server status` requires `PREFECT_API_URL`; it does not infer the local server URL when no API URL is configured.

## `prefect server start`

Live-help-verified options include:

| Option | Use |
| --- | --- |
| `--host` | Bind address, from `PREFECT_SERVER_API_HOST`. |
| `--port` | Server port, from `PREFECT_SERVER_API_PORT`. |
| `--keep-alive-timeout` | Keep-alive timeout seconds. |
| `--log-level` | Server logging level. |
| `--scheduler` / `--no-scheduler` | Toggle scheduler service. |
| `--analytics-on` / `--analytics-off` | Toggle server analytics. |
| `--late-runs` / `--no-late-runs` | Toggle late-run service. |
| `--ui` / `--no-ui` | Toggle serving the UI. |
| `--no-services` | Run only API and UI, not background services. |
| `--background` / `-b` | Run in the background and write a PID file. |
| `--workers N` | Run multiple API worker processes. |

If `--workers` is greater than one, Prefect runs API workers without in-process services. Multi-worker mode requires PostgreSQL and Redis-backed messaging, event ordering, and concurrency lease storage; SQLite and in-memory backends are not suitable.

## Status And Readiness

Use status before running API-dependent commands:

```bash
prefect server status --output json
prefect server status --wait --timeout 30 --output json
python scripts/prefect_cli_doctor.py --check-server --server-timeout 30
```

For load balancers or external health checks, the server health endpoint is `/api/health` and should return HTTP 200 with a healthy payload. Keep UI URL and API URL separate: the API URL usually appends `/api` to the server base URL.

## Background Server Stop

If a server was started with `--background`, stop it with:

```bash
prefect server stop
```

If no background PID file exists, Prefect reports that no background server is running. If the port is in use but no background PID exists, choose another `--port` or identify the owning process outside Prefect.

## Database Commands

Command map:

| Command | Risk | Notes |
| --- | --- | --- |
| `prefect server database upgrade --dry-run` | Lower | Shows migrations without applying them. Still confirm target DB. |
| `prefect server database upgrade -y` | Mutating | Applies Alembic migrations. Use backups and maintenance windows for production. |
| `prefect server database downgrade -y -r REV` | Mutating/high risk | Reverts schema. Requires explicit rollback plan. |
| `prefect server database reset -y` | Destructive | Drops and recreates all Prefect tables. Never run against production without explicit approval. |
| `prefect server database stamp REV` | Mutating/high risk | Changes migration bookkeeping without running migrations. Maintainer-only. |
| `prefect server database revision` | Writes migration files | Repo-maintainer workflow, not routine operations. |

For large databases, increase the database timeout before migrations when needed:

```bash
export PREFECT_API_DATABASE_TIMEOUT=600
prefect server database upgrade -y
```

Production self-hosting should use PostgreSQL 14.9 or newer. PostgreSQL deployments require the `pg_trgm` extension. Disable automatic migrations in multi-server deployments with `PREFECT_API_DATABASE_MIGRATE_ON_START=false` and run migrations as a separate controlled step.

## Server Services

Command map:

| Command | Use |
| --- | --- |
| `prefect server services ls` / `list` | Read-only list of available services, enabled status, and controlling environment variables. |
| `prefect server services start` / `enable` | Starts enabled background loop services in one process. Long-running unless `--background` is used. |
| `prefect server services stop` / `disable` | Stops background services previously started by Prefect. |

For scaled deployments, run API servers separately with `prefect server start --no-services`, and run background services with `prefect server services start`. Configure shared PostgreSQL, Redis messaging/cache, event ordering, concurrency lease storage, and `PREFECT_SERVER_DOCKET_URL` so multiple service replicas coordinate correctly.

## Database Maintenance

Prefect stores flow runs, task runs, state history, logs, deployments, variables, artifacts, work pool status, events, and automations. Common growth points are `events`, logs, flow runs, task runs, and state tables.

Operational settings worth checking:

```bash
prefect config view --show-sources | grep -E 'DATABASE|DB_VACUUM|EVENTS_RETENTION|DOCKET|MESSAGING|REDIS'
prefect server services ls
```

The database vacuum service can remove old events by default and can be configured to remove old terminal flow runs plus orphaned logs/artifacts. Enabling flow-run cleanup permanently deletes data; test in a non-production environment and back up first.

## Logging Operations

The default logging level is `INFO`. Use profile or environment settings for operational changes:

```bash
prefect config set PREFECT_LOGGING_LEVEL=DEBUG
prefect config set PREFECT_LOGGING_LOGGERS_PREFECT_FLOW_RUNS_LEVEL=ERROR
```

Custom logging can be supplied by a `logging.yml` file under `PREFECT_HOME` or by setting `PREFECT_LOGGING_SETTINGS_PATH`. Logging settings load at runtime, so remote workers or server processes need the setting in their own environment or profile.

## Self-Hosted Scaling Pattern

A scaled self-hosted deployment normally has:

- Multiple API/UI server instances behind a load balancer.
- Background service processes for scheduler, automations, event persistence, late runs, and cleanup.
- PostgreSQL for persistent state.
- Redis for messaging, event ordering, concurrency lease storage, and Docket coordination.
- Health checks against `/api/health`.

Start simple: one API server plus one service process, then scale only after measuring API latency, database connections, Redis memory, and background-service lag.
