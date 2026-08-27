# Profiling and artifacts

Composer profiling combines a schedule, one or more trace handlers, optional PyTorch profiling, optional system profiling, and ordinary logger file upload. Keep profiling windows short unless the user explicitly wants high-overhead traces.

## Minimal Profiler recipe

```python
from composer.profiler import Profiler, JSONTraceHandler, cyclic_schedule

profiler = Profiler(
    schedule=cyclic_schedule(skip_first=0, wait=0, warmup=1, active=4, repeat=1),
    trace_handlers=[
        JSONTraceHandler(
            folder="{run_name}/traces",
            filename="ep{epoch}-ba{batch}-rank{rank}.json",
            remote_file_name="{run_name}/traces/ep{epoch}-ba{batch}-rank{rank}.json",
            merged_trace_filename=None,
            merged_trace_remote_file_name=None,
            overwrite=False,
        ),
    ],
    torch_prof_folder="{run_name}/torch_traces",
    torch_prof_memory_filename=None,
)

trainer = Trainer(..., profiler=profiler)
```

Use `overwrite=True` or a unique `run_name` for repeated local smoke tests. Keep `merged_trace_filename=None` for live runs if trace merging would add blocking overhead.

## `cyclic_schedule` semantics

`cyclic_schedule(skip_first=0, wait=0, warmup=1, active=4, repeat=1)` returns a function from `State` to `ProfilerAction`.

Per epoch, after `skip_first` batches plus any resumption offset, each cycle does:

1. `wait` batches as `SKIP`.
2. `warmup` batches as `WARMUP`.
3. `active` batches as `ACTIVE`, with the final active batch as `ACTIVE_AND_SAVE`.

`repeat=1` captures one profiling window per epoch. `repeat=0` continues cycling for the entire epoch. To capture only one short window, choose small `warmup` and `active`, ensure the training run lasts at least `wait + warmup + active` batches, and set `repeat=1`.

## `JSONTraceHandler` essentials

`JSONTraceHandler(folder="{run_name}/traces", filename="ep{epoch}-ba{batch}-rank{rank}.json", remote_file_name="{run_name}/traces/ep{epoch}-ba{batch}-rank{rank}.json", merged_trace_filename="merged_trace.json", merged_trace_remote_file_name="{run_name}/traces/merged_trace.json", overwrite=False, num_traces_to_keep=-1)` writes Chrome JSON traces.

Important behaviors:

- `folder` uses dist placeholders such as `{run_name}` and `{rank}`.
- `filename` and `remote_file_name` can also use time placeholders such as `{epoch}` and `{batch}`.
- With `overwrite=False`, the trace folder must be empty at initialization.
- Set `remote_file_name=None` to disable trace upload calls.
- Set `merged_trace_filename=None` to disable per-node merged traces.
- Set `num_traces_to_keep=0` with a remote uploader to remove local JSON traces immediately after upload; remote files are not deleted.

## PyTorch and system profiler options

`Profiler(...)` can also create internal callbacks:

- `SystemProfiler` is added when any of `sys_prof_cpu`, `sys_prof_memory`, `sys_prof_disk`, or `sys_prof_net` is enabled. Defaults record CPU statistics.
- `TorchProfiler` is added when any PyTorch profiler flag is enabled: `torch_prof_record_shapes`, `torch_prof_profile_memory`, `torch_prof_with_stack`, or `torch_prof_with_flops`. The defaults include PyTorch memory/flop profiling, so set `torch_prof_profile_memory=False` and `torch_prof_with_flops=False` if you want a JSONTraceHandler-only smoke.
- `torch_prof_folder`, `torch_prof_filename`, `torch_prof_remote_file_name`, `torch_prof_overwrite`, `torch_prof_use_gzip`, and `torch_prof_num_traces_to_keep` control PyTorch trace files.
- `torch_prof_memory_filename` controls the HTML memory timeline. If it is not `None`, all three flags must be true: `torch_prof_with_stack=True`, `torch_prof_record_shapes=True`, and `torch_prof_profile_memory=True`.

Use the Profiler marker API for custom events:

```python
marker = state.profiler.marker("data/prepare", categories=["input"])
with marker:
    prepare_batch()
```

Markers record duration, instant, and counter events through configured trace handlers according to the current schedule action.

## File and artifact upload patterns

A remote artifact is produced only when a file generator and an upload-capable destination are both configured.

Common file generators:

- `FileLogger`: local text log; default filename is `{run_name}/logs-rank{rank}.txt`.
- `TensorboardLogger`: TensorBoard event files under `tensorboard_logs/{run_name}` unless `log_dir` is set.
- `JSONTraceHandler`: Composer profiler JSON traces.
- `TorchProfiler`: PyTorch profiler JSON traces and optional memory timeline HTML.
- `MemorySnapshot` and `OOMObserver`: CUDA memory debugging artifacts.

Common upload destinations:

```python
from composer.loggers import RemoteUploaderDownloader, WandBLogger, NeptuneLogger

remote = RemoteUploaderDownloader(
    bucket_uri="s3://bucket-name",
    file_path_format_string="{remote_file_name}",
    num_concurrent_uploads=1,
    use_procs=True,
    num_attempts=3,
)
wandb = WandBLogger(log_artifacts=True)
neptune = NeptuneLogger(upload_checkpoints=True)
```

`RemoteUploaderDownloader` stages files before background upload. `upload_staging_folder` can point to faster temporary storage, but it must have enough space for the largest in-flight files. `num_attempts` retries transient object-store failures.

The helper `composer.utils.file_helpers.maybe_create_remote_uploader_downloader_from_uri(uri, loggers)` auto-adds a remote uploader for supported URI schemes when needed. Local paths return `None`. `s3://`, `oci://`, `gs://`, `azure://`, and supported `dbfs:` paths can be routed. `wandb://` is not a remote uploader URI; use `WandBLogger(log_artifacts=True)`.

## Download and validation helpers

- `RemoteUploaderDownloader.download_file(remote_file_name, destination, overwrite=False, progress_bar=True)` downloads from its configured backend.
- `composer.utils.file_helpers.get_file(path, destination, object_store=None, overwrite=False, progress_bar=True)` handles local files, URLs, supported object-store URIs, and `.symlink` indirection.
- `composer.utils.file_helpers.parse_uri(uri)` returns `(backend, bucket_name, path)` and strips leading object path slashes for remote URIs.
- `composer_validate_remote_path <remote-uri>` validates a remote path by listing objects. It expects exactly one remote URI argument.

## Environment reports

Use environment collection when debugging import/runtime mismatches, GPU availability, distributed world size surprises, or user bug reports.

CLI:

```bash
composer_collect_env
```

Python:

```python
from composer.utils.collect_env import print_env, get_composer_env_dict

print_env()                  # PyTorch + Composer text report
info = get_composer_env_dict()  # Structured Composer fields
```

`print_env()` includes PyTorch environment information when PyTorch is available, then Composer version, commit hash when available, CPU model/count, node count, accelerator model, accelerators per node, world size, and CUDA device count. `configure_excepthook()`, `enable_env_report()`, and `disable_env_report()` control automatic report printing on unhandled exceptions.

## Bundled smokes

- `scripts/logger_smoke.py` runs a tiny CPU classification loop with `InMemoryLogger` and `FileLogger`.
- `scripts/profiler_smoke.py` runs a tiny CPU profiling window with `Profiler`, `cyclic_schedule`, and `JSONTraceHandler` without downloads or external credentials.
