---
name: sdk-client
description: "Use LeptonAI's Python SDK Client and v2 API resource/model objects
  safely from scripts and notebooks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# sdk-client

Use this sub-skill when the task is to call a deployed Lepton endpoint from Python, inspect endpoint OpenAPI-derived methods, or build SDK scripts/notebooks with `leptonai.api.v2` resource objects and Pydantic models.

## Route here for

- `Client(workspace_or_url, deployment=None, token=None, stream=None, chunk_size=None, timeout=None, no_check=False, http2=True)` endpoint-call code.
- `local(port)`, `Client.local(port)`, `current()`, and `Client.current()` usage.
- Dynamic `PathTree` behavior for OpenAPI paths exposed as Python attributes.
- `APIClient(...)` workspace API resource objects and their method surfaces.
- `APIResourse.safe_json(...)` model serialization and v2 Pydantic spec construction.
- Pure parsing helpers `make_mounts_from_strings(...)` and `make_env_vars_from_strings(...)`.

## Route elsewhere

- Workspace login, workspace record maintenance, token refresh, or auth setup: use the `workspace-and-auth` route.
- Shell-first workload recipes such as endpoint/job/pod/Ray/finetune create/list/update/delete: use the `workload-management` route.
- Storage, secrets, ingress, or canary routing plans: use the storage/ingress route even when SDK model helpers appear in the plan.

## Safety rule

Creating a `Client(...)` for a real URL or workspace endpoint performs network checks and tries to fetch `openapi.json`. `APIClient` resource methods perform authenticated workspace API requests. Do not run live or credentialed cloud calls unless the user has explicitly authorized the operation and supplied an appropriate workspace context. The bundled scripts in this sub-skill are designed to avoid network calls.

## Quick starts

### Inspect the installed SDK without network calls

```bash
python scripts/sdk_introspection.py
python scripts/client_path_tree_demo.py
```

The first script prints the installed package version, important signatures, and `APIClient` resource method surfaces without constructing a live workspace client. The second script demonstrates `PathTree` and `local(...)` behavior with fake callables only.

### Call a deployed endpoint from Python

```python
import os
from leptonai.client import Client, local

# Local endpoint URL plan; constructing the client contacts the local service.
c = Client(local(port=8080), timeout=60, no_check=True)
print(list(c.paths()))

# Workspace endpoint URL plan; pass an auth token explicitly if the endpoint is private.
remote = Client(
    "workspace-id",
    "endpoint-name",
    token=os.environ.get("LEPTON_WORKSPACE_TOKEN"),
    timeout=None,
)
# OpenAPI path /run becomes remote.run(...)
result = remote.run(inputs="hello")
```

For dynamic path rules, streaming return behavior, and failure modes, read [client-api.md](references/client-api.md).

### Build v2 specs without cloud calls

```python
from leptonai.api.v2.api_resource import APIResourse
from leptonai.api.v2.spec_utils import make_env_vars_from_strings, make_mounts_from_strings
from leptonai.api.v2.types.common import Metadata
from leptonai.api.v2.types.deployment import LeptonDeployment, LeptonDeploymentUserSpec

spec = LeptonDeployment(
    metadata=Metadata(name="example"),
    spec=LeptonDeploymentUserSpec(
        envs=make_env_vars_from_strings(["MODE=test"], ["API_SECRET"]),
        mounts=make_mounts_from_strings(["/data:/mnt/data:node-local"]),
    ),
)
payload = APIResourse.safe_json(APIResourse.__new__(APIResourse), spec)
```

For resource surfaces, serialization caveats, and spec helpers, read [api-resources.md](references/api-resources.md) and [specs-and-models.md](references/specs-and-models.md).

## Troubleshooting index

- OpenAPI path not found, invalid identifier, or confusing attribute name: [troubleshooting.md](references/troubleshooting.md#openapi-path-or-attribute-not-found).
- `current()` says no current workspace: [troubleshooting.md](references/troubleshooting.md#current-has-no-workspace).
- 401/403/auth token required: [troubleshooting.md](references/troubleshooting.md#authtoken-needed).
- Pydantic v1/v2 model or validator issues: [troubleshooting.md](references/troubleshooting.md#pydantic-v1v2-compatibility).
- `safe_json` dropped `None` unexpectedly or rejected a dict: [troubleshooting.md](references/troubleshooting.md#safe_json-and-explicit-null-values).
- Mount/env parsing errors: [troubleshooting.md](references/troubleshooting.md#mountenv-validation-errors).
