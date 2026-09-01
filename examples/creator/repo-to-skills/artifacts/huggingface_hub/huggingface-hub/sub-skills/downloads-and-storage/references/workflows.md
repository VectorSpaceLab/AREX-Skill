# Downloads and Storage Workflows

Use these recipes after selecting the API surface in the router. Examples marked
**local/read-only** do not contact the Hub when their stated fixtures already
exist. Examples marked **network** need Hub access; private/gated resources also
need an authorized token. Replace identifiers and inspect planned destinations
before execution.

## 1. Download One Repository File

**Network; read-only remote operation.** Prefer a full commit hash when the
result must be reproducible.

```python
from pathlib import Path
from huggingface_hub import hf_hub_download

path = Path(
    hf_hub_download(
        repo_id="org/model",
        filename="config.json",
        repo_type="model",
        revision="0123456789abcdef0123456789abcdef01234567",
        token=None,  # normal stored/implicit-token policy; never hardcode a token
    )
)
assert path.is_file()
# Do not modify `path`: it normally points into the managed shared cache.
```

For a normal writable result, materialize it rather than editing the shared
cache:

```python
path = Path(
    hf_hub_download(
        repo_id="org/dataset",
        repo_type="dataset",
        filename="data/train.jsonl",
        local_dir="./dataset-copy",
    )
)
assert path == Path("./dataset-copy/data/train.jsonl").resolve()
```

`local_dir` preserves the repository path and creates local metadata under
`./dataset-copy/.cache/huggingface/`. That metadata can prevent unnecessary
future transfers, but it is not the downloaded payload.

## 2. Plan and Fetch a Filtered Snapshot

**Network.** Dry-run first, aggregate only payloads that would transfer, then
make the real call with exactly the same identity and filters.

```python
from huggingface_hub import snapshot_download

request = dict(
    repo_id="org/model",
    repo_type="model",
    revision="main",
    allow_patterns=["*.json", "tokenizer/**"],
    ignore_patterns=["tokenizer/debug-*.json"],
    cache_dir="./hf-cache",
    max_workers=4,
)

plan = snapshot_download(**request, dry_run=True)
pending = [item for item in plan if item.will_download]
print({
    "commit": sorted({item.commit_hash for item in plan}),
    "selected_files": len(plan),
    "pending_files": len(pending),
    "pending_bytes": sum(item.file_size for item in pending),
})

snapshot = snapshot_download(**request)
```

Expected checks:

```python
from pathlib import Path

root = Path(snapshot)
assert root.is_dir()
assert all(item.commit_hash == root.name for item in plan)
for item in plan:
    assert (root / item.filename).is_file()
```

Dry run does not transfer file payloads, but it resolves repository metadata and
can update lightweight revision metadata. It cannot be used as a guaranteed
offline listing. To avoid branch movement between plan and fetch, take the
single commit hash returned by the plan and use it as `revision` for the real
call.

## 3. Prepare and Rehearse Offline Use

The preparation phase is **network**; the rehearsal phase is **local/read-only**.
Set `local_files_only=True` for call-scoped behavior. Use `HF_HUB_OFFLINE=1`
before process startup only when the entire process must avoid Hub HTTP calls.

```python
from pathlib import Path
from huggingface_hub import snapshot_download

cache = "./hf-cache"
filters = ["*.json"]

# Preparation with network access.
prepared = snapshot_download(
    "org/model",
    repo_type="model",
    revision="0123456789abcdef0123456789abcdef01234567",
    cache_dir=cache,
    allow_patterns=filters,
)

# Rehearsal: no network is permitted by this call.
offline = snapshot_download(
    "org/model",
    repo_type="model",
    revision="0123456789abcdef0123456789abcdef01234567",
    cache_dir=cache,
    allow_patterns=filters,
    local_files_only=True,
)
assert Path(offline) == Path(prepared)
assert list(Path(offline).glob("*.json"))
```

Do not add `force_download=True` to an offline call. `local_files_only` means
“use matching materialized content or fail”; `force_download` means “perform a
fresh transfer,” which needs remote metadata and network access.

If `IncompleteSnapshotError` is raised, retain its diagnostic path but do not
consume it as complete:

```python
from huggingface_hub.errors import IncompleteSnapshotError

try:
    snapshot_download(..., local_files_only=True)
except IncompleteSnapshotError as error:
    print(f"Partial content is at: {error.snapshot_path}")
    # Restore network/access and repeat the same pinned, filtered request.
    raise
```

