# Troubleshooting

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| Two event files or scrambled counters from worker processes | More than one `GlobalSummaryWriter` instance was created, or the writer was created too late for the process model being used. | Create one writer in the owner process, install it before workers start, and close it after join. On spawn-based systems, validate the handoff carefully or fall back to a queue-based design. |
| Events do not appear until the process exits | The writer was never closed or flushed, or `flush_secs` is too long for the smoke you are running. | Call `close()` in the owning process and use a shorter flush interval for smoke checks. |
| `RecordWriter("s3://...")` behaves like a local file or fails to route | The path prefix is wrong or no factory is registered for that scheme. | Use the exact `s3://` or `gs://` scheme and avoid colons in custom prefixes. |
| `ImportError: boto3 must be installed for S3 support.` | S3 support is optional and `boto3` is missing. | Install `boto3` or use the local filesystem / mock S3 smoke instead. |
| `ImportError: google-cloud-storage` for a `gs://` path | GCS support is optional and `google-cloud-storage` is missing. | Install the dependency or stay on the local fallback path. |
| S3 uploads fail even though `boto3` is installed | Bad credentials, wrong bucket/key, network failure, or a bad `S3_ENDPOINT`. | Check the bucket name, object key, endpoint, and credentials. Use the bundled mock S3 smoke first. |
| GCS uploads fail or race with other writers | A different writer changed the blob generation or the path is being reused concurrently. | Use a fresh path, keep one writer per output, and respect the generation-match behavior. |
| Comet turns on unexpectedly or raises on enable | The default is disabled, or `disabled=False` was set without `comet_ml` and Pillow. | Leave Comet disabled for local work or install the missing dependencies before enabling it. |
| Comet warns about an existing global experiment | A manual Comet experiment already exists in the process. | Avoid creating a separate experiment in the same process, or accept the warning if that is intentional. |
| The GPU telemetry helper cannot import `nvidia_smi` | The telemetry source is optional and missing, or no NVIDIA runtime is available. | Skip that path and log only the values you already have. |
| `register_writer_factory` rejects a custom scheme | The prefix included `:`. | Choose a simple prefix without a colon. |
| The bundled multiprocessing smoke skips multiprocessing | The platform does not expose the `fork` start method. | Run the single-process path, or redesign the process handoff for the platform's start method. |

## Reminder

This sub-skill does not promise real cloud verification, Comet delivery, or GPU
sampling. Those are optional integrations and should stay help-only unless the
user explicitly requests otherwise.
