---
name: downloads-and-storage
description: "Routes Hugging Face Hub file and snapshot downloads, cache and offline recovery, Xet-backed storage, HfFileSystem and hf:// URIs, buckets, and safe copy or sync planning. Use for model, dataset, Space, or kernel downloads; allow/ignore patterns; cache corruption; fsspec browsing; volume mounts; and bucket file movement."
disable-model-invocation: true
license: Apache-2.0
metadata:
  disco-role: operating
---

# Downloads and Storage

Use this sub-skill to select and operate the Hub's read/download and storage
surfaces without confusing repository snapshots, local cache metadata, and
bucket object storage.

## Trigger Routes

Load this sub-skill when the request mentions any of the following:

- download one Hub file, model, dataset, Space, or kernel repository;
- snapshot a revision with allow/ignore patterns or estimate it with dry run;
- inspect, verify, prune, relocate, or troubleshoot the local Hub cache;
- run offline, recover from an interrupted or incomplete snapshot, or diagnose
  a cache miss;
- enable, disable, or troubleshoot Xet-backed transfers and chunk storage;
- browse or open Hub files through `HfFileSystem`, fsspec, or `hf://` paths;
- parse a Hub URI or a mount such as `hf://datasets/org/data:/mnt:ro`;
- browse/download bucket objects or plan a local↔bucket sync;
- reason about trailing-slash semantics for safe remote copy operations.

## Read the Focused References

- Read [API reference](references/api-reference.md) for verified signatures,
  return values, parameter matrices, URI forms, filesystem methods, and bucket
  APIs.
- Read [workflows](references/workflows.md) for copyable download, offline,
  cache, fsspec, bucket, copy, and plan/apply recipes.
- Read [configuration, cache, and Xet](references/configuration-cache-and-storage.md)
  before changing cache paths, offline mode, symlink mode, timeouts, or Xet
  settings.
- Read [troubleshooting](references/troubleshooting.md) for revision/repo-type,
  access, disk, cache, symlink, Xet, URI, prefix, and traversal failures.
- Run the bundled read-only
  [download environment diagnostic](scripts/diagnose_download_env.py) when the
  effective cache roots, import-time settings, free space, token presence, Xet
  availability, or cache structure is uncertain.

## Keep the Boundaries Clear

This sub-skill owns downloads, read-only filesystem access, local cache
operations, bucket reads, and safe movement planning. It covers upload/copy
only far enough to choose a safe file-movement surface. Although
`HfFileSystem` exposes write/delete methods, do not execute those mutations from
this route; send repository or bucket mutations to the appropriate operations
workflow.

- Route repository and bucket creation, commits, branches, uploads, deletes,
  moves, visibility changes, and other mutations to the `hub-operations`
  sibling sub-skill.
- Route exhaustive CLI flag selection, output formats, authentication setup,
  and shell automation to the `cli-and-automation` sibling sub-skill.
- Do not use `HfFileSystem` as the default high-throughput download API; prefer
  `hf_hub_download`, `snapshot_download`, or the corresponding `HfApi` methods.
- Do not bundle or run credentialed upload helpers or networked installers from
  this skill.

## Choose the Download Surface

1. Use `hf_hub_download(repo_id, filename, ...)` for exactly one repository
   file. It returns a file path, normally a pointer inside the shared cache.
2. Use `snapshot_download(repo_id, ...)` for a coherent repository tree,
   multiple files, pattern filtering, or parallel file downloads. It returns a
   snapshot directory.
3. Use `local_dir` when the caller needs a normal materialized directory they
   may modify. Otherwise prefer `cache_dir`/the shared cache and treat returned
   cache paths as immutable.
4. Set `repo_type` explicitly for datasets, Spaces, and kernels; model is the
   default. Pin `revision` to a full commit hash for reproducible or prepared
   offline execution.
5. Use `dry_run=True` to inspect `DryRunFileInfo`; it may perform remote metadata
   calls but does not transfer file payloads. It is not an offline inventory
   mechanism.
6. Use `allow_patterns` and `ignore_patterns` only with snapshots. Both apply;
   ignored files remain excluded after allow filtering. Tune `max_workers` for
   concurrent files, not Xet byte-range concurrency.

