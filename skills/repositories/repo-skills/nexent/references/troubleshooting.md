# Cross-Cutting Troubleshooting

## Which sub-skill should handle this?

- Import/signature, agent runtime, model/tool/MCP/A2A, sandbox, scheduler, monitoring: SDK agent runtime.
- HTTP route/service/database/env/exception/auth/tenant/prompt behavior: backend services/API.
- Document ingestion, vector DB, storage, knowledge search, memory, data-process worker: knowledge/data/memory.
- Next.js UI, frontend services/types, streaming chat rendering, i18n, build/type/lint: frontend integration.
- Docker/K8s/offline packages, env files, SQL migrations/init, image builds, uninstall/upgrade: deployment operations.

## Dependency conflicts

Symptoms:
- `pip check` reports incompatible `orjson` or `pypdf` requirements when installing SDK and backend/data-process extras together.
- SDK-only imports succeed, but data-process imports require extra dependencies.

Fix:
- Use environment variants that match the task: SDK-only for SDK runtime inspection; backend/data-process for backend and ingestion workflows.
- Do not edit package pins casually to silence resolver conflicts. First identify which package surface actually needs the dependency variant.

## Network or provider failures

Symptoms:
- Stopword/model/provider download warnings, MCP connection timeout, external search/model API failures.

Fix:
- Treat network/model/search/MCP/provider calls as optional unless the user supplies credentials/endpoints.
- Mock providers in tests.
- For production deployment troubleshooting, verify env names and service URLs without exposing secret values.

## Wrong layer changed

Symptoms:
- Frontend-only fix hides a backend permission bug.
- Service raises `HTTPException`.
- SDK starts reading deployment env vars.
- SQL migration updates upgraded deployments but fresh installs still fail.

Fix:
- Re-route through the correct sub-skill and update the neighboring layers through documented cross-links.
- Add focused tests at the layer boundary where the bug first appears.

## Live infrastructure required

Redis, PostgreSQL/Supabase, Elasticsearch, MinIO, Ray/Celery, Docker, Kubernetes, model providers, and external APIs are not assumed available. If a task truly needs them, confirm target, credentials, data-preservation policy, and expected runtime before acting.
