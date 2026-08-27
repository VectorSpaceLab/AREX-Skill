# Quality Outputs and Legacy Expectation Suites

## When to read

Read this when a user wants the raw profile summary, alert data, JSON output, or
legacy expectation-suite generation.

## Summary and JSON outputs

```python
summary = profile.get_description()
json_text = profile.to_json()
```

The JSON output includes the main keys needed for downstream validation and
reporting:

- `analysis`
- `table`
- `variables`
- `alerts`
- `missing`
- `sample`
- `duplicates`
- `correlations`
- `package`
- `scatter`
- `time_index_analysis`

Use `get_description()` when you need the full structured object for further
Python processing.

## Alerts and quality interpretation

A report surfaces missingness, duplicates, correlations, rejected variables,
and time-series warnings. Use `get_rejected_variables()` when you need a set of
variable names that were excluded from deeper analysis.

## Legacy Great Expectations surface

The source code still provides `to_expectation_suite()` for older workflows.
However, the public docs state that Great Expectations integration is no longer
supported in current package versions and point to an older compatible pair of
versions.

Typical behavior:

- If `great_expectations` is absent, `to_expectation_suite()` raises
  `ImportError`.
- If the user only needs a profile-based quality summary, prefer JSON or the
  description object instead of requiring GE.

## Minimal quality check

```python
profile = ProfileReport(df, minimal=True, progress_bar=False)
summary = profile.get_description()
assert "analysis" in profile.to_json()
assert len(summary.variables) > 0
```
