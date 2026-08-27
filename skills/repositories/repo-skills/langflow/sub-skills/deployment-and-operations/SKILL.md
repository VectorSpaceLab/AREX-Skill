---
name: deployment-and-operations
description: "Install, run, configure, deploy, and troubleshoot Langflow in
  local, Docker, Compose, and operational environments."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Deployment and Operations

Use this sub-skill when the task is to install Langflow, start or configure the server, prepare `.env` files, run Docker or Docker Compose deployments, preserve data while upgrading, package flows or custom code into images, or diagnose operational failures around databases, volumes, credentials, networking, logging, storage, and runtime dependencies.

Route elsewhere when the task is primarily:

- Editing Langflow source, tests, formatting, generated files, or release policy: use `../repo-maintenance/`.
- Implementing REST, SDK, or application client code against a running server: use `../sdk-and-api-clients/`.
- Backend route/service internals or database migration implementation: use `../backend-runtime/`.
- `lfx run` or `lfx serve` stateless executor workflows: use `../executor-cli/`.

## Start Here

1. Read [references/install-and-run.md](references/install-and-run.md) for local package installs, source runs, CLI commands, `.env` loading, precedence, superuser/API-key operations, and safe upgrade checks.
2. Read [references/deployment.md](references/deployment.md) for Docker, Compose, PostgreSQL, volumes, custom flow images, custom Langflow images, multi-worker/Redis, reverse proxy, and observability patterns.
3. Read [references/troubleshooting.md](references/troubleshooting.md) when startup, imports, optional dependencies, database URLs, migrations, credentials, Docker networking, storage, logs, or worker queues fail.
4. Validate `.env` files before deployment with the bundled helper:

```bash
python scripts/check_env_vars.py --env-file .env --context docker-compose
```

## Fast Operational Checklist

- Prefer `uv run langflow run` from an environment where `langflow` is installed; use direct `langflow run` only when the executable is intentionally on `PATH`.
- Remember precedence: CLI options override `.env`; `.env` overrides system environment; Docker `-e` and Compose `environment` entries are system environment inside the container unless an `--env-file` or service `env_file` supplies values.
- For local production-like persistence, set `LANGFLOW_CONFIG_DIR` and back it up with the database; for Compose, mount the config directory and PostgreSQL data on persistent volumes.
- For PostgreSQL, use a full `LANGFLOW_DATABASE_URL` such as `postgresql://user:password@postgres:5432/langflow` from inside Compose, not `localhost` unless the database is in the same container namespace.
- For public or shared deployments, disable automatic login, set a non-default secret key, create a superuser, protect API keys, and put Langflow behind HTTPS/reverse-proxy authentication appropriate to the environment.
- For multi-worker deployments, configure all workers consistently and use `LANGFLOW_JOB_QUEUE_TYPE=redis` plus a shared Redis queue URL; mixed `asyncio`/Redis workers are not supported.

## Useful Commands

```bash
uv pip install -U langflow
uv run langflow run --host 127.0.0.1 --port 7860
uv run langflow run --env-file .env --backend-only --log-level info
uv run langflow superuser --username admin --password 'change-me'
uv run langflow api-key
uv run langflow migration
docker run --rm -p 7860:7860 langflowai/langflow:latest
docker compose up -d
docker compose logs -f langflow
```

Run `langflow migration` before `langflow migration --fix`, and only run fix mode after backing up the database or confirming the environment is disposable.

## Evidence Base

This guidance is distilled from Langflow's README quickstart, development setup guidance, CLI configuration docs, environment-variable docs, Docker deployment docs, deployment overview, Compose examples, setup scripts, and verified installed package facts for `langflow`, `langflow-base`, `lfx`, and `langflow-sdk`. Runtime instructions here are self-contained and do not require reopening those source files.
