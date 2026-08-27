# v2 APIClient resources

This reference covers `leptonai.api.v2.client.APIClient` and the resource objects attached to it. Use it when writing Python automation against Lepton workspace APIs. These methods are live workspace HTTP operations unless explicitly called out as local validation.

## Constructor and workspace resolution

```python
from leptonai.api.v2.client import APIClient

client = APIClient(
    workspace_id=None,
    auth_token=None,
    url=None,
    workspace_origin_url=None,
)
```

Resolution order inside `APIClient`:

1. `workspace_id` argument.
2. `LEPTON_WORKSPACE_ID` environment variable.
3. Current workspace record.
4. If still missing, raise a workspace configuration error.

If `workspace_id` contains a colon and `auth_token` was not supplied, the string is split as `workspace_id:token`. Do not log that form.

Auth token resolution order:

1. `auth_token` argument.
2. `LEPTON_WORKSPACE_TOKEN` environment variable.
3. token from the selected workspace record.

URL resolution order:

1. `url` argument.
2. `LEPTON_WORKSPACE_URL` environment variable.
3. URL from the selected workspace record.
4. the default workspace API URL derived from the workspace id.

`workspace_origin_url` follows the same pattern using its argument, `LEPTON_WORKSPACE_ORIGIN_URL`, workspace record, then URL-derived fallback.

The constructor creates a `requests.Session`, headers, timeout default (`120` seconds), and resource objects. It does not by itself list/create resources. Resource method calls do perform HTTP.

## Feature flag dispatch for deployment and pod

`client.deployment` and `client.pod` are properties, not simple attributes.

- `client.deployment` dispatches to legacy `DeploymentAPI` or new `EndpointAPI` depending on the workspace `features.enable_new_deployment_api` flag.
- `client.pod` dispatches to legacy `PodAPI` or new `DevPodAPI` using the same flag.
- The first property access resolves `/workspace` with bounded retries, then caches the boolean per process and workspace URL/credential fingerprint.
- Long-lived notebooks that must observe a server-side flag change can call `reset_new_deployment_api_flag_cache(...)` before the next dispatch.
- Tests and advanced scripts can temporarily override `client.deployment` or `client.pod`; the setter preserves a historically writable surface.

Avoid touching `client.deployment` or `client.pod` merely for introspection if you do not want network I/O. Use the bundled `scripts/sdk_introspection.py` for no-network method-surface discovery.

## Resource method surface

The following public resource attributes and methods are exposed by this package version. Method calls generally issue HTTP through the workspace API client and parse responses through `APIResourse.ensure_*` helpers.

| APIClient attribute | Resource class | Public methods |
| --- | --- | --- |
| `nodegroup` | `DedicatedNodeGroupAPI` | `list_all`, `get`, `list_nodes`, `list_idle_nodes`, `list_reservations`, `batch_fetch_nodes` |
| `job` | `JobAPI` | `list_all`, `list_matching`, `create`, `get`, `update`, `delete`, `get_events`, `get_replicas`, `get_log` |
| `secret` | `SecretAPI` | `list_all`, `create`, `delete` |
| `ingress` | `IngressAPI` | `list_all`, `create`, `get`, `delete`, `update`, `create_endpoint`, `delete_endpoint` |
| `storage` | `StorageAPI` | `get_file_type`, `list_storage`, `get_file`, `get_dir`, `create_file`, `create_dir`, `delete_file_or_dir`, `check_exists`, `total_file_system_usage_bytes` |
| `log` | `LogAPI` | `get_log_time_series`, `get_log` |
| `template` | `TemplateAPI` | `render`, `list_public`, `list_private`, `get_public`, `get_private` |
| `finetune` | `FineTuneAPI` | `list_all`, `create`, `get`, `update`, `delete`, `list_supported_models`, `list_trainers` |
| `shapes` | `ResourceShapeAPI` | `list_shapes` |
| `raycluster` | `RayClusterAPI` | `list_all`, `create`, `get`, `update`, `delete` |
| `deployment` | `DeploymentAPI` or `EndpointAPI` | `list_all`, `create`, `create_pod`, `get`, `update`, `stop`, `delete`, `restart`, `get_readiness`, `get_termination`, `get_replicas`, `get_log`, `get_events`; new endpoint mode may raise explicit unsupported errors for legacy-only sub-operations |
| `pod` | `PodAPI` or `DevPodAPI` | legacy/new-compatible pod methods including `list_all`, `create`, `get`, `update`, `stop`, `delete`, `restart`, readiness/termination/log methods where supported; new devpod mode explicitly reports unsupported legacy-only details |

