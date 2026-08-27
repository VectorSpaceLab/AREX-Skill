# Backend Architecture

This reference covers app construction, middleware and auth, tenant/session boundaries, settings, tracing, and file store behavior.

## App construction and startup

- The API server is built from a factory, not from import-time side effects.
- Startup validates deployment flags early and fails fast on incompatible settings.
- In single-tenant mode, startup pins the default tenant context, warms telemetry, seeds the public bootstrap state, and initializes the file store backend if needed.
- In multi-tenant mode, bootstrap is split so tenant-aware setup happens through the multi-tenant path instead of the single-tenant path.
- Route function names become operation IDs after the app is assembled, so keep names stable when the client surface matters.

## Middleware and auth

- Middleware order matters. Keep client-IP, request ID, endpoint context, CORS, captcha gating, latency logging, and metrics behavior in the established order.
- The app performs a central route-auth audit before serving traffic.
- Public endpoints are explicit. Do not assume a route is public because it is small or informational.
- New routes that read or mutate user, chat, document, connector, or tenant-scoped data must declare an auth dependency.
- Recognized auth patterns include the current user, chat-accessible user, curator/admin user, limited-user access, websocket auth, and permission-based dependencies.

## Tenant and session boundaries

- Request code and background jobs carry tenant state through the tenant context, not through module globals.
- Use the tenant-aware DB session helpers for per-tenant data.
- Use the public-schema session path for shared bootstrap data.
- Do not construct ad hoc engines in route handlers.
- Every ID lookup is untrusted until the user and tenant ownership checks succeed.
- Treat missing tenant scoping or missing ownership checks as a security bug, not a convenience issue.

## Settings and tracing

- Startup validates auth secrets, cache/vector-DB compatibility, and other deployment gates before the app serves traffic.
- Tracing is initialized during startup.
- Every model, embedding, rerank, voice, or intent-classification call should emit a named generation span.
- If a feature adds a new model-call path, update tracing coverage at the same time.

## File store

- The file store stores metadata in the database and file bodies in the selected storage backend.
- Supported backends include S3-compatible storage, Google Cloud Storage, Azure Blob Storage, and PostgreSQL large objects.
- The backend selection comes from configuration; callers should use the default factory without threading backend choice through every call site.
- File-store initialization belongs in startup, not in ad hoc route or task code.
- Multi-tenant deployments should expect storage provisioning to be handled by infrastructure when the deployment model requires it.

## Quick route inventory

- Use the bundled route inventory helper when you only need the current method/path/name map and do not want to start the API server.
