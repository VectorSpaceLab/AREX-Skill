# Downloads and Storage Troubleshooting

Start read-only. Record the exact API/CLI call without token values, exception
type, repository or bucket URI, revision, selected patterns, and effective cache
root. Run:

```bash
python scripts/diagnose_download_env.py --pretty --scan-cache
```

Then use the narrow row below. See [configuration and cache semantics](configuration-cache-and-storage.md)
for layout details and [workflows](workflows.md) for corrected recipes.

## Fast Triage

1. **Identity:** confirm repository/bucket id, resource type, revision, path, and
   custom endpoint.
2. **Access:** decide whether the resource is public, private, or gated; check
   token presence without displaying it.
3. **Mode:** identify ordinary, `dry_run`, `local_files_only`, process-wide
   offline, or `force_download` behavior.
4. **Storage:** confirm `cache_dir` versus `local_dir`, payload existence, free
   space, permissions, and symlink mode.
5. **Transfer:** determine whether HTTP or Xet was selected and whether a
   bounded fallback is possible.
6. **Mutation:** for copy/sync, stop before execution and re-check URI types,
   prefixes, trailing slash, plan actions, and traversal safety.

## Repository Identity, Revision, and Access

| Symptom | Likely cause | Recovery and validation | Stop/defer condition |
|---|---|---|---|
| `RepositoryNotFoundError` / 404 | Wrong id, wrong `repo_type`, renamed/deleted repo, or private resource hidden by auth | Compare the browser/API identity; set `repo_type="dataset"`, `"space"`, or `"kernel"` explicitly where needed; retry a metadata read with authorized token policy. Do not assume 404 means public nonexistence. | Defer if identity or access rights cannot be established. |
| `RevisionNotFoundError` | Branch/tag/ref absent for that repository/type; short or malformed commit; URI parsed revision differently | List refs when network is authorized; use full 40-character commit; encode `/` in ordinary branch names as `%2F`; use `refs/pr/N` directly for PR refs. | Do not fall back silently to `main` when reproducibility matters. |
| Offline `LocalEntryNotFoundError` for a known download | Different cache root, repo type, revision, endpoint, or filename; payload absent; branch ref missing | Compare the preparation and offline calls field by field. Inspect `refs/`, snapshot path, and payload existence. Retry with full prepared commit. `try_to_load_from_cache` can distinguish payload, known absence, and unknown. | Restore network/access if no matching payload exists; metadata cannot create content offline. |
| `DryRunError` from snapshot | Dry run needs repository access to resolve/list the snapshot | Run dry run during an authorized online/preparation phase, then pin its commit. For offline inventory, use `get_cached_repo_tree` plus payload existence checks, not dry run. | Defer remote sizing when network/access is unavailable. |
| `GatedRepoError`, 401, or access-request message | Terms not accepted, missing/expired token, token lacks read scope, or implicit token disabled | Accept gating terms in the proper account; use a read-scoped token from a secret source; check `HF_HUB_DISABLE_IMPLICIT_TOKEN`; retry a minimal metadata read. Never paste the token in logs. | User/account authorization is required; do not bypass gating. |
| Public call works but private/gated listing does not | `token=False`, disabled implicit token, wrong active account, or secret not injected | Check `HF_TOKEN` presence and stored token presence with the diagnostic; use `token=True` only when a stored token is expected, or pass a vault-loaded value. | Defer if credential provenance is unclear. |
| Wrong files from `main` across multiple calls | Branch moved between independently resolved calls | Use one `snapshot_download`, or resolve once and pass a `ResolvedRevision`/full commit to every download. | Do not claim a coherent snapshot from separately moving branch heads. |

## Missing, Incomplete, or Corrupted Local Content

