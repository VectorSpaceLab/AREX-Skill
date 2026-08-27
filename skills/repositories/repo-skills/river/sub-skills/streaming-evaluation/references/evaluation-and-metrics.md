# Evaluation and metrics

## Evaluation modes

Choose the lightest API that still matches the question you want to answer.

### Manual loop

Use a manual loop when you need custom bookkeeping, custom prediction routing, or to debug a stream step by step.

```python
for x, y in dataset:
    y_pred = model.predict_one(x)
    metric.update(y, y_pred)
    model.learn_one(x, y)
```

If samples carry per-row kwargs, unpack them and forward `w` or other model-specific arguments when the model accepts them.

### `evaluate.progressive_val_score`

Use this for the standard online predict-then-learn loop.
It validates that the metric and model are compatible before scoring, and it automatically chooses the right prediction style.

It accepts streams of `(x, y)` or `(x, y, kwargs)` tuples.
When `kwargs` includes `w`, the weight is forwarded to `learn_one` for models whose signature accepts `w`.

The evaluator also handles delayed labels through `moment` and `delay`, and it adapts to active learning classifiers.

### `evaluate.iter_progressive_val_score`

Use this when you want checkpoints instead of a single final metric.
Each yielded checkpoint is a dictionary that can include:

- one entry per metric when you pass a metric container
- `Step`
- `Prediction` when requested
- `Time` and `Memory` when enabled
- `Samples used` for active learning classifiers

### Forecasting evaluation

For multi-step forecasting, use `river.evaluate.forecasting.evaluate` or `iter_evaluate` with a horizon and a regression metric.
This is a forecasting-specific evaluation loop, not `progressive_val_score`.

## What `progressive_val_score` does for you

The evaluator checks `metric.works_with(model)` and raises a clear error if the pairing is invalid.
It then picks the prediction method from the model and metric type:

- regular classifiers with label-based classification metrics use `predict_one`
- classifiers with probability-based metrics use `predict_proba_one`
- anomaly detectors use `score_one`
- anomaly filters use `score_one` and then `classify`
- clustering metrics receive `x`, `y_pred`, and the current cluster centers
- regressors use `predict_one`

For clustering, `Silhouette` is minimized in River: lower is better.

## Metric selection by task

### Classification

Use label metrics when you care about the final class decision:

- `Accuracy`
- `F1`, `Precision`, `Recall`
- `BalancedAccuracy` for imbalance

Use probability metrics when calibrated probabilities matter:

- `ROCAUC`
- `LogLoss`
- `CrossEntropy`

If you need more than one view of performance, combine metrics with `+`.

```python
metric = metrics.Accuracy() + metrics.F1() + metrics.LogLoss()
```

### Regression

Common choices are:

- `MAE` for absolute error
- `RMSE` for larger-error emphasis
- `R2` for explained variance style reporting
- `SMAPE` when you want a percentage-like error measure

### Clustering

Use `Silhouette` when you do not have labels.
It compares each point to its assigned centroid and the next-closest centroid.

If you do have labels and want an external agreement score, use a label-aware clustering metric instead of `Silhouette`.

### Anomaly detection

Anomaly detectors usually output raw scores rather than calibrated probabilities.
That means metric choice matters:

- `ROCAUC` is appropriate only when the score has been normalized to `[0, 1]`
- `RollingROCAUC` is scale-invariant and suitable for unbounded anomaly scores
- `RollingPRAUC` is also scale-invariant and is often useful under class imbalance

### Forecasting

Forecasting metrics are regression metrics evaluated at a horizon.
Common choices are `MAE`, `RMSE`, and `SMAPE`.
Use the forecasting evaluation API, not the generic classification-style progressive validation loop.

## Delayed labels and active learning

When labels arrive late, pass `moment` and `delay` so the evaluator can replay the stream in reveal order.
If the model is an active learning classifier, the evaluator respects the model's label request and reports how many samples were actually used for learning.

This is the right place to model production-like behavior where prediction and learning are separated in time.
