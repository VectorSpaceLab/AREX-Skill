---
name: "backend-platform"
description: "Use backend-platform for Unstract's Django/DRF APIs, hosted MCP
  servers, route wiring, auth, and backend configuration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Backend Platform

Use this sub-skill when the task is about the Django backend itself: URL routing, auth, API deployment, pipeline APIs, file management, platform API keys, or the hosted MCP server.

## Owns

- Backend URL composition in `backend/backend/*.py`.
- API families such as `account_v2`, `api_v2`, `pipeline_v2`, `file_management`, `platform_api`, and related route wiring.
- The hosted MCP server, tool registry, tool authorization, spend guard, and redaction tests.
- Backend settings, environment-variable contracts, and developer / test startup checks.

## Excludes

- Full-stack deployment and container bootstrap — use `platform-deployment`.
- Worker queue routing and Celery / PG-queue operations — use `workers`.
- Frontend routing or runtime config — use `frontend`.
- Shared tool / SDK / registry authoring — use `sdk-and-tools`.
- Test-group manifests and e2e runtime selection — use `testing-rig`.

## Start Here

Read `references/routes-and-mcp.md` first for route families, MCP URLs, auth behavior, and the tool catalog.

Read `references/configuration.md` for the backend env var contract, startup command shape, and safe inspection environment.

Read `references/troubleshooting.md` when the issue is a failed import, a missing backend env var, a route mismatch, or an MCP authorization problem.

For a safe backend smoke check, use the root checker from this skill tree:

```bash
python ../../scripts/check_unstract_packages.py --backend
```

## Shared References

- `references/routes-and-mcp.md` — route families, hosted MCP topology, tool catalog, and auth behavior.
- `references/configuration.md` — settings contract, env vars, and startup commands.
- `references/troubleshooting.md` — backend import, routing, auth, and hosted-MCP failures.
- `../../references/service-map.md` — repo-wide service ownership map.
- `../../references/installation-and-env.md` — install and env matrix for backend and adjacent services.
- `../../scripts/check_unstract_packages.py` — shared package / backend smoke checker.

## Common Task Routing

| User request | Read next |
| --- | --- |
| "Why does this route 404 or 403?" | `references/routes-and-mcp.md` |
| "How do the MCP servers differ?" | `references/routes-and-mcp.md` |
| "What env vars does the backend need?" | `references/configuration.md` |
| "Why did the backend import fail?" | `references/troubleshooting.md` |
| "What should the API deployment or pipeline route look like?" | `references/routes-and-mcp.md` |

## Safety Boundaries

- Do not assume live PostgreSQL, Redis, or RabbitMQ are available unless the user asks for runtime validation.
- Do not suggest direct access to credential-bearing endpoints that the hosted MCP server intentionally excludes.
- Do not rely on direct view calls for middleware-authenticated behavior; always use the real URL path when checking auth semantics.
