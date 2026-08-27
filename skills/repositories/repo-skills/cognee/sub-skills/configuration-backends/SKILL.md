---
name: configuration-backends
description: "Configure Cognee runtime, optional extras, provider settings,
  storage/database backends, paths, environment variables, and backend
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Cognee Configuration and Backend Router

Use this sub-skill when the task is about installing Cognee, choosing optional
extras, setting environment variables, configuring `cognee.config`, selecting
LLM/embedding providers, changing storage paths, or diagnosing database/cache
backend setup.

## Route here for

- Python/package install requirements and optional extras selection.
- `.env` style setup for LLMs, embeddings, storage, databases, cache, tracing,
  auth posture, and local model providers.
- Runtime setters under `cognee.config`, including LLM, embedding, graph,
  vector, relational, migration, data-root, and system-root configuration.
- Backend choices: default SQLite/LanceDB/Ladybug/Kuzu, Postgres/pgvector,
  Neo4j, Turso/libSQL, Neptune Analytics, S3 storage, Redis/session cache, and
  local LLM/embedding providers.
- Safe preflight checks that should not call LLMs, connect to databases, print
  secrets, or mutate data.

## Route away

- Running memory ingestion/search/improvement flows: read
  [core-memory](../core-memory/SKILL.md).
- CLI invocation, long-running API servers, Docker, MCP, UI, CORS deployment,
  and service hardening: read [api-cli-services](../api-cli-services/SKILL.md).
- Custom graph schemas, pipelines, ontology resolvers, migrations, and advanced
  graph operations: read
  [advanced-graphs-pipelines](../advanced-graphs-pipelines/SKILL.md).

## Operating workflow

1. Read [configuration.md](references/configuration.md) for install range,
   environment tiers, runtime config classes, and safe `cognee.config` setters.
2. Read [backend-matrix.md](references/backend-matrix.md) before changing extras
   or backend provider names. Treat every external service and credentialed
   provider as optional unless the user explicitly selected it.
3. If the user reports an error, read
   [troubleshooting.md](references/troubleshooting.md) and identify whether the
   failure is missing credentials, missing optional extras, provider inference,
   vector dimensions, access-control/handler mismatch, cache/S3 path handling,
   or database subprocess/file locking.
4. For a non-mutating local preflight, run the bundled checker after Cognee is
   installed:

   ```bash
   python scripts/check_cognee_environment.py --help
   python scripts/check_cognee_environment.py --json
   ```

   The checker redacts secrets and absolute paths, constructs config objects
   safely, and reports optional modules as present/missing.

## Safety rules

- Never ask the user to paste secret values. Ask whether a secret is set, or use
  placeholders in examples.
- Do not install broad extras by default. Select the smallest extra set needed
  for the chosen provider/backend.
- Set environment variables before importing `cognee` in service or notebook
  entrypoints when those variables must affect pydantic settings at import time.
- Do not use this sub-skill to execute real memory flows or service startup; it
  owns configuration only.