If the error is `LocalEntryNotFoundError`, first compare `repo_id`, `repo_type`,
`revision`, `cache_dir`, and filters with the preparation call. A branch name
also needs a cached `refs/` mapping; a full commit hash removes that ambiguity.

## 4. Inspect Cache Without Deleting

**Local/read-only.** From this sub-skill directory:

```bash
python scripts/diagnose_download_env.py --pretty --scan-cache
```

To inspect an alternate cache without printing credentials:

```bash
python scripts/diagnose_download_env.py \
  --cache-dir ./hf-cache \
  --scan-cache \
  --pretty
```

The helper reports effective cache paths, import-time offline/symlink/Xet
settings, token presence (never the token value), free bytes, scan warnings, and
incomplete-file counts.

Equivalent Python inspection:

```python
from huggingface_hub import scan_cache_dir
from huggingface_hub.errors import CacheNotFound

try:
    report = scan_cache_dir("./hf-cache")
except CacheNotFound:
    print("No cache exists at that path")
else:
    print({
        "repositories": len(report.repos),
        "bytes": report.size_on_disk,
        "incomplete_files": len(report.incomplete_files),
        "incomplete_bytes": report.incomplete_size_on_disk,
        "warnings": [str(w) for w in report.warnings],
    })
```

A warning means the scanner ignored or partially diagnosed an inconsistent
entry; it does not prove all other payload checksums. Do not infer content from
`refs`, tree-listing, or `.no_exist` metadata alone.

## 5. Preview Cache Cleanup

`hf cache rm` and `hf cache prune` are local but destructive without
`--dry-run`. Start with inspection and previews:

```bash
hf cache ls --revisions --show-warnings --cache-dir ./hf-cache
hf cache rm model/org/model --cache-dir ./hf-cache --dry-run
hf cache prune --cache-dir ./hf-cache --dry-run
```

- `rm` selects named repositories or exact revision hashes and computes a safe
  deletion strategy for shared blobs.
- `prune` targets detached revisions and orphaned `*.incomplete` files.
- `verify` compares local payload checksums with the selected Hub revision; it
  can require network, access credentials, and remote metadata:

```bash
# Network/access may be required.
hf cache verify org/model --repo-type model --revision main \
  --cache-dir ./hf-cache
```

Only remove content after reviewing selected revisions and expected freed size.
Never manually delete one shared blob while snapshots still refer to it.

## 6. Browse Repository or Bucket Files with fsspec

**Network unless a higher-level fsspec consumer provides its own caching.** Use
`HfFileSystem` for compatibility and remote browsing, not as a replacement for
the download cache.

```python
from huggingface_hub import HfFileSystem

fs = HfFileSystem(token=None)
root = "datasets/org/data@main"

names = fs.ls(root, detail=False)
json_paths = fs.glob(f"{root}/**/*.json")
assert fs.exists(f"{root}/README.md")

with fs.open(f"{root}/README.md", "r") as handle:  # text mode is explicit
    first_line = handle.readline()
```

For a bucket:

```python
bucket_root = "buckets/org/archive"
for item in fs.ls(bucket_root, detail=True, refresh=True):
    print(item["name"], item["type"], item["size"])

with fs.open(f"{bucket_root}/runs/summary.json", "r") as handle:
    summary = handle.read()
```

Use `refresh=True` after out-of-band changes. Directory metadata is cached by
`HfFileSystem`; that dircache is separate from downloaded repository payloads.
Do not pass a `revision` for buckets.

External integrations use protocol-qualified paths:

```python
import fsspec

with fsspec.open("hf://datasets/org/data@main/data/train.csv", "r") as handle:
    header = handle.readline()
```

## 7. Parse and Validate URIs and Mounts

Parsing is **local/read-only** and makes no network request.

```python
from huggingface_hub import parse_hf_uri
from huggingface_hub.utils import parse_hf_mount

repo = parse_hf_uri("hf://datasets/org/data@refs/pr/3/train.jsonl")
assert (repo.type, repo.id, repo.revision, repo.path_in_repo) == (
    "dataset", "org/data", "refs/pr/3", "train.jsonl"
)

bucket = parse_hf_uri("hf://buckets/org/archive/runs/1.json")
assert bucket.is_bucket and bucket.revision is None

mount = parse_hf_mount("hf://buckets/org/archive/runs:/mnt/runs:ro")
assert mount.source.is_bucket
assert mount.mount_path == "/mnt/runs"
assert mount.read_only is True
```

Use the returned fields; never recover type/id/revision/path by ad hoc slash or
colon splitting. Parsing does not make a path safe for local use. Reject every
path with an absolute root, drive/UNC anchor, empty segment, or `..` segment.

