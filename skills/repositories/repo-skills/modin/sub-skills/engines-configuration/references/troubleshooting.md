# Engines and configuration troubleshooting

## Missing extras or startup failures

- Ray/Dask import errors usually mean the matching extra is missing. Install `modin[ray]` or `modin[dask]` and retry from a fresh interpreter.
- Dask and Ray are sensitive to Python multiprocessing. Put executable work under `if __name__ == "__main__":` and run it from a real `.py` file rather than stdin.
- MPI / Unidist requires external MPI tooling and launch mechanics. Treat it as prerequisite-heavy and not part of the default local smoke path.

## Engine and backend ambiguity

- Prefer `MODIN_BACKEND` when you want one value that picks the global backend cleanly.
- Do not set `MODIN_BACKEND` together with a conflicting `MODIN_ENGINE` or `MODIN_STORAGE_FORMAT` unless you know the resulting pair is valid.
- For the native local path, use `MODIN_BACKEND=Pandas` or `cfg.Backend.put("Pandas")`. `MODIN_ENGINE=Native` by itself is not enough.

## Backend switching problems

- `set_backend` / `move_to` only affect one object. They do not change the default backend for future DataFrames.
- Transfers can materialize data to pandas locally and rebuild on the target backend. That is correct but can be slow and memory intensive.
- If backend-switch progress is noisy, disable `MODIN_BACKEND_SWITCH_PROGRESS`.
- If switching fails because the target backend is unknown, inspect `Backend.choices` or the exported config CSV.

## Logging, metrics, and progress

- `MODIN_LOG_MODE`, `MODIN_LOG_MEMORY_INTERVAL`, and `MODIN_LOG_FILE_SIZE` are only useful after the engine is configured.
- `MODIN_PROGRESS_BAR=true` can help with long-running operations, but it does not fix performance problems.
- Metrics and logging settings may emit extra console output; keep them off for routine smoke tests.

## Range partitioning and async reads

- Range partitioning changes execution strategy, not correctness, but it can expose ordering assumptions in tests.
- `MODIN_ASYNC_READ_MODE` only applies to the supported readers. If a reader falls back to synchronous mode, compare results rather than assuming a performance regression.

## Dask and Ray diagnostics

- If a Dask smoke succeeds but prints cleanup warnings on exit, treat that as a scheduler-shutdown caveat rather than a correctness failure.
- If Ray initialization hangs or conflicts with a previous session, restart the interpreter and lower the requested resources.
- Use `python -m modin --versions` and `python -m modin.config --export-path <csv>` to confirm the active package and config values before chasing a deeper API bug.
