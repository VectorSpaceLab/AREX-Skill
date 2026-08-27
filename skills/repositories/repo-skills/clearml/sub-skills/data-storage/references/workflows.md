# Data and Storage Workflows

These workflows are self-contained patterns for ClearML dataset versioning, storage access, and retrieval. Replace placeholder names, IDs, and URIs with user-provided values.

## Python: Create, Upload, Finalize

```python
from clearml import Dataset

archive = Dataset.create(
    dataset_project="datasets/examples",
    dataset_name="csv-archive",
    dataset_version="1.0.0",
    output_uri="s3://bucket/clearml/csv-archive",
    description="CSV archive dataset",
)
added = archive.add_files(path="data/csv", dataset_path="raw", verbose=True)
print(f"added {added} files")
archive.upload(output_url="s3://bucket/clearml/csv-archive", verbose=True)
archive.finalize(verbose=True)
print(archive.id)
```

Use this when the user wants explicit Python code and can run against a configured ClearML backend. Keep `output_uri` and `upload(output_url=...)` aligned unless the user intentionally changes storage between creation and upload.

## Python: Parent/Child Version

```python
from clearml import Dataset

parent = Dataset.get(dataset_id="PARENT_DATASET_ID")
child = Dataset.create(
    dataset_project="datasets/examples",
    dataset_name="csv-archive",
    dataset_version="1.1.0",
    parent_datasets=[parent.id],
)
child.add_files(path="patches/new-files", dataset_path="raw", verbose=True)
child.upload(verbose=True)
child.finalize(verbose=True)
```

Use parent IDs rather than names when possible. A parent should already be finalized; otherwise downstream retrieval and comparison may be unstable.

## Python: Multiple Parents

```python
from clearml import Dataset

merged = Dataset.create(
    dataset_project="datasets/examples",
    dataset_name="train-test-combined",
    dataset_version="2.0.0",
    parent_datasets=["TRAIN_DATASET_ID", "TEST_DATASET_ID"],
    output_uri="s3://bucket/clearml/train-test-combined",
)
merged.finalize(auto_upload=True)
```

Use this when the child only merges existing parents and adds no local files. If adding new files, call `add_files()` or `sync_folder()` before finalization.

## Python: Sync a Folder Before Closing

```python
from clearml import Dataset

ds = Dataset.get(dataset_id="DATASET_ID")
removed, added, modified = ds.sync_folder(
    local_path="data/train",
    dataset_path="train",
    verbose=True,
)
if removed or added or modified:
    ds.upload(verbose=True)
ds.finalize(verbose=True)
```

Use `sync_folder()` when local changes should mirror a folder tree and removals matter. Use `add_files()` when only additions are expected.

## Python: Retrieve a Dataset

```python
from clearml import Dataset

ds = Dataset.get(dataset_id="DATASET_ID", only_completed=True)
local_read_only = ds.get_local_copy()
print(local_read_only)

local_writable = ds.get_mutable_local_copy(target_folder="working-copy", overwrite=True)
print(local_writable)
```

Use `get_local_copy()` for consumers that should not mutate the cache. Use `get_mutable_local_copy()` when a downstream process writes into the folder.

## Python: Direct Storage Operations

```python
from clearml import StorageManager

local_zip = StorageManager.get_local_copy(
    remote_url="https://example.com/data.zip",
    cache_context="datasets",
    extract_archive=True,
)
print(local_zip)

remote = StorageManager.upload_file(
    local_file="reports/manifest.json",
    remote_url="s3://bucket/clearml/manifests/manifest.json",
)
print(remote)
```

Use `StorageManager` for direct object operations. If the user is versioning a dataset, prefer `Dataset` APIs and use `StorageManager` only for auxiliary downloads/uploads.

## CLI: Separate Create/Add/Upload/Close

```bash
clearml-data create --project datasets/examples --name csv-archive --version 1.0.0 --storage s3://bucket/clearml/csv-archive
clearml-data add --id DATASET_ID --dataset-folder raw --files data/csv --verbose
clearml-data upload --id DATASET_ID --storage s3://bucket/clearml/csv-archive --verbose
clearml-data close --id DATASET_ID --disable-upload --verbose
```

Use this when each step should be inspectable. `close --disable-upload` ensures finalization fails if uploads are still pending.

## CLI: One-Command Folder Sync

```bash
clearml-data sync \
  --folder data/train \
  --dataset-folder train \
  --project datasets/examples \
  --name images \
  --version 1.0.0 \
  --storage s3://bucket/clearml/images \
  --verbose
```

By default, `sync` uploads and finalizes after syncing. Add `--skip-close` to leave the dataset open for review or additional `add` commands.

## CLI: Parent/Child with No Upload Execution

When the user asks only for commands and explicitly says not to run uploads, provide a dry plan:

```bash
clearml-data create --project datasets/examples --name images --version 1.1.0 --parents PARENT_A_ID PARENT_B_ID --storage s3://bucket/clearml/images
clearml-data add --id CHILD_DATASET_ID --dataset-folder train --files local/train
clearml-data add --id CHILD_DATASET_ID --dataset-folder test --files local/test
# Optional later, when ready:
clearml-data upload --id CHILD_DATASET_ID --storage s3://bucket/clearml/images --verbose
clearml-data close --id CHILD_DATASET_ID --disable-upload --verbose
```

If the child dataset ID is not known until `create` runs, clearly mark `CHILD_DATASET_ID` as the ID printed by the create command.

## CLI: External Links

```bash
clearml-data create --project datasets/examples --name linked-raw --version 1.0.0
clearml-data add --id DATASET_ID --dataset-folder raw --links s3://bucket/raw-images gs://other-bucket/raw-labels
clearml-data close --id DATASET_ID --verbose
```

Use links when data is already in object storage and ClearML should track references. Make sure all consumers have credentials to read the linked URIs.

## CLI: Retrieval and Verification

```bash
clearml-data get --id DATASET_ID --copy dataset-copy --overwrite
clearml-data verify --id DATASET_ID --folder dataset-copy --verbose
clearml-data list --id DATASET_ID --filter "train/*.jpg"
```

Use `--filesize` in `verify` only when hash checks are too expensive or unavailable; it is weaker than full hash verification.

## Offline Planning with Bundled Scripts

Build a no-execution command plan:

```bash
python scripts/dataset_cli_plan.py \
  --project datasets/examples \
  --name images \
  --version 1.1.0 \
  --parent PARENT_A_ID \
  --parent PARENT_B_ID \
  --storage s3://bucket/clearml/images \
  --add train=local/train \
  --add test=local/test \
  --include-upload \
  --include-close
```

Validate a JSON plan:

```bash
python scripts/validate_dataset_plan.py plan.json
```

The planner and validator are safe for design review because they do not import ClearML, read credentials, or contact a backend.

## Choosing Between APIs

- Choose `Dataset` when the primary unit is a versioned dataset with metadata, parents, upload/finalize state, or retrieval by dataset ID.
- Choose `clearml-data` when the user asks for shell commands, quick dataset operations, or folder sync without writing Python.
- Choose `StorageManager` when the user needs direct object storage download/upload/cache behavior outside dataset versioning.
- Choose HyperDataset/DataView when the user mentions frame/source/annotation queries or needs to sample/query annotated entries rather than file trees.
