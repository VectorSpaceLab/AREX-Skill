---
name: deployment-api
description: "Install, configure, start, deploy, and troubleshoot the Khoj
  Python server/API surface."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Khoj Deployment and API

Use this sub-skill when a task is about installing Khoj, self-hosting it with pip or Docker, configuring server environment variables, starting the FastAPI/Django service, validating CLI parser behavior, mapping top-level REST API routes, or diagnosing deployment failures.

## Start Here

- For server startup lifecycle, CLI parser behavior, route prefixes, and REST endpoint families, read [server-and-api.md](references/server-and-api.md).
- For pip, Docker, database, domain, auth, admin, model-provider, gunicorn, and optional service configuration, read [configuration.md](references/configuration.md).
- For failures involving `khoj --help`, PostgreSQL, embedded DB, CSRF/host/cookies, model providers, static files, Docker memory, dependency conflicts, or Rust/tokenizers builds, read [troubleshooting.md](references/troubleshooting.md).
- To inspect parser defaults safely without importing `khoj.main` or touching the database, run [inspect_cli.py](scripts/inspect_cli.py).

## Boundaries

This sub-skill owns deployment, startup, configuration, API surface orientation, and deployment troubleshooting. Route document ingestion details to [content-indexing](../content-indexing/SKILL.md), search ranking/filter behavior to [search-retrieval](../search-retrieval/SKILL.md), chat/agent/tool payload internals to [chat-agents](../chat-agents/SKILL.md), automations and memory behavior to [automations-memory](../automations-memory/SKILL.md), and contributor workflows to [development](../development/SKILL.md).

## Safety Notes

- Do not use `khoj --help` as a harmless parser probe on an unconfigured host; the console script resolves `khoj.main:run`, and importing `khoj.main` initializes Django, runs migrations, and collects static files before CLI parsing.
- Prefer `python scripts/inspect_cli.py --args -- --help` or direct `khoj.utils.cli.cli(...)` inspection for parser-only validation.
- Do not start the server, mutate databases, pull containers, or install dependencies unless the user explicitly asks for an operational change.