## 8. List and Download Bucket Files

**Network; private buckets require access.** Buckets have no revisions.

```python
from pathlib import Path
from huggingface_hub import download_bucket_files, list_bucket_tree

selected = [
    item
    for item in list_bucket_tree("org/archive", prefix="runs/42", recursive=True)
    if item.type == "file" and item.path.endswith(".json")
]

destination = Path("./bucket-copy").resolve()
files = []
for item in selected:
    relative = Path(item.path).relative_to("runs/42")
    local = (destination / relative).resolve()
    if destination not in local.parents:
        raise ValueError(f"Unsafe destination: {relative}")
    files.append((item, local))

download_bucket_files("org/archive", files, raise_on_missing_files=True)
```

Passing `BucketFile` objects avoids another metadata lookup. Always enforce a
component boundary for prefixes: `runs/42` must match itself or
`runs/42/...`, not `runs/420`.

## 9. Plan and Apply Local↔Bucket Sync

**Network.** Planning lists remote objects but does not transfer payload.
`--delete` can schedule destructive actions; inspect them explicitly.

```bash
# Generate a JSONL plan; no transfer.
hf sync ./checkpoints hf://buckets/org/archive/checkpoints \
  --include "*.safetensors" \
  --exclude "*.tmp" \
  --plan sync-plan.jsonl

# Review the header and every operation before execution.
cat sync-plan.jsonl

# Apply only a trusted, unchanged plan.
hf sync --apply sync-plan.jsonl
```

For a non-persistent preview, `--dry-run` prints the same JSONL shape to stdout:

```bash
hf sync hf://buckets/org/archive/results ./results --dry-run
```

Python equivalent:

```python
from huggingface_hub import sync_bucket

plan = sync_bucket(
    "./checkpoints",
    "hf://buckets/org/archive/checkpoints",
    include=["*.safetensors"],
    exclude=["*.tmp"],
    dry_run=True,
)
print(plan.summary())
```

A sync accepts one local directory and one bucket URI. It is not for
repo↔bucket or bucket↔bucket remote copies. Use `copy_files` for supported
remote movement.

## 10. Copy One File or Remote Trees

### One local/remote file with CLI

**Network; uploads and remote copies mutate destinations.** Route exhaustive CLI
flags and auth setup to `cli-and-automation`; route repository commit policy to
`hub-operations`.

```bash
# Repo file -> local file
hf cp hf://org/model/config.json ./config.json

# Bucket file -> stdout
hf cp hf://buckets/org/archive/summary.json -

# Local file -> bucket (mutation)
hf cp ./summary.json hf://buckets/org/archive/runs/42/summary.json
```

Use `hf download` for repository directories and `hf sync` for bucket
directories. `hf cp` rejects local→local copies.

### Remote copy with Python

```python
from huggingface_hub import copy_files

# Source trailing slash means copy contents, not the directory node.
copy_files(
    "hf://datasets/org/source@main/processed/",
    "hf://buckets/org/archive/processed/",
)
```

Before executing, verify:

1. source and destination parse to the intended resource types;
2. repository source revision is pinned when reproducibility matters;
3. source trailing slash matches the desired nesting behavior;
4. destination exists/does not exist as expected;
5. source and destination storage regions support server-side copy;
6. the direction is not bucket→repo, which is unsupported.

Large Xet-backed files can copy server-side by hash. Small non-Xet repository
files copied to buckets may be downloaded and re-uploaded. Never assume
`copy_files` is always zero-transfer.

## 11. Difficult Synthetic Offline/Cache Case

**Local-only validation with mocked metadata; no Hub service, credentials, or
real bucket is needed.** This catches a subtle distinction between a dry-run
plan, the cached tree listing, selected snapshot files, and an offline cache
miss. Use a temporary cache and a fresh Python process in a test harness. The
mocked download writer below only creates fixture bytes in the temporary cache;
it is not a production downloader.

