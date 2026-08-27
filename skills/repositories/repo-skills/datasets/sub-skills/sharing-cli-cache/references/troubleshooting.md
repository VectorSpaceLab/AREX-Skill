# Sharing, CLI, Cache, and Filesystem Troubleshooting

Start by classifying the failure as auth/permission, repository/card structure, upload/sharding, CLI misuse, cache/offline behavior, or filesystem/storage options. Then use the targeted section below.

## Auth, Token, and Private Repository Errors

Symptoms include 401/403 responses, private dataset not found, inability to push, or `RepositoryNotFoundError` for a repo that exists.

Checks:

- Confirm the token has write permission for uploads and delete/config PR operations.
- Prefer `token=True` or a logged-in Hub token rather than pasting token strings.
- Confirm `repo_id` includes the organization/user namespace when uploading to an org.
- For private loads, pass auth through the relevant API, for example `token=True` or `DownloadConfig(token=True)`.
- Verify the token belongs to an account with access to the private repository and the target revision.
- If OS credential helpers are involved, stale credentials can override the intended token; refresh the Hub login.

Do not print full tokens in debugging output. Redact all secrets before sharing logs.

## Dataset Card and Metadata Issues

Symptoms include missing configs in the Hub UI, wrong default config, dataset viewer not recognizing splits, or poor discoverability.

Checks:

- Ensure `README.md` starts with valid YAML frontmatter delimited by `---`.
- Include `configs` when automatic split/config detection is insufficient.
- Always include `config_name` in explicit configs, even if there is only one config.
- Use `default: true` on the intended default config in multi-config cards.
- Keep metadata such as license, language, task category, and dataset size accurate.
- Avoid stale `dataset_info` or `config_names` entries after deleting or renaming configs.

Use `../scripts/dataset_card_minimal.md` as a starting point, then fill in responsible-use and licensing details before publishing.

## Repository Structure, `data_dir`, and `config_name` Mismatches

Symptoms include missing files, all files loaded as one split, wrong config loaded, or a pushed config overwriting another config's files.

Checks:

- Match `config_name` in `push_to_hub` with the README `configs` entry and expected load call.
- Use distinct `data_dir` values for multiple configs if their generated files should not collide.
- Validate glob paths in README YAML against repository file names.
- Check split names in file names or YAML; automatic detection relies on recognized delimiters and split patterns.
- Route schema/data type failures to `../../features-formats/SKILL.md`; route loading API failures to `../../loading-local-hub/SKILL.md`.

## Upload Sharding and Embedded Files

Symptoms include upload timeouts, too many requests, repeated commits, broken media references, or missing external files after publishing.

Checks:

- Reduce shard count or increase `max_shard_size` when too many shards/commits stress the Hub.
- Retry interrupted large uploads; already-uploaded shards can often be skipped by content hash.
- Keep `embed_external_files=True` when image/audio/other external file references must survive outside the local machine.
- Use `num_shards` only when exact shard layout matters; otherwise prefer `max_shard_size`.
- Use `create_pr=True` for large/risky uploads so reviewers can inspect repository structure before merge.
- Upgrade to a recent Datasets version when encountering Hub rate-limit behavior known to affect older versions.

## `datasets-cli test` Problems

Symptoms include unexpected config selection, verification failures, or cache deletion surprises.

Checks:

- Do not combine `--name` and `--all_configs`.
- Use a dedicated `--cache_dir` for reproducible CLI tests.
- `--clear_cache` requires `--cache_dir` and deletes the builder/download cache under that directory.
- `--save_info` / `--save_infos` writes dataset card info and ignores verifications.
- `--force_redownload` bypasses cache reuse for downloads.

If the issue is in builder code, dataset loading semantics, or local/Hub file resolution, switch to `../../loading-local-hub/SKILL.md`.

## Offline and Cache Surprises

Symptoms include attempted network access in offline mode, stale data after updates, unexpected cache locations, or failures when mixing local files, URLs, and Hub datasets.

Checks:

- Set `HF_HUB_OFFLINE=1` to block Hub/network access globally for Hugging Face Hub calls.
- Use `DownloadConfig(local_files_only=True)` when only a specific load/download should avoid the network.
- Remember that `HF_DATASETS_CACHE` controls Datasets Arrow/cache artifacts while `HF_HUB_CACHE` controls raw Hub downloads. Use `HF_HOME` to move both together.
- Use `download_mode="force_redownload"` or `DownloadConfig(force_download=True)` when data must be refreshed.
- Confirm all required remote metadata and files are already cached before expecting offline operation to succeed.
- Keep local files, arbitrary URLs, and Hub IDs separate in diagnostics; each has different cache and auth behavior.

Use `../scripts/cli_cache_smoke.py` for a safe summary of cache-related environment variables and CLI availability.

## Corrupted or Bloated Cache

Symptoms include checksum mismatches, decoding errors from cached artifacts, disk pressure, or repeated use of stale transformed data.

Checks:

- Prefer targeted cleanup: `Dataset.cleanup_cache_files()` for loaded datasets or a dedicated test cache directory for experiments.
- Use `load_from_cache_file=False` on `Dataset.map` to recompute transforms without deleting shared caches.
- Use `download_mode="force_redownload"` for stale raw downloads.
- Avoid deleting shared `HF_HOME`, `HF_HUB_CACHE`, or `HF_DATASETS_CACHE` directories without confirming no other jobs depend on them.
- If using `datasets-cli test --clear_cache`, always provide a disposable `--cache_dir`.

## fsspec and `storage_options` Failures

Symptoms include protocol not known, access denied on cloud paths, proxy failures, or compression/chained URL errors.

Checks:

- Install the backend package for the URI scheme, such as `s3fs`, `gcsfs`, or `adlfs`; these are optional and not guaranteed by default.
- Scope `storage_options` by protocol where needed, for example `{"s3": {"anon": False}}`.
- Check that credentials come from the intended environment or cloud profile and are not accidentally serialized into logs.
- For HTTP(S), proxy settings may be read from environment variables; verify corporate proxy settings separately.
- For compressed or chained fsspec paths, confirm options apply to the protocol Datasets ultimately opens.

## Destructive Hub Operations

Before `datasets-cli delete_from_hub` or any upload with delete patterns:

- Confirm the exact `repo_id`, `config_name`, `revision`, and owner.
- Confirm the operation is intended for a supported data-only dataset repository.
- Prefer PR-based changes and inspect the file diff before merging.
- Avoid literal tokens in shell history; use login/environment-backed auth.
- Communicate that `delete_from_hub` opens a PR but the proposed changes are destructive if merged.

## When To Escalate or Re-route

- Use `../../loading-local-hub/SKILL.md` for `load_dataset` path resolution, builder scripts, private loads, or local data-file API usage.
- Use `../../features-formats/SKILL.md` for schema, `Features`, image/audio/video columns, Parquet/Arrow/CSV conversion, and metadata types.
- Use `../../processing-streaming/SKILL.md` for streaming, `map`, multiprocessing transforms, iterable datasets, and performance after data is loaded.
