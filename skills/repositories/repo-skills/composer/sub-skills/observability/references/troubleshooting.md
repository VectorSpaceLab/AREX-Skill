# Observability troubleshooting

Use this when logs, metrics, traces, uploads, or environment reports are missing or failing. If the root cause is checkpoint policy, training construction, distributed launcher setup, or export semantics, diagnose the observability surface here and then reroute to the owning sub-skill.

## Optional dependency failures

Symptom: constructing a logger/callback raises `MissingConditionalImportError` or `ModuleNotFoundError`.

Likely fixes:

- `WandBLogger`: install the `wandb` optional dependency and configure the run mode/credentials before training.
- `MLFlowLogger`: install `mlflow`; Databricks-backed registry/tracking may also require the Databricks SDK.
- `CometMLLogger`: install `comet_ml`; table logging may require `pandas`.
- `NeptuneLogger`: install `neptune` and provide project/token settings or offline/debug mode.
- `TensorboardLogger`: install `tensorboard` so `torch.utils.tensorboard.SummaryWriter` is available.
- `SlackLogger`: install the Slack SDK and provide API key/channel settings, either as constructor args or supported environment variables.
- `RemoteUploaderDownloader` / object stores: install the backend package for the URI, such as S3/GCS/OCI/Libcloud/SFTP/DBFS support. S3 and SFTP routes may surface `streaming`, `boto3`, or `paramiko` dependency messages.
- `SystemMetricsMonitor` on CUDA: install the NVIDIA monitoring dependency if GPU metrics are requested.

Do not add optional integrations to a minimal local smoke unless the user needs that backend.

## Credentials or service setup missing

Symptom: logger initializes but sends nothing, prints warnings about missing keys/channel/project, or fails at first network call.

Checklist:

1. Confirm the service package is installed.
2. Confirm the service is in the intended mode: online, offline, disabled, debug, or read-only as supported by that integration.
3. Provide project/workspace/entity/run names through constructor args when reproducibility matters.
4. For Slack, `include_keys` must be non-empty and match metric names, and key/channel settings must be present.
5. For Neptune, set `upload_checkpoints=True` only when file upload to Neptune is desired.
6. For WandB file artifacts, set `log_artifacts=True`; metrics can work even when file uploads are disabled.
7. For distributed artifact capture, verify whether `rank_zero_only=True` is discarding files or metrics from nonzero ranks.

## Local file exists or output folder is not empty

Symptom: `FileExistsError` during logger/profiler/callback initialization or first flush.

Common causes and fixes:

- `FileLogger(overwrite=False)` opens the text log in exclusive-create mode. Use a unique `run_name`, include `{rank}`, choose a new filename, or set `overwrite=True` for disposable smokes.
- `JSONTraceHandler(overwrite=False)`, `TorchProfiler(overwrite=False)`, `MemorySnapshot(overwrite=False)`, and `OOMObserver(overwrite=False)` require their output folders to be empty. Use a unique `{run_name}` folder or set `overwrite=True` when replacing old smoke outputs is safe.
- Time placeholders can create future-name conflicts in checkpoint-like patterns. If the conflict involves checkpoint filenames or autoresume behavior, reroute configuration changes to `../training/SKILL.md` after identifying the filename pattern.

## Logger generated files but no remote upload happened

Symptom: checkpoints, trace files, TensorBoard event files, or text logs exist locally but nothing appears in remote storage.

Diagnosis:

1. Confirm an upload-capable destination is in `Trainer(loggers=[...])` at the same time as the file generator.
2. `FileLogger`, `TensorboardLogger`, `JSONTraceHandler`, `TorchProfiler`, `MemorySnapshot`, and `OOMObserver` generate files but do not themselves provide general remote storage.
3. Add `RemoteUploaderDownloader(...)`, `WandBLogger(log_artifacts=True)`, or `NeptuneLogger(upload_checkpoints=True)` depending on the target.
4. Check whether the component set `remote_file_name=None`; that disables upload calls for that file type.
5. Check rank filtering: `rank_zero_only=True` can intentionally suppress nonzero-rank uploads for some integrations.
6. Verify that `Trainer.fit()`, `Trainer.eval()`, `Trainer.predict()`, or `trainer.close()` reached the event where the uploader waits for workers. Early process termination can leave background uploads unfinished.

## Remote URI parse and object-store issues

Symptom: `NotImplementedError`, credential validation failure, empty remote listing, or upload worker crash.

Checklist:

