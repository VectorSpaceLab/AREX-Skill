# Backend Routes And MCP

This backend is a Django/DRF application with several route families composed into one public / tenant / deployment surface. It also exposes two hosted MCP servers inside the same backend process.

## Route Families

| Route family | Example paths | Notes |
| --- | --- | --- |
| Tenant-facing backend routes | `/<tenant>/...` | Composed from `backend/backend/urls.py` and `backend/backend/base_urls.py` |
| Public backend routes | `/api/v1/...` and `/api/v1/unstract/...` | Public docs, auth, pipeline, feature flags, and tenant-scoped MCP surface |
| Deployment API routes | `/deployment/api/<org>/<api_name>/...` | API deployment execution and the deployment-scoped MCP server |
| Internal API routes | `/internal/...` | Worker / service communication |

## Key Route Files

- `backend/backend/base_urls.py` combines tenant, public, deployment, and internal route groups.
- `backend/backend/urls.py` includes the tenant-facing authenticated app routes.
- `backend/backend/public_urls_v2.py` carries the public app surface, including docs, health, and public pipeline APIs.
- `backend/api_v2/urls.py`, `backend/pipeline_v2/urls.py`, `backend/platform_api/urls.py`, `backend/file_management/urls.py`, and `backend/account_v2/urls.py` define the main API families.
- `backend/mcp_server/urls.py` mounts the deployment-scoped MCP server under the deployment execution URL.

## Hosted MCP Servers

Unstract runs two MCP servers in the backend process:

| Server | Scope | URL | Credential |
| --- | --- | --- | --- |
| Deployment server | One API deployment | `/deployment/api/<org>/<api_name>/mcp` | That deployment's API key |
| Platform server | One organization | `/api/v1/unstract/<org>/mcp/` | A platform API key |

### Deployment Server Highlights

- Shares the deployment's existing API key.
- Supports the deployment-scoped extract and poll-status tools.
- Does not use the platform key tier logic because the credential is already deployment-scoped.

### Platform Server Highlights

- Lives behind `CustomAuthMiddleware` and the platform API-key permission tier.
- Exposes discovery, observability, state-change, and billable prompt / extraction tools.
- Declares `required_method` per tool so a POST-only JSON-RPC request can still be checked against the equivalent REST permission tier.
- Uses a per-organization billable-call guard to bound repeated paid operations.
- Deliberately excludes credential-returning and destructive operations.

## Route / Permission Invariants To Remember

- A `read` tier platform key cannot use the platform MCP server because every MCP call is an HTTP POST.
- The platform MCP path must stay outside the whitelisted deployment prefix or auth will be bypassed.
- `getExecutionStatus` on a completed run is a one-shot read; the result store is acknowledged when it is read.
- The platform server should never return connector credentials, adapter credentials, or key material.

## Useful Evidence

- `backend/mcp_server/registry.py` — tool catalog, billable guard, and annotation logic.
- `backend/mcp_server/README.md` — the public rationale for the deployment vs platform split.
- `backend/mcp_server/tests/` — auth, redaction, spend-guard, and credential-leak tests.
- `backend/tests_common/test_route_wiring.py` — route wiring checks that catch dead or misbound endpoints.

## When To Read This File

Read this file when you need to know:

- which URL family owns a backend endpoint,
- why a tool or route is authenticated the way it is,
- how the hosted MCP servers differ,
- or which endpoint family should be adjusted for a backend change.
