# Data and Storage API Reference

This reference summarizes the ClearML dataset/storage APIs that are most useful to coding agents. Dataset methods require a configured ClearML backend unless the code path explicitly works with local paths only; the bundled scripts in this skill are offline helpers and do not import ClearML.

## `Dataset` Lifecycle

Import with:

```python
from clearml import Dataset
```

Primary creation and lookup signatures observed from the installed package:

```python
Dataset.create(
    dataset_name=None,
    dataset_project=None,
    dataset_tags=None,
    parent_datasets=None,
    use_current_task=False,
    dataset_version=None,
    output_uri=None,
    description=None,
) -> Dataset

Dataset.get(
    dataset_id=None,
    dataset_project=None,
    dataset_name=None,
    dataset_tags=None,
    only_completed=False,
    only_published=False,
    include_archived=False,
    auto_create=False,
    writable_copy=False,
    dataset_version=None,
    alias=None,
    overridable=False,
    shallow_search=False,
    silence_alias_warnings=False,
    **kwargs,
) -> Dataset
```

Use `Dataset.create()` for a mutable dataset version. Pass `parent_datasets=[PARENT_ID, ...]` when the new version should inherit from one or more finalized versions. Pass `dataset_version="1.2.0"` for deterministic version selection and `output_uri="s3://..."`, `"gs://..."`, `"azure://..."`, or a shared path when the dataset files should upload outside the default files server.

Use `Dataset.get(dataset_id="...")` when the user has an ID. Use `Dataset.get(dataset_project="...", dataset_name="...", dataset_version="...")` when the ID is unknown. Without an explicit version, ClearML resolves the highest semantic version if available, otherwise the most recently updated dataset.

## Mutating Dataset Contents

Important signatures:

```python
Dataset.add_files(
    path,
    wildcard=None,
    local_base_folder=None,
    dataset_path=None,
    recursive=True,
    verbose=False,
    max_workers=None,
) -> int

Dataset.sync_folder(local_path, dataset_path=None, verbose=False) -> (int, int, int)

Dataset.upload(
    show_progress=True,
    verbose=False,
    output_url=None,
    compression=None,
    chunk_size=None,
    max_workers=None,
    retries=3,
    preview=True,
    upload_as_external_links=False,
) -> Optional[bool]

Dataset.finalize(verbose=False, raise_on_error=True, auto_upload=False) -> bool
```

Guidance:

- `add_files()` adds local files or folders to a mutable dataset. Use `dataset_path` to place files under a logical dataset folder such as `train` or `labels`.
- `sync_folder()` compares a local folder with the dataset path and returns `(removed, added, modified)` counts.
- `upload()` transfers pending dataset changes to the default storage or `output_url`.
- `finalize()` closes the dataset version. After finalization, create a child dataset instead of mutating the closed version.
- `finalize(auto_upload=True)` is convenient in scripts, but separate `upload()` then `finalize()` makes troubleshooting easier.

For external links, the CLI exposes `clearml-data add --links`; the underlying Dataset API includes external-file/link entries and upload can also record local files as external links with `upload_as_external_links=True` when the storage design calls for references rather than copied objects.

## Retrieval, Verification, and Diffs

Useful methods:

```python
Dataset.get_local_copy(
    use_soft_links=None,
    part=None,
    num_parts=None,
    raise_on_error=True,
    max_workers=None,
    files=None,
) -> str

Dataset.get_mutable_local_copy(target_folder, overwrite=False, part=None, num_parts=None, max_workers=None) -> str
Dataset.list_files(dataset_path=None, recursive=True) -> list[str]
Dataset.list_added_files(dataset_id=None) -> list[str]
Dataset.list_modified_files(dataset_id=None) -> list[str]
Dataset.list_removed_files(dataset_id=None) -> list[str]
Dataset.verify_dataset_hash(local_copy_path=None, skip_hash=False, verbose=False) -> list[str]
Dataset.get_default_storage() -> Optional[str]
Dataset.is_dirty() -> bool
Dataset.is_final() -> bool
```

Use `get_local_copy()` for read-only cached materialization. Use `get_mutable_local_copy()` when the caller needs a writable directory copy. Use `part` and `num_parts` for sharded retrieval; the smallest practical shard is a dataset chunk or parent chunk.

`is_dirty()` means local changes are pending upload. A dirty dataset cannot be finalized unless the code or CLI uploads first. `is_final()` means the dataset is completed/published/failed and should no longer be treated as mutable.

## Dataset Management Helpers

Common class methods:

