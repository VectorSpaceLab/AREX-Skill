# CVAT SDK API reference

This reference summarizes the stable CVAT Python SDK surfaces that future agents should prefer for automation. Install with `pip install cvat-sdk`; add extras only for the workflows that need them.

## Package and optional extras

| Need | Install | Notes |
|---|---|---|
| Core REST/high-level SDK | `pip install cvat-sdk` | Includes generated API client, high-level `Client`, task/project/job/user/organization/issue repositories, upload/download helpers, Pillow, progress utilities, and urllib3 transport. |
| Mask helpers | `pip install "cvat-sdk[masks]"` | Adds NumPy for `cvat_sdk.masks` helpers such as bitmap mask encoding. |
| PyTorch dataset adapter and built-in torchvision AA functions | `pip install "cvat-sdk[pytorch]"` | Adds PyTorch/TorchVision/scikit-image plus the mask extra. Use only when a workflow really needs ML dataset objects or torchvision model helpers. |

## Top-level imports

```python
from cvat_sdk import (
    AuthStore,
    Client,
    ClientAuthParameters,
    Config,
    ProfileEntry,
    configure_client_auth_arguments,
    get_auth_store_path,
    make_client,
    make_client_from_cli,
    make_client_from_profile,
)
from cvat_sdk.core.proxies.tasks import ResourceType
```

Confirmed public signatures include:

```python
Client(url: str, *, logger=None, config: Config | None = None,
       check_server_version: bool = True)
make_client(host: str, *, port: int | None = None,
            credentials=None, access_token: str | None = None) -> Client
Task.upload_data(resources, *, resource_type=ResourceType.LOCAL,
                 pbar=None, params=None, wait_for_completion=True,
                 status_check_period=None) -> None
Task.download_frames(frame_ids, *, image_extension=None, outdir='.',
                     quality='original',
                     filename_pattern='frame_{frame_id:06d}{frame_ext}')
Project.import_dataset(format_name: str, filename, *, conv_mask_to_poly=None,
                       status_check_period=None, pbar=None)
```

`ResourceType` values stringify as `local`, `share`, and `remote`.

## Client and configuration

`Client` is the session root. It normalizes the server URL, owns an `ApiClient`, and lazily exposes repositories:

- `client.tasks`
- `client.projects`
- `client.jobs`
- `client.users`
- `client.organizations`
- `client.issues`
- `client.api_client` for generated low-level API groups when the high-level layer has no wrapper.

`Config` fields:

| Field | Default | Use |
|---|---:|---|
| `status_check_period` | `5` | Polling interval in seconds for background requests. |
| `allow_unsupported_server` | `True` | If `False`, version mismatch raises instead of logging a warning. |
| `verify_ssl` | `None` | Set `False` only for explicitly trusted/self-hosted test servers. |
| `cache_dir` | platform user cache | Local SDK cache root for dataset adapters and cached server data. |

Use the context manager so HTTP resources close cleanly:

```python
from cvat_sdk import make_client

with make_client("https://cvat.example.com", access_token=token) as client:
    ...
```

## Authentication and profiles

Preferred methods:

1. PAT authentication: `make_client(url, access_token=token)` or `Client.login(AccessTokenCredentials(token))`.
2. CLI-style profile reuse: `AuthStore().get_profile(name)` then `make_client_from_profile(profile)`.
3. CLI argument parity: add shared flags with `configure_client_auth_arguments(parser)`, parse user arguments, then call `make_client_from_cli(args)`.
4. Password authentication: `make_client(url, credentials=(user, password))` only when a PAT/profile is unavailable.

`make_client_from_cli` follows the CLI's resolution order:

- `--profile NAME` supplies both server and PAT and is mutually exclusive with `--server-host`, `--server-port`, and `--auth`.
- Without explicit server/credential, the default profile is used when configured.
- `CVAT_ACCESS_TOKEN` counts as an explicit credential.
- `--auth USER[:PASS]` uses password auth; if the password is omitted, the SDK/CLI uses `PASS` or prompts.
- Server defaults to configured default server or `http://localhost`.

