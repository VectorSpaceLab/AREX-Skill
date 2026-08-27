# Backend API Troubleshooting

## Wrong Route Prefix or 404

Symptoms:

- A new route returns JSON 404 with `Not Found: /api/v1/...`.
- A legacy client hits `/v1/...` but the handler exists only under `/api/v1`.
- A route works in one test client but not another because one client prepends the version prefix.

Likely causes and fixes:

- The file is in the wrong route family. Move modern routes to `api/apps/restful_apis/` for `/api/v1`, or add an explicit compatibility alias in `api/apps/backward_compat.py`.
- The route path duplicated the version prefix. In RESTful modules, `@manager.route()` should usually start at the resource path, not `/api/v1/...`.
- The module name does not match dynamic discovery patterns. RESTful files must be under `restful_apis`; legacy files must end with `_app.py`.
- Compatibility needs both `/api/v1` and `/v1`; register against the correct backward-compat blueprint and test both URLs.

The bundled `scripts/list_routes.py` helper can statically list `@manager.route` declarations and infer likely prefixes before starting services.

## Request Validator Rejects Valid-Looking Input

Symptoms:

- `RetCode.ARGUMENT_ERROR` reports missing required arguments.
- JSON strings or arrays fail even though the body is valid JSON.
- Form requests behave differently from JSON requests.

Likely causes and fixes:

- `validate_request` expects a JSON object or form key/value mapping. Send an object such as `{ "name": "..." }`, not a raw string or list.
- The content type is not `application/json`, so body parsing falls back to form handling.
- Required arguments are checked before the handler runs; defaults inside the handler will not rescue missing fields.
- `not_allowed_parameters` rejects keys even if the handler ignores them.

Use `await get_request_json()` in async handlers, and keep tests explicit about content type and body shape.

## Async Quart Context Errors

Symptoms:

- Runtime warnings about coroutines never awaited.
- Access to request data fails outside a request context.
- Blocking behavior appears when a route calls slow sync work directly.

Likely causes and fixes:

- Quart request helpers such as body/form parsing are async; await existing helpers like `get_request_json()`.
- `login_required` wraps handlers through `current_app.ensure_async`; keep handlers async when they await request or downstream async APIs.
- Do not read `request`, `g`, `session`, or `current_user` in module import time code. Resolve them inside route/service execution.
- For channel bootstrap and other background work, use the existing async/thread handoff style and keep failures contained per channel or task.

## Auth Decorator, Session, and API Token Confusion

Symptoms:

- Login succeeds but follow-up requests are 401.
- API key requests authenticate as a different tenant than expected.
- Browser OAuth redirect works briefly, then fails after local Authorization state changes.

Likely causes and fixes:

- Use the `Authorization` response header from login for bearer requests, not the raw `data.access_token` from the response body.
- `APIToken.token` and `APIToken.beta` authenticate through different `auth_types`. If a route is beta-only, failed auth returns a data-error style response instead of raising the usual unauthorized path.
- Session fallback only applies when JWT auth is allowed and `session["_user_id"]` resolves to an active user with a valid access token.
- Logout invalidates access tokens by rewriting user state; stale sessions and signed tokens should not continue to authorize.

When adding protected routes, use `@login_required` in the same order as adjacent handlers: route decorator outermost, auth decorator directly above the function.

## Peewee Connection Pool or Transaction Errors

Symptoms:

- `OperationalError`, `InterfaceError`, deadlock code `1213`, stale connection, or pool exhaustion errors appear during API requests.
- Tests pass individually but fail under broader API runs.

Likely causes and fixes:

- DB operations should run under service helpers with `@DB.connection_context()` or within `DB.atomic()` for batches.
- Do not hold Peewee model instances or query iterators across request/background-task boundaries.
- Use existing retry helpers for connection loss or deadlocks when matching adjacent service behavior.
- Ensure app teardown still calls `close_connection()`; do not bypass the normal request lifecycle in tests without cleanup.

## Password Hash and Base64 Login Failures

Symptoms:

- A known password fails after creating or updating a user.
- Browser login and manual API login disagree.
- Tests hash `demo` but login verifies `ZGVtbw==`.

Likely causes and fixes:

- RAGFlow verifies the hash of `Base64(raw_password)`, not the raw password.
- `api/utils/crypt.py:crypt()` encrypts the Base64 representation; `decrypt()` returns that Base64 string to the login code.
- When manually setting a stored hash, generate it from the Base64 string.
- When debugging manual clients, distinguish RSA-encrypted browser-style input from already-compatible plaintext/backward-compatible flows.

## Service Layer Mismatch

Symptoms:

- A route duplicates DB logic already present in `api/db/services/`.
- A DB service starts importing Quart request globals or `current_user` unnecessarily.
- Permission checks differ between RESTful and legacy paths.

Likely causes and fixes:

- Put persistence primitives in `api/db/services/`, API payload/permission orchestration in `api/apps/services/`, and route-only formatting in `api/apps/restful_apis/`.
- Pass user/tenant IDs into services explicitly instead of reading request context deep in DB services.
- Reuse the same app-service function from modern and compatibility routes when behavior must stay identical.

## Backward Compatibility Alias Drift

Symptoms:

- Modern route behavior changes but deprecated aliases still call old logic.
- A compatibility route logs deprecation but returns different errors or data shape.
- Frontend, SDK, and HTTP docs disagree on the endpoint name.

Likely causes and fixes:

- Update `api/apps/backward_compat.py` forwarding calls when moving handler signatures.
- Keep path parameters and JSON payload translation explicit in the alias route.
- Add route-unit tests for both current and deprecated paths.
- Cross-check public endpoint families in the HTTP API reference when changing externally documented behavior.

## Source Installation Troubleshooting

During source-level inspection, importing `api` and `common` succeeded, but full editable installation can fail because package metadata names a top-level `graphrag` package while the GraphRAG code is located below `rag/graphrag`. Treat this as environment/install troubleshooting, not as backend API behavior. Prefer source-tree inspection for route/service work unless the packaging configuration has been fixed.
