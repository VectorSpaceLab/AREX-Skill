---
name: backend-core
description: "Operate on BiSheng FastAPI backend core surfaces: DDD modules,
  routers, schemas, settings/context, models, error codes, and focused backend
  tests."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# backend-core

Use this sub-skill when a task touches BiSheng's FastAPI backend core: app startup, route registration, DDD module boundaries, common API schemas, settings/context lifecycle, SQLModel/DAO model surfaces, backend error codes, or focused backend tests.

## Start Here

Run bundled helper commands from this sub-skill directory, or adjust the script path to this directory after import.


1. Identify the exact backend surface before editing. The bundled helper can inspect a checkout without importing application modules:
   ```bash
   python scripts/inspect_backend_surface.py --repo-root <bisheng-checkout> --format text
   ```
2. Read [references/workflows.md](references/workflows.md) for concrete backend workflows, entry points, commands, and review checklists.
3. If the failure mode is unclear, start with [references/troubleshooting.md](references/troubleshooting.md).

## Owned Responsibilities

- FastAPI app factory/lifespan and middleware ordering around `src/backend/bisheng/main.py`.
- Global API router registration in `src/backend/bisheng/api/router.py`, including `/api/v1` frontend routes and `/api/v2` RPC routes.
- DDD backend module shape: `api/`, `domain/services/`, `domain/models/`, `domain/schemas/`, and repository boundaries.
- Common response/pagination/SSE schemas in `src/backend/bisheng/common/schemas/api.py`.
- Error-code discipline in `src/backend/bisheng/common/errcode/`.
- Settings and application context surfaces in `src/backend/bisheng/core/config/settings.py` and `src/backend/bisheng/core/context/`.
- SQLModel/DAO model surfaces in `src/backend/bisheng/database/models/` and domain model directories.
- Focused backend tests under `src/backend/test/`, especially `test/common/`, `test/core/`, `test/database/`, and module-specific tests.

## Route Sibling Areas Instead of Duplicating Them

- Use `workflow-engine` for LangGraph DAG execution, workflow nodes, edges, callbacks, and workflow Celery task behavior.
- Use `knowledge-rag` for knowledge base ingestion, RAG, Milvus/Elasticsearch dual recall, file parsing, and knowledge workers.
- Use `identity-permissions-tenancy` for OpenFGA/ReBAC permission flows, tenant hierarchy, admin scope, SSO/org sync, and quota semantics.
- Use `linsight-mcp` for Linsight worker/runtime, deepagents, MCP integrations, and Linsight task-mode behavior.
- Use `frontend-apps` for Platform or Client React code and API client usage.
- Use `deployment-maintenance` for Docker Compose, Nginx, production deployment, operational scripts, and environment rollout concerns.

## Non-Negotiables for Backend Core Work

- Preserve the layered call chain: Router → Endpoint → Service → Repository/DAO → DB. Do not add endpoint-to-model shortcuts for new code.
- Keep `common/` and `core/` independent of application domains and API modules.
- Return success and business errors through the shared response/error-code helpers; do not hide internal exceptions by converting every failure to `resp_500(message=str(e))`.
- Treat MySQL and DM8 as co-equal targets. Use dialect helpers for JSON, large text, and update timestamps.
- Respect tenant ContextVar semantics. ORM SELECTs are auto-filtered, but bulk updates/deletes and raw SQL require explicit tenant-safe design.
- Backend tests run from `src/backend/` with uv; new tests belong under `test/<module>/`, not the test root.
