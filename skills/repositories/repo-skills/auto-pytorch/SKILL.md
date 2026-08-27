---
name: auto-pytorch
description: "Route Auto-PyTorch tabular and forecasting workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Auto-PyTorch

Auto-PyTorch is an AutoML toolkit for PyTorch-based tabular classification, tabular regression, and time series forecasting. Use this skill when you need to search over pipeline components, tune hyperparameters, inspect ensembles, or validate data shapes before a run.

## Install

Use the public package name:

```bash
pip install autoPyTorch
pip install autoPyTorch[forecasting]
```

Use the forecasting extra whenever you need the time-series APIs, validators, or forecasting metrics.

## Quick smoke check

Run the bundled install check script after installation:

```bash
python scripts/check_install.py
```

That script prints the installed version, importability of the public modules, and the most important API signatures.

## Route map

### `sub-skills/tabular-automl/`
Use this route for:

- `TabularClassificationTask` and `TabularRegressionTask`
- `get_dataset(...)`, `get_search_space(...)`, `fit_pipeline(...)`, `search(...)`, and `refit(...)`
- feature typing, categorical handling, dataset compression, and resampling strategy selection
- custom search spaces via `include_components`, `exclude_components`, and `search_space_updates`
- traditional learners such as LightGBM, CatBoost, RandomForest, ExtraTrees, SVM, and KNN
- ensemble inspection with `show_models()`, `sprint_statistics()`, and `plot_perf_over_time()`

Read `sub-skills/tabular-automl/SKILL.md` when the task is about tabular classification or regression, even if the user also wants custom configs, portfolios, or result inspection.

### `sub-skills/forecasting/`
Use this route for:

- `TimeSeriesForecastingTask`
- uni-variant and multi-variant sequence layouts
- `start_times`, `freq`, `series_idx`, `known_future_features`, and `n_prediction_steps`
- forecasting validators, sequence construction, and forecast-horizon handling
- forecasting-specific metrics such as `mean_MASE_forecasting` and `mean_MAPE_forecasting`

Read `sub-skills/forecasting/SKILL.md` when the task names time series forecasting, sequence validation, known future features, or forecast horizon setup.

## Core usage pattern

Most tasks follow the same shape:

1. Build or load dataset inputs.
2. Let the validator normalize the data.
3. Create the task object.
4. Search, fit a single configuration, or refit the selected model.
5. Inspect predictions, scores, and ensemble output.

If you need the detailed API surface, open `references/package-overview.md` first for a compact summary, then open the closest sub-skill reference instead of trying to infer it from the router.

## Common inputs and outputs

- Inputs can be NumPy arrays, pandas objects, or Python lists for the supported task type.
- Tabular workflows may need `feat_types` when dtype inference is ambiguous.
- Forecasting workflows may need `series_idx`, `start_times`, and `known_future_features` to preserve sequence identity.
- `search(...)` returns the fitted task object after the search completes.
- `fit_pipeline(...)` returns a fitted pipeline plus run metadata for a single configuration.
- `predict(...)` and `score(...)` operate on the fitted task or pipeline.

## Common failures

Read `references/troubleshooting.md` for cross-cutting install, import, data-shape, optional-dependency, and package-resolution issues.

The most common problems are:

- missing forecasting extras when importing forecasting APIs
- missing or uninitialized `automl_common` submodule when using a source checkout
- OpenML or other network-backed example data not being available
- `scikit-learn`, `torch`, or compiled dependency version mismatches

## Related references

- `references/package-overview.md` — compact package API and task summary
- `references/troubleshooting.md` — cross-cutting install and import problems
- `references/repo-provenance.md` — source commit and package version snapshot
- `references/repo-routing-metadata.json` — router metadata for managed imports
- `scripts/check_install.py` — lightweight install and import smoke check
- `sub-skills/tabular-automl/` — tabular classification and regression workflows
- `sub-skills/forecasting/` — time series forecasting workflows
