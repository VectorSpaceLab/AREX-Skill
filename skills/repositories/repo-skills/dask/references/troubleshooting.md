# Cross-Cutting Troubleshooting

## Import or Extra Missing

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'numpy'` while importing `dask.array` | Array extra not installed | Install `dask[array]` or add NumPy to the environment |
| `ImportError` for pandas or pyarrow while importing dataframe APIs | DataFrame extra not installed | Install `dask[dataframe]` |
| `ImportError` for bokeh or jinja2 in diagnostics | Diagnostics extra not installed | Install `dask[diagnostics]` |
| `distributed` import fails | Distributed is a separate optional package | Install the metadata-pinned `dask[distributed]` extra when remote scheduling is required |

## Lazy Execution Surprises

- Dask collections are lazy. Most transformations build graphs and do not execute until `compute`, `persist`, or a scheduler call.
- Avoid calling `.compute()` inside reusable graph-building functions; it makes later optimization, fusion, and scheduler selection harder.
- Use `visualize`, graph keys, `__dask_graph__`, or the root/sub-skill smoke scripts to inspect graph shape without materializing expensive data.

## Scheduler Problems

- **Multiprocessing pickling errors:** lambdas, nested functions, open file handles, locks, and many closures cannot be serialized reliably. Move functions to module scope or use `scheduler="threads"` / `"synchronous"` for local debugging.
- **Unexpected single-thread behavior:** confirm the scheduler configuration with `dask.config.get("scheduler", default=None)` and any active `with dask.config.set(...)` contexts.
- **Distributed-specific options ignored:** core local schedulers do not understand Distributed-only worker/resource/retry behavior; route those tasks to Distributed docs or install the Distributed package.

## Config Not Taking Effect

- Use `dask config find <key>` to locate the YAML file that defines a value.
- Use `dask config get <key>` or `dask.config.get("section.key")` to verify the active value.
- Set import-time flags such as `array.query-planning` and `dataframe.query-planning` before importing `dask.array` or `dask.dataframe` in a fresh process.
- When setting values in tests or scripts, prefer `with dask.config.set({...}):` to avoid leaking global state.

## Metadata, Chunks, Divisions, and Schema

- Unknown array chunks can block reshape/rechunk/slicing algorithms or produce poor plans. Use source metadata, explicit chunks, or safe chunk discovery.
- Unknown dataframe divisions can make joins, `set_index`, repartitioning, and indexing expensive. Use sorted indexes, `set_index`, `clear_divisions`, or explicit `divisions` when appropriate.
- DataFrame `map_partitions` and Bag-to-DataFrame conversions often need explicit `meta` to avoid expensive or incorrect inference.

## Optional IO and Backend Failures

- Cloud URLs use fsspec adapters and may need optional packages, credentials, or `storage_options`.
- Compression, Avro, SQL, HDF, ORC, Parquet, CuPy, sparse, image, and TileDB workflows each have optional dependencies; install only what the current workflow needs.
- For verification, prefer help commands and tiny local fixtures. Skip network, credential, GPU, and large-data native cases unless the environment explicitly supports them.
