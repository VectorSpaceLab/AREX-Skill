# Installation and Environment Reference

## Package Identity

- Distribution name: `dask`.
- Import module: `dask`.
- Console script: `dask`, routed through `dask.__main__:main`.
- Supported Python range in the inspected metadata: Python `>=3.10`.
- Core runtime dependencies include `click`, `cloudpickle`, `fsspec`, `packaging`, `partd`, `pyyaml`, and `toolz`.

## Extras By Workflow

| Extra | Use When | Main Dependencies |
| --- | --- | --- |
| `dask[array]` | Working with `dask.array` and NumPy-like chunked arrays | `numpy` |
| `dask[dataframe]` | Working with `dask.dataframe`, parquet, pyarrow strings, pandas-like tabular APIs | `dask[array]`, `pandas`, `pyarrow` |
| `dask[diagnostics]` | Using local diagnostics, profiler visualization, progress/dashboard-style helpers | `bokeh`, `jinja2` |
| `dask[distributed]` | Connecting to the separate Distributed scheduler package | `distributed` pinned by the repo metadata |
| `dask[complete]` | Broad user installs that need array, dataframe, distributed, diagnostics, and compression extras | larger dependency set; avoid for minimal repros |
| `dask[test]` | Contributor test environment | pytest and test tooling; not required for runtime usage |

## Minimal Checks

From the root of this generated skill directory, run:

```bash
python -c "import dask; print(dask.__version__)"
dask --help
python scripts/dask_package_smoke.py --scheduler synchronous
```

For collection-specific checks, run the nearest sub-skill script from the corresponding sub-skill directory:

- `sub-skills/core-graphs-schedulers/scripts/core_smoke.py`
- `sub-skills/array-workflows/scripts/array_smoke.py`
- `sub-skills/dataframe-workflows/scripts/dataframe_smoke.py`
- `sub-skills/bag-bytes-workflows/scripts/bag_text_smoke.py`
- `sub-skills/configuration-diagnostics-cli/scripts/dask_cli_smoke.py`

## Environment Selection

- Use `scheduler="synchronous"` for deterministic local reproductions and unit-style smoke checks.
- Use `scheduler="threads"` for NumPy, pandas, fsspec, and IO-heavy work that releases the GIL or benefits from concurrency.
- Use `scheduler="processes"` only when functions and inputs are pickleable and the calling script has a proper `if __name__ == "__main__"` guard.
- Use Distributed only after installing `dask[distributed]` or the matching `distributed` package; core Dask can schedule locally without it.

## Optional Backends

Dask integrates with optional packages such as CuPy, sparse arrays, image readers, SQLAlchemy drivers, HDF libraries, cloud filesystem adapters, and Avro readers. Keep those dependencies scoped to the task:

- Do not require GPU/CuPy just because array APIs are in scope.
- Do not install cloud filesystem packages unless the target URL scheme needs them.
- Prefer tiny local fixtures for smoke tests and skip network/credential-backed examples unless the user explicitly provides access.
