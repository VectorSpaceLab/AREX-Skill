# Loggers and callbacks

Composer routes run observability through a central `composer.loggers.Logger`. `Trainer`, callbacks, algorithms, and custom code call `logger.log_metrics(...)`, `logger.log_hyperparameters(...)`, `logger.log_table(...)`, `logger.log_images(...)`, `logger.log_traces(...)`, or `logger.upload_file(...)`; each configured `LoggerDestination` decides what to store, display, upload, or ignore.

## Local-safe logger choices

| Need | Use | Notes |
| --- | --- | --- |
| Interactive progress | `Trainer(progress_bar=True)` / `ProgressBarLogger` | Progress bar is the default Trainer behavior. It shows train loss and validation metric snippets. Avoid enabling `progress_bar` and `log_to_console` together unless duplicate output is acceptable. |
| Plain console metrics | `Trainer(log_to_console=True, progress_bar=False, console_log_interval="100ba", console_stream="stdout" or "stderr")` / `ConsoleLogger` | Prefer Trainer arguments instead of manually constructing `ConsoleLogger`; manual construction causes related Trainer console options to be ignored. |
| Durable text log | `FileLogger(filename="{run_name}/logs-rank{rank}.txt", remote_file_name="{run_name}/logs-rank{rank}.txt", flush_interval=100, overwrite=False)` | Captures stdout/stderr by default and flushes through `logger.upload_file(...)`. Keep `{rank}` in multi-process filenames. Set `remote_file_name` explicitly when the local filename is absolute or otherwise not a good object name. |
| Programmatic assertions/notebooks | `InMemoryLogger()` | Stores `data`, `most_recent_values`, `most_recent_timestamps`, `hyperparameters`, `tables`, and provides `get_timeseries(metric)`. It is ideal for smoke tests and debugging small runs. |

## Optional integration loggers

These require their optional packages and service credentials/modes before use.

- `WandBLogger(project=None, group=None, name=None, entity=None, tags=None, log_artifacts=False, rank_zero_only=True, init_kwargs=None)` logs metrics, tables, images, hparams, and optionally artifacts. Set `log_artifacts=True` for Composer file uploads. In distributed checkpoint/artifact workflows, avoid losing nonzero-rank artifacts by considering `rank_zero_only=False`.
- `MLFlowLogger(experiment_name=None, run_name=None, tags=None, tracking_uri=None, rank_zero_only=True, flush_interval=10, model_registry_prefix="", model_registry_uri=None, synchronous=False, log_system_metrics=True, rename_metrics=None, ignore_metrics=None, ignore_hyperparameters=None, run_group=None, resume=False, logging_buffer_seconds=10, log_duplicated_metric_every_n_steps=100)` is an experiment tracker and can log system metrics through MLflow. It does not replace an upload-capable Composer `LoggerDestination` for `logger.upload_file(...)` artifacts.
- `CometMLLogger(workspace=None, project_name=None, log_code=False, log_graph=False, name=None, rank_zero_only=True, exp_kwargs=None)` logs metrics, hparams, tables, and images to Comet.
- `NeptuneLogger(project=None, api_token=None, rank_zero_only=True, upload_checkpoints=False, base_namespace="training", mode=None, **neptune_kwargs)` logs metrics/hparams/traces and can upload files only when `upload_checkpoints=True` and the destination is enabled.
- `TensorboardLogger(log_dir=None, flush_interval=100, rank_zero_only=True)` writes event files under `tensorboard_logs/{run_name}` when `log_dir` is omitted, and uploads event files through the central logger when another upload destination is present.
- `SlackLogger(include_keys=(), formatter_func=None, log_interval="1ba", max_logs_per_message=50, slack_logging_api_key=None, channel_id=None)` posts selected metrics/hparams/traces. It is for notifications, not artifact storage.
- `RemoteUploaderDownloader(bucket_uri, backend_kwargs=None, file_path_format_string="{remote_file_name}", num_concurrent_uploads=1, upload_staging_folder=None, use_procs=True, num_attempts=3)` is the general Composer file upload/download destination for object stores and remote filesystems.

## Monitoring callbacks that log through Logger

Add monitoring callbacks through `Trainer(callbacks=[...])`. They emit metrics to every configured logger destination.