`EndpointAPI` exposes the deployment method surface while translating between legacy `LeptonDeployment`-shaped SDK objects and the newer `/endpoints` HTTP routes. `DevPodAPI` does the same for `/devpods` routes and pod-shaped deployment specs.

## Common resource patterns

### List/get/create/update/delete

Most resource classes follow a familiar shape:

```python
items = client.job.list_all()
job = client.job.get("job-id-or-name")
# client.job.create(model) and delete/update perform live mutations.
```

For mutation methods, require explicit user confirmation and a selected workspace context before running. For command-line workload recipes, route to workload-management.

### Response parsing helpers

Every resource inherits helpers from `APIResourse`:

- `ensure_ok(response) -> bool`: raise for 4xx/5xx, otherwise return `True`.
- `ensure_type(response, Model) -> Model`: parse response JSON into a Pydantic model.
- `ensure_list(response, Model, list_key=None) -> List[Model]`: parse a list, optionally from a dict key; invalid items are skipped with stderr diagnostics.
- `ensure_json(response) -> Any`: return decoded JSON after status checks.
- `safe_json(model_or_list)`: serialize Pydantic model(s) for outbound JSON.

4xx responses raise `ClientError`; 5xx responses raise `ServerError`. Workspace `info()` maps common auth/lookup statuses to workspace-specific unauthorized, forbidden, not-found, or configuration errors.

## No-cloud validation patterns

### Validate a create payload shape locally

Some new-mode APIs expose `validate_create(spec)` to translate/validate a model without issuing a request:

```python
from leptonai.api.v2.endpoint import EndpointAPI
from leptonai.api.v2.types.common import Metadata
from leptonai.api.v2.types.deployment import LeptonContainer, LeptonDeployment, LeptonDeploymentUserSpec

api = EndpointAPI.__new__(EndpointAPI)
spec = LeptonDeployment(
    metadata=Metadata(name="endpoint"),
    spec=LeptonDeploymentUserSpec(container=LeptonContainer(image="registry.example/app:latest")),
)
# validate_create translates the legacy-shaped SDK object to the new endpoint
# request body and raises locally if the model cannot be translated.
api.validate_create(spec)
```

If a method needs `_get`, `_post`, or `_patch`, it is not a pure local validation method.

### Build update payload in a fake resource

For unit tests, create the resource with `__new__`, inject a fake HTTP method, and replace parser methods. This is the pattern used to verify merge-patch payloads without cloud access:

```python
from leptonai.api.v2.deployment import DeploymentAPI
from leptonai.api.v2.types.common import Metadata
from leptonai.api.v2.types.deployment import LeptonDeployment, LeptonDeploymentUserSpec

api = DeploymentAPI.__new__(DeploymentAPI)
captured = {}
api._patch = lambda url, json=None, **kwargs: captured.setdefault("json", json) or "ok"
api.ensure_type = lambda response, typ: response

spec = LeptonDeploymentUserSpec()
spec.load_balance_config = {"least_request": None, "maglev": {}}
dep = LeptonDeployment(metadata=Metadata(id="ep", name="ep"), spec=spec)
api.update("ep", dep)
assert captured["json"]["spec"]["load_balance_config"]["least_request"] is None
```

This technique is only for SDK tests or payload inspection. Do not fake API calls in production notebooks unless the goal is explicitly a dry-run/unit-test fixture.
