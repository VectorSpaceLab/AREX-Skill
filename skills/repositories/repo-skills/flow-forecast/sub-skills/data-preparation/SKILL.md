---
name: data-preparation
description: "Repository operating skill for preparing, validating, and loading
  Flow Forecast time-series data, including CSV, temporal-feature, series-id,
  classification, and USGS/ASOS/GCS workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Data Preparation

Use this sub-skill when the task is about getting data into the shape that Flow Forecast expects: CSV schema checks, interpolation, datetime normalization, temporal features, train/valid/test slicing, series-id loaders, classification loaders, or the special loaders used by DA-RNN and related workflows.

Start with:

- [references/data-formats.md](references/data-formats.md) for the core loader contracts.
- [references/loader-api.md](references/loader-api.md) for the loader class list and the important constructor arguments.
- [references/workflows.md](references/workflows.md) for end-to-end loader selection and the safe validation flow.
- [references/troubleshooting.md](references/troubleshooting.md) for timezone, missing-column, and network/credential issues.
- [scripts/validate_timeseries_csv.py](scripts/validate_timeseries_csv.py) for a safe preflight check before training or inference.

## What This Sub-skill Covers

- `CSVDataLoader` and `CSVTestLoader` for the default forecasting path.
- `TemporalLoader` and `TemporalTestLoader` for datetime-aware forecasting.
- `CSVSeriesIDLoader` and `SeriesIDTestLoader` for parallel multi-series tasks.
- `GeneralClassificationLoader` and `VariableSequenceLength` for classification / variable-length sequence tasks.
- `AEDataloader` and DA-RNN preprocessing helpers, including the version-specific `features`/`targets` vs `feats`/`targs` adapter caveat.
- Interpolation, timezone cleanup, and temporal feature generation.
- USGS / ASOS / GCS data access caveats when they affect loader construction or validation.

## What Belongs Elsewhere

- Training loops, model selection, and checkpoints belong in [training](../training/SKILL.md).
- Saved-model forecasting, evaluation, plots, and SHAP belong in [inference](../inference/SKILL.md).
- Catchment `.npz` records, contrastive pretraining, and GR4 / ODE hybrid models belong in [multimodal-physics](../multimodal-physics/SKILL.md).

## Typical Workflow

1. Validate the CSV with `scripts/validate_timeseries_csv.py`.
2. Decide whether you need the default loader, a temporal loader, a series-id loader, or a specialized classification / variable-length loader.
3. Check whether the chosen loader needs sorted datetimes, temporal features, interpolation, or an explicit scaling object.
4. Only then hand the data path to the training or inference sub-skill.

## Common Decision Points

### Default forecasting CSV

Use the default loader when you have a single time series table with a target column and one or more relevant columns. The minimum config contract is `file_path`, `forecast_history`, `forecast_length`, `target_col`, and `relevant_cols`.

### Temporal forecasting

Use `TemporalLoader` when the model needs explicit datetime features such as month, day, day-of-week, or hour. These workflows usually need a `sort_column` and `feature_param["datetime_params"]`.

### Series-id forecasting

Use `CSVSeriesIDLoader` when one file contains multiple parallel series distinguished by a series ID column. The loader returns dictionaries keyed by series index and may require `return_method` and `series_id_col`.

### Classification and variable-length sequences

Use `GeneralClassificationLoader` or `VariableSequenceLength` when the task is classification, anomaly detection, or variable-length sequence handling instead of plain forecasting. Their output shapes differ from the default CSV loader.

### DA-RNN preprocessing

Use the DA-RNN preprocessing helpers when the training path needs the `TrainData` container used by `flood_forecast.da_rnn.train_da`.

## When To Read The References

- Read [references/data-formats.md](references/data-formats.md) when choosing columns, sequence lengths, or split boundaries.
- Read [references/loader-api.md](references/loader-api.md) when you need constructor arguments or the return shape of a specific loader.
- Read [references/troubleshooting.md](references/troubleshooting.md) whenever a datetime column, missing value, or loader mismatch causes a failure.
