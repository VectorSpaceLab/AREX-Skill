# Configuration, Cache, Symlinks, and Xet

Read this before changing environment variables, moving a cache, diagnosing an
offline snapshot, disabling symlinks, or altering Xet behavior. These settings
are process configuration: set them before importing `huggingface_hub`.

## Effective Cache Roots

Default layout:

```text
~/.cache/huggingface/
├── hub/       # repository refs, blobs, snapshots, and cached tree listings
├── xet/       # Xet chunk/shard/staging optimization data
├── assets/    # downstream-library assets, not Hub repository snapshots
└── token      # normal stored-token path; never inspect or print its contents
```

Precedence and purpose:

| Setting | Purpose | Default/precedence |
|---|---|---|
| `XDG_CACHE_HOME` | Base cache root on Unix-like systems | Used only when `HF_HOME` is unset. |
| `HF_HOME` | Base for Hub data and token | Defaults to `~/.cache/huggingface`, or `$XDG_CACHE_HOME/huggingface`. |
| `HF_HUB_CACHE` | Shared model/dataset/Space/kernel repository cache | Defaults to `$HF_HOME/hub`; overrides the legacy `HUGGINGFACE_HUB_CACHE`. |
| `HF_XET_CACHE` | Xet cache root | Defaults to `$HF_HOME/xet`. Place on fast local storage when possible. |
| `HF_ASSETS_CACHE` | Cache for downstream-generated/downloaded assets | Defaults to `$HF_HOME/assets`; it is separate from repository payloads. |
| `HF_TOKEN_PATH` | Stored token file | Defaults to `$HF_HOME/token`. Diagnose presence only; never read it into logs. |
| `cache_dir=` | Per-call repository cache override | Overrides the default repository cache for that call. |
| `local_dir=` | Materialized payload destination | It is not a cache-root override; repository layout is copied directly here. |

Use the bundled read-only diagnostic to see resolved paths and the nearest
existing filesystem's free space:

```bash
python scripts/diagnose_download_env.py --pretty --scan-cache
```

Because variables are read at import time, setting `os.environ[...]` after
`import huggingface_hub` does not reliably reconfigure already imported
constants.

## Shared File Cache Semantics

Each repository has a type-qualified directory such as
`models--org--name`, `datasets--org--name`, or `spaces--org--name`:

```text
hub/<type>s--<namespace>--<name>/
├── refs/
│   └── main                  # text: branch/tag -> commit hash
├── blobs/
│   └── <etag-or-content-id>  # downloaded payload bytes
├── snapshots/
│   └── <commit>/
│       └── config.json       # normally a relative symlink to a blob
├── trees/
│   └── <commit>.json         # immutable file listing + download metadata
└── .no_exist/
    └── <commit>/optional     # empty marker for known remote absence
```

Operational meanings:

- **Refs** answer “which commit did this branch/tag last resolve to?” They do not
  prove any payload was downloaded.
- **Blobs** are the content store and can be reused by multiple snapshots.
- **Snapshots** expose repository paths for a commit. A snapshot can contain
  only the files selected or downloaded so far.
- **Trees** record what an immutable commit contains, including paths, sizes,
  blob/LFS identifiers, and valid Xet hashes when available. They allow
  completeness checks and can avoid per-file metadata calls.
- **`.no_exist`** records that one attempted path did not exist at a commit. It
  is metadata, not a zero-byte downloaded payload.
- **`*.incomplete`** files under blobs or local-dir metadata are interrupted
  transfer state. They are not valid payloads.

Never infer “downloaded and usable” from a ref, tree entry, `.no_exist` marker,
or cache scan row. Confirm that the selected snapshot path resolves to a file.
`try_to_load_from_cache` is the local no-network helper for one file: string
means a payload path, `_CACHED_NO_EXIST` means known absence, and `None` means
unknown.

A `CACHEDIR.TAG` marks cache content as re-downloadable so supporting backup
tools can omit it.

## `local_dir` Semantics

With `local_dir`, files are ordinary files under the requested repository
layout; cache symlinks are not used. The library creates:

