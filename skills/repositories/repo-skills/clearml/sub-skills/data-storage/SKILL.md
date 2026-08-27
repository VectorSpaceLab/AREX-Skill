---
name: data-storage
description: "Use ClearML Dataset, StorageManager, clearml-data CLI, storage
  backends, cache behavior, and HyperDataset/DataView routing for dataset
  versioning and retrieval."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ClearML Data and Storage

Use this sub-skill when the user needs to create, version, upload, finalize, retrieve, verify, or troubleshoot ClearML datasets, build `clearml-data` commands, manage remote storage URIs, or reason about `StorageManager` caching and HyperDataset/DataView routing.

## Route First

- Use this sub-skill for `Dataset`, `StorageManager`, `clearml-data`, dataset parents/versions, local copies, external links, storage credentials/extras, cache limits, and HyperDataset/DataView selection.
- Route experiment task setup, scalar/image reporting, and non-dataset `Task.upload_artifact()` usage to `../experiment-tracking/SKILL.md`.
- Route queued task execution, agents, `clearml-task`, `Task.execute_remotely()`, or remote job launch to `../remote-execution-cli/SKILL.md`.
- Route pipelines that consume datasets as pipeline inputs or steps to `../automation-pipelines/SKILL.md`.

## Core Dataset Pattern

Use a two-stage mental model: a dataset version is mutable until finalized, and after finalization it should be retrieved or used as a parent for a new version.

```python
from clearml import Dataset

base = Dataset.create(
    dataset_project="datasets/examples",
    dataset_name="images",
    dataset_version="1.0.0",
    output_uri="s3://bucket/clearml/images",
)
base.add_files(path="data/train", dataset_path="train")
base.upload(output_url="s3://bucket/clearml/images", verbose=True)
base.finalize()

child = Dataset.create(
    dataset_project="datasets/examples",
    dataset_name="images",
    dataset_version="1.1.0",
    parent_datasets=[base.id],
)
child.sync_folder(local_path="data/train", dataset_path="train", verbose=True)
child.upload(verbose=True)
child.finalize()
```

Prefer explicit IDs after creation. `Dataset.get()` can search by project/name/version, but `dataset_id` avoids ambiguity when multiple semantic versions or recent updates match.

## CLI Planning

Use `clearml-data` when the user wants shell commands or quick dataset lifecycle operations. The CLI stores the most recent dataset ID in `~/.clearml_data.json`; commands without `--id` may silently target the last accessed dataset, so production instructions should include `--id` after `create` unless the user intentionally wants one-shell stateful use.

```bash
clearml-data create --project datasets/examples --name images --version 1.0.0 --storage s3://bucket/clearml/images
clearml-data add --id DATASET_ID --dataset-folder train --files data/train
clearml-data upload --id DATASET_ID --storage s3://bucket/clearml/images --verbose
clearml-data close --id DATASET_ID --verbose
```

Use `scripts/dataset_cli_plan.py` to generate safe command sequences without running ClearML calls. Use `scripts/validate_dataset_plan.py` to check JSON plan invariants before translating a plan to Python or CLI.

## Storage Guidance

- `Dataset.create(..., output_uri=...)`, `Dataset.upload(output_url=...)`, and CLI `--storage` accept `s3://...`, `gs://...`, `azure://...`, a shared filesystem path, or the default ClearML files server.
- Cloud storage support requires the matching package extras: install ClearML with `s3`, `gs`, or `azure` extras when those schemes are used.
- Credentials are read from ClearML configuration and provider defaults; do not put secrets in generated commands, scripts, dataset names, or skill content.
- Use `StorageManager.get_local_copy()` for remote file caching/downloading and `StorageManager.upload_file()` or `upload_folder()` for direct storage operations that are not dataset-versioning workflows.

## References

- `references/api-reference.md` documents Dataset, StorageManager, and HyperDataset/DataView signatures and behavior notes.
- `references/cli-reference.md` documents `clearml-data` subcommands, required flags, state behavior, and safe command construction.
- `references/workflows.md` gives Python and CLI workflows for create/add/sync/upload/finalize/get/parents/external links.
- `references/troubleshooting.md` covers credentials, storage extras, stale CLI state, missing IDs, pending uploads, parent mistakes, and cache/local-copy pitfalls.
- `scripts/dataset_cli_plan.py` builds offline `clearml-data` command plans.
- `scripts/validate_dataset_plan.py` validates JSON dataset plan invariants with the Python standard library only.
