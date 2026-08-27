# Shared Troubleshooting

## Purpose

Use this for cross-package setup and routing failures before moving into a focused sub-skill. It is intentionally actionable and avoids live provider/API calls by default.

## Quick triage

| Symptom | Likely cause | First check | Route deeper to |
| --- | --- | --- | --- |
| Backend package import fails | Python version below 3.13, deps not installed, missing secrets/config, backend/MCP `app` import collision | Use separate backend and MCP Python contexts; run root and backend checkers | `backend-core` |
| MCP imports backend `app` by accident | Backend and MCP packages both use top-level `app` | Use separate environments or set cwd/sys.path to the MCP package when checking MCP | `mcp-server` |
| Frontend cannot reach backend | Wrong `VITE_API_URL`, backend down, CORS mismatch, runtime config bypassed | Confirm `resolveApiUrl()` and `API_CONFIG.baseUrl`; check backend URL and CORS | `frontend-portal`, then `backend-core` |
| Native backend tests fail before running app code | Docker unavailable, testcontainers cannot start Postgres/Redis, explicit test URLs missing | `docker compose version`; inspect test DB/Redis config | `backend-core` |
| Provider appears in code but not coverage matrix | Strategy/enum/factory/coverage constants drift | Run provider inventory and coverage checks | `provider-integrations` |
| MCP tool returns 401 | Wrong/revoked API key or backend auth semantics changed | Use MCP config checker; verify key through developer credentials workflow | `mcp-server`, then `backend-core` |
| MCP tool returns 404 on `/api/v1/users` | `OPEN_WEARABLES_API_URL` points at frontend host or incompatible backend version | Use API base host only; do not include `/api/v1` in env var | `mcp-server` |
| Svix/outgoing webhook features do nothing | `OUTGOING_WEBHOOKS_ENABLED=false`, Svix service not running, bad Svix token | Check backend env and Docker services; keep secrets redacted | `backend-core` |
| Raw payload replay/storage fails | S3/AWS config missing, endpoint incompatible, replay requires live API key | Avoid replay by default; use only with explicit credentials and disposable targets | `backend-core` |
| pnpm command missing | pnpm not installed but Node/Corepack may exist | Use Corepack if policy allows; otherwise install pnpm through normal project setup | `frontend-portal` |

## Safe generated checks

```bash
python skills/disco/open-wearables/scripts/check_open_wearables_install.py --repo-root .
python skills/disco/open-wearables/sub-skills/backend-core/scripts/check_backend_core.py --repo-root .
python skills/disco/open-wearables/sub-skills/provider-integrations/scripts/provider_inventory.py --check-count
python skills/disco/open-wearables/sub-skills/frontend-portal/scripts/check_frontend_metadata.py --repo-root .
python skills/disco/open-wearables/sub-skills/mcp-server/scripts/check_mcp_config.py --mcp-root mcp --no-import-check
```

Use these before broader native tests. They are read-only and mostly static.

## Secret and credential rules

- Never print, commit, or paste real `.env` files, API keys, OAuth tokens, JWTs, application secrets, Svix tokens, AWS keys, or master encryption material.
- Treat placeholders in templates as placeholders; they are not valid live-call credentials.
- For provider or MCP live calls, first confirm the task explicitly requires network/credentials. Otherwise use mocked tests and config validation.
- If logs are needed, redact values after their first few safe identifying characters or avoid logging them entirely.

## Backend/MCP import collision

The backend package and MCP package both expose top-level `app`. A single Python environment can install both packages, but import inspection becomes ambiguous. Keep package inspection or live checks separated by package root/environment, or explicitly set the target package path for the one being inspected. If a script imports the wrong `app`, symptoms include missing FastMCP tool routers, missing backend route modules, or config keys from the other package.

## Service dependency failures

Backend service checks may need PostgreSQL, Redis, Celery, and Svix. Use Docker Compose for local development. Do not run destructive database reset or payload replay scripts unless the target is disposable and the user explicitly asks for those side effects.

If a native test fails because Docker is unavailable, report it as a verification environment gap rather than changing backend code blindly.

## Docs and API navigation drift

When an endpoint tagged `External: *` is added, removed, renamed, or retagged, update API Reference navigation metadata in the docs. If navigation drift is discovered during checks, decide whether the endpoint is intentionally public. Do not hide the drift by removing a route from tests; fix docs or retag the route with the owning backend guidance.

## When to stop

Stop and ask for explicit authorization when the next step would:

- mutate a user-provided Python/Node environment,
- start long-running services in a shared environment,
- use live provider/MCP/API credentials,
- replay raw payloads or reset a database,
- run broad test suites that require Docker/network/service side effects, or
- import this generated skill into a live router despite the production request saying not to import.