```text
<local_dir>/.cache/huggingface/
├── download/      # per-file commit/etag metadata and locks
├── trees/         # per-commit repository file listings
└── .gitignore and CACHEDIR.TAG metadata
```

The main `cache_dir` is not the payload destination in this mode, although a
matching file already present in the shared cache can be copied into the local
directory. The local metadata enables update checks and interrupted-transfer
recovery. It may be removed after a successful download without deleting the
payload, but later pulls can require more metadata work.

`local_files_only=True` with `local_dir` may return an existing local file even
when its contents cannot be revalidated remotely. If strict provenance matters,
pin a commit, preserve metadata, and verify expected hashes under controlled
network/access conditions.

## Tree Listings and Incomplete Snapshots

A successful non-dry-run snapshot writes a per-commit tree listing. During an
offline/cache fallback, the library filters that listing with the same
`allow_patterns` and `ignore_patterns`, then checks every selected path under
the snapshot or `local_dir`.

- Missing selected path + known tree ⇒ `IncompleteSnapshotError` with
  `snapshot_path`.
- Files excluded by patterns do not count as missing.
- No cached tree listing ⇒ completeness cannot be proven; older or handmade
  caches may still be returned. Treat this as unknown completeness, not proof.
- A wrong `repo_type`, `revision`, or `cache_dir` can look exactly like a miss.
- A branch/tag requires a cached ref mapping when offline; a full commit hash
  directly selects the immutable snapshot.

Recovery sequence:

1. Preserve the partial path for diagnosis; do not label it complete.
2. Compare repository identity, type, revision, filters, and cache root with the
   preparation request.
3. Inspect cache warnings and incomplete-file count.
4. Restore network and required access, then repeat the same pinned request.
5. Rehearse with `local_files_only=True` and assert selected paths.

`hf cache prune --dry-run` shows detached revisions and orphaned incomplete
files. Only run the real prune after reviewing the selection.

## Symlink and No-Symlink Modes

The efficient shared cache stores one blob and creates relative symlinks from
snapshots. This deduplicates unchanged files across revisions.

If symlinks are unavailable (commonly Windows without Developer Mode/admin
rights) or explicitly disabled, payloads are placed/copied into snapshot
locations instead. Downloads still work, but the same large content can occupy
space more than once across revisions.

| Setting | Effect |
|---|---|
| `HF_HUB_DISABLE_SYMLINKS=1` | Proactively use degraded no-symlink mode. Useful for cross-platform/shared filesystems that cannot traverse one another's links. Costs disk deduplication. |
| `HF_HUB_DISABLE_SYMLINKS_WARNING=1` | Hides only the warning. It does not enable symlinks or restore deduplication. |

Troubleshooting rules:

- Do not replace cache symlinks with edited files.
- On Windows, prefer Developer Mode when policy allows; otherwise accept
  no-symlink mode and budget duplicate disk usage.
- On NAS/shared mounts, use no-symlink mode only when link portability is the
  actual failure. It is not a general corruption repair.
- Cache scanners support copied snapshot files as well as symlinks; size totals
  differ because copies are counted separately.

## Offline and Timeout Configuration

| Setting | Effect |
|---|---|
| `HF_HUB_OFFLINE=1` | Disables Hub HTTP calls process-wide. Downloads use local content; ordinary `HfApi` calls raise `OfflineModeIsEnabled`. |
| `local_files_only=True` | Disables network only for the specific download call. Prefer for a controlled offline rehearsal. |
| `HF_HUB_ETAG_TIMEOUT` | Metadata timeout in seconds. On timeout, cached content may be used when available. |
| `HF_HUB_DOWNLOAD_TIMEOUT` | Payload request timeout in seconds. Increase for slow links; a miss still fails. |
| `HF_HUB_DISABLE_IMPLICIT_TOKEN=1` | Avoids sending the stored token on read requests unless explicitly requested. Private/gated reads then need `token=True` or a supplied token. |
| `HF_TOKEN` | Overrides the stored token for the process. Record only whether it is set, never its value. |

`force_download=True` is incompatible with offline intent. When metadata cannot
be fetched, it cannot establish the fresh payload to request; combining it with
`local_files_only=True` raises instead of falling back.

## Xet Transfer and Cache Behavior

