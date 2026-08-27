# CVAT SDK workflows

## Build a profile-compatible automation script

Use this pattern when a Python script should honor the same `--profile`, `--server-host`, `--auth`, `CVAT_ACCESS_TOKEN`, `--insecure`, and `--organization` behavior as `cvat-cli`.

```python
import argparse
from cvat_sdk import configure_client_auth_arguments, make_client_from_cli

parser = argparse.ArgumentParser()
configure_client_auth_arguments(parser)
parser.add_argument("--task-id", type=int, required=True)
args = parser.parse_args()

with make_client_from_cli(args) as client:
    task = client.tasks.retrieve(args.task_id)
    print(task.name, task.size)
```

This is safer than hard-coding credentials and lets operators reuse profiles created by `cvat-cli profile create`.

## Create a task from local files

```python
from cvat_sdk import make_client, models
from cvat_sdk.core.proxies.tasks import ResourceType

labels = [
    {
        "name": "vehicle",
        "type": "rectangle",
        "attributes": [
            {
                "name": "occluded",
                "mutable": True,
                "input_type": "checkbox",
                "default_value": "false",
                "values": [],
            }
        ],
    }
]

with make_client("https://cvat.example.com", access_token=token) as client:
    task = client.tasks.create_from_data(
        spec=models.TaskWriteRequest(name="sdk-demo", labels=labels),
        resource_type=ResourceType.LOCAL,
        resources=["frame001.jpg", "frame002.jpg"],
        data_params={
            "image_quality": 70,
            "sorting_method": "lexicographical",
            "use_cache": True,
        },
    )
    print(task.id)
```

Use `ResourceType.REMOTE` for URLs and `ResourceType.SHARE` for server-share files. When uploading annotations during creation, pass `annotation_path`, `annotation_format`, and `status_check_period` to `create_from_data()`.

## Upload data to an existing task

```python
from cvat_sdk.core.proxies.tasks import ResourceType

task = client.tasks.retrieve(task_id)
task.upload_data(
    ["more1.jpg", "more2.jpg"],
    resource_type=ResourceType.LOCAL,
    params={"image_quality": 70, "sorting_method": "natural"},
)
```

If `wait_for_completion=False`, the server processes data asynchronously and the local `Task` object will not refresh automatically.

## Import and export annotations or datasets

Task annotation import:

```python
task = client.tasks.retrieve(task_id)
task.import_annotations("YOLO 1.1", "labels.zip", conv_mask_to_poly=False)
```

Task dataset export:

```python
task.export_dataset("COCO 1.0", "task-coco.zip", include_images=False)
```

Project import/export:

```python
project = client.projects.retrieve(project_id)
project.import_dataset("CVAT 1.1", "project-dataset.zip")
project.export_dataset("Datumaro 1.0", "project-datumaro.zip", include_images=True)
```

Format selection and caveats live in `../dataset-ops/references/formats-and-data-flows.md`.

## Download frames and previews

```python
from pathlib import Path

task = client.tasks.retrieve(task_id)
Path("frames").mkdir(exist_ok=True)
task.download_frames([0, 10, 20], outdir="frames", quality="compressed")

with open("preview.jpg", "wb") as f:
    f.write(task.get_preview().read())
```

Use `quality="original"` when exact image pixels are required for model evaluation, and `quality="compressed"` for lightweight QA thumbnails.

## Back up and restore resources

```python
task = client.tasks.retrieve(task_id)
task.download_backup("task-backup.zip")
restored = client.tasks.create_from_backup("task-backup.zip")

project = client.projects.retrieve(project_id)
project.download_backup("project-backup.zip")
restored_project = client.projects.create_from_backup("project-backup.zip")
```

Backups can contain server-specific metadata. Use them for CVAT-to-CVAT restore; use dataset export formats for ML training pipelines or external tools.

## Work inside an organization

```python
client.organization_slug = "team-slug"
print([task.id for task in client.tasks.list()])

with client.organization_context("other-team"):
    print([project.id for project in client.projects.list()])
```

Organization context affects list/create/retrieve operations. If a resource appears missing, verify whether it belongs to the personal workspace or a team workspace.

## Handle background failures

High-level upload/import/export helpers wait for server background requests by default. Wrap them and report actionable failures:

```python
from cvat_sdk.core.exceptions import BackgroundRequestException

try:
    task.import_annotations("COCO 1.0", "annotations.zip")
except BackgroundRequestException as exc:
    raise SystemExit(f"CVAT background import failed: {exc}")
```

Common causes: wrong format name, malformed archive layout, labels not matching, server storage permissions, or insufficient worker capacity.

## When to use low-level API

Use `client.api_client` only when no high-level method exists or when a new server endpoint has not been wrapped. Keep low-level calls narrow and document endpoint/method explicitly:

```python
_, response = client.api_client.call_api(
    "/api/functions",
    "GET",
    _parse_response=False,
)
print(response.status)
```

If the low-level object models are needed, import them from `cvat_sdk.models` rather than relying on private generated module paths.
