# Downloads and Storage API Reference

Use this reference when selecting exact Python parameters, interpreting return
values, constructing an `hf://` location, or choosing between repository and
bucket APIs. Signatures were checked from the prepared `huggingface_hub` 1.29.0
package; treat later package versions as a reason to re-inspect signatures.

## Repository Download Signatures

```python
hf_hub_download(
    repo_id: str,
    filename: str,
    *,
    subfolder: str | None = None,
    repo_type: str | None = None,
    revision: str | None = None,
    library_name: str | None = None,
    library_version: str | None = None,
    cache_dir: str | Path | None = None,
    local_dir: str | Path | None = None,
    user_agent: dict | str | None = None,
    force_download: bool = False,
    etag_timeout: float = 10,
    token: bool | str | None = None,
    local_files_only: bool = False,
    headers: dict[str, str] | None = None,
    endpoint: str | None = None,
    tqdm_class: type[tqdm] | None = None,
    dry_run: bool = False,
) -> str | DryRunFileInfo
```

```python
snapshot_download(
    repo_id: str,
    *,
    repo_type: str | None = None,
    revision: str | None = None,
    cache_dir: str | Path | None = None,
    local_dir: str | Path | None = None,
    library_name: str | None = None,
    library_version: str | None = None,
    user_agent: dict | str | None = None,
    etag_timeout: float = 10,
    force_download: bool = False,
    token: bool | str | None = None,
    local_files_only: bool = False,
    allow_patterns: list[str] | str | None = None,
    ignore_patterns: list[str] | str | None = None,
    max_workers: int = 8,
    tqdm_class: type[tqdm] | None = None,
    headers: dict[str, str] | None = None,
    endpoint: str | None = None,
    dry_run: bool = False,
) -> str | list[DryRunFileInfo]
```

### Practical Distinctions

| Need | Use | Returned value | Important consequence |
|---|---|---|---|
| One known file | `hf_hub_download` | file path | Shared-cache path is managed content; do not edit it. |
| Whole or filtered repository | `snapshot_download` | snapshot directory | Resolves one commit, lists files, filters, and downloads files concurrently. |
| Estimate without payload transfer | either with `dry_run=True` | one info object or list | Remote metadata/listing can still be required; snapshot dry run fails if the repository cannot be accessed. |
| Reusable content-addressed storage | omit `local_dir`; optionally set `cache_dir` | cache pointer/tree | Blobs can be shared across revisions through symlinks. |
| Ordinary editable/output tree | set `local_dir` | direct local path/tree | `cache_dir` is not the payload destination; `.cache/huggingface/` metadata is placed under `local_dir`. |
| Prepared offline read | `local_files_only=True` | existing path/tree only | Never fetches missing payload; a cache miss raises. |
| Fresh transfer | `force_download=True` | same target path after transfer | Requires metadata/network and conflicts with offline intent. |

### Shared Parameters

| Parameter | Operational meaning and constraint |
|---|---|
| `repo_id` | Repository identifier. Plain API identifiers may be canonical or namespaced, but canonical `hf://` URIs require `namespace/name`. |
| `repo_type` | `None`/`"model"` by default; set `"dataset"`, `"space"`, or `"kernel"` when applicable. A wrong type looks like a missing repository. |
| `revision` | Branch, tag, special ref, or full 40-character commit hash. Pin a commit for immutable and reliable offline selection. |
| `token` | `None` uses normal implicit-token policy; `True` requires a stored token; a string is explicit; `False` disables auth. Never hardcode or log a token. |
| `cache_dir` | Root of the shared repository cache for this call. Environment defaults are described in the configuration reference. |
| `local_dir` | Materializes the repository layout directly. Use for files that will be modified or delivered as outputs. |
| `local_files_only` | Forbids network for that call and returns only matching local content. It is not a request to download into a local folder. |
| `force_download` | Re-downloads even when content is cached. It is not corruption diagnosis and cannot repair an offline miss. |
| `dry_run` | Returns planning records instead of payload paths. It can resolve remote metadata and may update lightweight revision metadata. |
| `etag_timeout` | Metadata lookup timeout. `HF_HUB_ETAG_TIMEOUT` can override the call value at import time. |

