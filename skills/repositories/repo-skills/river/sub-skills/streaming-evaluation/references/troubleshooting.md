# Troubleshooting

## CSV values stay strings

`stream.iter_csv` treats every field as a string unless you cast it.
Add `converters` for numeric or custom fields and `parse_dates` for timestamps.
If a converter returns `None`, remember that `drop_nones=False` leaves the key in place.

## The target column is missing

If `target` or `target_name` is wrong, the row pop will fail when the stream tries to split features from labels.
Check the exact header spelling and whether the field was dropped earlier.
For multioutput CSVs, make sure every target name exists.

## The metric and model do not match

`progressive_val_score` checks compatibility before evaluation.
Typical pairs are:

- classifier metrics with classifiers
- regression metrics with regressors
- `Silhouette` with clusterers
- anomaly metrics with anomaly detectors or anomaly filters
- forecasting metrics with the forecasting evaluation API

If you mix a probability metric with a model that only returns labels, scoring will fail or produce the wrong prediction style.

## Delayed labels appear in the wrong order

The evaluator does not sort the source stream.
The input must already be in arrival order, and `moment` and `delay` must be comparable.
Use `datetime` plus `timedelta`, or integer moments plus integer delays.
If the reveal order looks wrong, check the original stream order first.

## Sample weights are ignored

Weights only route when the dataset item is a triple like `(x, y, {"w": ...})` and the model's `learn_one` accepts a `w` parameter.
If the model signature does not include `w`, the evaluator will still run, but the weight has no effect.

## Predictions are empty or `None`

Some models or wrappers can return `None` or an empty prediction mapping early in the stream.
`progressive_val_score` skips metric updates in that case.
If the metric stays flat, confirm that the model really emits the prediction type the metric expects.

## Anomaly scores make `ROCAUC` collapse

`metrics.ROCAUC` assumes scores in `[0, 1]`.
Raw anomaly scores are usually unbounded, so the metric can degenerate.
Normalize the scores first or use `metrics.RollingROCAUC` / `metrics.RollingPRAUC` instead.

## A dataframe adapter fails

`stream.iter_frame` only accepts eager frames.
Collect lazy dataframes before iterating.
If `iter_pandas`, `iter_polars`, `iter_sql`, `iter_sklearn_dataset`, or `iter_vaex` is unavailable, the most likely cause is a missing optional dependency.
Install the missing dependency or switch to a core adapter such as `iter_csv` or `iter_array`.
