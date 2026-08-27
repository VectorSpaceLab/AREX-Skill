# SDK troubleshooting

Use this troubleshooting reference for Python `Client`, `APIClient`, Pydantic model, and spec-helper failures. Keep live cloud operations gated behind explicit user approval.

## OpenAPI path or attribute not found

Symptoms:

- `AttributeError: No such endpoint named ... found.`
- `No paths found... Check the following debug messages...`
- A path exists in OpenAPI but `client.<name>` is missing.
- `client.debug_record()` mentions an invalid identifier or unsupported method.

Likely causes and fixes:

1. **OpenAPI was not fetched.** Constructing `Client(...)` fetches `/openapi.json`. If the deployment does not expose it, dynamic methods cannot be created. Check `client.debug_record()` and call the route owner to expose a valid spec.
2. **The path name was rectified.** Hyphens and dots become underscores, and Python keywords get a trailing underscore. Try `dir(client)` and `list(client.paths())`.
3. **Path parameters are unsupported as dynamic identifiers.** Components such as `{item_id}` are ignored by `PathTree` and logged in the debug record. Use a fixed OpenAPI route where possible, or use a narrow direct `_get`/`_post` fallback.
4. **Both leaf and nested paths exist.** If `/branch` and `/branch/leaf` both exist, `client.branch` becomes a subtree. The leaf callable is preserved on `client.branch[""]`.
5. **Only unsupported HTTP methods are present.** Dynamic creation supports `get` and `post`. Other methods are skipped with debug messages.

Safe diagnostic snippet:

```python
print(list(client.paths()))
print(dir(client))
print(client.debug_record())
```

## Positional arguments rejected

Dynamic endpoint methods accept keyword arguments. A call such as `client.run("hello")` raises a runtime message and may suggest the keyword equivalent from OpenAPI schema metadata.

Fix:

```python
client.run(inputs="hello")
```

If unsure, inspect `client.run.__doc__` or `help(client.run)`.

## `current()` has no workspace

Symptom:

```text
RuntimeError: No current workspace is set.
```

`leptonai.client.current()` only reads the current workspace id from the local workspace record. It does not create or login to a workspace.

Fixes:

- Route workspace selection/authentication to the `workspace-and-auth` sub-skill.
- Pass a known workspace id explicitly to `Client(workspace_id, deployment, ...)`.
- For local endpoint testing, avoid workspace context and use `Client(local(port=...))`.

## Auth/token needed

Symptoms:

- Endpoint returns 401/403 or a workspace unauthorized/forbidden error.
- A private endpoint works from CLI but not from a notebook.
- `Client(current(), deployment)` builds a URL but requests are not authorized.

Facts to remember:

- `Client` adds `Authorization: Bearer ...` only when its `token` argument is not `None`.
- `APIClient` resolves `auth_token` from argument, `LEPTON_WORKSPACE_TOKEN`, or workspace record, then uses it for workspace API calls.
- Do not print raw tokens or credential strings.

Fix pattern:

```python
import os
from leptonai.client import Client

client = Client(
    "workspace-id",
    "deployment-name",
    token=os.environ.get("LEPTON_WORKSPACE_TOKEN"),
)
```

If the user needs login or token refresh guidance, route to `workspace-and-auth`.

## Client construction makes network calls

`Client(...)` immediately checks health and fetches OpenAPI. This can fail before any user method call.

Use cases and actions:

- **No local server is running:** do not instantiate `Client(local(...))`; first start/verify the service through the owning workflow.
- **Endpoint is newly created:** allow for endpoint readiness delay; use workload status/log routes before retrying.
- **Endpoint has no `/healthz`/`/health`:** this only records a warning; `openapi.json` may still work.
- **No OpenAPI:** dynamic methods cannot be created. If you control the service, add OpenAPI metadata; otherwise use direct `_get`/`_post` sparingly.

For no-network introspection, run the bundled scripts rather than constructing `Client` for a real URL.

