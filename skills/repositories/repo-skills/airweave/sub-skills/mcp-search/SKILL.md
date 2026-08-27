---
name: mcp-search
description: "Operate the Airweave MCP search server in stdio and Streamable
  HTTP modes, including tool registration, collection and organization
  resolution, auth modes, Prometheus metrics, deployment knobs, and search-tool
  behavior."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# mcp-search

Use this sub-skill when you need to start, configure, inspect, or troubleshoot the Airweave MCP search server.

## Covers
- stdio and Streamable HTTP entrypoints
- MCP tool registration and tool naming
- collection resolution and organization resolution
- API key and OAuth/Bearer auth paths
- Prometheus metrics and health endpoints
- deployment knobs, env vars, and safe smoke checks

## Does not cover
- backend endpoint implementation details
- dashboard UI or frontend internals
- Connect widget internals
- Monke orchestration

## Start here
1. Read `references/mcp-overview.md` for entrypoints, env vars, and deployment knobs.
2. Read `references/transport-and-tools.md` for the collection-specific tool surface and search behavior; use `tools/list` or `get-config` before calling a search.
3. Read `references/auth-and-troubleshooting.md` for auth, org resolution, metrics, and common failures.
4. Use `scripts/mcp-smoke.sh` for a safe version/build/test/entrypoint smoke pass.

## Cross-links
- Use `backend-api` for backend search-route and collection semantics.
- Use `frontend-dashboard` only when a dashboard-driven setup or auth-context issue changes how MCP credentials or collection IDs are obtained.

## Working notes
- stdio requires `AIRWEAVE_API_KEY` and `AIRWEAVE_COLLECTION`; `AIRWEAVE_BASE_URL` is optional.
- HTTP mode serves `/mcp`, `/health`, `/metrics`, and `GET /` server info.
- HTTP auth can use `X-API-Key` or `Authorization: Bearer ...`; OAuth mode adds Auth0, Redis, and org resolution.
- Search tools are collection-specific (`search-<collection>`), with `get-config` as the second tool.

## Verification expectations
- Missing stdio credentials should fail fast with a clear config error.
- HTTP OAuth requests should resolve the organization for the target collection.
- Tool lists, metrics, and search responses should remain readable and non-secret.