```python
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from huggingface_hub import HfApi, HfFileMetadata, RepoFile, hf_hub_download, snapshot_download
from huggingface_hub.errors import LocalEntryNotFoundError

COMMIT = "0123456789abcdef0123456789abcdef01234567"
WRONG_COMMIT = "fedcba9876543210fedcba9876543210fedcba98"
FILES = {
    "config.json": b'{"ok": true}',
    "nested/params.json": b'{"n": 1}',
    "weights.bin": b"not-really-weights",
    "secret.json": b'{"private": true}',
}
TREE = [RepoFile(path=name, size=len(content), oid=f"etag-{name.replace('/', '-')}") for name, content in FILES.items()]


def fake_metadata(url, **kwargs):
    filename = next(name for name in FILES if url.endswith("/" + name))
    return HfFileMetadata(
        commit_hash=COMMIT,
        etag=f"etag-{filename.replace('/', '-')}",
        location=url,
        size=len(FILES[filename]),
        xet_file_data=None,
    )


def fake_materialize(*, destination_path, filename, **kwargs):
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    destination_path.write_bytes(FILES[filename])


def test_dry_run_then_filtered_offline_snapshot(tmp_path):
    cache = tmp_path / "hub-cache"
    request = {
        "repo_id": "org/example",
        "revision": "main",
        "cache_dir": cache,
        "allow_patterns": ["*.json"],
        "ignore_patterns": ["secret.json"],
        "max_workers": 1,
    }
    with (
        patch("huggingface_hub.file_download.get_hf_file_metadata", side_effect=fake_metadata),
        # Both snapshot resolution and file metadata use this same public API class.
        patch.object(HfApi, "repo_info", return_value=SimpleNamespace(sha=COMMIT)),
        patch.object(HfApi, "list_repo_tree", return_value=TREE),
        patch("huggingface_hub.file_download._download_to_tmp_and_move", side_effect=fake_materialize),
    ):
        plan = snapshot_download(**request, dry_run=True)
        assert {item.filename for item in plan} == {"config.json", "nested/params.json"}
        assert all(item.commit_hash == COMMIT and item.will_download for item in plan)

        prepared = snapshot_download(**request)
        assert (Path(prepared) / "config.json").read_bytes() == FILES["config.json"]
        assert (Path(prepared) / "nested/params.json").read_bytes() == FILES["nested/params.json"]
        assert not (Path(prepared) / "weights.bin").exists()
        assert not (Path(prepared) / "secret.json").exists()

    # No mocks or network are needed now: the cached tree and selected files are enough.
    offline = snapshot_download(
        "org/example",
        revision=COMMIT,
        cache_dir=cache,
        allow_patterns=["*.json"],
        ignore_patterns=["secret.json"],
        local_files_only=True,
    )
    assert Path(offline) == Path(prepared)
    assert (Path(offline) / "nested/params.json").is_file()

    with pytest.raises(LocalEntryNotFoundError):
        snapshot_download("org/example", revision=WRONG_COMMIT, cache_dir=cache, local_files_only=True)

    with pytest.raises(ValueError, match="force_download=True"):
        hf_hub_download(
            "org/example",
            "config.json",
            revision=COMMIT,
            cache_dir=cache,
            local_files_only=True,
            force_download=True,
        )
```

Interpretation: `dry_run=True` may resolve remote metadata but transfers no
payload; it is not an offline inventory. The subsequent filtered download
writes the tree listing and selected payloads. `local_files_only=True` then
checks only the matching cached revision and selected files. A wrong commit (or
wrong repo type/cache root) is a cache miss, not permission to fall back to
`main`. `force_download=True` requests a fresh transfer and must be retried
online after checking disk space; it is incompatible with local-only/offline
mode.

### Deferred mocked bucket path/traversal case

Keep this case **deferred** until bucket service access and a reviewable plan
fixture are available; do not create a bucket or apply a plan as part of the
local test above. Mock `list_bucket_tree` with files under `logs/a.txt`,
`logs/sub/b.txt`, the colliding prefix `logs-old/other.txt`, and an untrusted
key such as `logs/../escape.txt`. Expected behavior is: only the exact
`logs` file boundary and `logs/...` descendants enter a `logs` selection;
`logs-old/...` is excluded; the traversal key is rejected visibly before local
materialization or plan application; and a crafted JSONL plan is revalidated at
apply time. Also assert that `download_bucket_files(...,
raise_on_missing_files=True)` fails for a missing required object. Record the
case as deferred rather than claiming bucket integration coverage.

## 12. CLI Routing Summary

- Repository one/many/tree downloads: `hf download`.
- Bucket single file or supported remote copy: `hf cp`.
- Local↔bucket directories: `hf sync` or `hf buckets sync`.
- Cache inventory and cleanup: `hf cache ls|verify|rm|prune`.
- Bucket discovery: `hf buckets list|ls|info`.

`hf download` intentionally rejects bucket URIs and points to sync. `hf sync`
intentionally rejects local↔local and remote↔remote pairs. Use semantic routing
before looking up exhaustive flags in `cli-and-automation`.
