# Cross-cutting Troubleshooting

Use this reference for installation, import, optional dependency, result export, and package-level issues that are not owned by one workflow sub-skill.

## Installation and import

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError` or runtime error involving LightGBM | LightGBM Python package or its native library dependencies are unavailable for the platform | Install NannyML from PyPI or Conda in a supported Python version and follow LightGBM platform installation requirements. Prefer Conda when system OpenMP/native libraries are the problem. |
| `ModuleNotFoundError: nannyml` | Package not installed in the active environment | Run `python -m pip install nannyml` in the same environment that will run the code, then verify with `python -c "import nannyml as nml; print(nml.__version__)"`. |
| `pkg_resources` missing while using the CLI banner | `pyfiglet` imports `pkg_resources`, which may be absent in very new Setuptools-only environments | Install or pin a Setuptools version that still provides `pkg_resources`, for example `python -m pip install 'setuptools<81'`, then rerun `nml --help`. |
| CLI emits a deprecation warning about `pkg_resources` | Current `pyfiglet` uses the deprecated API | Usually safe to ignore. Pinning Setuptools below the removal boundary avoids a hard failure. |
| Optional database writer import fails | `sqlmodel` and database driver dependencies are not installed | Install `nannyml[db]`. For PostgreSQL, make sure the driver and connection string are valid. |
| `ArrowStringArray` reshape or pandas strict dtype assignment errors | NannyML 0.13.1 can be sensitive to pandas 3 string inference and stricter dtype assignment | Prefer `pandas<3` for this release, or set `pd.options.future.infer_string = False` before loading string-heavy data and keep categorical columns as `object`/`category`. |
| Cloud filesystem paths fail | S3/GCS/Azure credentials or fsspec implementation details are missing | Pass provider-specific credentials through config or environment and verify a tiny read/write path before running the full monitor. |

## Public package check

Run this after installation:

```bash
python - <<'PY'
import nannyml as nml
print('nannyml', nml.__version__)
for name in ['CBPE', 'DLE', 'PerformanceCalculator', 'UnivariateDriftCalculator', 'RawFilesWriter']:
    print(name, hasattr(nml, name))
PY
```

For a more complete self-contained check, run:

```bash
python scripts/check_install.py --check all
```

## Python and dependency expectations

NannyML 0.13.1 declares support for Python `>=3.9,<3.13`. The base package depends on NumPy, SciPy, pandas, scikit-learn, PyArrow, category-encoders, LightGBM, FLAML, Plotly/Kaleido, fsspec cloud filesystem libraries, Pydantic, Click, Rich, PyYAML, Jinja2, APScheduler, and supporting utilities.

This release was verified against pandas 2-style behavior. If you are on pandas 3 and hit `ArrowStringArray` reshape errors or stricter dtype-assignment failures, prefer `pandas<3` or disable future string inference with `pd.options.future.infer_string = False` before loading string-heavy data.

Use the optional `db` extra only when reading from or writing to relational databases:

```bash
python -m pip install 'nannyml[db]'
```

## Data and schema validation

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `InvalidArgumentsException` about missing columns | A calculator or estimator was configured with a column name absent from reference or analysis data | Check the selected route's API reference, then inspect `reference_df.columns` and `analysis_df.columns`. Column names must match between reference and analysis for the same semantic role. |
| Empty dataframe error | `fit`, `calculate`, or `estimate` received no rows | Validate upstream filters, file reads, target joins, and chunking before constructing the monitor. |
| Time-based plots fall back to chunk indices | No `timestamp_column_name` was provided or the timestamp column could not be parsed | Provide a timestamp column parseable by pandas and use the same timestamp naming across reference and analysis. |
| Period-based chunking fails | `chunk_period` requires a timestamp column | Add `timestamp_column_name` or use `chunk_size`, `chunk_number`, or an explicit `Chunker`. |
| Too few chunk warning | The chunker produced fewer than the recommended number of chunks | Use smaller chunks, more analysis data, or a chunking strategy that yields more periods. |

## Result export and persistence

`RawFilesWriter` and `PickleFileWriter` write to local or fsspec-supported paths. Both require a `filename` when calling `write`:

```python
writer = nml.RawFilesWriter(path='out')
writer.write(result, filename='monitoring-result.parquet', format='parquet')
```

`FilesystemStore` persists fitted calculators for later `runner.run` reuse and also supports fsspec-backed paths. For cloud paths, verify credentials and object-store permissions before scheduling a recurring run.

## Usage logging and privacy

NannyML has usage-logging helpers exposed at the top level (`enable_usage_logging`, `disable_usage_logging`, `log_usage`). When operating in restricted or private environments, explicitly disable usage logging before running monitoring code if required by policy:

```python
import nannyml as nml
nml.disable_usage_logging()
```

## Route-specific troubleshooting

- Performance estimation/calculation failures: [../sub-skills/performance-monitoring/references/troubleshooting.md](../sub-skills/performance-monitoring/references/troubleshooting.md)
- Drift method, type override, and ranking failures: [../sub-skills/drift-monitoring/references/troubleshooting.md](../sub-skills/drift-monitoring/references/troubleshooting.md)
- Data requirements, chunking, thresholds, and quality/stat calculators: [../sub-skills/data-setup/references/troubleshooting.md](../sub-skills/data-setup/references/troubleshooting.md)
- CLI/config/scheduling/store failures: [../sub-skills/cli-and-automation/references/troubleshooting.md](../sub-skills/cli-and-automation/references/troubleshooting.md)
