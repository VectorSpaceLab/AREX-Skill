# Load, resolve, and cache

## Handle types

`hub.resolve(handle)` and `hub.load(handle)` expect string handles. Supported handle shapes in this package version include:

| Handle shape | Typical use | Result |
| --- | --- | --- |
| Local filesystem directory | A SavedModel you already exported or downloaded | Returned as a path after an existence check |
| `gs://...` directory | Cloud path to a SavedModel | Resolved through the path resolver if the TensorFlow filesystem can see it |
| Smart HTTP/HTTPS handle | A `tfhub.dev` or Kaggle Models style handle, or another endpoint that serves Hub formats | Routed through the HTTP resolver chain |
| HTTP/HTTPS `.tar`, `.tar.gz`, or `.tgz` archive | Packaged SavedModel archive | Downloaded and unpacked into cache |
| `gs://...tar`, `gs://...tar.gz`, or `gs://...tgz` archive | GCS archive | Downloaded and unpacked into cache |

If a handle does not map to a known or existing module shape, resolution fails instead of guessing.

## Load format selection

`TFHUB_MODEL_LOAD_FORMAT` controls which HTTP resolver is used.

| Value | Behavior |
| --- | --- |
| `AUTO` | Default. HTTP(S) resolves with compressed behavior. |
| `COMPRESSED` | Download archives and extract them into cache. |
| `UNCOMPRESSED` | Request a `303` redirect to a `gs://...` location and load directly from that location. |

Use `AUTO` or `COMPRESSED` for ordinary local testing and archive-backed handles. Use `UNCOMPRESSED` only when the server is expected to return a `gs://` target; a normal archive URL will not satisfy that protocol.

## Cache directory selection

`TFHUB_CACHE_DIR` chooses the cache root for downloaded modules. The effective cache is selected in this order:

1. `TFHUB_CACHE_DIR`
2. the `tfhub_cache_dir` flag
3. a caller-provided default
4. a temporary cache directory when the resolver is allowed to use one

Local SavedModel paths do not need a download step, so they can load even when no cache directory is configured.

## Download and cache artifacts

When a remote handle is cached, the resolver creates:

- a content directory for the downloaded model;
- a sibling `*.descriptor.txt` file for human identification;
- a sibling `.lock` file while a download is in progress;
- a temporary `.<task_uid>.tmp` directory during the download.

The descriptor is only an identifier. It is not a semantic input to `hub.load`, `hub.resolve`, or `KerasLayer`.

If another process owns the lock, the resolver waits. A stale lock can be reclaimed after the download temp directory shows no progress for long enough. Do not delete cache directories blindly while another process may still be downloading.

## TLS and progress knobs

- `TFHUB_DOWNLOAD_PROGRESS`: any non-empty value enables interactive download progress output.
- `TFHUB_DISABLE_CERT_VALIDATION=true`: disables TLS certificate validation for trusted test endpoints only. Leave it unset for normal public HTTPS handles.

## Safe no-download validation strategies

- Use a tiny local SavedModel directory when you want to validate `hub.resolve`, `hub.load`, or `KerasLayer` without network traffic.
- Run `../scripts/smoke_load_and_wrap.py` from this sub-skill to create and load local SavedModels automatically.
- Point `TFHUB_CACHE_DIR` at a writable temporary directory when you want to observe cache behavior without touching a shared cache.
- If the task only needs API wiring, do not start with a public network handle. Prove the local path first, then move to network resolution if the task actually requires it.

## Common failure signals

- `IOError: ... does not exist.` — the local path or mounted filesystem path is wrong.
- `ValueError: Trying to load a model of incompatible/unknown type...` — the directory is not a SavedModel directory or is missing `saved_model.pb`/`saved_model.pbtxt`.
- `IOError: ... does not appear to be a valid module.` — the archive is corrupt or not a valid Hub/SavedModel archive.
- Repeated waiting on a `.lock` file — the cache is contended or a previous download was interrupted.
