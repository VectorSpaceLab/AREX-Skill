# Route Patterns

## URL Prefix Rules

RAGFlow has several route families that can look similar but are registered differently:

| Family | Source pattern | Prefix | Typical use |
| --- | --- | --- | --- |
| RESTful APIs | `api/apps/restful_apis/*_api.py` | `/api/v1` | New public API families such as users, datasets, documents, chunks, providers, models, memories, system, agents, MCP, OpenAI-compatible endpoints. |
| Legacy apps | `api/apps/*_app.py` | `/v1/<page_name>` | Older web/API routes and page-specific handlers. |
| SDK routes | `api/apps/sdk/*.py` | `/v1/<page_name>` through dynamic registration | SDK-oriented compatibility routes. |
| Backward compatibility | `api/apps/backward_compat.py` | Explicit `/api/v1` and `/v1` blueprints | Deprecated aliases that forward to modern handlers or preserve old paths. |

The version segment comes from `api.constants.API_VERSION`. Route tests often use `configs.VERSION` to construct expected `/api/<version>` paths.

## Adding a RESTful Endpoint

Use this checklist for a new RESTful API endpoint:

1. Add or edit the domain file in `api/apps/restful_apis/`.
2. Declare the route with `@manager.route("/resource[/<id>]", methods=[...])`.
3. Add `@login_required` unless the endpoint is intentionally public, such as basic health/config/version routes.
4. Read JSON/form bodies through `await get_request_json()` or rely on `@validate_request(...)` when matching an existing pattern.
5. Keep tenant/user scoping explicit through `current_user.id`, `UserTenantService`, or domain service helpers.
6. Delegate persistence to `api/db/services/` and API orchestration to `api/apps/services/`.
7. Return standard envelopes with `get_json_result`, `construct_json_result`, `get_data_error_result`, or `server_error_response`.
8. Add or update route-unit tests near `test/testcases/restful_api/test_*_routes_unit.py` and integration-style API tests near the matching `test/testcases/restful_api/test_<domain>.py` file.

## Maintaining Legacy and Alias Paths

When a new RESTful path replaces an older path, preserve compatibility intentionally:

- Add forwarding aliases in `api/apps/backward_compat.py` when old clients still rely on the previous URL.
- Register aliases with the correct blueprint: `manager` for `/api/v1` compatibility and `legacy_v1_manager` for `/v1` compatibility.
- Keep response shape identical unless the compatibility route logs deprecation and deliberately adapts arguments.
- Add tests proving both modern and legacy paths work when clients require both.

Typical difficult case: a RESTful endpoint under `/api/v1/foo` must coexist with an older `/v1/foo_app` or `/v1/foo/...` style URL and a frontend service URL. The backend change is incomplete until all path owners agree on prefix, auth, and response shape.

## Public System Routes

`api/apps/restful_apis/system_api.py` contains mixed public and protected endpoints:

- Public: `/system/ping`, `/system/version`, `/system/config`, `/system/healthz`.
- Protected: `/system/status`, `/system/oceanbase/status`, `/system/tokens` operations.

Status routes touch document storage, object storage, database, Redis, task executor heartbeats, and OceanBase-specific health helpers. Keep these routes defensive: status failures should be reported in the returned object where possible rather than crashing the whole status response.

## Validation and Request Bodies

`api/utils/api_utils.py` centralizes body handling:

- `_coerce_request_data()` caches the parsed body on the request object, accepts empty bodies as `{}`, parses JSON only when the content type starts with `application/json`, accepts form payloads otherwise, and rejects non-object JSON payloads.
- `get_request_json()` awaits `_coerce_request_data()`.
- `validate_request(*required, **fixed_values)` checks required fields and exact allowed values before calling the handler.
- `not_allowed_parameters(*params)` rejects forbidden keys.

If a route fails validation unexpectedly, inspect content type, body shape, and whether the client sent a JSON array/string instead of an object. For multipart/file routes, follow existing `await request.form` and file handling patterns in the file/document API modules.

## Response Conventions

Most JSON API routes return an envelope like:

```json
{"code": 0, "message": "success", "data": {...}}
```

Common helpers:

- `get_json_result(code=RetCode.SUCCESS, message="success", data=None)` for standard JSON responses.
- `construct_json_result(...)` omits `data` when it is `None`.
- `get_data_error_result(...)` logs data errors and returns an error envelope.
- `server_error_response(e)` maps unhandled exceptions, unauthorized conditions, missing chunks, and generic exceptions to JSON envelopes.
- `build_error_result(...)` sets an HTTP status code when possible.

Avoid mixing raw Quart `jsonify` responses into route families unless the adjacent module already uses that shape, such as health endpoints.

## Tests and Native Candidates

Useful native tests to consult or extend:

- `test/testcases/restful_api/test_router_contracts.py` for not-found and prefix behavior.
- `test/testcases/restful_api/test_*_routes_unit.py` for isolated route contracts.
- `test/testcases/restful_api/test_system.py` and `test/testcases/test_web_api/test_system_app/test_system_routes_unit.py` for system route behavior.
- `test/unit_test/api/utils/test_doc_validation.py` and nearby `api/utils` tests for validation helpers.
- `test/unit_test/api/db/services/*` for service-layer and Peewee behavior.

Prefer small route-unit tests with mocked service calls for prefix/auth/validation behavior, then broader API tests only when the behavior requires real request flow.