| Symptom | Likely cause | Recovery and validation | Stop/defer condition |
|---|---|---|---|
| `IncompleteSnapshotError` | Cached tree listing knows selected files are missing after interruption/deletion | Read `error.snapshot_path` only for diagnosis. Keep identical `repo_id`, `repo_type`, revision, and filters; restore network/access and rerun. Rehearse offline and assert every selected path. | Never treat the partial directory as a complete snapshot. |
| Snapshot directory exists but completeness is uncertain | Old/handmade cache has no `trees/<commit>.json`; folder existence alone is weak evidence | Use `get_cached_repo_tree`; if no listing exists, repopulate through an authorized snapshot call and verify files/checksums. | Keep status “unknown,” not “complete,” until verified. |
| `hf_hub_download(..., local_files_only=True)` returns an existing `local_dir` file with suspect contents | Local mode permits existing materialized content when remote validation is impossible | Preserve evidence, compare local metadata and expected commit/hash, then run `hf cache verify ... --local-dir ...` under authorized network conditions or re-materialize to a clean directory. | Do not use suspect bytes for security-sensitive work. |
| `RemoteEntryNotFoundError` / missing filename | Path does not exist at selected revision, case mismatch, wrong subfolder, or `.no_exist` records known absence | List the selected revision, check exact case and POSIX separators, and distinguish `_CACHED_NO_EXIST` from `None`. Correct the path; do not create a zero-byte substitute. | Defer if listing requires unavailable access. |
| Cache scan reports broken symlink, missing snapshots, invalid repo layout, or ref to missing commit | Manual deletion/edit, interrupted external cleanup, or filesystem damage | Record `scan_cache_dir().warnings`; identify affected repo/revision. Prefer re-download into a clean cache root. Preview `hf cache rm <target> --dry-run` before removing only the affected entry. | Do not manually delete shared blobs while snapshots reference them. |
| `*.incomplete` files consume space | Interrupted downloads left partial blobs | Confirm no transfer is active; run `hf cache prune --dry-run`; review incomplete count/bytes; then prune with approval. | Do not delete an active download's temporary state. |
| Cache metadata exists but payload does not | Refs/trees/`.no_exist` are metadata, not content; snapshot pointer may have been removed while blob remains or vice versa | Use `try_to_load_from_cache`; inspect both selected snapshot path and blob/pointer state; rerun normal download to recreate safe pointers/materialize content. | Do not claim cache hit based only on metadata. |
| User edited a shared-cache file | Returned pointer targeted a deduplicated blob, potentially affecting several snapshots | Stop consumers; identify all affected revisions with cache scan; remove/re-download the affected cached revision through supported cleanup/download flows. Future edits belong in `local_dir` or a copy. | Treat affected cache content as untrusted until revalidated. |

## Offline, Force, Timeout, and Network Mode

| Symptom | Likely cause | Recovery and validation | Stop/defer condition |
|---|---|---|---|
| `ValueError` mentions both `force_download` and `local_files_only` | Conflicting requests: fresh network transfer versus no network | Remove `force_download` for offline use. If corruption requires replacement, restore network and run a clean/forced online call after free-space checks. | A fresh transfer cannot be completed offline. |
| `ValueError: Cannot pass force_download=True when offline mode is enabled` | `HF_HUB_OFFLINE=1` was read at import | Start a fresh process with offline disabled for the authorized repair. Changing the variable after import is insufficient. | Defer when process policy forbids network. |
| Existing cached file still triggers metadata HTTP | Normal mode checks whether a branch/tag changed | Pin a full commit or prepared `ResolvedRevision`, or set call-scoped `local_files_only=True`; use process-wide offline only when all Hub calls must be blocked. | Do not disable freshness checks unknowingly for mutable revisions. |
| Metadata timeout falls back or call is slow | `HF_HUB_ETAG_TIMEOUT`, proxy/firewall, or slow endpoint | Run diagnostic; test endpoint resolution; set a bounded timeout before import; use cached pinned content if valid. `HF_HUB_DOWNLOAD_TIMEOUT` governs payload requests separately. | Proxy, SSL, or firewall repair needs host/operator ownership. |
| Proxy error is raised instead of cache fallback | Proxy configuration errors are surfaced deliberately | Correct proxy/CA settings or use a verified offline cache. Do not repeatedly force. | Defer infrastructure configuration to the operator. |
| Retry loops on a large file | Unstable network, low payload timeout, insufficient disk, or Xet failure | Stop repeated forced attempts; check free space and incomplete state; isolate HTTP versus Xet with one bounded file; increase timeout only with evidence. | Avoid expensive retries without size/budget approval. |

