# Evaluation and backtesting workflows

These workflows are self-contained recipes for operating installed GluonTS evaluation APIs. They assume the data is already in GluonTS dataset form and that a predictor or forecast iterator exists.

## 1. Trailing holdout evaluation with `make_evaluation_predictions`

Use this pattern for a predictor and a test dataset that already contains the full target including the forecast horizon.

```python
from gluonts.dataset.common import ListDataset
from gluonts.evaluation import Evaluator, make_evaluation_predictions
from gluonts.model.seasonal_naive import SeasonalNaivePredictor

prediction_length = 4
freq = "D"

dataset = ListDataset(
    [
        {
            "item_id": "demo",
            "start": "2024-01-01",
            "target": [10, 11, 12, 13, 10, 11, 12, 13, 10, 11, 12, 13],
        },
    ],
    freq=freq,
)

predictor = SeasonalNaivePredictor(
    prediction_length=prediction_length,
    season_length=4,
)

forecast_it, target_it = make_evaluation_predictions(
    dataset=dataset,
    predictor=predictor,
    num_samples=100,
)

# Iterators are single-use; materialize if you need to inspect and evaluate.
forecasts = list(forecast_it)
targets = list(target_it)

for forecast, target in zip(forecasts, targets):
    assert forecast.index.isin(target.index).all()
    assert forecast.index.equals(target.index[-prediction_length:])

agg_metrics, item_metrics = Evaluator(
    quantiles=(0.1, 0.5, 0.9),
    num_workers=0,
)(
    iter(targets),
    iter(forecasts),
    num_series=len(forecasts),
)

print(agg_metrics["MSE"], item_metrics[["item_id", "forecast_start", "MSE"]])
```

Why this avoids alignment mistakes:

- The predictor never sees the trailing `prediction_length` target values.
- The target iterator remains in the same order as the forecast iterator.
- `Evaluator` receives target objects whose indexes contain `forecast.index` plus enough history to compute seasonal-error-based metrics.

For predictors with a nonzero `lead_time`, the withheld window is `prediction_length + lead_time`; do not assume the input cut and forecast start are adjacent.

## 2. One-call predictor backtest with `backtest_metrics`

Use this wrapper when you do not need to inspect forecasts before evaluation.

```python
from gluonts.evaluation import Evaluator, backtest_metrics

agg_metrics, item_metrics = backtest_metrics(
    test_dataset=dataset,
    predictor=predictor,
    evaluator=Evaluator(quantiles=(0.1, 0.5, 0.9), num_workers=0),
    num_samples=100,
)
```

Operational notes:

- `backtest_metrics` expects a `Predictor`, not an `Estimator`; train the estimator first if needed.
- It uses the same trailing-holdout logic as `make_evaluation_predictions`.
- The optional `logging_file` argument writes aggregate metric log lines; item metrics are returned as the DataFrame.
- For many series, use a bounded `num_workers` and `chunk_size` rather than relying on the default CPU count.

## 3. Evaluating split-generated rolling windows

When you need multiple evaluation windows, create `TestData` with the dataset splitter, predict on `test_data.input`, then use either classic or `gluonts.ev` evaluation.

```python
from gluonts.dataset.split import split
from gluonts.model import evaluate_model
from gluonts.ev.metrics import MSE, RMSE, ND, WeightedSumQuantileLoss

prediction_length = 3
_, test_template = split(dataset, offset=-12)
test_data = test_template.generate_instances(
    prediction_length=prediction_length,
    windows=4,
)

# The predictor's prediction_length must match the generated instance length.
assert predictor.prediction_length == prediction_length

metrics_df = evaluate_model(
    model=predictor,
    test_data=test_data,
    metrics=[MSE(), RMSE(), ND(), WeightedSumQuantileLoss(0.5)],
    axis=None,
    batch_size=16,
    seasonality=1,  # optional explicit scale for tiny or unusual data
)
```

Use `axis=None` for scalar aggregate rows. Use `axis=1` for univariate per-item/per-window rows aggregated over forecast time. Use `axis=0` to inspect per-horizon behavior aggregated across items and windows.

## 4. Evaluating forecasts you already generated

If forecasts were produced elsewhere, pass them to `Evaluator` only after proving alignment.

```python
from gluonts.evaluation import Evaluator

forecasts = list(forecast_iterator)
targets = list(target_iterator)

assert len(forecasts) == len(targets)
for index, (forecast, target) in enumerate(zip(forecasts, targets)):
    if not forecast.index.isin(target.index).all():
        raise ValueError(f"forecast {index} is outside its target index")

agg_metrics, item_metrics = Evaluator(num_workers=0)(
    iter(targets),
    iter(forecasts),
    num_series=len(forecasts),
)
```

Best practices:

- Use pandas `PeriodIndex` or a time index that matches the forecast frequency.
- Keep full targets when possible, not just the prediction slice, so seasonal errors are meaningful.
- Preserve forecast order from `predictor.predict(dataset)`; do not sort one iterator without sorting the other by the same key.

## 5. Inspecting and saving item metrics

Item metrics expose series-level failures that aggregates can hide.

```python
columns = [
    "item_id",
    "forecast_start",
    "MSE",
    "abs_error",
    "abs_target_sum",
    "MASE",
    "Coverage[0.5]",
]
existing = [column for column in columns if column in item_metrics.columns]
print(item_metrics[existing].sort_values("abs_error", ascending=False).head())

item_metrics.to_csv("item_metrics.csv", index=False)
```

When item metrics contain `nan` or `inf`, inspect `abs_target_sum`, `seasonal_error`, `num_masked_target_values`, and the underlying forecast quantiles before deciding that the model is poor.

## 6. Custom classic Evaluator metric

`custom_eval_fn` lets you add one-off metrics to both aggregate and item outputs.

```python
import numpy as np
from gluonts.evaluation import Evaluator


def rmsle(target, forecast):
    return np.sqrt(np.mean(np.square(np.log1p(target) - np.log1p(forecast))))


evaluator = Evaluator(
    quantiles=(0.1, 0.5, 0.9),
    custom_eval_fn={"RMSLE": [rmsle, "mean", "mean"]},
    num_workers=0,
    allow_nan_forecast=False,
)
agg_metrics, item_metrics = evaluator(targets, forecasts, num_series=len(forecasts))
```

The callable receives the extracted target values and the selected forecast array. Use `"mean"` only when the forecast object provides a mean; otherwise use `"median"`.

## 7. When to choose classic `Evaluator` vs `gluonts.ev`

| Need | Prefer | Reason |
| --- | --- | --- |
| Compatibility with established GluonTS aggregate/item metric names | `Evaluator` | Produces the familiar dictionary/DataFrame with names such as `MASE`, `ND`, and `wQuantileLoss[0.5]`. |
| Simple predictor backtest | `backtest_metrics` | Wraps holdout prediction and classic evaluation in one call. |
| Axis-aware metric arrays over `TestData` windows | `evaluate_model` or `evaluate_forecasts` with `gluonts.ev.metrics` | Can aggregate over dataset, time, and target dimensions explicitly. |
| Manual NumPy batch metric streaming | `gluonts.ev.evaluate` | Useful for custom batched evaluation data with keys like `label`, `mean`, `0.5`, and `seasonal_error`. |

Treat `gluonts.model.evaluate_model` and `evaluate_forecasts` as experimental. Prefer classic `Evaluator` for user-facing reports unless the task specifically needs axis-aware `gluonts.ev` behavior.
