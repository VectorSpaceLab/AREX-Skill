# Core Forecasting Troubleshooting

## Import or dependency errors before fitting

Symptoms:

- `ModuleNotFoundError: No module named 'pytorch_lightning'` or missing Torch/Lightning runtime dependencies.
- `ModuleNotFoundError: No module named 'pkg_resources'` while importing Lightning.
- `AttributeError: 'Series' object has no attribute 'view'` during frequency inference.

Likely causes and recovery:

- If `pytorch_lightning` or Torch dependencies are missing, run forecasting scripts from an environment where `neuralprophet` and its base dependencies are installed.
- This NeuralProphet version uses Lightning components that still import `pkg_resources`; install a setuptools release that still ships it, for example `pip install 'setuptools<81'` in the user's environment.
- Current source code uses pandas APIs removed in pandas 3; use `pip install 'pandas<3'` until the package version is refreshed.
- Re-run a minimal import and `scripts/smoke_forecast.py` after changing dependencies.

## Dataframe schema failures

Symptoms:

- Missing-column errors for `ds` or `y`.
- Timestamps are not parseable.
- Duplicate datestamps produce confusing split or frequency behavior.

Recovery:

1. Run `python scripts/validate_neuralprophet_dataframe.py data.csv` or `python scripts/validate_neuralprophet_dataframe.py --input-file data.csv`.
2. Ensure `ds` can be parsed by pandas and sort it ascending.
3. Keep `y` numeric for training/testing data. Future-only prediction rows may have missing `y`.
4. For multi-series data, include `ID` and avoid duplicate `(ID, ds)` pairs.

## Frequency inference is wrong

Symptoms:

- `freq='auto'` chooses an unexpected frequency.
- Training warns about missing dates or imputation.
- Future dataframe timestamps drift from expected calendar boundaries.

Recovery:

- Pass an explicit pandas frequency string such as `"D"`, `"H"`, `"MS"`, or `"5min"` to `fit`, `split_df`, and cross-validation helpers.
- Fill or remove duplicate and irregular timestamps before fitting.
- Use `n_lags` and `n_forecasts` deliberately: lagged models need enough history before prediction boundaries.

## `fit` returns `None` for metrics

Symptoms:

- Code indexes `metrics.columns` and gets `AttributeError: 'NoneType' object has no attribute 'columns'`.

Recovery:

- Check whether metrics were disabled via `collect_metrics=False` or `fit(..., metrics=False)`.
- Treat `metrics is None` as valid when metrics collection is intentionally off.
- For quick smoke tests, disabled metrics are fine; for evaluation workflows use `collect_metrics=True` or pass a metrics list/dict.

## Future prediction fails with missing extra columns

Symptoms:

- Prediction complains about missing event, future regressor, or conditional seasonality columns.

Recovery:

- If the model uses `add_future_regressor`, pass a matching `regressors_df` to `make_future_dataframe` for future periods.
- If the model uses `add_events`, pass `events_df` and use `create_df_with_events` for history when needed.
- Route component-specific column requirements to `../components-and-exogenous/SKILL.md`.

## Optional plotting warning

Symptoms:

- A Plotly failure mentions a missing resampler even though fitting and prediction work.

Recovery:

- The base package does not install optional `plotly-resampler`. This sub-skill avoids plotting; install the optional plotting extra only for plotting workflows and route plotting details to `../operations-and-migration/SKILL.md`.

## Smoke-test recovery

Run this from the sub-skill directory:

```bash
python scripts/smoke_forecast.py --epochs 1 --periods 3
```

A healthy run prints a forecast row count and at least `yhat1`.