## `APIClient.deployment` or `pod` unexpectedly contacts `/workspace`

`APIClient.deployment` and `APIClient.pod` are dispatching properties. First access resolves the workspace feature flag via `info()`, which calls `/workspace` and caches the result.

Fixes:

- Do not access these properties merely to list method names; use `scripts/sdk_introspection.py`.
- In a long-lived notebook where the workspace flag changed, call `reset_new_deployment_api_flag_cache(...)` before the next dispatch.
- For tests, inject resource doubles through the writable `deployment` or `pod` property, or instantiate resource classes with `__new__` and fake HTTP methods.

## Pydantic v1/v2 compatibility

Symptoms:

- Import errors for Pydantic symbols such as `field_validator` or `ConfigDict`.
- A validator runs under Pydantic v2 but not under v1.
- Root models serialize differently from ordinary models.

Facts:

- The package exposes `PYDANTIC_MAJOR_VERSION`, `compatible_field_validator`, `v2only_field_validator`, and `CompatibleRootModel` in `leptonai.config`.
- `v2only_field_validator` intentionally does not validate under Pydantic v1.
- Some v2 API type modules use Pydantic v2-only names directly.

Fixes:

- Prefer a supported Pydantic 2.x environment for full v2 API model coverage.
- When validating compatibility, include both model construction and serialization checks.
- If only endpoint calling is needed, narrow the task to `Client` surfaces that are importable in the user's environment.

## `safe_json` and explicit null values

Symptoms:

- A field set to `None` is missing from the outgoing JSON.
- A raw dict passed to `safe_json` raises `ValueError`.
- A JSON merge patch fails to clear a previously configured nested field.

Facts:

- `safe_json` accepts Pydantic `BaseModel` objects or lists of them, not raw dicts.
- It serializes with `exclude_none=True` and `by_alias=True`.
- Nested `None` values inside a raw dict assigned to a model field can be preserved because the field itself is not `None`.

Fix for load-balance merge patches:

```python
spec = LeptonDeploymentUserSpec()
spec.load_balance_config = {"least_request": None, "maglev": {}}
payload = APIResourse.safe_json(APIResourse.__new__(APIResourse), LeptonDeployment(spec=spec))
assert payload["spec"]["load_balance_config"]["least_request"] is None
```

Use this pattern only for fields where the backend expects explicit JSON `null` under merge-patch semantics.

## Mount/env validation errors

### Mount strings

Expected format:

```text
FROM_PATH:MOUNT_PATH:VOLUME
```

Valid examples:

```text
/data:/mnt/data:node-local
/shared:/mnt/shared:node-nfs:training-data
```

Common failures:

- `/data:/mnt/data` → missing `VOLUME`.
- `/data:/mnt/data:node-nfs` → missing storage name.
- `/data:/mnt/data:node-:name` → missing storage type.
- `/data:/mnt/data:node-nfs:name:extra` → too many colons in `VOLUME` after the first two separators.

### Env and secret strings

Plain env variables must be `KEY=VALUE`. Secret references may be `SECRET_NAME` or `LOCAL_NAME=REMOTE_SECRET_NAME`.

Common failures:

- `MODE` in the `env` list → missing `=`.
- reserved internal Lepton environment names → rejected by the helper.
- expecting secret existence validation locally → not supported; helper builds references only.

Validation snippet:

```python
from leptonai.api.v2.spec_utils import make_env_vars_from_strings, make_mounts_from_strings

make_mounts_from_strings(["/data:/mnt/data:node-local"])
make_env_vars_from_strings(["MODE=test"], ["API_SECRET"])
```

## When to stop and ask the user

Ask before proceeding when:

- the next step would make a live workspace API call that creates, updates, stops, restarts, deletes, or reads private resource data;
- the user has not selected a workspace or supplied an auth route and the endpoint is private;
- a direct `_get`/`_post` fallback would bypass an OpenAPI contract and could hit a destructive custom route;
- a payload contains secret names or token-like strings and the task asks to print, paste, or store them.
