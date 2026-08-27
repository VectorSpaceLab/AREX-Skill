# Filesystems

Raster Vision uses a URI-dispatched file-system layer. This reference covers the built-in local, HTTP, S3, and GDAL VSI paths that matter for cloud and remote storage setup.

## Dispatch and built-ins

- `FileSystem.get_file_system(uri, mode)` consults the registry and returns the first matching file system.
- Built-in file systems live in the pipeline package:
  - `HttpFileSystem` for `http://` and `https://` reads.
  - `LocalFileSystem` as the catch-all fallback for bare local paths.
- Plugins add remote file systems:
  - `S3FileSystem` from `rastervision.aws_s3`.
  - `VsiFileSystem` from `rastervision.gdal_vsi`.
- Package initialization loads plugins before built-ins, so remote file systems are considered before the local fallback.

## Configuration and credential boundaries

Raster Vision reads config from environment variables first, then a `.env` file, then RV config files. The default RV profile file is `~/.rastervision/default`.

| Setting | Effect |
| --- | --- |
| `RV_CONFIG` | Explicit RV config file path |
| `RV_CONFIG_DIR` | Directory containing profile files |
| `RV_PROFILE` | Profile name used to pick the config file |
| `TMPDIR` / `TEMP` / `TMP` | Temporary-directory root |
| `AWS_REQUEST_PAYER=requester` | Explicit requester-pays override |
| `[AWS_S3] requester_pays=True` or `AWS_S3_REQUESTER_PAYS=yes` | RV config / env fallback for requester-pays buckets |
| `AWS_NO_SIGN_REQUEST=yes` | Use an unsigned S3 client |

Keep the AWS credential boundary explicit: requester-pays access is not the same thing as unsigned public access.

## S3 file system

`S3FileSystem` is the AWS storage plugin.

- `parse_uri()` splits `s3://bucket/key` into bucket and key.
- `local_path()` stores cached downloads under `<download_dir>/s3/<bucket>/<key>`.
- `read_bytes()` and `write_bytes()` use `boto3` with progress bars.
- `sync_from_dir()` and `sync_to_dir()` shell out to `aws s3 sync`.
- `copy_to()` uploads a file or falls back to a directory sync.
- `copy_from()` downloads a file to a local path.
- `list_paths()` returns `s3://...` URIs.

Common S3 failure modes:

- missing `AWS_NO_SIGN_REQUEST=yes` for public unsigned buckets
- missing requester-pays configuration for requester-pays buckets
- absent AWS CLI when using `sync_*` helpers

## GDAL VSI file system

`VsiFileSystem` lets GDAL handle remote and archive-backed paths.

Supported URI forms include:

- regular file paths
- `http://`, `https://`, `ftp://`
- `s3://` and `gs://`
- archive prefixes such as `zip+s3://bucket/archive.zip!inner/file.tif`
- `tar+...!`, `gzip+...!`, and `zip+...!` archive URIs

Key behavior:

- `matches_uri()` only accepts `/vsi...` paths.
- `/vsicurl/` paths are read-only for writes.
- `file_exists()`, `read_*()`, `write_*()`, `sync_*()`, and `list_paths()` all use GDAL VSI primitives.
- `local_path()` stores downloads by filename under the requested cache directory.
- `last_modified()` reports the file's mtime when available.

The plugin depends on GDAL 3.6.3.

## Local cache helpers

- `download_if_needed()` downloads a remote URI into the RV cache directory unless the local cache is already present.
- `download_or_copy()` copies local files directly and downloads remote files before moving them into the target directory.
- `start_sync()` runs a background sync loop for a local directory and a remote destination.
- `get_local_path()` centralizes the cache-path decision.

## What not to infer here

Do not use this reference to reason about training recipes, model bundles, or pipeline command semantics. Those belong in other sub-skills.
