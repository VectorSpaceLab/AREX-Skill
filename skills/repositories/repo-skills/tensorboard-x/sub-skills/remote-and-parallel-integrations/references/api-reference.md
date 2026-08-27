# API Reference

This sub-skill covers integration boundaries, not payload-shape detail. For
scalar, image, audio, video, text, mesh, graph, and projector payload rules,
see the sibling sub-skills.

## GlobalSummaryWriter

| Symbol | Verified signature or behavior |
| --- | --- |
| `GlobalSummaryWriter.__init__` | `__init__(logdir=None, comment='', purge_step=None, max_queue=10, flush_secs=120, filename_suffix='', write_to_disk=True, log_dir=None, coalesce_process=True, **kwargs)` |
| `GlobalSummaryWriter.add_scalar` | `add_scalar(tag, scalar_value, walltime=None)`; step counters are managed per tag. |
| `GlobalSummaryWriter.add_image` | `add_image(tag, img_tensor, walltime=None, dataformats='CHW')`. |
| `GlobalSummaryWriter.add_text` | `add_text(tag, text_string, walltime=None)`. |
| `GlobalSummaryWriter.getSummaryWriter` | Returns the in-process singleton; creates one on demand if missing. |
| `GlobalSummaryWriter.close` | Flushes and closes the underlying writer. |
| `file_writer` property | Proxies the underlying file writer for logdir and flush access. |

Practical rule: create one `GlobalSummaryWriter` in the owner process before
starting workers. If multiple modules call `getSummaryWriter()`, they should all
resolve to that same process-local singleton.

## RecordWriter and prefix factories

| Symbol | Verified signature or behavior |
| --- | --- |
| `register_writer_factory(prefix, factory)` | Registers a backend factory. `prefix` cannot contain `:`. |
| `REGISTERED_FACTORIES` | Built-in registry includes `s3` and `gs`. |
| `directory_check(path)` | Uses the registered factory when the prefix matches; otherwise creates a local directory. |
| `open_file(path)` | Uses the registered factory when the prefix matches; otherwise opens a local file in binary mode. |
| `RecordWriter(path)` | Routes to the registered factory when the path has a known prefix; otherwise uses the local filesystem. |
| `RecordWriter.write(data)` | Wraps the data in TensorFlow record framing before forwarding to the file backend. |
| `RecordWriter.flush()` | Flushes the underlying writer and fsyncs local files when possible. |
| `RecordWriter.close()` | Closes the underlying writer. |

## Remote backends

| Symbol | Verified signature or behavior |
| --- | --- |
| `S3RecordWriter(path)` | Requires `boto3`. Accepts `s3://bucket/key` style paths. |
| `S3RecordWriter.bucket_and_path()` | Splits the bucket name from the remaining object key. |
| `S3RecordWriter.flush()` | Uploads the current buffer with a boto3 S3 client and honors `S3_ENDPOINT` when set. |
| `S3RecordWriterFactory` | Registered under the `s3` prefix. |
| `GCSRecordWriter(path)` | Requires `google-cloud-storage`. Accepts `gs://bucket/key` style paths. |
| `GCSRecordWriter.bucket_and_path()` | Splits the bucket name from the remaining blob path. |
| `GCSRecordWriter.flush()` | Uploads with a generation-match constraint to reduce race conditions. |
| `GCSRecordWriterFactory` | Registered under the `gs` prefix. |

Local files remain the default fallback when no prefix factory matches.

## Comet forwarding

| Symbol | Verified signature or behavior |
| --- | --- |
| `CometLogger(comet_config={"disabled": True})` | Default disabled mode; no network side effect. |
| `CometLogger(... disabled=False ...)` | Raises if `comet_ml` or Pillow are missing. |
| `SummaryWriter(..., comet_config=...)` | Supports Comet forwarding for supported writer events when enabled. |

Comet runs are opt-in. Keep the disabled default for ordinary local or mock
checks.

## Optional telemetry source

The package does not own GPU sampling. A telemetry source such as `nvidia_smi`
may provide numbers that you pass to `SummaryWriter.add_scalar`. If the source is
missing or there is no GPU, treat that path as optional and skip it.
