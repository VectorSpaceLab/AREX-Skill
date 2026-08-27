# Specs, Pydantic models, and serialization

Lepton's v2 SDK models live under `leptonai.api.v2.types`. They are ordinary Pydantic models with aliases and compatibility helpers. Use this reference to build JSON payloads safely and to validate human-friendly mount/env strings before any live API call.

## Model construction basics

Common imports:

```python
from leptonai.api.v2.api_resource import APIResourse
from leptonai.api.v2.types.common import Metadata
from leptonai.api.v2.types.deployment import (
    LeptonDeployment,
    LeptonDeploymentUserSpec,
    LeptonContainer,
    ResourceRequirement,
)
```

Example deployment spec object:

```python
spec = LeptonDeployment(
    metadata=Metadata(name="example-endpoint"),
    spec=LeptonDeploymentUserSpec(
        container=LeptonContainer(image="registry.example/app:latest"),
        resource_requirement=ResourceRequirement(resource_shape="gpu.a10"),
    ),
)
```

Many backend field names that would collide with Python syntax are exposed as Python-safe attributes with aliases:

| Python attribute | JSON alias | Example models |
| --- | --- | --- |
| `id_` | `id` | `Metadata`, `Replica`, node/resource models |
| `type_` | `type` | event, replica, and resource models |
| `from_` | `from` | `Mount`, dedicated node group `Volume` |

Always serialize with aliases before sending JSON.

## `safe_json` contract

`APIResourse.safe_json(content)` accepts either a Pydantic `BaseModel` or a list of Pydantic models. It returns JSON-ready dictionaries using:

```python
model.dict(exclude_none=True, by_alias=True)
```

Consequences:

- `None` fields on Pydantic models are omitted.
- Alias fields such as `from_` become JSON keys such as `from`.
- Lists of models are supported.
- Raw dicts are rejected with `ValueError("safe_json only accepts BaseModel or List[BaseModel] as input.")`.

Minimal use without a live client:

```python
resource = APIResourse.__new__(APIResourse)
payload = resource.safe_json(spec)
```

## Explicit null preservation for merge patches

`safe_json` intentionally drops Pydantic model fields whose value is `None`. That is normally correct for create/update payloads, but JSON merge patch sometimes needs an explicit `null` to clear a previously selected server-side sub-field.

The deployment load-balance update case demonstrates the safe pattern:

```python
from leptonai.api.v2.api_resource import APIResourse
from leptonai.api.v2.types.common import Metadata
from leptonai.api.v2.types.deployment import LeptonDeployment, LeptonDeploymentUserSpec

spec = LeptonDeploymentUserSpec()
# Assign a raw dict after construction so nested nulls stay inside the dict.
spec.load_balance_config = {"least_request": None, "maglev": {}}
dep = LeptonDeployment(metadata=Metadata(id="ep", name="ep"), spec=spec)

payload = APIResourse.safe_json(APIResourse.__new__(APIResourse), dep)
assert payload["spec"]["load_balance_config"]["least_request"] is None
```

Do not replace this with `LoadBalanceConfig(least_request=None, maglev=...)` when the desired wire behavior is an explicit null; model-level `exclude_none=True` would omit the null field.

## Mount string helper

```python
from leptonai.api.v2.spec_utils import make_mounts_from_strings

mounts = make_mounts_from_strings([
    "/data:/mnt/data:node-local",
    "/shared:/mnt/shared:node-nfs:training-data",
])
```

Input format:

```text
FROM_PATH:MOUNT_PATH:VOLUME
```

Parsing details:

- The string is split on the first two colons only: `mount_str.split(":", 2)`.
- `VOLUME` may be `node-local`.
- `VOLUME` may be `node-<type>:<storage_name>`, for example `node-nfs:training-data`.
- Empty input (`None` or `[]`) returns `None`.
- Missing fields, missing storage type, missing storage name, or too many storage colons raise `ValueError` with an `Invalid mount definition` message.
- The returned models serialize with `from` as the JSON key, not `from_`.

Validation-only snippet:

```python
resource = APIResourse.__new__(APIResourse)
for mount in make_mounts_from_strings(["/data:/mnt/data:node-local"]):
    print(resource.safe_json(mount))
# {'path': '/data', 'mount_path': '/mnt/data', 'from': 'node-local'}
```

## Env and secret helper

```python
from leptonai.api.v2.spec_utils import make_env_vars_from_strings

envs = make_env_vars_from_strings(
    env=["MODE=prod", "MAX_BATCH=8"],
    secret=["API_TOKEN_SECRET", "DB_PASSWORD=prod-db-password"],
)
```

Rules:

- Plain env strings must be `KEY=VALUE`; splitting happens at the first `=`.
- Secret strings may be `SECRET_NAME`, which maps local env name to the same secret name.
- Secret strings may be `LOCAL_ENV_NAME=REMOTE_SECRET_NAME`.
- Reserved internal Lepton environment names raise `ValueError`.
- Empty `env` and `secret` inputs return `None`.

Serialized shapes:

```python
resource = APIResourse.__new__(APIResourse)
for item in envs:
    print(resource.safe_json(item))
# {'name': 'MODE', 'value': 'prod'}
# {'name': 'API_TOKEN_SECRET', 'value_from': {'secret_name_ref': 'API_TOKEN_SECRET'}}
```

Do not print real secret values. The helper only builds references; it does not check whether the named secret exists remotely.

## Pydantic v1/v2 compatibility notes

The package includes compatibility helpers in `leptonai.config`:

- `PYDANTIC_MAJOR_VERSION` records the detected major version.
- `compatible_field_validator` maps to a simple v1-compatible validator or Pydantic v2 `field_validator`.
- `v2only_field_validator` is a no-op wrapper under Pydantic v1 and a real field validator under Pydantic v2.
- `CompatibleRootModel` gives simple root-model behavior across v1/v2, with `dict()` and `json()` returning the underlying `root` content.

Native compatibility tests verify:

- a compatible root model serializes `{}` and populated dictionaries consistently;
- `compatible_field_validator` rejects invalid values under both supported paths;
- `v2only_field_validator` runs under Pydantic v2 and intentionally does not validate under v1.

Some v2 API model modules use Pydantic v2 names directly. If a runtime environment raises import errors for `field_validator` or `ConfigDict`, use a supported Pydantic 2.x version for those surfaces or narrow the script to modules that are confirmed importable in that environment.

## Recommended validation sequence before a live SDK mutation

1. Build Pydantic models in a script or notebook cell.
2. Parse mount/env/secret strings with the helpers above.
3. Serialize with `APIResourse.safe_json(...)` and inspect the redacted payload shape.
4. Verify `None` handling for merge-patch fields; use a raw dict assignment only when explicit JSON `null` is required.
5. Only after user confirmation and workspace/auth checks, pass the model to an `APIClient` resource method.
