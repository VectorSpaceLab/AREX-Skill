# Forecasting Workflows

These recipes are designed for future agents answering user prompts without reopening AutoGluon source docs.

## Offline-Safe Quick Forecast

Use this when the user wants a minimal working forecast, has no network access, or only wants to validate plumbing.

```python
from autogluon.timeseries import TimeSeriesDataFrame, TimeSeriesPredictor

prediction_length = 3
data = TimeSeriesDataFrame(raw_data, id_column="series", timestamp_column="date")
train_data, test_data = data.train_test_split(prediction_length)

predictor = TimeSeriesPredictor(
    prediction_length=prediction_length,
    target="target",
    eval_metric="WQL",
    verbosity=0,
)
predictor.fit(
    train_data,
    hyperparameters={"Naive": {}, "SeasonalNaive": {}, "Theta": {}},
    time_limit=60,
)
predictions = predictor.predict(train_data)
scores = predictor.evaluate(test_data)
leaderboard = predictor.leaderboard(test_data)
```

Why this is safe:

- Statistical baselines train locally and do not require foundation-model downloads.
- `train_test_split` preserves the last horizon in `test_data` for scoring.
- `WQL` uses quantile forecasts by default and works for probabilistic output.

## Production-Oriented Fit

Use presets when the user values accuracy and has adequate runtime/backends.

```python
predictor = TimeSeriesPredictor(
    prediction_length=prediction_length,
    freq="D",
    target="demand",
    eval_metric="WQL",
    quantile_levels=[0.05, 0.1, 0.5, 0.9, 0.95],
    path="AutogluonModels/timeseries-demand",
)
predictor.fit(
    train_data,
    presets="high_quality",
    time_limit=3600,
    excluded_model_types=["AutoARIMA"],
)
```

Guidance:

- Set `freq` when source timestamps are irregular, when resampling is desired, or when AutoGluon cannot infer a single frequency.
- Use `excluded_model_types` to avoid models that are too slow or unsupported in the user environment.
- `presets="fast_training"` maps to very light statistical/tabular models. `medium_quality`, `high_quality`, and `best_quality` add deeper model coverage and can include Chronos/Chronos2 depending on version and installed dependencies.

## Known Future Covariates

Use known covariates for features available through the forecast horizon, such as holidays, scheduled promotions, prices, or weather forecasts.

```python
known_names = ["promotion", "is_weekend"]
predictor = TimeSeriesPredictor(
    prediction_length=14,
    known_covariates_names=known_names,
    eval_metric="WQL",
)
predictor.fit(train_data, hyperparameters={"DirectTabular": {}, "TemporalFusionTransformer": {}})

future_covariates = predictor.make_future_data_frame(train_data)
future_covariates["promotion"] = planned_promotion_values
future_covariates["is_weekend"] = future_covariates["timestamp"].dt.weekday.isin([5, 6]).astype(int)
predictions = predictor.predict(train_data, known_covariates=future_covariates)
```

Checklist:

- The training frame must include `target` plus every column in `known_covariates_names`.
- The prediction call must pass `known_covariates` with all declared columns for every future row.
- Extra columns, timestamps, or items can be present, but do not rely on extras; keep the frame clean to avoid confusion.
- Chronos/Chronos-Bolt do not natively use future covariates, although they may be combined with external covariate regressors. Chronos-2 supports covariates natively.

## Static Features

Use static features for item metadata such as store region, product category, sensor type, or capacity.

```python
static = static_features_df.set_index("item_id")
static["region"] = static["region"].astype("category")
train_data.static_features = static
predictor.fit(train_data, hyperparameters={"RecursiveTabular": {}, "DirectTabular": {}})
```

Checklist:

- Static features must include every item ID in the time-series frame.
- Use categorical dtype for integer-coded categories to avoid treating IDs as continuous numbers.
- If a user slices data or creates future inputs manually, verify `static_features` remains attached and indexed correctly.

## Evaluation and Backtesting

```python
train_data, test_data = data.train_test_split(prediction_length=prediction_length)
predictor.fit(train_data, num_val_windows=2, val_step_size=prediction_length)
scores = predictor.evaluate(test_data, metrics=["WQL", "MASE", "RMSE"])
lb = predictor.leaderboard(test_data, extra_metrics=["MASE", "WAPE"], extra_info=True)
```

Notes:

- `evaluate` and `leaderboard` score the final horizon in `test_data` by default.
- Use `cutoff` to score at a different relative endpoint when working with long held-out data.
- Increasing `num_val_windows` improves validation robustness but increases training cost and raises the minimum data length needed per item.
- `refit_full=True` can retrain selected models on all available data after validation; avoid it when the user needs fastest iteration.

## Probabilistic Forecasts

Predictions contain a point forecast and quantile forecasts.

```python
predictions = predictor.predict(train_data)
mean_forecast = predictions["mean"]
p10 = predictions["0.1"]
p90 = predictions["0.9"]
```

- `mean` is the expected value point forecast.
- Quantile columns encode uncertainty; `0.1` is P10, `0.5` is the median, and `0.9` is P90.
- Customize levels in the predictor constructor with `quantile_levels=[0.05, 0.5, 0.95]`.
- Choose `WQL` or `SQL` when the user asks for calibrated prediction intervals or probabilistic scoring.

## Feature Importance

```python
fi = predictor.feature_importance(
    data=test_data,
    model="Chronos2",
    method="permutation",
    relative_scores=True,
    time_limit=120,
)
```

Use this when the user asks whether covariates/static features help. For a quick diagnostic, `method="naive"` is faster but less robust. Importance estimates are only meaningful for features visible to the selected model.

## Save and Load

```python
predictor.save()
loaded = TimeSeriesPredictor.load("AutogluonModels/timeseries-demand", require_version_match=True)
predictions = loaded.predict(new_data, known_covariates=future_covariates)
```

- Prefer `require_version_match=True` when reproducibility matters.
- If a user moved machines and load fails, consult root package troubleshooting for version/import/backend checks and this sub-skill's model-specific notes.
- Predictor artifact paths should be local. Do not use S3 as the predictor `path` argument.

## Tiny Smoke Script

Run the bundled smoke without training:

```bash
python sub-skills/time-series-forecasting/scripts/timeseries_smoke.py
```

Run the optional tiny fit only when the environment has AutoGluon time-series installed and local statistical models available:

```bash
python sub-skills/time-series-forecasting/scripts/timeseries_smoke.py --fit --prediction-length 2
```
