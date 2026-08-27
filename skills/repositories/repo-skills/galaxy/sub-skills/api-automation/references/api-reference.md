# Galaxy API Reference

This reference distills Galaxy's API examples, API testing guide, and route modules into safe guidance for future agents. Use it to plan HTTP requests, write repository API tests, and reason about API-key behavior without depending on the original source tree.

## API Surface Orientation

- Galaxy exposes REST-like routes under `/api/...`; useful discovery routes include public `GET /api/version`, authenticated `GET /api/whoami`, `GET /api/configuration`, and resource collections such as `/api/histories`, `/api/tools`, `/api/workflows`, `/api/jobs`, `/api/users`, and `/api/libraries`.
- Newer API surfaces are described by FastAPI routers and Pydantic schemas; OpenAPI output is produced from Galaxy's FastAPI application and is useful for route names, required payload fields, response models, and admin-only markers.
- Legacy examples pass the API key as a `key` query parameter. Modern clients should prefer an API key header when their HTTP library or Galaxy deployment supports it, but query-key examples remain common in Galaxy scripts and tests.
- Encoded Galaxy IDs are opaque strings. Do not decode or fabricate them except through admin-only helper endpoints in a controlled test/admin context.

## Minimal Safe Client Flow

1. Normalize the base URL by stripping trailing `/` and avoid double `/api/api` mistakes.
2. Probe `GET /api/version` without credentials to verify the service and base path.
3. Probe `GET /api/whoami` with credentials to confirm the key maps to the expected user before writes.
4. Create a disposable history with `POST /api/histories` and a JSON body like `{"name": "API smoke"}`.
5. For dataset upload or workflow execution, keep all generated objects in that disposable history unless the user names an existing target.
6. Poll async resources using explicit terminal states; do not assume a submit response means outputs are ready.

## Authentication and Authorization

- Missing or wrong keys usually surface as `401 Unauthorized` or an unauthenticated/null user response depending on the endpoint and deployment.
- Non-admin keys receive `403 Forbidden` for admin-only routes such as administrative configuration, user/role management, and some import/export or decoding operations.
- Galaxy API tests distinguish ordinary user requests from admin requests with an `admin=True` flag on test helper calls.
- Admin impersonation in tests uses a `run-as` header on an admin-authenticated request; it is for test/admin contexts and should not be suggested for ordinary user automation unless the user explicitly administers the instance.
- Treat `ADMIN_REQUIRED` as a permission classification, not as something to bypass. Choose an admin key, change to a non-admin endpoint, or redesign the workflow.

## Histories and Datasets

Common history operations:

- `GET /api/histories`: list histories visible to the current user. Query options vary by view, sharing, archive, and admin scope.
- `POST /api/histories`: create a new history, usually with a `name` field.
- `GET /api/histories/{history_id}`: inspect one history.
- `PUT /api/histories/{history_id}` or PATCH-style helper routes: update metadata such as name, archive/delete state, or sharing settings depending on route.
- `GET /api/histories/{history_id}/contents`: list history datasets and collections.

Dataset and upload patterns:

- For tests, prefer `DatasetPopulator.new_history()`, `DatasetPopulator.new_dataset(..., wait=True)`, and `DatasetPopulator.run_tool(...)` over hand-built HTTP unless the behavior under test is the HTTP boundary.
- For direct HTTP uploads, Galaxy's tool/fetch endpoints accept JSON and multipart forms; payloads should identify the destination history and the input source type.
- Dataset states are asynchronous. Plan for states such as queued/running/ok/error and poll the history contents, job endpoint, or helper populator until terminal state.

## Tools and Jobs

- Tool execution commonly posts to tool endpoints with a `history_id` and nested `inputs` mapping where datasets are represented as `{"src": "hda", "id": "..."}` and collections as `{"src": "hdca", "id": "..."}`.
- Protected internal tools may not be callable directly; if an endpoint rejects a protected tool, use the public upload/fetch route or the documented workflow path.
- Jobs and outputs may become visible before completion. Always assert or poll final job and dataset states before reading output content.

## API Test Patterns

Galaxy API tests are server-backed Python tests. They generally belong in the API test suite when the behavior needs a running Galaxy server but not a browser or custom server configuration.

Typical shape:

```python
from galaxy_test.base.populators import DatasetPopulator, WorkflowPopulator
from ._framework import ApiTestCase

class TestFeatureApi(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.dataset_populator = DatasetPopulator(self.galaxy_interactor)
        self.workflow_populator = WorkflowPopulator(self.galaxy_interactor)

    def test_feature(self):
        history_id = self.dataset_populator.new_history("feature smoke")
        response = self._post("histories", data={"name": "another"})
        self._assert_status_code_is(response, 200)
```

Use wrapped HTTP helpers for endpoint-focused tests:

- `self._get("histories")`
- `self._post("histories", data={"name": "Test"})`
- `self._put(f"histories/{history_id}", data=payload)`
- `self._patch(...)`
- `self._delete(...)`
- Add `admin=True` for admin-authenticated helper requests.
- Add `headers={"run-as": user_id}` only with admin-authenticated tests that intentionally exercise impersonation behavior.

Use populator convenience methods for fixture setup and workflow/tool execution:

- `DatasetPopulator.new_history(name)`
- `DatasetPopulator.new_dataset(history_id, content="...", wait=True)`
- `DatasetPopulator.run_tool(tool_id, inputs, history_id)`
- `DatasetPopulator.wait_for_tool_run(history_id, result, assert_ok=True)`
- `WorkflowPopulator.upload_yaml_workflow(yaml_content)`
- `WorkflowPopulator.run_workflow(...)`
- `WorkflowPopulator.wait_for_invocation(...)` or `wait_for_invocation_and_completion(...)`

Use raw helper variants when testing errors:

```python
response = self.workflow_populator.import_workflow_from_path_raw(workflow_path)
self._assert_status_code_is(response, 403)
self._assert_error_code_is(response, error_codes.error_codes_by_name["ADMIN_REQUIRED"])
```

## Response and Error Assertions

- Prefer explicit status assertions over truthiness.
- For success, assert the HTTP status and required response keys before using IDs.
- For failures, assert status, error code, and a stable message fragment. Avoid exact full messages when the route includes dynamic IDs or validation internals.
- `400` generally means malformed JSON, missing required fields, invalid mutually-exclusive fields, schema validation failure, or a payload shape mismatch.
- `403` generally means insufficient role/user/admin permission.
- `404` may mean the route does not exist, the ID is not visible to the current user, or the base URL is wrong.

## OpenAPI Use

- OpenAPI schema output is best for route discovery, request/response model names, required fields, tags, and admin/public hints.
- Schema inspection does not prove runtime permissions, database state, tool availability, or whether a particular ID exists.
- The bundled `scripts/inspect_openapi_routes.py` can summarize an exported JSON/YAML schema. Without a schema path it prints offline guidance and example workflows.

## Avoid These Pitfalls

- Do not reuse production histories for smoke tests unless the user explicitly names them.
- Do not print full URLs that contain `?key=...`; redact keys before logging.
- Do not assume a browser session cookie is equivalent to an API key in standalone automation.
- Do not use `run-as` with non-admin keys.
- Do not make tests depend on a public Galaxy service or network unless the test is explicitly marked external and bounded.
