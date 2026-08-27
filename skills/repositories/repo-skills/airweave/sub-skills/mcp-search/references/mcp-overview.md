# MCP Search Overview

This sub-skill covers the Airweave MCP server as a client-facing transport layer, not the backend implementation behind the search API.

## Transport modes

| Mode | Entry point | Required config | Notes |
| --- | --- | --- | --- |
| stdio | `npm run start` / packaged binary | `AIRWEAVE_API_KEY`, `AIRWEAVE_COLLECTION` | Best for desktop MCP clients. `AIRWEAVE_BASE_URL` is optional and defaults to the public API. |
| Streamable HTTP | `npm run start:http` | `X-API-Key` or Bearer auth, plus a collection source | Serves `/mcp` and is stateless at the transport layer. OAuth adds Auth0 and Redis-backed auth state; Redis is not used for long-lived MCP transport sessions. |

## Core endpoints

- `POST /mcp` — MCP transport endpoint.
- `GET /health` — health check with transport and mode details.
- `GET /` — server info, auth hints, and endpoint map.
- `GET /metrics` — Prometheus metrics.
- `DELETE /mcp` — stateless no-op for protocol compatibility.

## Deployment knobs

### Local and stdio defaults
- `AIRWEAVE_API_KEY` — required.
- `AIRWEAVE_COLLECTION` — required.
- `AIRWEAVE_BASE_URL` — optional; defaults to the public Airweave API.

### HTTP and hosted mode
- `PORT` — HTTP listen port, default `8080`.
- `AIRWEAVE_COLLECTION` or `X-Collection-Readable-ID` — default collection source.
- `AIRWEAVE_BASE_URL` — backend API base URL.
- `MCP_OAUTH_ENABLED=true` — enable OAuth authorization routing.
- `MCP_BASE_URL` — public base URL used in OAuth redirects.
- `MCP_REDIS_URL` or `REDIS_HOST` / `REDIS_PORT` / `REDIS_PASSWORD` — Redis connection for OAuth state and registered clients.
- `AUTH0_DOMAIN`, `AUTH0_CLIENT_ID`, `AUTH0_CLIENT_SECRET`, `AUTH0_AUDIENCE` — required when OAuth is enabled.
- `POSTHOG_API_KEY`, `POSTHOG_HOST` — optional analytics knobs.
- `MCP_OAUTH_PENDING_TTL_SECONDS`, `MCP_OAUTH_CODE_TTL_SECONDS`, `MCP_OAUTH_CLIENT_TTL_SECONDS` — auth state TTLs.

## Observability

Prometheus metrics are exposed on `/metrics`. The most important series are:
- `mcp_http_request_duration_seconds`
- `mcp_http_requests_total`
- `mcp_search_duration_seconds`
- `mcp_search_requests_total`
- `mcp_org_resolution_duration_seconds`
- `mcp_org_cache_hits_total`
- `mcp_org_cache_misses_total`
- `mcp_org_cache_entries`
- `mcp_oauth_token_verification_duration_seconds`
- `mcp_oauth_token_verifications_total`
- `mcp_oauth_code_exchange_duration_seconds`

## Routing reminders

- Use `backend-api` for the Airweave search endpoint contract, collection semantics, and any question about the backend result shape.
- Use `frontend-dashboard` only when a dashboard flow changes how a user obtains the API key, collection readable ID, or auth context used by MCP setup.

## Smoke-check tip

The bundled smoke helper uses the current package's localhost test-key mock path to exercise search without requiring a live backend service.
