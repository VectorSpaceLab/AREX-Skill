# CLI, Cache, Download, and Filesystem Reference

Use this reference for operational commands and cache/download controls around `datasets`.

## `datasets-cli` Commands

The verified console script is `datasets-cli` with these commands:

```bash
datasets-cli --help
datasets-cli env
datasets-cli test --help
datasets-cli delete_from_hub --help
```

### `datasets-cli env`

Use `datasets-cli env` for diagnostics. It prints versions for `datasets`, Python, platform, `huggingface_hub`, PyArrow, Pandas, and `fsspec`. It is safe and non-mutating, but still review output before sharing because platform details may reveal environment information.

### `datasets-cli test`

Use `datasets-cli test` to test dataset loading through a builder-style path:

```bash
datasets-cli test my_dataset --name default --cache_dir ./tmp-datasets-cache
```

Important flags:

- `--name`: Dataset config name.
- `--data_dir`: Manual data directory for supported builders.
- `--all_configs`: Test every builder config; do not combine with `--name`.
- `--save_info` / `--save_infos`: Save dataset info into a dataset card; this also ignores verifications.
- `--ignore_verifications`: Skip checksum and split checks.
- `--force_redownload`: Force download instead of reusing cache.
- `--clear_cache`: Remove downloaded files and builder cache after each config test; it requires an explicit `--cache_dir`.
- `--num_proc`: Parallel preparation where supported.

Safety notes:

- Prefer a dedicated temporary `--cache_dir` when using `--clear_cache`.
- Do not run `test` against untrusted dataset scripts without reviewing the loading path and execution mode.
- Use sibling loading/processing sub-skills when the failure is about `load_dataset`, builder code, streaming, or transforms rather than CLI operation.

### `datasets-cli delete_from_hub`

This command deletes a configuration from a supported Hub dataset and opens a PR for the deletion:

```bash
datasets-cli delete_from_hub USER_OR_ORG/DATASET_NAME CONFIG_NAME --revision main
```

Arguments:

- `dataset_id`: Hub dataset id such as `username/name` or `org/name`.
- `config_name`: Configuration to remove.
- `--revision`: Source branch/revision.
- `--token`: Hub token; prefer login/environment auth over literal tokens in command history.

Confirm the dataset id, config name, and revision before running. This command stages deletions for data files belonging to the selected config and updates `README.md` metadata; it is intentionally destructive even though the implementation creates a PR.

## Cache Directory Model

Datasets uses two relevant cache families:

- Hub raw-file cache: usually under the Hugging Face Hub cache and controlled by `HF_HUB_CACHE` or the broader `HF_HOME`.
- Datasets Arrow/cache data: usually under the Datasets cache and controlled by `HF_DATASETS_CACHE` or the broader `HF_HOME`.

Common environment variables:

```bash
export HF_HOME="/path/to/hf-cache-root"
export HF_DATASETS_CACHE="/path/to/datasets-arrow-cache"
export HF_HUB_CACHE="/path/to/hub-raw-cache"
export HF_DATASETS_IN_MEMORY_MAX_SIZE="0"
```

Use `HF_HOME` to relocate all Hugging Face caches together. Use `HF_DATASETS_CACHE` only for Datasets-generated Arrow/cache artifacts and set `HF_HUB_CACHE` separately when raw Hub downloads must move too.

## Per-call Cache and Redownload Controls

For `load_dataset`, pass `cache_dir` to control Datasets cache location:

```python
from datasets import load_dataset

ds = load_dataset("user_or_org/dataset_name", cache_dir="./tmp-datasets-cache")
```

Use `download_mode="force_redownload"` when stale raw/downloaded data must be refreshed. Use `Dataset.cleanup_cache_files()` to remove unused cache files for a loaded dataset object; it returns the number of removed files.

For transforms, use `load_from_cache_file=False` on `Dataset.map` when recomputation is required. Use `datasets.disable_caching()` only as a deliberate global behavior change; it can slow repeat work and remove reproducibility clues.

## `DownloadConfig`

`DownloadConfig` controls lower-level downloads and filesystem access. Important fields include:

- `cache_dir`: Override cache location.
- `force_download` / `resume_download` / `local_files_only`: Control network/cache behavior.
- `proxies`, `user_agent`, `max_retries`, `disable_tqdm`: HTTP and UX controls.
- `token`: Boolean or string token for Hub access; prefer `True` over literal secrets.
- `storage_options`: fsspec backend options for cloud/object stores and authenticated filesystems.
- `num_proc`: Parallel file downloads.
- `extract_compressed_file`, `force_extract`, `delete_extracted`, `extract_on_the_fly`: Archive extraction behavior.

Example with local-only behavior:

```python
from datasets import DownloadConfig, load_dataset

config = DownloadConfig(local_files_only=True, token=True)
ds = load_dataset("user_or_org/private_dataset", download_config=config)
```

Example with fsspec storage options:

```python
from datasets import DownloadConfig, load_dataset

config = DownloadConfig(storage_options={"s3": {"anon": False}})
ds = load_dataset("parquet", data_files="s3://bucket/path/*.parquet", download_config=config)
```

Optional filesystem packages such as `s3fs`, `gcsfs`, `adlfs`, or cloud SDKs are not guaranteed to be installed. Install only the backend needed by the target URI scheme.

## Offline and Local-files Behavior

Use offline mode when a workflow must not make network calls:

```bash
export HF_HUB_OFFLINE=1
```

For per-call behavior, prefer `DownloadConfig(local_files_only=True)` or API-specific local-files flags when available. Offline/local-only mode works only if required files and metadata already exist in the relevant caches or local paths.

Diagnose mixed local/URL/Hub workflows by separating each input source:

- Local files should resolve without network.
- Remote URLs need network unless already cached and addressed through the cache-aware path.
- Hub datasets need cached metadata, dataset files, and auth state when private.
- `storage_options` must match the actual URI protocol after compression or chained fsspec URLs are considered.

## Cloud and fsspec Notes

Datasets relies on `fsspec` for many filesystem operations and cloud storage integrations. Typical backends include S3, Google Cloud Storage, Azure, Oracle, HTTP(S), compression filesystems, and Hugging Face filesystem paths.

Operational guidance:

- Match `storage_options` to the protocol: for example `{"s3": {...}}` for `s3://` paths.
- Avoid putting secrets in notebook outputs, CLI logs, or dataset cards.
- Verify optional backend packages are installed before diagnosing Datasets itself.
- For large cloud imports, stage data in batches and use Hub upload or `push_to_hub` after creating Datasets objects.
- Route streaming and transformation of cloud-backed datasets to `../../processing-streaming/SKILL.md`.

## Safe Local Smoke Helper

Run `../scripts/cli_cache_smoke.py --help` to inspect available diagnostics. Its default mode prints planned checks and cache-related environment variables without network or mutation.