### Snapshot-only Parameters

| Parameter | Meaning |
|---|---|
| `allow_patterns` | Keep paths matching at least one fnmatch-style pattern. Accepts a string or list. |
| `ignore_patterns` | Remove paths matching any pattern. When both filters are set, both constraints apply. |
| `max_workers` | Concurrent file-download worker count; default `8`. It does not control Xet range requests within a file. |

`DryRunFileInfo` exposes `commit_hash`, `file_size`, `filename`, `local_path`,
`is_cached`, and `will_download`. `will_download` is true when the payload is
not cached or `force_download=True`. A cache-mode blob can be present even if a
snapshot pointer is missing, so `is_cached` is not the same as “the requested
snapshot path currently exists.” In `local_dir` mode, the materialized file is
the relevant content.

## Download and Cache Helpers

```python
try_to_load_from_cache(
    repo_id,
    filename,
    cache_dir=None,
    revision=None,
    repo_type=None,
) -> str | _CACHED_NO_EXIST | None
```

This helper performs no network call. A string is a materialized cached file,
`_CACHED_NO_EXIST` means the remote absence was cached for that revision, and
`None` means the cache cannot answer. Neither a `refs/` file nor a tree-listing
record alone makes this return a payload path.

```python
scan_cache_dir(cache_dir=None) -> HFCacheInfo
```

The report contains repositories, revisions, files, orphaned
`*.incomplete` payloads, total sizes, and non-fatal cache-corruption warnings.
It is immutable. `HFCacheInfo.delete_revisions(...)` builds a
`DeleteCacheStrategy`; inspect `expected_freed_size` before calling its
irreversible `execute()`.

`get_cached_repo_tree(repo_id, repo_type=None, revision=None, cache_dir=None,
local_dir=None)` returns a cached per-commit listing without network. It proves
what the commit should contain, not that every listed payload exists.

## `HfFileSystem` and fsspec

Construct `HfFileSystem(token=..., endpoint=..., block_size=...,
expand_info=...)`, or use the global `hffs`. Direct method paths may omit the
`hf://` prefix; external fsspec integrations should use it.

| Method | Verified shape | Operational notes |
|---|---|---|
| `ls(path, detail=True, refresh=False, revision=None)` | list of paths or metadata dicts | `detail=False` returns paths. `refresh=True` bypasses cached directory data. |
| `glob(path, maxdepth=None, **kwargs)` | list of matching paths | Pass `revision=` in kwargs or encode it in the URI, but never conflict. |
| `find(path, maxdepth=None, withdirs=False, detail=False, refresh=False, revision=None)` | paths or detail map | Recursive listing; `maxdepth` must be at least one. |
| `exists(path, **kwargs)` | bool | Use `refresh=True` after remote mutation when stale results are possible. |
| `open(path, mode="rb", block_size=None, ...)` | file object | Binary by default. Use `"r"` for text. Append mode is unsupported. `block_size=0` streams. |
| `read_text(path, ...)` | string | Convenience read through fsspec. |
| `get_file(rpath, lpath, ...)` | `None` | Prefer download or bucket APIs for performance and reliability. |
| `cp_file(path1, path2, revision=None, ...)` | `None` | Repository-only; bucket involvement raises `NotImplementedError`. Route mutations elsewhere. |

`HfFileSystem` introduces fsspec compatibility overhead. Prefer
`HfApi.list_repo_tree`, `get_paths_info`, `hf_hub_download`, and bucket APIs
when fsspec compatibility is not required.

## HF URI and Mount Grammar

```text
hf://[<TYPE>/]<namespace>/<name>[@<REVISION>][/<PATH>]
hf://[<TYPE>/]<namespace>/<name>[@<REVISION>][/<PATH>]:<MOUNT_PATH>[:ro|:rw]
```

| Resource | Examples | Revision support |
|---|---|---|
| Model | `hf://org/model/config.json`, `hf://models/org/model@v1` | yes; type prefix optional |
| Dataset | `hf://datasets/org/data@refs/pr/3/train.csv` | yes; plural prefix required |
| Space | `hf://spaces/user/app/app.py` | yes |
| Kernel | `hf://kernels/org/kernel` | yes |
| Bucket | `hf://buckets/org/archive/logs/run.json` | no |

