# DocsGPT verification matrix

Use this to choose the smallest validation set that actually covers the change.

## Core backend smoke set

Good first-pass checks for repo-skill work and most backend edits:

1. `python skills/disco/docs-gpt/scripts/check_local_config.py --repo .`
2. `python skills/disco/docs-gpt/scripts/inspect_api_routes.py --repo . --contains /api`
3. `ruff check .`
4. `python -m pytest tests/core/test_model_registry_yaml.py tests/core/test_db_uri.py`
5. `python -m pytest tests/parser/test_document_reader.py`

## Endpoint and transport coverage

Use these for API/SSE/OpenAI-compatible changes:

- `tests/api/test_async_sse_routes.py`
- `tests/test_asgi.py`
- `tests/integration/test_v1_api.py`
- `tests/integration/test_chat.py`
- `tests/services/test_mcp_server.py`
- `tests/api/test_rbac_endpoints.py`

Preferred runtime:

```bash
uvicorn application.asgi:asgi_app --host 0.0.0.0 --port 7091 --reload
```

Do not validate ASGI-only routes with `flask run`.

## Sources / ingestion / retrieval

Use these when changing uploads, parsers, chunking, retrieval, or vector stores:

- `tests/parser/*`
- `tests/retriever/*`
- `tests/graphrag/*`
- `tests/api/test_source*` and `tests/api/test_upload*` style paths if present
- `tests/e2e/specs/tier-b/upload.spec.ts`

If the change touches GraphRAG, verify the pgvector + `GRAPHRAG_ENABLED` path explicitly; CPU fallback is not a full substitute for graph extraction logic.

## Agents / tools / workflows

Use these when touching agent types, tools, workflow nodes, MCP, artifacts, or schedule execution:

- `tests/agents/test_workflow_engine.py`
- `tests/agents/*`
- `tests/api/test_agents*`, `tests/api/test_tools*`, `tests/api/test_workflows*` if present
- `tests/services/test_mcp_server.py`
- `tests/e2e/specs/tier-a/tools.spec.ts`
- `tests/e2e/specs/tier-b/workflow-builder.spec.ts`

## Auth / access control / ops

Use these when changing login, roles, teams, SCIM, OIDC, admin, or audit behavior:

- `tests/api/test_admin_dashboard.py`
- `tests/api/test_rbac_endpoints.py`
- `tests/api/test_teams_endpoints.py`
- `tests/integration/test_scim.py`
- `tests/devices/*`
- `tests/e2e/specs/auth/*`

For OIDC/SCIM checks, a mock IdP is preferable unless the task explicitly requires a real provider.

## Frontend / docs / e2e

Use these when changing UI or docs:

- `cd frontend && npm run lint && npm run build`
- `cd frontend && npm run test`
- `cd docs && npm run build`
- `cd tests/e2e && npm run e2e`

## Runtime/environment checks

When investigating startup or deployment problems, record:

- Python version in the target prefix
- `python -m pip check`
- whether `POSTGRES_URI` is reachable
- whether Redis is reachable on the configured broker/cache DBs
- whether the selected backend is actually present (for example, `torch.cuda.is_available()` when CUDA matters)

## Final reporting

A final handoff is not complete until you can say which candidate set was verified and which ones were intentionally deferred. Use the private environment report plus a concise summary of:

- what ran
- what passed
- what was skipped
- any backend/service limitation that remains
