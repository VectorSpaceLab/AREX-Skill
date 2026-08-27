# Package overview

Read this for repository-level facts before choosing a sub-skill or deciding whether an installed LeptonAI package matches the task.

## Purpose and entry points

LeptonAI is the Python library and `lep` command-line interface for NVIDIA DGX Cloud Lepton. It supports:

- Workspace authentication and context management.
- A `Client` for calling deployed endpoints as Python methods derived from endpoint OpenAPI schemas.
- A workspace `APIClient` with v2 resource objects for endpoints/deployments, dev pods, jobs, Ray clusters, fine-tuning jobs, templates, storage, secrets, ingress, resource shapes, nodes, and logs.
- Pythonic Pydantic spec objects and helper parsers for workload configuration.
- The `lep` CLI for workspace, workload, storage, secret, ingress, and log operations.

Package metadata:

| Fact | Value |
| --- | --- |
| Distribution name | `leptonai` |
| Import package | `leptonai` |
| CLI entry point | `lep = leptonai.cli:lep` |
| Python support | `>=3.9,<3.14` |
| Public install | `pip install -U leptonai` |
| Test extra | `pip install -e .[test]` for repository-native pytest checks |
| Optional local lint extra | `pip install -e .[lint]` for maintainer formatting/linting, not needed for ordinary package use |

## Top-level CLI groups

The installed `lep --help` is authoritative. The source snapshot verified these top-level groups:

- Visible groups: `endpoint`, `workspace`, `job`, `pod`, `secret`, `ingress`, `log`, `raycluster`, `template`, `finetune`, `node`.
- Hidden compatibility groups: `deployment` mirrors endpoint/deployment operations; `storage` and `file` share the file-storage command group in the current source, with `storage` hidden in the Click registration but documented by help when invoked.
- Root commands: `lep login`, `lep logout`, `lep -v` / `lep --version`.

Because command availability and flags can vary by package version and server feature flags, always run `lep <group> --help` before executing unfamiliar commands.

## Important public Python APIs

High-level endpoint client:

```python
from leptonai.client import Client, local, current

client = Client(local(port=8080), timeout=60, no_check=True)
remote = Client("workspace-id", "endpoint-name", token="<token>")
```

Verified `Client` signature:

```text
Client(workspace_or_url, deployment=None, token=None, stream=None, chunk_size=None, timeout=None, no_check=False, http2=True)
```

Workspace API client:

```python
from leptonai.api.v2.client import APIClient

api = APIClient(workspace_id="workspace-id", auth_token="<token>")
# api.deployment, api.pod, api.job, api.storage, api.secret, api.ingress, ...
```

Shared helpers:

```python
from leptonai.api.v2.spec_utils import make_mounts_from_strings, make_env_vars_from_strings

mounts = make_mounts_from_strings(["/data:/mnt/data:node-local"])
envs = make_env_vars_from_strings(["MODE=prod"], ["API_KEY"])
```

For complete SDK guidance, route to [../sub-skills/sdk-client/SKILL.md](../sub-skills/sdk-client/SKILL.md).

## Configuration and environment variables

Common package/runtime settings:

| Variable | Purpose |
| --- | --- |
| `LEPTON_CACHE_DIR` | Local cache directory for workspace records, logs, and version-check cache. Set before importing `leptonai` when isolating tests. |
| `LEPTON_DEFAULT_TIMEOUT` | Default deployment timeout; false-like values disable the default. |
| `LEPTON_DEFAULT_RESOURCE_SHAPE` | Overrides default workload resource shape. |
| `LEPTON_TIMEOUT_KEEP_ALIVE` | Default keep-alive timeout. |
| `LEPTON_INCOMING_TRAFFIC_GRACE_PERIOD` | Local deployment shutdown grace period. |
| `LEPTON_LOCAL_DEPLOYMENT_TOKEN` | Token for local deployments when explicitly set. |
| `LEPTON_WORKSPACE_ID`, `LEPTON_WORKSPACE_TOKEN`, `LEPTON_WORKSPACE_URL`, `LEPTON_WORKSPACE_ORIGIN_URL` | Workspace API fallback values used by `APIClient`; see workspace/auth sub-skill. |

The CLI also has local workspace records. Do not assume a current workspace just because environment variables are present; route to workspace/auth for context checks.

## Pydantic compatibility

The package supports both Pydantic 1.x and 2.x with compatibility helpers in `leptonai.config`:

- `PYDANTIC_MAJOR_VERSION` records detected major version.
- `compatible_field_validator` maps simple field validators across versions.
- `v2only_field_validator` is a no-op under Pydantic 1.x for advanced v2-only validators.
- `CompatibleRootModel` backports a simple root model API.

When writing code that serializes Lepton models, prefer model methods or `APIResourse.safe_json(...)` and verify whether explicit `None` values must be preserved for JSON merge patch semantics.

## Version behavior

- Source builds derive the package version from Git tags via `setuptools_scm` and may produce a development version on untagged commits.
- The `lep` CLI performs a best-effort PyPI version check once per cache interval and may print a newer-version notice. This warning does not mean the command failed.
- If version/source alignment matters, read [repo-provenance.md](repo-provenance.md) before using or refreshing this skill.
