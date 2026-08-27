---
name: server-ops
description: "Operate and deploy Argilla server 2.8.0dev0 with safe CLI,
  configuration, Docker, Spaces, Kubernetes, OAuth, telemetry, reindexing, and
  troubleshooting guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Argilla server operations

Use this sub-skill when the user needs to deploy, configure, start, migrate, reindex, secure, or debug the Argilla server stack. It covers Argilla 2.8.0dev0 server behavior, not dataset authoring with the Python SDK or legacy v1/Rubrix migration.

## Route to this sub-skill for

- Choosing between Hugging Face Spaces, `rg.Argilla.deploy_on_spaces`, local Docker Compose, direct Python server package use, and Kubernetes/Helm-style deployments.
- Writing or reviewing server environment variables for database, search engine, Redis, base URL/proxy, CORS/docs, OAuth/SSO, auth secret, dataset limits, telemetry, and Docker startup defaults.
- Using the `python -m argilla_server` CLI for `start`, `database`, `database users`, `search-engine reindex`, and `worker` operations.
- Debugging server startup, private Space access, persistent storage, OAuth redirect, Elasticsearch/OpenSearch, PostgreSQL/SQLite, Redis, Docker logs, reindexing, or Typer/Click CLI dependency issues.

## Do not handle here

- Current Argilla SDK dataset/settings/records/search/webhook code: route to `python-sdk`.
- Legacy v1/Rubrix dataset migration: route to `legacy-migration`.
- Internal frontend development, repo CI, docs-generation, notebooks, or live service integration tests.

## Bundled references and scripts

- Read [references/deployment.md](references/deployment.md) when choosing a deployment path, adapting the bundled Compose file, planning Hugging Face Spaces, or giving Kubernetes/proxy guidance.
- Read [references/server-cli-and-config.md](references/server-cli-and-config.md) when you need exact `argilla_server` CLI commands, startup order, environment variables, OAuth YAML shape, or telemetry/auth configuration.
- Read [references/troubleshooting.md](references/troubleshooting.md) when startup, search, DB, Redis, OAuth, private Space, proxy, reindex, Docker, or CLI dependency symptoms need diagnosis.
- Use [scripts/docker-compose.argilla.local.yaml](scripts/docker-compose.argilla.local.yaml) as a self-contained local Compose template only when the user intentionally wants a local service stack; validate with `docker compose -f ... config` before running and replace sample credentials first.
- Run [scripts/check_server_cli.py](scripts/check_server_cli.py) to safely verify that `argilla_server` imports and that root/start/database/search-engine/worker CLI help renders without starting services.

## Operating safety

- Treat all server starts, Docker/Kubernetes operations, migrations, reindexing, user creation, and Hugging Face Space deployment as user-approved operations because they can create services, mutate databases/search indexes, or contact external APIs.
- Prefer help/config checks first. The bundled CLI helper renders help only; it does not start Uvicorn, workers, migrations, databases, Redis, search engines, Docker, or network calls.
- Never use real credentials in examples. Replace sample usernames, passwords, API keys, OAuth secrets, and auth secret keys before any shared or production deployment.