Profiles are stored in a secure local `auth.json` path owned by the user. If permissions are too broad, SDK and CLI raise `AuthStoreError`.

## Organization context

Set all requests to an organization with:

```python
client.organization_slug = "team-slug"
```

Or scope a block:

```python
with client.organization_context("team-slug"):
    tasks = client.tasks.list()
```

Set an empty organization slug only when the user explicitly wants the personal workspace. Leave it as `None` when no organization context should be sent.

## High-level repositories and entities

High-level repositories return entity objects whose fields mirror server data and whose methods combine one or more REST calls.

### Tasks

Common task operations:

```python
from cvat_sdk import models
from cvat_sdk.core.proxies.tasks import ResourceType

task = client.tasks.create_from_data(
    spec=models.TaskWriteRequest(
        name="task name",
        labels=[{"name": "car", "type": "rectangle"}],
    ),
    resource_type=ResourceType.LOCAL,
    resources=["image1.jpg", "image2.png"],
    data_params={"image_quality": 70, "sorting_method": "lexicographical"},
)

task = client.tasks.retrieve(task_id)
task.update({"name": "new name"})
task.fetch()                      # refresh local object from server
task.remove()                     # delete server task
jobs = task.get_jobs()
meta = task.get_meta()
labels = task.get_labels()
```

Data/resource notes:

- `ResourceType.LOCAL`: upload local files with multipart upload.
- `ResourceType.REMOTE`: server downloads URLs listed in `remote_files`.
- `ResourceType.SHARE`: server reads paths from its configured file share; pass `copy_data` in params when needed.
- `params` accepted by `upload_data()` include `chunk_size`, `copy_data`, `image_quality`, `sorting_method`, `start_frame`, `stop_frame`, `use_cache`, `use_zip_chunks`, `job_file_mapping`, `filename_pattern`, `cloud_storage_id`, `server_files_exclude`, `validation_params`, and `frame_step` (converted to `frame_filter=step=...`).

Task data access:

```python
task.download_frames([0, 10], outdir="frames", quality="compressed")
frame_bytes = task.get_frame(0, quality="original")
preview_bytes = task.get_preview()
chunk_bytes = task.download_chunk(0, output_file)
```

Task annotation/dataset operations:

```python
task.import_annotations("COCO 1.0", "annotations.zip", conv_mask_to_poly=True)
task.export_dataset("YOLO 1.1", "out.zip", include_images=False)
task.download_backup("task-backup.zip")
```

### Projects

```python
project = client.projects.create_from_dataset(
    spec=models.ProjectWriteRequest(
        name="project name",
        labels=[{"name": "car", "type": "rectangle"}],
    ),
    dataset_path="dataset.zip",
    dataset_format="CVAT 1.1",
)

project = client.projects.retrieve(project_id)
project.import_dataset("YOLO 1.1", "labels.zip")
annotations = project.get_annotations()
tasks = project.get_tasks()
labels = project.get_labels()
project.export_dataset("COCO 1.0", "project.zip", include_images=False)
project.download_backup("project-backup.zip")
```

### Low-level fallback

When the high-level layer does not expose a server endpoint, use the generated API client:

```python
about, _ = client.api_client.server_api.retrieve_about()
result, response = client.api_client.call_api(
    "/api/functions",
    "GET",
    _parse_response=False,
)
```

Prefer high-level repositories when available, because they handle polling, entity refresh, upload/download details, and object wrappers.

## Background operations

Many upload/import/export/backup operations return a request id internally and then poll until completion. `Client.wait_for_completion(rq_id, status_check_period=...)` raises `BackgroundRequestException` on a failed server request. When exposing long-running scripts, make the status check period configurable and log request ids if available.

## Compatibility and version checks

`Client` checks server version by default. The SDK supports the current minor and the next minor by major/minor compatibility. With `allow_unsupported_server=True`, incompatible versions warn rather than fail. If an SDK call behaves strangely, verify server and SDK versions first and consider installing the matching `cvat-sdk` package for the server.
