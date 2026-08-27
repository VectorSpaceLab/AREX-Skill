# Cross-Cutting Troubleshooting

## When to read

Read this when a BiSheng issue is not clearly owned by one subsystem, or when install, configuration, service startup, storage, auth, or frontend/backend contract failures cross multiple sub-skills.

## First triage

1. Identify the failing process: FastAPI API, Celery knowledge worker, Celery workflow worker, Celery beat/default worker, Linsight worker, Platform SPA, Client SPA, Docker/Nginx, commercial gateway, or storage service.
2. Identify the failing contract: HTTP route, WebSocket, Celery queue, Redis key, database model, vector index, MinIO object path, OpenFGA tuple, frontend route, frontend request wrapper, or config layer.
3. Route to the owning sub-skill after this page narrows the failure.

## Installation and import failures

### Backend editable install fails on license metadata

Symptoms:
- `pip install -e src/backend` fails while validating `project.license`.
- Error mentions the value `Apache 2.0` not matching the current PEP 621 schema.

Likely cause:
- Current setuptools validation expects `Apache-2.0` or a license table, while the repository metadata uses a legacy string.

Recovery:
- For normal development, use the repo-supported command from `src/backend`: `uv sync --frozen`.
- For read-only inspection, use a source-root `PYTHONPATH` or a private `.pth` file rather than editing metadata just to inspect imports.
- Do not publish a skill or docs that depends on a private inspection prefix.

### Import works from repo root but not outside it

Symptoms:
- `import bisheng` works while current working directory is `src/backend`, but not from another directory.

Recovery:
- For production/development, install with `uv sync --frozen` from `src/backend`.
- For ad hoc scripts, set `PYTHONPATH=./` when running from `src/backend`, matching backend script conventions.
- For skill helper scripts, pass `--repo-root` so helpers add or scan the correct checkout explicitly.

## Runtime services

### API starts but workers fail

Likely causes:
- Missing Redis broker configuration.
- Wrong `config` environment variable.
- Storage services not running.
- Worker launched from the wrong directory.

Recovery:
- Start commands run from `src/backend`.
- Ensure the same `config` value is used by API, Celery, and one-off scripts.
- Use `knowledge-rag` for knowledge worker failures, `workflow-engine` for workflow worker failures, and `linsight-mcp` for Linsight worker failures.

### Config change appears ignored

Likely cause:
- Runtime config is layered and DB-derived values are cached in Redis for about 100 seconds.

Recovery:
- Confirm whether the value comes from YAML, `BS_*` environment, database config, or Redis cache.
- Wait for cache TTL or clear the relevant cache through an approved operational path.
- Never write plaintext passwords to YAML to test a hypothesis; passwords are Fernet-encrypted.

### MinIO files or frontend images return 403

Likely cause:
- Signed object URL host does not match frontend dev proxy host.

Recovery:
- Match frontend MinIO proxy target to backend `object_storage.minio.sharepoint` exactly.
- Platform and Client have separate Vite env variables and separate path prefixes.
- Route UI details to `frontend-apps`; route backend object-storage config to `deployment-maintenance`.

## Data/config validation failures

### Tenant data is invisible in scripts

Likely cause:
- Scripts run outside request middleware, so tenant ContextVar is not set. Multi-tenant SELECT filters may use default or raise depending on mode.

Recovery:
- Use the backend script conventions: initialize app context when using Redis/Milvus/ES/OpenFGA, and use the provided tenant bypass helpers for cross-tenant maintenance reads.
- Do not add blanket manual `WHERE tenant_id` to ORM code; route tenant semantics to `identity-permissions-tenancy`.

### Permission list or route visibility is wrong

Likely causes:
- Resource tuple missing in OpenFGA.
- Backend menu key differs from frontend route permission key.
- Cursor pagination scan loop is using the wrong cursor boundary after permission filtering.

Recovery:
- Use `identity-permissions-tenancy` before patching frontend route guards.
- Check whether the API needs PermissionService authorization or a startup/backfill script.
- For cursor lists, advance scan cursors by the last DB row, not the last visible row.

## Workflow-specific routing

- Backend envelopes, error codes, routers, and DDD boundaries: `backend-core`.
- Workflow DAG execution, LangGraph nodes, callbacks, and resume behavior: `workflow-engine`.
- Knowledge file ingestion, parser providers, RAG indexes, and knowledge worker retries: `knowledge-rag`.
- Linsight task-mode state, deepagents, SOP/Skill migration, and MCP tool wrapping: `linsight-mcp`.
- Permission, tenant, gateway, approval, org sync, and cursor performance: `identity-permissions-tenancy`.
- React route/state/request/i18n/theme/test failures: `frontend-apps`.
- Docker Compose, uv/npm setup, migrations, ops scripts, arch guard, and SDD process: `deployment-maintenance`.