`hf_xet` is the optional Rust-backed transfer implementation used automatically
when the server provides Xet metadata and the package is available. Current
normal `huggingface_hub` installation includes it, but the Python APIs remain
the same if it is unavailable.

Download path at a high level:

1. Hub metadata identifies the file and provides Xet reconstruction data.
2. `hf_xet` obtains authorized content-addressed-storage (CAS) ranges.
3. Immutable byte ranges are fetched/deduplicated.
4. The destination file is reconstructed and validated at its expected size.
5. The ordinary Hub blob/snapshot or `local_dir` path remains the user-facing
   payload location.

If Xet metadata exists but `hf_xet` is unavailable or explicitly disabled,
repository file downloads can fall back to ordinary HTTP. Xet is acceleration
and deduplication, not the only cache truth. Buckets themselves are Xet-backed
object storage, so bucket operations still depend on the service's storage
semantics.

Xet directory purposes:

```text
$HF_XET_CACHE/<environment-or-region>/
├── chunk_cache/  # downloaded immutable ranges; an optimization
├── shard_cache/  # file-to-chunk mappings used primarily for upload dedupe
└── staging/      # resumable upload session metadata
```

There may be several environment/region subdirectories. High-level Hub cache
APIs manage repository payloads, not these internal Xet caches.

| Setting | Operational use |
|---|---|
| `HF_HUB_DISABLE_XET=1` | Disable automatic Xet use to isolate a transfer failure; set before import. |
| `HF_XET_CACHE` | Put Xet state on a suitable disk. Fast local SSD/NVMe is preferred. |
| `HF_XET_CHUNK_CACHE_SIZE_BYTES` | Download chunk-cache capacity. Current package docs state `0` by default (disabled); enable only when reuse benefits outweigh cache overhead. |
| `HF_XET_SHARD_CACHE_SIZE_LIMIT` | Soft shard-cache limit. Current package docs state 16 GB; verify against the installed `hf_xet` version when capacity matters. |
| `HF_XET_NUM_CONCURRENT_RANGE_GETS` | Concurrent range requests per file; current documented default is 16. Tune only with network/disk evidence. |
| `HF_XET_HIGH_PERFORMANCE=1` | Attempts to saturate network, CPU, and disk. Avoid on shared or resource-limited hosts without approval. |
| `HF_XET_RECONSTRUCT_WRITE_SEQUENTIALLY=1` | Prefer sequential reconstruction writes for spinning disks. |

`HF_HUB_ENABLE_HF_TRANSFER` is deprecated and does not restore the removed
`hf_transfer` path. Use Xet settings instead.

Safe Xet diagnosis:

1. Run the bundled diagnostic and record package presence, disabled state, cache
   root, and free space.
2. Retry a bounded file with normal settings and debug logging, redacting auth
   headers and signed URLs.
3. In a fresh process, set `HF_HUB_DISABLE_XET=1` and retry to test HTTP
   fallback for repository files.
4. If fallback works, treat the Xet layer as isolated; update compatible
   packages or report Xet diagnostics. Do not repeatedly force a very large
   transfer.
5. Delete an Xet cache only when no transfers/uploads are active and the caller
   accepts losing optimization/resume state. Start with inspection; deletion is
   not the first repair.

## Installation and Source-Script Decisions

Normal package installation is intentionally simple:

```bash
python -m pip install --upgrade huggingface_hub
# or
uv pip install --upgrade huggingface_hub
```

The upstream standalone shell and PowerShell CLI installers are reference-only
for this skill. They fetch artifacts and mutate host configuration, so they
were not bundled and must not be piped into a shell by this operating context.
Use an approved package manager or route installation policy to
`cli-and-automation`.

The upstream hardware-flavor checker is a networked maintainer utility for
updating enums/docs, not a download/runtime diagnostic; it was not bundled.
Source package modules are evidence, not scripts to copy.

The bundled `scripts/diagnose_download_env.py` is a purpose-built, self-contained
read-only helper. It inspects effective settings, paths, free space, package/Xet
availability, token presence, and optional cache-scan summaries. It never reads
a token value, contacts the Hub, installs software, downloads payloads, or
deletes cache content.
