# Evaluation and Benchmarking Workflows

## Forecasting holdout metric

```python
from sktime.split import temporal_train_test_split
from sktime.performance_metrics.forecasting import mean_absolute_percentage_error

y_train, y_test = temporal_train_test_split(y, test_size=12)
# fit forecaster on y_train, predict y_test.index, then score
```

## Backtesting with `evaluate`

Use temporal splitters and `error_score="raise"` while debugging. Set `strategy` to `refit`, `update`, or `no-update_params` intentionally; do not mix future information into transforms or model selection.

```python
from sktime.forecasting.model_evaluation import evaluate
from sktime.forecasting.naive import NaiveForecaster
from sktime.performance_metrics.forecasting import MeanAbsolutePercentageError
from sktime.split import SlidingWindowSplitter

cv = SlidingWindowSplitter(fh=[1, 2], window_length=24, step_length=3)
metric = MeanAbsolutePercentageError(symmetric=True)
results = evaluate(NaiveForecaster(strategy="last"), cv=cv, y=y, scoring=metric,
                   strategy="refit", error_score="raise")
```

## Tiny benchmark pattern

Create one or two estimators, one tiny dataset loader, a small splitter, and an explicit scorer before expanding. Use in-memory or user-controlled output files. Avoid broad grids until the smoke path is correct.

## Analyzers

Benchmark analyzers consume tabular benchmark results. Validate columns such as `validation_id`, `model_id`, and metric summary columns before ranking or plotting.
