---
name: observability
description: "Configure Composer logging, callbacks, artifact uploading,
  profiling, environment reports, and monitoring for training runs."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Composer Observability

Use this sub-skill when a Composer task is about making run state visible: metrics/loggers, callback-based monitoring, file and artifact uploads, profiler traces, TensorBoard, environment reports, or diagnosing why observability outputs are missing.

## Route here

- Add local metrics capture with `InMemoryLogger`, `ConsoleLogger`, `ProgressBarLogger`, or `FileLogger`.
- Configure external experiment trackers such as Weights & Biases, MLflow, Comet ML, Neptune, Slack, or TensorBoard.
- Decide which callback owns a monitoring concern: speed, memory, learning-rate, optimizer, NaN/OOM, early stopping, threshold stopping, runtime estimate, image visualization, or MLPerf reporting.
- Upload Composer-generated files such as checkpoints, logs, TensorBoard event files, profiler traces, or custom artifacts.
- Configure `Profiler`, `JSONTraceHandler`, `cyclic_schedule`, and short trace windows.
- Run or interpret `composer_collect_env` output when debugging hardware, Python, PyTorch, or CUDA availability.
- Diagnose missing log files, empty metric collections, absent uploaded artifacts, invalid remote paths, or profiler option conflicts.

## Reroute

- Training loop construction, optimizer/dataloader setup, checkpoint save/load/autoresume semantics: use `../training/SKILL.md`.
- Algorithm method behavior, method-specific events, or speedup recipe choices: use `../methods/SKILL.md`.
- Distributed launcher, rank topology, backend initialization, FSDP/TP config, or automatic microbatching: use `../distributed/SKILL.md`.
- Model export APIs and export callback ownership: use `../inference-export/SKILL.md`.

## Read first

- [Loggers and callbacks](references/loggers-and-callbacks.md): choose logger destinations, monitoring callbacks, run-name placeholders, and upload-capable destinations.
- [Profiling and artifacts](references/profiling-and-artifacts.md): configure `Profiler`, `JSONTraceHandler`, file upload routing, trace retention, and `composer_collect_env`.
- [Troubleshooting](references/troubleshooting.md): optional dependencies, credentials, upload gaps, URI parsing, placeholder mistakes, profiler conflicts, and remote validation.
- [Logger smoke](scripts/logger_smoke.py) and [profiler smoke](scripts/profiler_smoke.py): tiny CPU/no-network sanity checks future agents can copy or run in a prepared Composer environment.

## Logger decision guide

1. Keep the default progress bar for quick interactive experiments.
2. Add `log_to_console=True` and `console_log_interval="100ba"` when stdout/stderr logs are easier to archive than progress bars.
3. Use `InMemoryLogger()` when a test, smoke script, or agent needs assertions over metrics and hyperparameters after the run.
4. Use `FileLogger(filename="{run_name}/logs-rank{rank}.txt")` for durable per-rank local text logs.
5. Use `TensorboardLogger(log_dir=...)` when users expect TensorBoard event files.
6. Use tracker loggers only after installing the matching optional extra and confirming credentials or offline/debug mode.
7. Use `RemoteUploaderDownloader(bucket_uri=...)` when the task is about object-store upload/download rather than experiment tracking.

## Artifact upload checklist

- A class must generate a local file first, such as a checkpoint callback, file logger, TensorBoard logger, profiler trace handler, or custom `trainer.logger.upload_file(...)` call.
- At least one logger destination must implement upload; otherwise the file remains local.
- Keep rank and run-name placeholders in filenames so multi-rank outputs do not clobber each other.
- If `autoresume=True`, avoid unsupported concurrent upload settings and keep a stable `run_name` plus checkpoint latest filename.
- For cloud/object stores, validate credentials and URI scheme separately from Trainer construction.

## Profiler decision guide

Use a short window before expanding trace collection:

```python
from composer.profiler import Profiler, JSONTraceHandler, cyclic_schedule

profiler = Profiler(
    schedule=cyclic_schedule(skip_first=0, wait=0, warmup=1, active=4, repeat=1),
    trace_handlers=[JSONTraceHandler(folder="traces", overwrite=True)],
    torch_prof_memory_filename=None,
)
```

Attach it as `Trainer(..., profiler=profiler)`. Prefer one or two batches first, then increase `active` or enable stack/memory options when the tiny trace is usable.

## Safe workflow

1. Start with a tiny `max_duration="1ba"` run and `InMemoryLogger()`.
2. Add one durable destination such as `FileLogger` or TensorBoard.
3. Add only one remote tracker or uploader at a time.
4. If files are generated but missing remotely, inspect upload-capable destinations before changing callbacks.
5. If profiler output is missing, check the schedule first; it may have stayed in `SKIP` or `WARMUP`.
6. Record `composer_collect_env` output when debugging PyTorch/CUDA/device issues, but do not put machine-specific paths into reusable project code.

## Bundled smoke scripts

Run from this sub-skill directory:

```bash
python scripts/logger_smoke.py
python scripts/profiler_smoke.py
```

Both scripts use random CPU tensors and temporary directories; they do not contact external services.

## Ask or stop before proceeding

- The user wants to log to a credentialed service and no token/offline mode is available.
- The task requires mutating external object storage or deleting existing remote artifacts.
- Profiling must run on a production-scale job rather than a tiny isolated reproduction.
- The issue depends on multi-rank launch behavior rather than logger/profiler configuration.
- Optional logger packages are absent and installation policy is unclear.