```python
Dataset.list_datasets(dataset_project=None, partial_name=None, tags=None, ids=None, only_completed=True, recursive_project_search=True)
Dataset.squash(dataset_name, dataset_ids=None, output_url=None)
Dataset.delete(dataset_id=None, dataset_project=None, dataset_name=None, force=False, dataset_version=None, entire_dataset=False)
Dataset.rename(new_dataset_name, dataset_project, dataset_name)
Dataset.move_to_project(new_dataset_project, dataset_project, dataset_name)
```

Use `list_datasets()` for discovery. Use `squash()` when several versions should be merged into a single dataset version. Treat delete/rename/move as destructive administrative operations; request user confirmation outside this skill when the user has not clearly asked for them.

## `StorageManager`

Import with:

```python
from clearml import StorageManager
```

Core signatures:

```python
StorageManager.get_local_copy(remote_url, cache_context=None, extract_archive=True, name=None, force_download=False) -> Optional[str]
StorageManager.upload_file(local_file, remote_url, wait_for_upload=True, retries=None) -> str
StorageManager.upload_folder(local_folder, remote_url, match_wildcard=None, retries=None) -> Optional[str]
StorageManager.download_file(remote_url, local_folder=None, overwrite=False, skip_zero_size_check=False, silence_errors=False) -> Optional[str]
StorageManager.download_folder(remote_url, local_folder=None, match_wildcard=None, overwrite=False, skip_zero_size_check=False, silence_errors=False, max_workers=None) -> Optional[str]
StorageManager.exists_file(remote_url) -> bool
StorageManager.get_file_size_bytes(remote_url, silence_errors=False) -> Optional[int]
StorageManager.list(remote_url, return_full_path=False, with_metadata=False, read_hash=False) -> Optional[list]
StorageManager.get_metadata(remote_url, return_full_path=False, read_hash=False) -> Optional[dict]
StorageManager.set_cache_file_limit(cache_file_limit, cache_context=None) -> int
```

Use `StorageManager` for direct object/file handling outside dataset versioning. It supports HTTP(S), S3, Google Storage, Azure Blob, and shared filesystems where the proper dependencies and credentials are configured.

Cache behavior:

- `get_local_copy()` returns a direct local path when possible; otherwise it downloads into a ClearML cache.
- The default cache context keeps up to 100 files; `set_cache_file_limit()` changes the file-count limit, not a byte-size quota.
- `extract_archive=True` extracts supported archives such as zip files and returns the extracted path.
- `force_download=True` refreshes an existing cached object.

## Storage Backends and Extras

Storage URI schemes and package support:

- `s3://bucket/path` requires the S3 extra and provider credentials, commonly `clearml[s3]`.
- `gs://bucket/path` requires the Google Storage extra, commonly `clearml[gs]`.
- `azure://container/path` requires the Azure extra, commonly `clearml[azure]`.
- Shared filesystem paths such as `/mnt/shared/data` require that all producers and consumers can access the same path.
- The default ClearML files server can be used when no explicit storage URI is provided.

Do not embed secrets in code examples. Use ClearML configuration, environment-level provider credentials, or cloud identity mechanisms.

## HyperDataset and DataView Routing

HyperDataset APIs are for advanced dataset collections, annotation sources, and server-backed DataView queries. Route to this section when the user mentions `HyperDataset`, `DataView`, `DataEntry`, `DataSubEntry`, frame queries, source queries, ROI filtering, or annotation-task-backed dataset versions.

Representative signatures:

```python
from clearml import HyperDataset
from clearml.hyperdatasets import DataView

HyperDataset.get(dataset_name=None, version_name=None, project_name=None, *, dataset_id=None, version_id=None)
HyperDataset.exists(dataset_name=None, version_name=None, project_name=None, *, dataset_id=None, version_id=None) -> bool
HyperDataset.list(project_name=None, partial_name=None, tags=None, ids=None, recursive_project_search=True, include_archived=True) -> list[dict]
hyper_dataset.commit_version(publish=False, force=False, calculate_stats=True, override_stats=None, publishing_task=None)
hyper_dataset.publish_version(force=False, publishing_task=None)

DataView(name=None, description=None, tags=None, iteration_order="sequential", iteration_infinite=False, iteration_random_seed=None, iteration_limit=None, auto_connect_with_task=True, project_name=None)
data_view.add_query(project_id="*", dataset_id="*", version_id="*", source_query=None, frame_query=None, weight=1.0, filter_by_roi=None, label_rules=None)
```

Use regular `Dataset` for ordinary versioned files and folders. Use HyperDataset/DataView when the workflow depends on querying annotated entries, source metadata, frame metadata, or sampling rules rather than copying folder trees.