## Disk Space, Paths, and Permissions

| Symptom | Likely cause | Recovery and validation | Stop/defer condition |
|---|---|---|---|
| “Not enough free disk space” warning or `ENOSPC` | Payload, duplicate no-symlink snapshots, Xet cache, or incomplete files exceed available capacity | Aggregate dry-run `will_download` bytes; check free bytes for Hub and Xet roots; preview cache prune/removal; move `HF_HUB_CACHE`/`HF_XET_CACHE` in a fresh process if approved. Leave headroom for reconstruction/temp files. | Do not start/force when capacity is below payload plus working space. |
| Cache path is a file / `scan_cache_dir` raises | Misconfigured `HF_HUB_CACHE` or `--cache-dir` | Point to a directory or create an approved empty directory; rerun diagnostic. | Do not overwrite an unrelated file. |
| Permission denied creating refs, blobs, locks, or local metadata | Cache/local directory not writable, wrong ownership, or read-only mount | Existing cache hits may work read-only, but new downloads need writable targets. Choose an owned cache/local directory; do not recursively chmod shared caches without authorization. | Host permission changes need owner approval. |
| Long path / invalid filename on Windows | Path length, absolute/drive/UNC path, or unsafe segment | Choose a shorter local/cache root; preserve POSIX repository-relative paths; reject absolute, drive-relative, UNC, and `..` segments. | Do not normalize away traversal indicators. |
| Local output overwritten/truncated unexpectedly | Single-file bucket/repo copy targeted an existing path | Use a new destination or explicit backup; inspect source and destination. Bucket download intentionally replaces the requested local file. | Preserve valuable local data before rerun. |

## Symlink and No-Symlink Failures

| Symptom | Likely cause | Recovery and validation | Stop/defer condition |
|---|---|---|---|
| Windows symlink warning | Developer Mode/admin unavailable | Enable Developer Mode only if policy permits; otherwise use degraded no-symlink mode and budget duplicate storage. `HF_HUB_DISABLE_SYMLINKS_WARNING` only hides the message. | Do not require elevation merely to silence a warning. |
| Broken links when cache is shared between Linux and Windows/NAS clients | Cross-platform link target semantics or filesystem limitation | Use per-platform caches, or set `HF_HUB_DISABLE_SYMLINKS=1` before import for a compatible copy-based cache. Re-download affected snapshots. | Avoid mixed-client mutation of an already inconsistent cache. |
| Disk usage much larger than logical revision sizes | Symlinks unavailable/disabled, so payloads are copied into snapshots | Confirm diagnostic symlink mode and scan sizes. Clean only with supported cache strategy; re-enable links only on a compatible filesystem. | Deduplication cannot be claimed in no-symlink mode. |
| Shared-cache returned path was treated as writable | Snapshot pointer/blob is cache-managed | Materialize with `local_dir` or copy outside cache. Revalidate any edited cache entries. | Stop downstream use until content integrity is known. |

## Xet Missing or Failing

