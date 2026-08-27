---
name: data-preparation
description: "Format, load, cache, generate, preprocess, synchronize, and
  convert tslearn time-series data before modeling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# Data preparation

Start from the root tslearn router (`../../SKILL.md`) when the request is broader than preparation. Use this sub-skill when the task is specifically to make time-series data usable: shape it, clean it, load it, synthesize it, resample it, symbolize it, or convert it to another package format.

## Owns

- `tslearn.utils` formatting, validation, text I/O, and conversion helpers.
- `tslearn.preprocessing` scalers, resampler, imputer, and feature synchronizer.
- `tslearn.piecewise` PAA, SAX, and 1d-SAX transforms plus inverse transforms.
- `tslearn.datasets` offline cached datasets and UCR/UEA loading/caching.
- `tslearn.generators` synthetic random-walk data.
- Interop with `sklearn`, `pyts`, `seglearn`, `stumpy`, and pandas-backed `sktime`, `pyflux`, `tsfresh`, plus `cesium` when installed.

## Does not own

- Distance metrics or backend choice -> `../metrics-backends/SKILL.md`.
- Clustering -> `../clustering/SKILL.md`.
- Supervised model fitting -> `../supervised-models/SKILL.md`.
- Forecasting -> `../forecasting/SKILL.md`.
- Model serialization or persistence of learned estimators -> `../analysis-and-persistence/SKILL.md`.
- Matrix profile -> route back through the root router (`../../SKILL.md`) or the sibling that owns profile-oriented analysis.

## Read first

- `references/workflows.md` for end-to-end preparation sequences.
- `references/interop.md` for exact conversion shapes and optional-package requirements.
- `references/troubleshooting.md` for common shape, cache, pandas, cesium, and timestamp failures.
- `scripts/data_preparation_smoke.py` for a deterministic tiny-data check; run it with a Python environment that can import `tslearn`.

## Typical route

1. Normalize raw sequences with `to_time_series_dataset`, `check_dataset`, or `check_variable_length_input`.
2. If the input has gaps or misaligned features, run `TimeSeriesImputer` and `TimeSeriesFeatureSynchronizer`.
3. If a fixed length is required, use `TimeSeriesResampler`.
4. If you need compression, apply `PiecewiseAggregateApproximation`, `SymbolicAggregateApproximation`, or `OneD_SymbolicAggregateApproximation`.
5. If you need an external format, use the matching helper from `tslearn.utils`.
6. If you need sample data, use `CachedDatasets`, `UCR_UEA_datasets`, `random_walks`, or `random_walk_blobs`.

## Quick guardrails

- `to_pyflux_dataset` only accepts one time series and needs pandas.
- `to_sktime_dataset`, `to_pyflux_dataset`, and `to_tsfresh_dataset` need pandas.
- `to_cesium_dataset` and `from_cesium_dataset` need cesium.
- PAA, SAX, and 1d-SAX expect dense equal-length data; resample before using them on ragged inputs.
- `TimeSeriesFeatureSynchronizer` expects timestamps with the same shape as `X` and increasing timestamps per feature.
- `TimeSeriesImputer(..., keep_trailing_nans=True)` preserves padded variable-length tails.

## Handoffs

- For backend-specific metric choice, leave this route and use `../metrics-backends/SKILL.md`.
- For model training or evaluation, leave this route and use the sibling route that owns the estimator family.
- For loading a dataset that may download, prefer the dataset notes in `references/workflows.md` and `references/troubleshooting.md` before retrying.
