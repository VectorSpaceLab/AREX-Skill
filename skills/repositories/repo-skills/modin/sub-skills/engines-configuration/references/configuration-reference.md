# Modin configuration reference

Modin configuration can be set via environment variables before import or by using `modin.config` at runtime. The safest pattern is to decide the execution mode first, set the environment, and then import `modin.pandas`.

## CLI and API inspection

```bash
python -m modin --versions
python -m modin.config
python -m modin.config --export-path modin-configs.csv
```

```python
import modin.config as cfg

print(cfg.Engine.get())
print(cfg.Backend.get())
print(cfg.NPartitions.get())
```

## Frequently used configs

| Config class | Env var | What it controls | Notes |
| --- | --- | --- | --- |
| `Engine` | `MODIN_ENGINE` | Execution runtime | Common choices: `Ray`, `Dask`, `Python`, `Unidist`, `Native`. |
| `Backend` | `MODIN_BACKEND` | Global backend alias | Common choices: `Ray`, `Dask`, `Python_Test`, `Unidist`, `Pandas`. |
| `StorageFormat` | `MODIN_STORAGE_FORMAT` | Internal storage format | Common choices: `Pandas`, `Native`. |
| `CpuCount` | `MODIN_CPUS` | Worker / CPU budget | Set before the engine starts. |
| `NPartitions` | `MODIN_NPARTITIONS` | Target partition count | Influences partitioning, shuffles, and some experimental features. |
| `Memory` | `MODIN_MEMORY` | Memory hint | Keep bounded to realistic local memory. |
| `ProgressBar` | `MODIN_PROGRESS_BAR` | Operation progress reporting | Useful when diagnosing slow operations. |
| `LogMode` | `MODIN_LOG_MODE` | Logging mode | Use `enable` when you need engine diagnostics. |
| `LogMemoryInterval` | `MODIN_LOG_MEMORY_INTERVAL` | Memory logging cadence | Pairs with `LogMode`. |
| `LogFileSize` | `MODIN_LOG_FILE_SIZE` | Log file rotation target | Keep small for local debug runs. |
| `MetricsMode` | `MODIN_METRICS_MODE` | Metrics collection | Enable only when you need metrics output. |
| `RangePartitioning` | `MODIN_RANGE_PARTITIONING` | Range-partitioned execution paths | Useful for some joins/groupbys. |
| `AsyncReadMode` | `MODIN_ASYNC_READ_MODE` | Async read support | Applies to `read_csv`, `read_fwf`, `read_table`, and `read_custom_text`. |
| `AutoSwitchBackend` | `MODIN_AUTO_SWITCH_BACKENDS` | Hybrid backend switching | Keep off unless you intentionally want hybrid behavior. |
| `ShowBackendSwitchProgress` | `MODIN_BACKEND_SWITCH_PROGRESS` | Progress feedback for backend transfer | Defaults to on. |
| `DaskThreadsPerWorker` | `MODIN_DASK_THREADS_PER_WORKER` | Dask worker thread count | Tune when Dask startup or scheduling is noisy. |
| `RayInitCustomResources` | `MODIN_RAY_INIT_CUSTOM_RESOURCES` | Custom Ray init resources | Use when Modin itself initializes Ray. |
| `RayTaskCustomResources` | `MODIN_RAY_TASK_CUSTOM_RESOURCES` | Custom Ray task/actor resources | Can cap parallelism for an operation or workflow. |
| `NativePandasMaxRows` | `MODIN_NATIVE_MAX_ROWS` | Native backend row threshold | Controls how much data is considered acceptable for local native pandas. |
| `NativePandasTransferThreshold` | `MODIN_NATIVE_MAX_XFER_ROWS` | Backend transfer threshold | Controls transfer behavior between distributed and native backends. |
| `NativePandasDeepCopy` | `MODIN_NATIVE_DEEP_COPY` | Transfer copy policy | False is faster; True is safer for mutation-heavy code. |
| `BackendMergeCastInPlace` | `MODIN_BACKEND_MERGE_CAST_IN_PLACE` | Merge cast behavior | Backend integration detail. |
| `BackendJoinConsiderAllBackends` | `MODIN_BACKEND_JOIN_CONSIDER_ALL_BACKENDS` | Join backend choice | Relevant when auto-switching is enabled. |

## Common recipes

### Native local debugging

```bash
MODIN_BACKEND=Pandas python debug_script.py
```

or:

```python
import modin.config as cfg
cfg.Backend.put("Pandas")
```

### Local Ray with two CPUs and quiet backend-switch transfer

```bash
MODIN_ENGINE=Ray MODIN_CPUS=2 MODIN_BACKEND_SWITCH_PROGRESS=false python my_script.py
```

### Local Dask with explicit worker threads

```bash
MODIN_ENGINE=Dask MODIN_CPUS=4 MODIN_DASK_THREADS_PER_WORKER=1 python my_script.py
```

Make sure `my_script.py` uses `if __name__ == "__main__":` for executable work.

### Enable diagnostics for one run

```bash
MODIN_LOG_MODE=enable MODIN_LOG_MEMORY_INTERVAL=5 MODIN_LOG_FILE_SIZE=10 MODIN_PROGRESS_BAR=true python my_script.py
```

### Export config help and inspect active engine

```bash
python -m modin --versions
python -m modin.config --export-path modin-configs.csv
python sub-skills/engines-configuration/scripts/backend_smoke.py --engine Ray --cpus 2
```

## Reading config changes safely

- Set execution variables before importing Modin.
- Use `cfg.context(...)` for temporary config changes inside a small scope.
- Do not mix `MODIN_BACKEND` with a conflicting engine/storage pair.
- Inspect the exported CSV rather than guessing whether a config exists.
