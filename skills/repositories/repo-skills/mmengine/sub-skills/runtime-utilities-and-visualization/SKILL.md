---
name: runtime-utilities-and-visualization
description: "Use MMEngine logging, message hubs, visualizer backends,
  distributed and device utilities, environment checks, timers, progress bars,
  manager mixins, and testing helpers safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Runtime Utilities and Visualization

Use this sub-skill when a task mentions `MMLogger`, `print_log`, `MessageHub`, `Visualizer`, `LocalVisBackend`, `TensorboardVisBackend`, `WandbVisBackend`, MLflow/ClearML/Aim/DVCLive/Neptune backends, `init_dist`, `get_dist_info`, `collect_results`, `master_only`, `get_device`, `collect_env`, `ManagerMixin`, progress bars, `Timer`, or MMEngine testing helpers.

## Read Order

- [references/logging-visualization-workflows.md](references/logging-visualization-workflows.md): Choose and use loggers, message hubs, visualizers, local outputs, and optional tracking-service backends.
- [references/distributed-device-utilities.md](references/distributed-device-utilities.md): Use distributed rank helpers, safe result collection, device detection, environment reports, timers, progress helpers, manager mixins, and testing utilities.
- [references/troubleshooting.md](references/troubleshooting.md): Diagnose duplicate loggers, optional backend dependency failures, visualization output surprises, distributed no-op behavior, collection mismatches, device fallback, and test-helper pitfalls.
- [scripts/runtime_env_check.py](scripts/runtime_env_check.py): Run a safe local import/environment diagnostic, construct a temporary `LocalVisBackend` visualizer, and report distributed availability without launching multi-process jobs.

## Scope

This sub-skill owns MMEngine runtime utilities: `mmengine.logging`, `mmengine.visualization`, `mmengine.dist`, `mmengine.device`, `mmengine.utils`, `mmengine.utils.dl_utils.collect_env`, `mmengine.testing`, `ManagerMixin`-based singleton behavior, progress helpers, and timers.

Route adjacent issues to sibling skills:

- Use `../runner-and-training/SKILL.md` for Runner `LoggerHook`, `NaiveVisualizationHook`, launch command placement, training log intervals, checkpoint/resume, and hook ordering.
- Use `../models-metrics-and-inference/SKILL.md` for model complexity/analysis APIs, `BaseModel`, `BaseMetric`, evaluator contracts, and inference/TTA behavior.
- Use `../data-structures-and-io/SKILL.md` for file format IO, file backends, datasets, samplers, collation, and data element schemas.
- Use `../configuration-and-registry/SKILL.md` for config syntax, registries, `DefaultScope`, and config-driven object construction.

## Fast Workflow

1. For one-off logging, call `print_log`; for reusable project logging, create a named `MMLogger.get_instance(...)` and reuse that instance name.
2. For training/runtime state shared across components, store numeric histories with `MessageHub.update_scalar(s)` and overwrite current metadata with `MessageHub.update_info`.
3. For visualization without credentials, prefer `Visualizer(..., vis_backends=[dict(type='LocalVisBackend')], save_dir=...)`; add TensorBoard or service backends only when dependencies and credentials are available.
4. For distributed-safe code, call `get_dist_info()` first; expect `(0, 1)` outside distributed launch and remember `master_only` silently returns `None` on non-main ranks.
5. Before debugging user environments, run `python scripts/runtime_env_check.py --help` from this sub-skill directory, then run it with an optional `--work-dir` that points to a disposable output directory.

## Safe Operating Rules

- Do not initialize distributed jobs from helper scripts unless the user has explicitly launched the process group with PyTorch, MPI, or Slurm environment variables.
- Do not require optional tracking services, credentials, network access, or original MMEngine repository files; use `LocalVisBackend` as the safe fallback.
- Treat visualizer `save_dir` as a user project output path and keep generated runtime skill files independent from any user experiment outputs.