- Parse first: `parse_uri("s3://bucket/path")` should yield a backend, bucket, and object path. Local paths have an empty backend.
- For general uploading, prefer `RemoteUploaderDownloader(bucket_uri="s3://bucket")` plus relative `remote_file_name` values. Put subfolders in `file_path_format_string` only when checkpoint latest-file/autoresume constraints do not apply.
- `maybe_create_remote_uploader_downloader_from_uri(...)` can auto-create uploaders for supported schemes such as `s3://`, `oci://`, `gs://`, `azure://`, and supported `dbfs:` paths. It intentionally rejects `wandb://`; use `WandBLogger(log_artifacts=True)` instead.
- `RemoteUploaderDownloader.init()` validates credentials by uploading a tiny object. A failure here usually means missing permissions, wrong bucket/container, wrong region/host, or a missing backend dependency.
- Upload workers surface fatal errors on later `batch_end` or `epoch_end`; if a worker died, inspect the original object-store exception, not only the generic worker-crash message.
- For duplicate remote names with `overwrite=False`, use unique `{run_name}`, `{rank}`, and time placeholders or pass `overwrite=True` when replacement is intended.

## `composer_validate_remote_path` surprises

Symptom: `composer_validate_remote_path --help` or no arguments raises an error instead of conventional help text.

This entry point expects exactly one remote URI argument. Use it as:

```bash
composer_validate_remote_path s3://bucket-name/prefix
```

It lists objects at the path and raises if no objects are found or credentials/path parsing fail. Use it to validate object-store access, not as a general CLI help command.

## Filename placeholder mistakes

Symptom: braces remain in output names, ranks overwrite each other, or uploads land under unexpected object names.

Fixes:

- Use dist placeholders (`{run_name}`, `{rank}`, `{local_rank}`, `{world_size}`, `{local_world_size}`, `{node_rank}`) for logger filenames and remote names.
- Use time placeholders (`{epoch}`, `{batch}`, `{sample}`, `{token}`, and `*_in_epoch` variants) only in contexts that format with a `Timestamp`, such as profiler trace filenames and checkpoint-style patterns.
- Always include `{rank}` for files written by all ranks.
- Set `FileLogger(remote_file_name=...)` when `filename` is an absolute or temporary local path; otherwise that path shape can leak into remote object names.
- Keep `RemoteUploaderDownloader(file_path_format_string="{remote_file_name}")` when using `save_latest_filename`; move checkpoint path structure into checkpoint save arguments instead.

## Autoresume with remote uploads

Symptom: constructing `Trainer(autoresume=True, ...)` fails with a message about concurrent uploads.

Composer requires every `RemoteUploaderDownloader` to use `num_concurrent_uploads=1` when `autoresume=True`. The reason is safety: a latest symlink/object could otherwise upload before the checkpoint it points to. Also, when `save_latest_filename` is enabled, non-default `file_path_format_string` on `RemoteUploaderDownloader` is not supported because latest-file contents do not account for that extra formatting. Diagnose the uploader here, but make checkpoint policy changes through `../training/SKILL.md`.

## Profiler memory timeline option errors

Symptom: `ValueError` says `torch_prof_memory_filename` requires three flags.

Fix:

```python
Profiler(
    ...,
    torch_prof_memory_filename="rank{rank}.{batch}.pt.memory_trace.html",
    torch_prof_with_stack=True,
    torch_prof_record_shapes=True,
    torch_prof_profile_memory=True,
)
```

If the memory timeline is not required, set `torch_prof_memory_filename=None`. For the lightest JSONTraceHandler-only smoke, also set `torch_prof_profile_memory=False` and `torch_prof_with_flops=False` to avoid creating the PyTorch profiler.

## Profiler captures too much or nothing

Symptom: trace folder is huge, no trace is saved, or only warmup events appear.

Checklist:

1. Ensure the run lasts at least `skip_first + wait + warmup + active` batches for one save.
2. Use `repeat=1` for one window, not `repeat=0`.
3. Use `train_subset_num_batches` or a short dataloader for controlled smokes.
4. Set `merged_trace_filename=None` to avoid merge overhead during live debugging.
5. Set `num_traces_to_keep=0` only when an upload destination is definitely present and working; otherwise local traces will be deleted after upload attempts.
6. Check that `remote_file_name` is not `None` if remote trace upload is expected.

## Callback order and duplicate output

Symptom: console output is duplicated, logs appear out of order, or custom callback metrics are missing.

Fixes:

- Avoid enabling both progress bar and console logging unless desired.
- Logger destinations are callbacks and can flush on events. Custom callbacks should call `logger.log_*` methods rather than writing directly to destination internals.
- If a metric is produced before a destination initializes, use destinations that queue early writes (`FileLogger` does this for text writes) or log at standard events such as `batch_end`, `epoch_end`, or `fit_end`.
- If a custom destination generates files and also uploads files, guard against recursive upload loops.