| Callback | Primary output | Use when |
| --- | --- | --- |
| `SpeedMonitor(window_size=100, gpu_flops_available=None, time_unit="hours")` | `throughput/*`, per-device throughput, optional MFU, `time/train`, `time/val`, `time/total` | You need throughput and runtime visibility. |
| `RuntimeEstimator(skip_batches=1, time_unit="hours")` | `time/remaining_estimate` plus unit | You need rough time-to-completion after warmup. |
| `SystemMetricsMonitor(log_all_data=False)` | CPU, memory, disk, network, and GPU utilization metrics | You need system resource monitoring. GPU metrics require the NVIDIA monitoring dependency when CUDA is available. |
| `MemoryMonitor(memory_keys=None, dist_aggregate_batch_interval=None)` | `memory/*` CUDA allocator statistics | You need GPU memory trend metrics. It warns and no-ops on CPU models. |
| `LRMonitor()` | `lr-{OPTIMIZER_NAME}/group{GROUP_NUMBER}` | You need learning-rate visibility for each optimizer group. |
| `OptimizerMonitor(log_optimizer_metrics=True, batch_log_interval=10)` | gradient and optimizer norms such as `l2_norm/grad/global` | You need gradient/optimizer diagnostics; it can reduce throughput on large models. |
| `ActivationMonitor(interval="25ba", ignore_module_types=None, only_log_wandb=True)` | activation statistics by module | You need activation health checks; keep the interval coarse because hooks add overhead. |
| `NaNMonitor()` | raises on NaN train loss | You want immediate failure instead of silent NaN propagation. |
| `MemorySnapshot(...)` and `OOMObserver(...)` | GPU memory snapshot artifacts | Use for CUDA memory debugging; see [profiling and artifacts](profiling-and-artifacts.md). |

## Custom callback hooks

A custom `Callback` method receives `state` and `logger`, so the safe pattern is to log only small scalar summaries and leave large file generation to an explicit artifact path:

```python
from composer import Callback, State
from composer.loggers import Logger

class EpochMonitor(Callback):
    def epoch_end(self, state: State, logger: Logger):
        logger.log_metrics({"debug/epoch": int(state.timestamp.epoch)})
```

`LoggerDestination` also subclasses `Callback`, so custom destinations can flush on events such as `batch_end`, `epoch_end`, `fit_end`, or `close`. If a custom destination both generates files and implements `upload_file`, ensure it does not upload its own generated files recursively.

## Run-name and filename placeholders

`Trainer(run_name=...)` sets `state.run_name`. If not supplied, Composer creates one. Composer format helpers fill placeholders at runtime:

- Dist placeholders for logger/file destinations: `{run_name}`, `{rank}`, `{local_rank}`, `{world_size}`, `{local_world_size}`, `{node_rank}`.
- Time placeholders for profiler/checkpoint-style files: `{epoch}`, `{batch}`, `{batch_in_epoch}`, `{sample}`, `{sample_in_epoch}`, `{token}`, `{token_in_epoch}`, `{total_wct}`, `{epoch_wct}`, `{batch_wct}`.

Rules of thumb:

1. Include `{rank}` in any local or remote file generated by every rank.
2. Use `{run_name}` as the first folder component for logs, traces, and TensorBoard runs.
3. Keep remote names relative; leading slashes may be stripped, but explicit relative names are less error-prone.
4. If a placeholder remains unformatted in an output path, verify whether that path used the dist-only formatter or the dist-and-time formatter.

## Artifact upload contract

Composer upload is pull-based from classes that generate local files:

1. A component writes one local file, such as a text log, TensorBoard event file, profiler trace, or memory snapshot.
2. The component calls `logger.upload_file(remote_file_name, file_path, overwrite=False or True)`.
3. `Logger` formats `remote_file_name` and `file_path` with `{run_name}` and dist placeholders, then calls `upload_file(...)` on every destination.
4. Only destinations whose implementation uploads files store the artifact remotely. Without one, the original local file may still exist, but no remote object is created.

Upload-capable built-ins for this skill are `RemoteUploaderDownloader`, `WandBLogger(log_artifacts=True)`, and `NeptuneLogger(upload_checkpoints=True)`. `FileLogger`, `TensorboardLogger`, `JSONTraceHandler`, `TorchProfiler`, `MemorySnapshot`, and `OOMObserver` generate files, but still need an upload-capable destination for remote storage.
