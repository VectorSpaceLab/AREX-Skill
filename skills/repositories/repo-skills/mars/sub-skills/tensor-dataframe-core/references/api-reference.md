# Tensor and DataFrame API Reference

## Purpose

Read this when you need the exact local-compute entry points for Mars tensor,
DataFrame, session, and eager-mode work.

## Verified session and execution APIs

| API | Verified signature or behavior | Use |
| --- | --- | --- |
| `mars.new_session(address=None, session_id=None, backend='mars', default=True, new=True, **kwargs)` | Creates a new default session or connects to an existing Mars cluster when an address is provided. | Start a local session before repeated compute or connect to a cluster later. |
| `mars.execute(tileable, *tileables, session=None, wait=True, new_session_kwargs=None, show_progress=None, progress_update_interval=1, **kwargs)` | Executes one or more Mars objects and can return a future when `wait=False`. | Batch tiny compute or expose execution to a caller. |
| `mars.fetch(tileable, *tileables, session=None, **kwargs)` | Fetches concrete values from executed Mars objects. | Turn an executed tensor/DataFrame/remote result into a concrete object. |
| `mars.stop_server()` | Stops the default local server/session if one was created. | Clean up after smoke runs and examples. |

## Verified configuration APIs

| API | Verified behavior | Use |
| --- | --- | --- |
| `mars.config.options` | Exposes mutable runtime options such as `eager_mode`, `show_progress`, and chunk-size settings. | Toggle local execution behavior and debug-friendly execution. |
| `mars.config.option_context(...)` | Context manager that temporarily overrides Mars options. | Make a short-lived eager-mode or tuning change in a snippet or smoke test. |

## Representative tensor APIs

The installed package exposes the familiar NumPy-like families below through
`mars.tensor as mt`:

- Constructors: `tensor`, `array`, `asarray`, `zeros`, `ones`, `full`, `arange`,
  `linspace`, `eye`, `identity`, `meshgrid`, `diag`, `indices`.
- Arithmetic and reductions: `add`, `subtract`, `multiply`, `divide`, `sum`,
  `mean`, `prod`, `max`, `min`, `var`, `std`, `all`, `any`, `argmax`, `argmin`.
- Shape and indexing: `reshape`, `transpose`, `ravel`, `split`, `stack`,
  `concatenate`, `take`, `compress`, `nonzero`, `where`.
- I/O and conversion: `from_hdf5`, `to_hdf5`, `from_zarr`, `to_zarr`,
  `from_dataframe`, `to_numpy` after execution.

Use the workflow reference for the smallest safe examples; this page is for the
API names and the behavior you can rely on without reopening the source repo.

## Representative DataFrame APIs

`mars.dataframe as md` exposes the usual pandas-like surface:

- Constructors: `DataFrame`, `Series`, `Index`, `from_records`, `from_tensor`,
  `read_csv`, `read_parquet`, `read_sql`, `date_range`.
- Transformations: `groupby`, `merge`, `concat`, `sort_values`, `sort_index`,
  `head`, `tail`, `loc`, `iloc`, `at`, `iat`, `apply`, `astype`, `fillna`.
- Conversion: `.execute()`, `.fetch()`, `.to_pandas()`, `.to_tensor()`.
- IO: `read_csv`, `read_parquet`, `to_csv`, `to_parquet`, `to_sql`.

Verified constructor signature:

```python
DataFrame(data=None, index=None, columns=None, dtype=None, copy=False,
          chunk_size=None, gpu=None, sparse=None, num_partitions=None)
```

Verified `read_csv` signature begins with:

```python
read_csv(path, names=None, sep=',', index_col=None, compression=None,
         header='infer', dtype=None, usecols=None, nrows=None, chunk_bytes='64M',
         gpu=None, head_bytes='100k', head_lines=None, incremental_index=True,
         use_arrow_dtype=None, storage_options=None, memory_scale=...)
```

The exact tail can vary by release; consult the installed signature if you need a
parameter not listed here.

## Runtime facts worth remembering

- `execute()` returns the Mars object itself; use `fetch()` for the concrete
  NumPy/pandas value.
- `option_context({'eager_mode': True})` is the cleanest way to make a short
  debugging session execute immediately.
- `mars.dataframe` import can touch optional Ray-related code early enough to
  expose a shadowed `ray` module problem.
- Tiny CSV/HDF5/Parquet examples should prefer temporary files and local paths.
