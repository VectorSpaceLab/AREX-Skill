# Engine and backend selection

Modin separates three related choices:

- **Engine**: the execution runtime. Common values are `Ray`, `Dask`, `Python`, `Unidist`, and `Native`.
- **StorageFormat**: the internal storage format. Common values are `Pandas` and `Native`.
- **Backend**: the user-facing global backend alias. Common values in the inspected package are `Ray`, `Dask`, `Python_Test`, `Unidist`, and `Pandas`.

The easiest global selector is usually `MODIN_BACKEND` or `cfg.Backend.put(...)`.

## Practical selection rules

| Goal | Recommended setting | Notes |
| --- | --- | --- |
| Local debugging with native pandas behavior | `MODIN_BACKEND=Pandas` | Selects the native pandas backend. Use when you want correctness and minimal distributed overhead. |
| Local Ray execution | `MODIN_ENGINE=Ray` or `MODIN_BACKEND=Ray` | Set Ray before importing `modin.pandas`. Install the Ray extra first. |
| Local Dask execution | `MODIN_ENGINE=Dask` or `MODIN_BACKEND=Dask` | Put work under `if __name__ == "__main__":` in scripts. Install the Dask extra first. |
| Python test engine | `MODIN_ENGINE=Python` | Used for small local checks and testing; the backend is normalized to `Python_Test`. |
| MPI / Unidist | `MODIN_ENGINE=Unidist` with external MPI setup | Optional and prerequisite-heavy. Treat as environment-specific rather than the default route. |

`MODIN_ENGINE=Native` by itself is not enough for the native local path; pair it with `MODIN_BACKEND=Pandas` or use the backend API directly.

## Per-object backend movement

`set_backend` and `move_to` change one DataFrame or Series object without changing the global default backend.

```python
import modin.pandas as pd
import modin.config as cfg

cfg.Backend.put("Ray")
df = pd.DataFrame([1, 2, 3])
small_native = df.set_backend("Pandas")
assert df.get_backend() == "Ray"
assert small_native.get_backend() == "Pandas"
```

Behavior to remember:

- Backend names are normalized case-insensitively (`"pandas"` -> `"Pandas"`, `"python_test"` -> `"Python_Test"`).
- `inplace=False` returns a new object; `inplace=True` updates the original and returns `None`.
- Switching to the same backend returns the same object (or `None` for inplace) and does not show progress.
- Backend transfer may use direct `move_to`/`move_from` implementations, or it may materialize to pandas locally and rebuild on the target backend. The fallback can be slow and memory intensive for large frames.
- `MODIN_BACKEND_SWITCH_PROGRESS` controls transfer progress output. It defaults to enabled. If `tqdm` is installed, Modin uses a progress bar; otherwise it prints a concise transfer line to stderr.
- Per-object switching is not the same as `Backend.put(...)`; it does not change the backend used by future new DataFrames.

## Native/Pandas backend tuning

Native/Pandas backend controls are useful when mixing distributed and native execution:

| Config | Default | Purpose |
| --- | --- | --- |
| `MODIN_NATIVE_MAX_ROWS` / `NativePandasMaxRows` | `10000000` | Maximum rows considered suitable for local native pandas processing. |
| `MODIN_NATIVE_MAX_XFER_ROWS` / `NativePandasTransferThreshold` | `10000000` | Target maximum rows for transfers between engines. |
| `MODIN_NATIVE_DEEP_COPY` / `NativePandasDeepCopy` | `False` | Whether to deep-copy when transferring to/from native pandas. False improves performance but can surprise code that mutates shared pandas data in place. |
| `MODIN_AUTO_SWITCH_BACKENDS` / `AutoSwitchBackend` | `False` | Allows automatic backend switching where backend implementations support it. Keep disabled unless you intentionally want hybrid behavior. |
| `MODIN_BACKEND_MERGE_CAST_IN_PLACE` / `BackendMergeCastInPlace` | `True` | Controls whether mixed-backend merge casts happen in place. |
| `MODIN_BACKEND_JOIN_CONSIDER_ALL_BACKENDS` / `BackendJoinConsiderAllBackends` | `True` | With auto-switching enabled, allows join pre-operation switching to consider all active backends. |

## Quick verification commands

```bash
python -m modin --versions
python -m modin.config --export-path modin-configs.csv
python sub-skills/engines-configuration/scripts/backend_smoke.py --engine Python
python sub-skills/engines-configuration/scripts/backend_smoke.py --engine Ray --cpus 2
python sub-skills/engines-configuration/scripts/backend_smoke.py --engine Dask --cpus 2
python sub-skills/engines-configuration/scripts/backend_smoke.py --engine Native
```

The bundled smoke script prints the requested engine, active engine, storage format, backend, and a tiny groupby result. If Ray or Dask is not installed, install the matching extra or choose a different engine.
