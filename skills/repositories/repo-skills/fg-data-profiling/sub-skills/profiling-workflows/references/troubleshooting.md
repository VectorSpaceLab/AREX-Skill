# Profiling Workflow Troubleshooting

## Empty data

Symptom: `ValueError: DataFrame is empty. Please provide a non-empty DataFrame.`

Likely causes:
- The input reader returned no rows.
- Filtering removed all data.
- `ProfileReport(..., lazy=False)` was constructed with `df=None`.

Recovery:
1. Check `df.shape` and `df.head()` before constructing the report.
2. Use a representative sample if the full dataset is too large.
3. For configuration-first code, keep the report lazy until data is attached.

## `minimal` and `config_file` conflict

Symptom: `ValueError: Arguments config_file and minimal are mutually exclusive.`

`minimal=True` selects the built-in minimal config. If the user needs a custom
YAML file, remove `minimal=True` and encode the desired minimal/performance
settings in the YAML file instead.

## Time-series sorting errors

Symptom: `KeyError` after passing `sortby="..."`.

The `sortby` column must exist in the pandas DataFrame. Verify column spelling
and use the current API spelling `tsmode=True`:

```python
assert "event_time" in df.columns
profile = ProfileReport(df, tsmode=True, sortby="event_time")
```

Spark DataFrames do not support time-series mode in this package; route Spark
users to the integration/backend sub-skill.

## Deprecated import warning

Symptom: `DeprecationWarning` when importing `ydata_profiling`.

Replace old imports with:

```python
from data_profiling import ProfileReport, compare
```

The old import may still work for compatibility, but future guidance should use
`data_profiling`.

## Notebook widget display looks like text

Symptom: widget output displays text such as `IntSlider(value=0)` instead of an
interactive UI.

The package can render a notebook widget UI, but the environment must have
ipywidgets installed and enabled. Use `to_notebook_iframe()` or `to_file()` as a
portable fallback, and read the integrations/backends sub-skill for widget setup.

## Report seems stale after configuration changes

Rendered HTML, JSON, widgets, report structures, and descriptions are cached.
If you mutate `profile.config` after rendering, call:

```python
profile.invalidate_cache()
```

or create a fresh `ProfileReport` object before exporting again.

## Full report is slow or memory-heavy

Start with `minimal=True`, sample the data, and disable correlations,
interactions, missing diagrams, samples, or duplicates through the configuration
sub-skill. Large outliers can also make histogram computation expensive; filter
or cap obvious invalid values before profiling.
