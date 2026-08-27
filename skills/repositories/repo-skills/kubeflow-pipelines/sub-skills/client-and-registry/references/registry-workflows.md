# Registry Workflows

`kfp.registry.RegistryClient` manages packages in a registry. It does not create
KFP experiments, runs, or recurring runs. To execute a registry package, first
obtain a pipeline package file and then submit it through `kfp.Client`.

## Constructor And Auth

Observed public constructor:

```python
RegistryClient(
    host,
    auth=None,
    config_file=None,
    auth_file=None,
)
```

| Input | Use | Notes |
| --- | --- | --- |
| `host` | Registry host/repository URL. | Required directly or via a registry context file. The KFP package registry host pattern includes Artifact Registry hosts such as `https://<location>-kfp.pkg.dev/<project>/<repo>`. |
| `auth` | `requests.auth.AuthBase` or Google credentials. | For token auth, use `ApiAuth(os.environ["KFP_REGISTRY_TOKEN"])`. For known Artifact Registry hosts, the client can use Google default credentials when no auth object is supplied. |
| `config_file` | Registry context JSON. | Supplies or overrides registry URL templates. Do not print local config paths from diagnostics. |
| `auth_file` | Registry credential JSON. | Contains credential material; treat as secret. Prefer environment variables or secure secret stores in examples. |

Token helper:

```python
from kfp.registry import ApiAuth, RegistryClient
```

`ApiAuth(token)` injects an `authorization: Bearer ...` header. Never print the
token.

## Public Methods

| Workflow | Methods | Notes |
| --- | --- | --- |
| Upload | `upload_pipeline(file_name, tags=None, extra_headers=None)` | Uploads a local YAML/package file to the registry and returns `(package_name, version)`. Tags may be a string or a list. |
| Download | `download_pipeline(package_name, version=None, tag=None, file_name=None)` | Requires either a version or a tag. Writes a local file and returns its file name. |
| Packages | `get_package`, `list_packages`, `delete_package` | Deletion is destructive and should require explicit user confirmation. |
| Versions | `get_version`, `list_versions`, `delete_version` | Version strings must start with `sha256:`. |
| Tags | `create_tag`, `get_tag`, `update_tag`, `list_tags`, `delete_tag` | Tags must not start with `sha256:`. `update_tag` moves a tag to a different version. |

## Upload And Tag A Package

```python
import os
from kfp.registry import ApiAuth, RegistryClient

registry = RegistryClient(
    host=os.environ["KFP_REGISTRY_HOST"],
    auth=ApiAuth(os.environ["KFP_REGISTRY_TOKEN"]),
)

package_name, version = registry.upload_pipeline(
    file_name="pipeline.yaml",
    tags=["dev", "latest"],
)
registry.create_tag(
    package_name=package_name,
    version=version,
    tag="prod",
)
```

Expected observations:

- `package_name` identifies the registry package.
- `version` is a digest-like string beginning with `sha256:`.
- Tags are human-readable labels and must not begin with `sha256:`.

## Download Then Submit To KFP

This is a two-client workflow. The registry client fetches a package; the KFP
client submits the package to a deployment.

```python
import os
import kfp
from kfp.registry import ApiAuth, RegistryClient

registry = RegistryClient(
    host=os.environ["KFP_REGISTRY_HOST"],
    auth=ApiAuth(os.environ["KFP_REGISTRY_TOKEN"]),
)
package_file = registry.download_pipeline(
    package_name="example-package",
    tag="prod",
    file_name="example-package-prod.yaml",
)

client = kfp.Client(
    host=os.environ["KFP_ENDPOINT"],
    namespace=os.environ.get("KFP_NAMESPACE", "kubeflow"),
    existing_token=os.environ.get("KFP_EXISTING_TOKEN"),
)
result = client.create_run_from_pipeline_package(
    pipeline_file=package_file,
    experiment_name="example-experiment",
    run_name="example-from-registry",
)
```

Do not say that `RegistryClient.upload_pipeline()` creates a run. It only stores
or versions a package.

## Listing And Inspecting

```python
packages = registry.list_packages()
versions = registry.list_versions("example-package")
tags = registry.list_tags("example-package")
metadata = registry.get_package("example-package")
```

For a specific version or tag:

```python
version_metadata = registry.get_version("example-package", "sha256:abc123")
tag_metadata = registry.get_tag("example-package", "prod")
```

## Cleanup

Registry cleanup is destructive and may remove artifacts used by other teams.
Require explicit confirmation and prefer dry-run inventory first:

```python
# After confirmation only:
registry.delete_tag("example-package", "dev")
registry.delete_version("example-package", "sha256:abc123")
registry.delete_package("example-package")
```

## Troubleshooting Registry Flows

- `ValueError: No host found.` means neither `host` nor a readable context
  supplied a registry host. Ask for the registry host or context mechanism.
- Version validation errors mean the version lacks the `sha256:` prefix.
- Tag validation errors mean a tag incorrectly starts with `sha256:`.
- Authentication failures depend on the registry backend. For token auth, verify
  that the expected token environment variable is set without printing it. For
  Artifact Registry, verify Google application default credentials and project
  access outside this runtime skill.
- A successful registry upload does not prove the KFP API endpoint is reachable.
  Run `check_client_configuration.py` and then a `Client` health/run/list call
  only when the endpoint and credentials are available.

## Evidence Notes

This reference was distilled from the RegistryClient implementation,
RegistryClient unit tests, SDK registry docs stub, and installed API-surface
facts for `kfp==2.15.2`.
