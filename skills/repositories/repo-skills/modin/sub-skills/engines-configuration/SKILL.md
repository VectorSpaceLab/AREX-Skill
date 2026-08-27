---
name: engines-configuration
description: "Configure Modin engines, backends, resources, diagnostics, and
  backend switching."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Modin engines and configuration

Use this sub-skill when a task needs execution-engine selection, `modin.config`, resource limits, backend movement, logging, metrics, progress bars, range partitioning, or Ray/Dask startup troubleshooting.

## Start here

1. Read [references/engine-selection.md](references/engine-selection.md) to distinguish Engine, StorageFormat, Backend, and per-object backend movement, and to choose Ray, Dask, Python, Native/Pandas, or optional Unidist/MPI.
2. Read [references/configuration-reference.md](references/configuration-reference.md) for exact environment variables, `modin.config` API usage, CLI export, progress/logging/metrics controls, async reads, and range partitioning.
3. Read [references/troubleshooting.md](references/troubleshooting.md) for Ray/Dask install/start failures, multiprocessing safe-main guard issues, MPI prerequisites, backend-switch errors, logging/progress/metrics problems, and range-partitioning surprises.
4. Run [scripts/backend_smoke.py](scripts/backend_smoke.py) to test a tiny DataFrame operation under `Ray`, `Dask`, `Python`, or `Native` execution.
5. Run [scripts/export_config_help.py](scripts/export_config_help.py) to export the installed Modin config catalog to CSV without using a source checkout.

## Routing boundaries

This sub-skill owns:

- Install extras for `modin[ray]`, `modin[dask]`, `modin[all]`, and optional `modin[mpi]` with external MPI prerequisites.
- `MODIN_ENGINE`, `MODIN_BACKEND`, `MODIN_STORAGE_FORMAT`, `MODIN_CPUS`, `MODIN_NPARTITIONS`, `MODIN_MEMORY`, `MODIN_PROGRESS_BAR`, `MODIN_RANGE_PARTITIONING`, `MODIN_ASYNC_READ_MODE`, `MODIN_LOG_MODE`, `MODIN_METRICS_MODE`, `MODIN_BACKEND_SWITCH_PROGRESS`, `MODIN_AUTO_SWITCH_BACKENDS`, `MODIN_DASK_THREADS_PER_WORKER`, `MODIN_NATIVE_MAX_ROWS`, `MODIN_NATIVE_MAX_XFER_ROWS`, `MODIN_NATIVE_DEEP_COPY`, `MODIN_BACKEND_MERGE_CAST_IN_PLACE`, `MODIN_BACKEND_JOIN_CONSIDER_ALL_BACKENDS`, `MODIN_RAY_INIT_CUSTOM_RESOURCES`, and `MODIN_RAY_TASK_CUSTOM_RESOURCES`.
- `python -m modin --versions`, `python -m modin.config`, and `python -m modin.config --export-path <csv>`.
- `DataFrame.set_backend`, `Series.set_backend`, `move_to`, `get_backend`, and backend-transfer progress control.
- Logging (`LogMode`, `LogMemoryInterval`, `LogFileSize`), metrics, and Dask/Ray main-guard guidance.

Route ordinary DataFrame recipes to `../core-pandas-api/SKILL.md`, reader/writer and conversion work to `../io-interoperability/SKILL.md`, and experimental APIs to `../advanced-extensions/SKILL.md`.

## Default operating pattern

1. Choose global execution before importing `modin.pandas` or before the first Modin operation.
2. Prefer `MODIN_BACKEND=<Ray|Dask|Pandas|Python_Test|Unidist>` for a complete global backend alias. Use `MODIN_ENGINE` only when you understand the storage-format pairing.
3. For native local pandas execution, set `MODIN_BACKEND=Pandas` rather than trying to force `MODIN_ENGINE=Native` alone.
4. Set `MODIN_CPUS`, `MODIN_NPARTITIONS`, and `MODIN_MEMORY` before the engine starts.
5. In `.py` files that run Ray or Dask work, put executable Modin work under `if __name__ == "__main__":`.
6. Use `df.set_backend(...)` / `df.move_to(...)` for one object only; it does not change the global default backend and may materialize large data locally.
7. Verify with the bundled smoke script and the config-export helper before diagnosing higher-level pandas or I/O behavior.
