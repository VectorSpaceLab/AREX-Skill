---
name: self-hosting
description: "Run and troubleshoot the Honcho API, worker, database, Redis,
  embeddings, and startup validation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: AGPL 3.0
---

# Self-hosting Honcho

Use this sub-skill when the task is about running Honcho locally or in a
production-like environment: API startup, worker startup, database schema,
Redis connectivity, embedding dimensions, vector-store mode, startup
validation, or server-side keys.

## What this route covers

- API server startup and shutdown.
- Deriver worker startup and queue processing.
- Database and schema prerequisites.
- Embedding-dimension validation.
- Vector-store mode selection and namespace behavior.
- Server-side key and auth setup.
- Queue health and deployment troubleshooting.

## What it does not cover

- SDK client code and REST client integration details.
- CLI command groups and config-file usage.
- Repo-wide testing and release hygiene.

Use `sub-skills/integrations/` for SDK and route usage, `sub-skills/cli-operations/`
for `honcho` terminal workflows, and `sub-skills/maintenance/` for tests and
release tasks.

## Read first

- `../../references/core-model.md`
- `../../references/configuration-and-environment.md`
- `../../references/troubleshooting.md`
- `references/workflow.md`
- `references/troubleshooting.md`
- `../../scripts/surface_report.py`
- `scripts/runtime_check.py`

## Typical questions this route should answer

- How do I start the API and worker safely?
- What database, Redis, and embedding settings do I need?
- Why did startup fail on vector dimensions?
- How do I tell whether queue processing is healthy?
- Which vector-store mode should I use?
- How should I configure keys and runtime secrets?

## Practical workflow

1. Read the configuration and environment reference.
2. Check the runtime surface with the bundled helper.
3. Confirm the database URI, schema, and embedding dimension.
4. Confirm the worker and queue are running.
5. Check the startup logs for the first closed-loop validation error.
6. If the deployment uses a non-default vector store, verify that mode before
   assuming pgvector behavior.

## Common decision points

- Use pgvector when you want the simplest local deployment.
- Treat external vector stores as optional and environment-specific.
- Treat an embedding mismatch as a blocking startup problem, not a warning.
- Treat queued memory work as asynchronous; do not expect immediate
  representation updates.

## Troubleshooting focus

This route owns startup failures caused by:

- bad database credentials or unreachable DB host,
- missing schema or extension prerequisites,
- Redis connection problems,
- wrong embedding dimension,
- mismatched vector-store settings,
- missing runtime secrets or provider keys,
- queue health problems that show up at startup or on the `/queue/status`
  surface.

See `references/troubleshooting.md` for symptoms, likely causes, and recovery
steps.

## Helpful bundled script

`scripts/runtime_check.py` prints a read-only summary of the current
configuration, route surface, and embedding validation status. Use it before
changing the deployment, or when you need a quick sanity check without digging
through source code.

## Good handoff phrases

- "How do I start Honcho locally?"
- "Why won't Honcho boot?"
- "What embedding dimension should I use?"
- "How do I check if the queue is healthy?"
- "What database and Redis settings do I need?"
