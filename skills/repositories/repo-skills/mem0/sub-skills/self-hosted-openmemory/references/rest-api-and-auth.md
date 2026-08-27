# REST API and Auth

Use this reference when a task asks how clients should talk to a self-hosted Mem0 REST API, how auth works, or how to reason about dashboard/API-key behavior.

## Endpoint Families

Self-hosted Mem0 exposes memory, entity, auth, API key, request log, settings/configuration, and dashboard-supporting routes. The exact route set depends on the deployed server version, but the practical families are:

- Memory operations: add, search, list/get, update, delete, history where enabled.
- Entity operations: list distinct entity identifiers and cascade-delete owned memories.
- Auth/session operations: dashboard login, registration/setup, refresh/logout.
- API key operations: create, label, revoke, and validate per-user keys.
- Request logs: audit API calls, status, latency, and auth mode.
- Runtime configuration: LLM/embedder/provider settings layered over environment defaults.

For hosted Platform SDK calls, route to `../sdk-memory/SKILL.md` instead. This reference is for self-hosted REST deployments.

## Auth Modes

| Mode | Use case | Header/client behavior |
| --- | --- | --- |
| Per-user API key | Recommended self-hosted programmatic access | Send the deployment’s API-key header expected by the server, usually `X-API-Key`. |
| Dashboard JWT | Browser dashboard sessions | Managed by UI login/session flow; do not paste tokens into code snippets. |
| Legacy `ADMIN_API_KEY` | Upgrade compatibility | Keep only when existing clients require it; prefer migrating to per-user keys. |
| `AUTH_DISABLED=true` | Local development only | Never use in production; call out risk in any generated plan. |

## Client Configuration Pattern

When wiring SDKs or custom clients to a self-hosted server:

1. Confirm the base URL and route prefix for that server version.
2. Use an API key created by the dashboard/admin path.
3. Keep keys in environment variables or secret stores.
4. Scope memory calls by `user_id`, `agent_id`, `run_id`, or the server’s supported entity filters.
5. Start with a non-production user/entity and a tiny add/search smoke test if the user approves live writes.

## CORS and Dashboard Origin

If the dashboard or frontend sits behind a custom domain, set the dashboard/API origin settings so browser calls are accepted. A CORS error in the browser can look like auth or API failure; inspect server logs and the configured dashboard URL before changing credentials.

## Request Logs

Request logs are valuable for diagnosing:

- Authentication mode and failures.
- Slow requests and upstream provider errors.
- Endpoint path mismatches.
- Memory write/search status.

They may contain metadata, route paths, and operational details. Do not paste full production request logs into prompts; summarize status codes, endpoint family, and redacted identifiers.

## Safe API Troubleshooting

- `401` on every protected route: auth enabled but no valid key/session path; check admin setup/API key/header.
- `403`: key exists but lacks required user/admin permission or target entity/app is disallowed.
- `404`: wrong route prefix, wrong server version, or dashboard URL used as API URL.
- `422`/validation error: payload shape mismatch, missing entity scope, invalid filters, or wrong content type.
- `500` on auth endpoints: missing `JWT_SECRET` or database/migration issue.
- `502`/upstream provider: LLM/embedder credential or provider configuration failure.

## Security Rules

- Do not reveal API keys, password reset tokens, JWTs, database URLs, or provider credentials.
- Prefer redacted config diagnostics and minimal reproducible request bodies.
- Confirm before any delete, cascade delete, volume reset, password reset, or retention prune.
- For production issues, collect logs/status first and avoid live write tests until the user identifies a safe tenant/entity.