Before a large or forced transfer, inspect `will_download` and `file_size`, run
the diagnostic helper, and confirm free space in both the Hub cache and Xet
cache locations.

## Preserve Cache and Offline Invariants

- `local_files_only=True` forbids network access for that call and succeeds only
  from already materialized content. `force_download=True` asks for a fresh
  transfer and is not an offline/cache-repair switch; do not combine them.
- `HF_HUB_OFFLINE=1` is process-wide and is read when the package is imported.
  Set it before Python starts. It also makes ordinary `HfApi` calls fail rather
  than contact the Hub.
- A cached `refs/` entry or `trees/*.json` record is metadata, not downloaded
  content. Confirm the selected snapshot files exist.
- If a cached tree listing proves requested files are missing, offline
  `snapshot_download` raises `IncompleteSnapshotError` instead of silently
  returning the partial tree. Pattern-excluded files do not count as missing.
- Use `scan_cache_dir` or `hf cache ls` for inspection. Preview `hf cache rm`
  and `hf cache prune` with `--dry-run`; deletion is irreversible.
- Never edit a returned shared-cache file. Materialize to `local_dir` or copy it
  elsewhere first.

## Browse with `HfFileSystem` and URIs

Use `HfFileSystem` or the global `hffs` for fsspec integrations and convenient
`ls`, `glob`, `find`, `exists`, and `open`. Text mode must be explicit because
fsspec `open` defaults to `"rb"`. Pass `refresh=True` when stale directory
metadata is plausible.

Use canonical `hf://[TYPE/]namespace/name[@REVISION][/PATH]` URIs. Dataset,
Space, kernel, and bucket prefixes are plural and required; a model prefix is
optional. Buckets do not support revisions. Encode ordinary branch names that
contain `/`; special refs such as `refs/pr/3` are recognized directly. Parse
mounts with `huggingface_hub.utils.parse_hf_mount`, not by splitting on `:`.

Treat URI parsing as identification, not path-safety authorization. Reject
absolute paths, drive/UNC paths, and every `..` segment before local
materialization or plan application.

## Handle Buckets and Movement Safely

Buckets are mutable Xet-backed object storage, not versioned repositories. Use
`list_bucket_tree`/`download_bucket_files` for Python reads, or `hf buckets
list`, `hf cp`, and `hf sync` for CLI workflows.

For one file, use `hf cp`; for local↔bucket directories, use `sync_bucket` or
`hf sync`. Generate `dry_run=True` output or a JSONL `plan`, review every action
and destination, then apply it. Treat `delete=True` as destructive.

For remote copies, `copy_files` supports repo→repo, repo→bucket, and
bucket→bucket; bucket→repo is unsupported. Server-side copies require compatible
storage regions. A trailing slash on the source means “copy contents”; without
it, the source directory may be nested at the destination. Verify bucket prefix
boundaries so `logs` does not accidentally match `logs-old`.

## Validate the Outcome

For a no-network regression rehearsal that exercises mocked metadata, a
temporary cache, filtered offline recovery, a wrong revision, and the
`local_files_only`/`force_download` conflict, run the focused case in
[workflows](references/workflows.md#11-difficult-synthetic-offlinecache-case).
Keep the bucket prefix/traversal case there deferred until a reviewed mock plan
and authorized bucket integration are available.

- Assert the returned path exists and is the requested file/snapshot.
- For dry runs, inspect `filename`, `commit_hash`, `local_path`, `is_cached`,
  `will_download`, and aggregate only entries where `will_download` is true.
- For offline snapshots, assert all pattern-selected files exist; catch
  `IncompleteSnapshotError` and report its `snapshot_path` without claiming the
  snapshot is complete.
- For cache repair, rescan and inspect warnings before deleting anything.
- For sync/copy, inspect source/destination URI types, revisions, prefixes,
  trailing slashes, regions, and the plan's upload/download/delete actions.
- Mark network-, credential-, private/gated-, and Xet-service integration as
  deferred unless the caller explicitly authorizes and provides them.
