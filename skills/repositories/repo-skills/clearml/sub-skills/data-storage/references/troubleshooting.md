# Data and Storage Troubleshooting

Use this guide when ClearML dataset creation, upload/finalization, retrieval, cache, or storage behavior is confusing.

## Missing Dataset ID

Symptoms:

- `clearml-data` prints `Dataset ID not specified, add --id <dataset_id>`.
- A command unexpectedly targets an old dataset.
- Commands work in one shell but fail or target the wrong dataset in another.

Cause: `clearml-data` restores the last dataset ID from `~/.clearml_data.json` when `--id` is omitted. `create` writes this state, and successful `close`, `publish`, `delete`, `rename`, or `move` may clear it.

Fix:

```bash
clearml-data create --project PROJECT --name NAME --version VERSION
# Copy the printed id=... value.
clearml-data add --id DATASET_ID --files data
clearml-data upload --id DATASET_ID --verbose
clearml-data close --id DATASET_ID --disable-upload --verbose
```

If state is stale, do not rely on implicit state. Pass `--id` explicitly or inspect/remove the state file manually outside automated instructions.

## Pending Uploads on Finalize

Symptoms:

- `clearml-data close --disable-upload` fails with pending uploads.
- `Dataset.finalize()` raises or returns failure because files are dirty.
- A dataset is created and files are added but downstream users cannot retrieve them.

Cause: files added by `add_files()`/`clearml-data add` are not necessarily uploaded yet. Finalization without upload is invalid when the dataset is dirty.

Fix in Python:

```python
if dataset.is_dirty():
    dataset.upload(verbose=True)
dataset.finalize(verbose=True)
```

Fix in CLI:

```bash
clearml-data upload --id DATASET_ID --storage STORAGE_URI --verbose
clearml-data close --id DATASET_ID --disable-upload --verbose
```

Alternative: omit `--disable-upload` on `close` if automatic upload is acceptable.

## Storage Extra or Credential Failures

Symptoms:

- S3, Google Storage, or Azure upload/download fails at import or runtime.
- `StorageManager.list()` returns `None` or logs a provider error.
- Dataset upload to a cloud URI fails while default files-server upload works.

Checks:

- `s3://...` needs the S3 extra, commonly `clearml[s3]`, and valid AWS-compatible credentials.
- `gs://...` needs the Google Storage extra, commonly `clearml[gs]`, and Google credentials.
- `azure://...` needs the Azure extra, commonly `clearml[azure]`, and Azure Blob credentials.
- Shared filesystem paths require the same mount/path to exist for every machine that uploads or consumes the dataset.

Fix: install the matching extra in the runtime environment and configure credentials through ClearML/provider configuration. Do not place access keys in command examples or checked-in code.

## Deprecated `--output-uri`

Symptoms: user examples mix `--output-uri` and `--storage`.

Cause: `clearml-data create` and `sync` still accept `--output-uri`, but help text marks it deprecated in favor of `--storage`.

Fix: generate new CLI commands with `--storage`. In Python, `Dataset.create(output_uri=...)` remains the API parameter; for CLI, prefer `--storage`.

## Parent/Version Mistakes

Symptoms:

- A child dataset does not include expected files.
- `Dataset.get()` returns a different dataset than expected.
- `clearml-data compare` shows unexpected additions/removals.

Causes and fixes:

- Parent IDs were omitted or wrong: pass `parent_datasets=["PARENT_ID"]` in Python or `--parents PARENT_ID ...` in CLI.
- Parent was not finalized: finalize parent versions before making children.
- Version resolution was ambiguous: pass `dataset_version` in Python or `--version` in CLI, or use explicit `dataset_id`.
- New files were placed at the wrong logical path: pass `dataset_path`/`--dataset-folder` explicitly.

## `sync` Finalized Too Early

Symptoms:

- `clearml-data sync` created, uploaded, and closed a dataset before the user could add more files.
- A dataset cannot be modified after `sync`.

Cause: `sync` uploads and finalizes by default unless `--skip-close` is set.

Fix:

```bash
clearml-data sync --folder data/train --project PROJECT --name NAME --skip-close
clearml-data add --id DATASET_ID --dataset-folder labels --files labels
clearml-data upload --id DATASET_ID --verbose
clearml-data close --id DATASET_ID --disable-upload --verbose
```

## Local Copy and Cache Pitfalls

Symptoms:

- Modifying a folder from `Dataset.get_local_copy()` corrupts later assumptions.
- A downloaded object appears stale.
- Cached files disappear between runs.

Causes and fixes:

- `get_local_copy()` returns a read-only/cache-oriented copy. Use `get_mutable_local_copy(target_folder=..., overwrite=True)` or `clearml-data get --copy ...` for writable work.
- `StorageManager.get_local_copy()` caches up to a file-count limit per context; older entries can be evicted. Use `StorageManager.set_cache_file_limit()` for larger file counts.
- Use `force_download=True` in `StorageManager.get_local_copy()` when a remote object changed at the same URI.
- `extract_archive=True` can return an extracted folder instead of the archive file; set `extract_archive=False` when the caller needs the original archive.

## External Links Do Not Download

Symptoms:

- Dataset metadata lists links but consumers cannot read the data.
- Upload appears fast because files were not copied.

Cause: `clearml-data add --links` records remote references. Consumers still need credentials and network access to those URIs.

Fix: use `--links` only when shared remote access is intentional. Use local `--files` plus `upload` when ClearML-managed copies are required.

## Chunk Size and Worker Surprises

Symptoms:

- Upload is slow to cloud storage.
- Upload memory/parallelism is not what the user expects.

Notes:

- CLI upload/close/sync default `--chunk-size` is 512 MB; pass `--chunk-size -1` for a single chunk.
- `--max-workers` controls upload/add/get worker threads where supported.
- CLI help notes cloud uploads default to one worker for cloud schemes unless overridden.

## HyperDataset/DataView Confusion

Symptoms:

- User asks about frame queries, annotation labels, ROI filtering, source queries, or DataView iteration.
- Regular `Dataset` folder examples do not fit the request.

Fix: route to HyperDataset/DataView APIs in `api-reference.md`. Use `Dataset` for ordinary file/folder versioning; use HyperDataset/DataView for server-backed annotated entries and query/sampling definitions.

## Safe Recovery Checklist

Before finalizing a data answer, confirm:

- The user has either a dataset ID or an explicit project/name/version lookup.
- Parent dataset IDs are final and intentionally selected.
- The command plan includes `--id` after create unless stateful CLI behavior is intended.
- Storage URI scheme has matching extras and credentials.
- The plan distinguishes external links from uploaded copies.
- `upload` happens before `close --disable-upload`, or `close` is allowed to auto-upload.
- Writable local work uses `get_mutable_local_copy()` or `clearml-data get --copy`, not the read-only cache path.