| Symptom | Likely cause | Recovery and validation | Stop/defer condition |
|---|---|---|---|
| `hf_xet` not installed | Minimal/old installation or optional package removed | Install/upgrade `huggingface_hub` through an approved package manager. For repository files, ordinary HTTP fallback should remain available. | Installation needs network and environment-mutation approval. |
| Xet metadata present but HTTP path used | Xet unavailable or `HF_HUB_DISABLE_XET=1` | Check diagnostic fields. If acceleration is wanted, start a fresh process with a compatible `hf_xet` and Xet enabled. | HTTP success is valid; do not call it cache corruption. |
| `XetDownloadError`, CAS/token refresh error, or reconstruction failure | Service/auth issue, incompatible `hf_xet`, bad cache state, or disk pressure | Check package versions, access, Xet root/free space. Retry one bounded file. In a fresh process set `HF_HUB_DISABLE_XET=1` to test repository HTTP fallback. Redact signed URLs/tokens from diagnostics. | Bucket storage or huge-file failures may require service/operator investigation. |
| Xet is slow on HDD | Parallel random reconstruction writes | In a fresh process try `HF_XET_RECONSTRUCT_WRITE_SEQUENTIALLY=1`; compare a bounded transfer. | Do not tune concurrency blindly on shared systems. |
| Host is saturated | `HF_XET_HIGH_PERFORMANCE=1` or excessive workers/range gets | Disable high-performance mode; lower snapshot `max_workers`; restore documented Xet range settings; rerun bounded measurement. | Resource policy/budget overrides throughput. |
| Xet cache is large | Chunk/shard/staging optimization/resume state accumulated | Confirm no active transfer. Inspect path and capacity; remove only with explicit approval, understanding that dedupe and upload-resume state is lost. | Do not delete active staging data. |
| `HF_HUB_ENABLE_HF_TRANSFER` warning | Deprecated transfer variable | Remove it; use Xet defaults or `HF_XET_HIGH_PERFORMANCE` only when approved. | Do not install deprecated `hf_transfer` as repair. |

## `HfFileSystem`, URI, and Mount Errors

| Symptom | Likely cause | Recovery and validation | Stop/defer condition |
|---|---|---|---|
| `HfUriError` says missing `hf://` | Plain path passed to strict URI parser | Add canonical protocol, or pass a recognized Hub web URL. `HfFileSystem` direct methods may omit protocol, but `parse_hf_uri` and fsspec URLs should not. | Never guess whether an arbitrary URL is a Hub resource. |
| “type prefix must be plural” | Used `model/`, `dataset/`, `space/`, or `bucket/` | Use `models/`, `datasets/`, `spaces/`, `kernels/`, or `buckets/`; model prefix may be omitted. | — |
| `hf://gpt2` rejected though plain API id works | Strict URI grammar requires `namespace/name` | Use the canonical namespaced repository identity in the URI, or use a plain API/CLI repo id where supported. | Do not invent a namespace. |
| Bucket URI rejects revision | Buckets are unversioned object storage | Remove `@revision`. If version history is required, use a repository rather than a bucket. | Do not emulate revision in URI parsing. |
| File path/revision split incorrectly for branch containing `/` | Ordinary branch slash was not encoded | Encode as `feature%2Fname`; special refs `refs/pr/N` and `refs/convert/...` remain explicit. Alternatively pass `revision=` separately where supported. | Avoid ambiguous ad hoc parsing. |
| Revision encoded in URI conflicts with `revision=` argument | Two sources disagree | Choose one authoritative revision and make both identical, or remove one. | Never silently prefer one for reproducible reads. |
| Mount parser says missing/invalid mount path | Missing `:/absolute/path`, root-only `/`, or malformed `:ro`/`:rw` | Use `parse_hf_mount("hf://...:/mnt[:ro|:rw]")`; mount path must be absolute and not `/`. | Mounting is an external runtime action; obtain relevant permission. |
| `open()` returns bytes or text handling fails | fsspec defaults to `"rb"` | Pass `"r"`/encoding for text. Use `block_size=0` only for intended streaming. Append is unsupported. | — |
| Stale `ls`/`exists` after mutation | `HfFileSystem` directory/resource caches | Pass `refresh=True` or call `invalidate_cache(path)`; then re-list. | Mutations themselves belong to `hub-operations`. |
| `HfFileSystem.cp_file` fails with buckets | That method is repository-only | Use `copy_files`, `download_bucket_files`, `hf cp`, or bucket sync depending direction. | Bucket→repo remains unsupported. |

