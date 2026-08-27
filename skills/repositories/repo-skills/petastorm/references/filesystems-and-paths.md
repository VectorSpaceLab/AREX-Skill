# Filesystems and Paths

## Purpose

Read this when a task uses local files, HDFS, S3, or GCS URLs, or when a workflow fails because a dataset path is malformed.

## Verified URL handling

Petastorm uses `FilesystemResolver` and `get_filesystem_and_path_or_paths` to turn dataset URLs into filesystem objects and dataset paths.

### Supported schemes

- `file://` for local paths
- `hdfs://` for HDFS-backed paths
- `s3://` for S3-backed paths
- `gs://` or `gcs://` for GCS-backed paths

### Rules that matter

- Scheme-less paths are rejected. Use `file://` for local data.
- `normalize_dir_url()` trims a trailing slash from directory URLs.
- `get_filesystem_and_path_or_paths()` requires every URL in a list to share the same scheme and netloc.
- `get_dataset_path()` returns the path component for `file://` and `hdfs://` URLs, and strips the protocol for fsspec-backed URLs.
- For S3 and GCS, the bucket must be in the netloc, not hidden in the path.

## HDFS notes

- `hdfs_driver='libhdfs3'` is the default path used by the package.
- `hdfs_driver='libhdfs'` uses the Java-based HDFS bridge.
- Resolver behavior depends on the Hadoop configuration that Spark provides.

## Storage options

`storage_options` is forwarded to the relevant fsspec filesystem constructor for supported non-HDFS schemes.

## Common failure signals

- `ValueError: ERROR! A scheme-less dataset url` means the path needs a `file://` prefix.
- `ValueError: URLs must be of the form s3://bucket/path` or a similar bucket error means the bucket/netloc is missing.
- `ValueError: The dataset url list must contain url with the same scheme and netloc` means mixed URL families were supplied.

## Next step

If the problem is only about how to spell the URL, fix the path first. If the problem is about missing filesystem support, read the
relevant sub-skill troubleshooting file for the exact extra or backend.
