---
name: time-series-and-data
description: "Use Darts TimeSeries constructors, shapes, static covariates,
  grouping, slicing, and export workflows safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Time series and data

Use this sub-skill when the user needs to create, inspect, reshape, split, combine, or export Darts `TimeSeries` objects before modeling.

## Read first

- [`references/data-formats.md`](references/data-formats.md) for pandas/Series/array/grouped constructors, missing dates, shape semantics, static covariates, and export patterns.
- [`references/api-reference.md`](references/api-reference.md) for important constructor signatures and validation checks.
- [`references/troubleshooting.md`](references/troubleshooting.md) for date-frequency, static covariate, component/sample, and grouped-data errors.
- [`scripts/timeseries_doctor.py`](scripts/timeseries_doctor.py) for a tiny self-contained construction and validation smoke.

## Route by user task

- **DataFrame or Series to Darts**: use `TimeSeries.from_dataframe()`, `from_series()`, or `from_times_and_values()` patterns in `data-formats.md`.
- **Missing or irregular timestamps**: validate duplicates/frequency first; use `fill_missing_dates=True` plus explicit `freq` when Darts should insert missing time points.
- **Multiple value columns**: explain that they become components in one multivariate `TimeSeries`, not separate series unless grouped intentionally.
- **Many entities/stores/items**: use `TimeSeries.from_group_dataframe()` to return a list of series, preserving static/metadata columns where appropriate.
- **Static covariates**: validate one global row or one row per component; keep component names aligned.
- **Modeling next**: route scaling/covariates to `../data-processing-and-covariates/`, forecasting to `../forecasting-workflows/` or `../torch-and-foundation-models/`, and metrics to `../evaluation-and-explainability/`.

## Safe check

From this sub-skill directory or by passing the full script path:

```bash
python scripts/timeseries_doctor.py --json
```

The script creates generated in-memory data, including a missing date and static covariates. It does not read source repo datasets or notebooks.

## Boundaries

This sub-skill owns Darts data representation, not preprocessing pipelines, model selection, anomaly scoring, or metric interpretation. Do not instruct future agents to open original repository docs/notebooks for data patterns; the required constructor and validation details are distilled here.