`parse_hf_uri(value, endpoint=None)` is a pure string parser returning an
immutable `HfUri` with `type`, `id`, `revision`, `path_in_repo`, `is_repo`, and
`is_bucket`. It also accepts supported Hugging Face web file/tree routes and
normalizes them. Unrecognized hosts and ambiguous pages are rejected.

`parse_hf_mount` is imported from `huggingface_hub.utils`. It returns an
`HfMount` with `source`, absolute non-root `mount_path`, and `read_only` (`True`,
`False`, or `None`). Do not split mount strings manually because revisions,
paths, Windows-like punctuation, and the final `:ro`/`:rw` marker are parsed by
the centralized grammar.

Important strictness:

- type prefixes are plural;
- URIs require a namespaced identifier, so `hf://gpt2` is invalid even though a
  plain `hf download gpt2`/API repo id can work;
- buckets reject `@revision`;
- empty revision/path segments are rejected;
- ordinary revision names containing `/` must encode the slash as `%2F`;
- special `refs/pr/N` and `refs/convert/...` revisions are recognized eagerly;
- a valid URI is not proof that its path is safe to materialize locally.

## Bucket APIs

Buckets are unversioned, mutable object stores backed by Xet. Core signatures:

```python
list_bucket_tree(bucket_id, prefix=None, *, recursive=None, token=None)
    -> Iterable[BucketFile | BucketFolder]

download_bucket_files(
    bucket_id,
    files: list[tuple[str | BucketFile, str | Path]],
    *,
    raise_on_missing_files=False,
    token=None,
) -> None

copy_files(source: str, destination: str, *, token=None) -> None

sync_bucket(
    source=None,
    dest=None,
    *,
    delete=False,
    ignore_times=False,
    ignore_sizes=False,
    existing=False,
    ignore_existing=False,
    include=None,
    exclude=None,
    filter_from=None,
    plan=None,
    apply=None,
    dry_run=False,
    verbose=False,
    quiet=False,
    token=None,
) -> SyncPlan
```

Pass `BucketFile` objects from `list_bucket_tree` to
`download_bucket_files` to avoid per-file metadata lookup. Missing files warn
and are skipped by default; set `raise_on_missing_files=True` when every source
is required.

`copy_files` accepts only remote `hf://` locations and supports files or
folders. It supports repo→repo, repo→bucket, and bucket→bucket. Bucket→repo is
unsupported. Xet-backed data can be copied server-side by hash when storage
regions are compatible; non-Xet small repository files may be downloaded and
re-uploaded. Repository destinations create commits, so route mutation details
to `hub-operations`.

`sync_bucket` requires exactly one local directory and one bucket URI. It does
not perform remote→remote sync. `dry_run=True` returns a `SyncPlan`; `plan=...`
saves JSONL; `apply=...` executes a saved plan. `delete=True` also removes
destination-only files. A plan is executable input: review and protect it from
untrusted edits.

## CLI Surface Boundary

| Goal | Command family | Key behavior |
|---|---|---|
| Repository payload | `hf download` | One filename uses single-file download; multiple/no filenames use snapshot semantics. `--include`, `--exclude`, `--local-dir`, `--force-download`, `--dry-run`, and `--max-workers` are available. Buckets are rejected. |
| Cache inspect/repair | `hf cache ls`, `verify`, `rm`, `prune` | `rm` and `prune` support `--dry-run`; `verify` checks a chosen remote revision against cache/local content and may require network/access. |
| Single file movement | `hf cp` | Local↔repo/bucket and supported remote→remote combinations. `hf repos cp` and `hf buckets cp` add resource-type guardrails. |
| Local↔bucket directory | `hf sync` / `hf buckets sync` | Pattern filters, comparison modes, delete, JSONL plan/apply, and dry run. |
| Bucket inventory | `hf buckets list` / `ls`, `info` | List buckets, prefixes, files, or recursive trees. |

Use the `cli-and-automation` sibling sub-skill for exhaustive flag and output
format guidance. Use this reference to choose the correct semantic surface.
