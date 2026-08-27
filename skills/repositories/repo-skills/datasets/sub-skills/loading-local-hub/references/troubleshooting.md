# Loading Troubleshooting

Use this checklist to diagnose loading failures without leaking tokens, forcing network access, or confusing raw data files with saved dataset snapshots.

## Missing or Ambiguous `data_files`

Symptoms:

- All rows appear under `train` when the user expected multiple splits.
- `load_dataset` cannot infer a builder or finds the wrong files.
- Files are silently skipped because a glob points at the wrong directory.

Fixes:

```python
data_files = {
    "train": "data/train/*.csv",
    "validation": "data/validation/*.csv",
    "test": "data/test.csv",
}
ds = load_dataset("csv", data_files=data_files)
```

- Prefer split mappings over bare strings or lists when split identity matters.
- Verify globs with the standard library before loading if local filesystem access is available.
- Use `data_dir` for a base subdirectory and `data_files` for selected files under that base.
- For archives, remote URLs, or nested paths, make the path pattern explicit and avoid assuming recursive discovery.

## Split and Config Mistakes

Symptoms:

- Error says a config name is required or invalid.
- Code receives a `DatasetDict` but expects a single `Dataset`.
- Code passes `split="validation"` but the dataset has no validation split.

Fixes:

- Use `load_dataset_builder(path, name=...)` to inspect the selected builder before loading rows.
- Treat `name` as the config/subset selector and `split` as the split selector; do not interchange them.
- Omit `split` when the caller wants all available splits as a dictionary-like object.
- Use exact split keys from metadata or builder inspection. Do not assume every dataset has `train`, `validation`, and `test`.

## Private Hub Auth and Tokens

Symptoms:

- `DatasetNotFound`, authorization, gated repository, or 401/403 errors for a known private dataset.
- Streaming private data fails while public data works.

Fixes:

```python
ds = load_dataset("namespace/private_dataset", split="train", token=True)
```

- Use `token=True` only when the user has already authenticated in the environment.
- If a literal token is required, read it from a secret source such as an environment variable and never print it.
- Confirm the user has accepted any gated dataset terms in the Hub UI when applicable.
- Confirm `revision` points to a branch/tag/commit the token can access.
- Do not run network calls during diagnosis unless the user permits network access.

## Network and Offline Mode

Symptoms:

- Offline mode errors mention missing cached files or inability to reach the Hub.
- A previously working Hub load fails with a new uncached `revision`.
- Remote URLs in `data_files` fail in a restricted environment.

Fixes:

- Treat Hub dataset ids and HTTP(S) `data_files` as network operations unless cached.
- Use local files or a `load_from_disk` snapshot for fully offline workflows.
- Keep `revision` pinned, but remember a pinned revision still needs to exist in cache for offline use.
- If the environment is intentionally offline, diagnose with local path checks and cache expectations rather than retrying network.

## Local Format Inference

Symptoms:

- A local directory loads with an unexpected packaged module.
- A raw file path is interpreted incorrectly.
- CSV separators, JSON nesting, or unsupported extensions cause bad rows.

Fixes:

- Prefer explicit packaged module names: `load_dataset("csv", data_files=...)`, `load_dataset("json", data_files=...)`, `load_dataset("parquet", data_files=...)`.
- Pass format-specific kwargs, such as CSV `sep` or JSON `field`, through `load_dataset`.
- Use explicit `features` when type inference would be ambiguous; route detailed feature work to `../../features-formats/SKILL.md`.
- Do not assume media/folder builders can decode optional formats without the corresponding optional dependencies.

## `load_from_disk` Path Mistakes

Symptoms:

- `load_from_disk` fails on a directory containing raw CSV/JSON/Parquet files.
- A path exists but lacks dataset snapshot metadata.
- A saved `DatasetDict` is treated like a single `Dataset`.

Fixes:

- Use `load_from_disk` only for directories produced by `save_to_disk`.
- Use `load_dataset` with a packaged module for raw files.
- Check whether the returned object is a `Dataset` or `DatasetDict` before indexing rows.
- For remote snapshots, pass required `storage_options` and avoid embedding credentials.

## `storage_options` Problems

Symptoms:

- `mock://`, `s3://`, `gs://`, or other fsspec paths fail while local paths work.
- Authentication or endpoint configuration is missing for remote files.
- Decoding fails because data files are read through a filesystem layer without the right options.

Fixes:

```python
ds = load_dataset(
    "text",
    data_files={"train": "s3://bucket/data/train.txt"},
    storage_options={"anon": False},
)
```

- Pass only the filesystem options needed by the backend.
- Source secrets from environment or runtime configuration, not committed code.
- Use the same storage options consistently for `load_dataset`, `load_dataset_builder`, builder preparation, and `load_from_disk` when they access the same remote filesystem.

## When to Route Elsewhere

- If loading succeeds and the task is to `map`, `filter`, `shuffle`, iterate streaming data, or use multiprocessing transforms, route to `../../processing-streaming/SKILL.md`.
- If the failure concerns feature casting, class labels, media decoding, pandas/NumPy/torch formatting, or schema mismatch, route to `../../features-formats/SKILL.md`.
- If the task involves cache deletion, pushing to Hub, dataset cards, sharing, or CLI commands, route to `../../sharing-cli-cache/SKILL.md`.
