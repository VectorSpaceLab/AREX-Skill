# Data and Exogenous Troubleshooting

## Purpose

Read this when the panel dataframe, exogenous columns, categorical setup, or
local scalers fail validation.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Missing `unique_id`, `ds`, or `y` | The frame is not in NeuralForecast long format. | Add the required columns or reshape the data. |
| Nulls in target, static, or exogenous columns | Incomplete data or bad merge logic. | Fill, drop, or impute before fit. |
| Duplicate `(unique_id, ds)` rows | The panel has repeated time stamps. | Deduplicate or aggregate before fit. |
| `futr_df` missing combinations | The future frame does not cover every horizon row. | Rebuild the complete future panel. |
| `futr_df` has extra rows | The future frame contains unused combinations. | Trim it down to the exact forecast horizon. |
| Categorical cardinality error | Declared category count is too small. | Raise the declared cardinality or reduce categories. |
| `sample_weight` error | Null or negative weight values. | Clean the weight column and rerun. |
| `available_mask` error | Non-binary mask values or missing mask logic. | Use a binary-like mask or remove the column. |
| Polars-only failure | Dtype or category handling differs from pandas. | Normalize the columns and re-run the validator. |
| Scaler inversion looks wrong | Wrong scaler choice or mixed column types. | Try a supported scaler and recheck the static/temporal split. |

## Next checks

1. Run `../../scripts/validate_panel.py` on a small sample.
2. Confirm the future dataframe shape and row coverage.
3. If the data is fine, route back to `core-forecasting`.

## When to stop

If the dataframe passes validation but the model still rejects the workflow,
check model-specific exogenous support in `model-selection`. If the problem is
only about loss choice or prediction intervals, route to
`probabilistic-losses`.
