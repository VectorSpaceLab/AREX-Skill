# Modin troubleshooting

## Installation and import

Install the engine extra that matches the requested runtime. A base `import modin` does not prove Ray, Dask, MPI, spreadsheet, XGBoost, Polars, or PyTorch support. Confirm the pandas range (`>=2.2,<2.4`) and run `python -m modin --versions` in the same environment as the workload. If `modin.pandas` warns about an unsupported pandas version, align pandas before debugging API behavior.

## Engine startup

Set the engine before the first operation and use a fresh interpreter after changing it. Ray may hang or retry when multiple kernels start at once; restart the kernel and lower resource limits. Dask worker startup is sensitive to Python multiprocessing: executable work belongs under a main guard and should run from a real `.py` file rather than stdin. MPI/Unidist needs a separately working MPI implementation and launcher.

## Conflicting configuration

Use either `MODIN_BACKEND` or the compatible `MODIN_ENGINE`/`MODIN_STORAGE_FORMAT` pair. Setting both can be ambiguous. `MODIN_CPUS`, `MODIN_NPARTITIONS`, and related resource settings should be bounded by available memory/CPU; inspect current values with `python -m modin.config`.

## `defaulting to pandas`

Modin supports a broad pandas API, but unsupported or partially supported operations may execute in pandas and convert back. This warning usually indicates a performance path, not wrong results. For large data, identify the operation, use a supported alternative when practical, and avoid repeatedly materializing data on the driver.

## Data and optional dependencies

For parallel CSV, specify dtypes for heterogeneous columns when exact inference matters. For parquet/Arrow/Excel/SQL/glob workflows, install only the parser/engine dependency needed and validate with a tiny local fixture first. Never embed cloud/database credentials in scripts or logs. Optional spreadsheet and Polars frontends are compatibility-sensitive and need import verification against the chosen dependency versions.

## Where to continue

- Core DataFrame correctness and pandas migration: [core pandas troubleshooting](../sub-skills/core-pandas-api/references/troubleshooting.md)
- Engine/configuration and backend movement: [engine troubleshooting](../sub-skills/engines-configuration/references/troubleshooting.md)
- I/O/conversion/partition failures: [I/O troubleshooting](../sub-skills/io-interoperability/references/troubleshooting.md)
- Experimental extension failures: [advanced troubleshooting](../sub-skills/advanced-extensions/references/troubleshooting.md)