## Bucket Prefix, Trailing Slash, Copy, and Sync Safety

| Symptom | Likely cause | Recovery and validation | Stop/defer condition |
|---|---|---|---|
| Listing/sync prefix `logs` includes `logs-old` or `sub` appears to include `submarine.txt` | Backend prefix matching is lexical rather than component-aware | Keep only paths equal to the prefix or beginning with `prefix + "/"`. Use the high-level filesystem/sync code that enforces this boundary; verify planned relative paths. | Do not apply a plan built by unsafe custom prefix stripping. |
| Double slash in remote destination | Prefix ended `/` and custom code appended another `/` | Normalize the URI with the centralized parser and join one separator. High-level sync handles trailing prefix slashes. | Do not normalize `..` away. |
| Copied folder nested unexpectedly | Source omitted trailing slash and destination exists as a directory | Decide explicitly: `source/` copies contents; `source` may nest the source directory. Dry-run/list destination where possible and inspect target paths. | Do not rerun until overwrite/nesting impact is known. |
| Files copied directly into destination unexpectedly | Source had trailing slash | Remove trailing slash to request directory nesting, or change destination. Remember the parser strips the slash but `copy_files` inspects the original source string. | Preserve existing destination files before correction. |
| Bucket→repo copy raises `ValueError` | Unsupported direction | Use an explicitly reviewed download-then-repository-upload/commit workflow and route mutation to `hub-operations`, or reverse the storage design. | Requires credentials, writes, and commit policy; do not improvise here. |
| Server-side copy fails across regions | Source and destination storage regions differ | Choose compatible destination region or use approved download/re-upload if supported. | Large transfer cost/network/credentials need approval. |
| Small repo file copy to bucket transfers data | File lacks Xet hash | Expected fallback: the client downloads and re-uploads it. Budget/network accordingly. | Do not claim every remote copy is server-side. |
| `sync_bucket` rejects two locals or two remotes | Exactly one side must be local directory and one side a bucket URI | Use OS tools for local↔local, `copy_files` for supported remote↔remote, and `snapshot_download`/`hf download` for repository trees. | — |
| Sync plan deletes unexpected files | `delete=True`, broad prefix, or altered/untrusted plan | Do not apply. Recompute without delete, narrow prefix/filter, inspect every `delete` action and plan header. Protect plan files as executable input. | Any unexplained delete is a hard stop. |
| Crafted plan contains `../`, absolute, drive, or UNC path | Untrusted/corrupt plan or malicious remote key | Reject before applying. High-level sync validates relative paths both when listing remote keys and when applying plan operations. Confirm destination containment with resolved paths. | Never bypass traversal validation. |
| Missing bucket file only warns | `download_bucket_files` defaults to `raise_on_missing_files=False` | Set `raise_on_missing_files=True` when completeness is required; verify all destination paths. | Do not report success for required missing files. |
| Bucket file download leaves unexpected old suffix | Unsafe/custom overwrite logic | Supported bucket download opens/truncates the destination. Re-run through `download_bucket_files` after preserving evidence and verifying source. | Do not concatenate or partially overwrite binary payloads. |

## Path Traversal Protection Checklist

Before materializing a repository/bucket path or applying a plan:

1. Treat remote path and plan content as untrusted.
2. Reject empty segments where the URI grammar forbids them.
3. Reject `..` as a complete segment under both `/` and `\` separators.
4. Reject POSIX absolute paths, Windows drive/drive-relative paths, and UNC
   roots.
5. Join to an absolute destination root, resolve the result, and assert the
   destination root is a parent (or the same allowed path).
6. Never “sanitize” by silently removing traversal segments; fail visibly.
7. Revalidate saved plans at apply time, not only when they were generated.

The high-level local-folder and bucket-sync implementations perform these
checks, including on loaded plans. Custom copy/materialization code must retain
the same protections.
