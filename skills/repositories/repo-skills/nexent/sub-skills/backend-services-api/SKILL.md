---
name: backend-services-api
description: "Operate Nexent backend FastAPI app/service/database changes,
  environment constants, domain exceptions, auth and tenant permissions, prompt
  templates, and API orchestration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Backend Services API

Use this sub-skill for Nexent backend work that changes or diagnoses FastAPI routes, service orchestration, database helpers, backend configuration constants, domain exceptions, tenant/auth permissions, prompt-template storage, agent/model/skill/repository/memory route wiring, or backend service entrypoints.

## Route here when

- Adding, changing, or debugging a route under backend app modules such as `/agent`, `/skills`, `/model`, `/repository/*`, `/prompt*`, `/tenant*`, `/user*`, `/mcp*`, `/nb/*`, or shared app construction.
- Tracing an API failure across app endpoint, service function, domain exception, database helper, auth utility, or prompt-template synchronization.
- Adding a backend environment variable, version constant, error code, exception, request/response Pydantic model, tenant/role permission check, or database CRUD helper.
- Updating backend NL2Agent/NL2Skill orchestration, prompt-generation templates, service startup composition, or route-to-service ownership.
- Selecting focused backend app/service pytest cases and mocks for route, service, auth, and database boundaries.

## Route elsewhere

- Direct SDK agent/model/tool usage, `AgentConfig`, `ModelConfig`, streaming SDK internals, MCP transport semantics, sandbox policy, scheduler primitives, or SDK skill-manager details: [`../sdk-agent-runtime/SKILL.md`](../sdk-agent-runtime/SKILL.md).
- Deep document ingestion, vector database implementation, storage, knowledge-base retrieval, memory records/retrieval/dreaming, Redis/Elasticsearch/MinIO live behavior, or data-process worker details: [`../knowledge-data-memory/SKILL.md`](../knowledge-data-memory/SKILL.md).
- Next.js service clients, TypeScript contracts, chat UI streaming components, stores, i18n, or frontend build issues: [`../frontend-integration/SKILL.md`](../frontend-integration/SKILL.md).
- Docker/Kubernetes/offline deployment, SQL migration/init synchronization, env-file deployment ownership, image builds, runtime operations, or uninstall/upgrade scripts: [`../deployment-operations/SKILL.md`](../deployment-operations/SKILL.md).

## Operating procedure

1. Read [`references/backend-architecture.md`](references/backend-architecture.md) for the layer contract, environment-variable source of truth, exception flow, tenant/auth rules, prompt-template ownership, and safe entrypoint reasoning.
2. Read [`references/api-service-map.md`](references/api-service-map.md) to identify the route family, app module, service owner, likely database helper, and boundary handoff before editing code.
3. Use [`scripts/list_fastapi_routes.py`](scripts/list_fastapi_routes.py) to statically inventory backend app routes from a checkout without importing the backend or starting services.
4. Read [`references/testing.md`](references/testing.md) before selecting app/service tests or mocks. Patch dependencies at the module lookup site and avoid live external services unless a test explicitly provisions them.
5. Read [`references/troubleshooting.md`](references/troubleshooting.md) when an import, route, permission, exception envelope, startup hook, prompt template, or service dependency behaves unexpectedly.

## Non-negotiable backend rules

- Only backend constants may read environment variables. Add or change backend env vars in `backend/consts/const.py`, import resolved constants elsewhere, and pass configuration to SDK code as parameters.
- App modules parse/validate HTTP input, derive auth context, call services, map domain exceptions to HTTP responses, and preserve existing route shapes. Do not put core business logic in an app endpoint.
- Services orchestrate business logic, database helpers, SDK calls, and external clients. Do not raise `HTTPException` or return FastAPI/Starlette responses from service code.
- Database helpers use `get_db_session()` as the transaction boundary, use `TableBase` audit fields for ordinary tables, soft-delete with `delete_flag='Y'`, and do not manually commit, rollback, or close sessions.
- Domain exceptions belong in `backend/consts/exceptions.py`; business error-code mappings belong in `backend/consts/error_code.py` and message mappings beside them.
- Keep prompt-template YAML placeholders and language variants aligned. Startup sync stores the system default prompt template, so template schema changes require service and test updates.
- Unit and route tests must mock storage, database, Redis, Elasticsearch, model providers, network clients, and SDK agent execution unless the selected native case explicitly supplies those services.
