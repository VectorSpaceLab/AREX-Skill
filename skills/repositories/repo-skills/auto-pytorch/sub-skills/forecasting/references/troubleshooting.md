# Forecasting troubleshooting

## Classification is not supported

**Symptoms**

- `Classification is currently not supported for forecasting tasks!`

**Likely cause**

The forecasting target validator only supports regression-style targets.

**Recovery**

- Use the tabular classification route for classification problems.
- Keep forecasting tasks as regression-style prediction problems.

## Sparse targets are not supported

**Symptoms**

- `Sparse Target is unsupported for forecasting task!`

**Likely cause**

The forecasting validator does not accept sparse targets.

**Recovery**

- Convert targets to a dense representation before fitting the validator.

## Sequence count or length mismatches

**Symptoms**

- `Inconsistent number of sequences for features and targets...`
- `Inconsistent number of test datapoints for features and targets...`
- `Index must have length as the input targets!`
- `Given index must have length as the input features!`
- `start_times_train must have the same length as y_train!`

**Likely cause**

The series layout, index length, or forecast-horizon assumptions are inconsistent.

**Recovery**

- Make sure every series has a matching feature and target sequence.
- Keep `start_times` aligned with the number of series.
- If you use `series_idx`, ensure the index columns are present and non-null.

## Missing features or wrong layout

**Symptoms**

- `Multi Variant dataset requires X as input!`
- `X must be given as series_idx!`
- `Targets must be given!`

**Likely cause**

The validator expected multi-variant data or a feature layout with series identifiers.

**Recovery**

- Pass `X` when the dataset is multi-variant.
- Pass `series_idx` only when the feature DataFrame actually stores series IDs.
- Pass targets whenever the validator is not in the future-features-only path.

## Missing forecasting extra

**Symptoms**

- import failures for the forecasting task or forecasting metrics
- missing `gluonts`, `sktime`, or `pytorch_forecasting`

**Likely cause**

The forecasting extra was not installed.

**Recovery**

- Install `autoPyTorch[forecasting]`.
- Re-run the install smoke check.

## Init-config or sliding-window confusion

**Symptoms**

- custom init config files are not found
- the default window size feels wrong for the horizon

**Likely cause**

The optional forecasting init file was missing or the automatic window adjustment was not appropriate for the data.

**Recovery**

- Provide a valid `custom_init_setting_path` when you want your own initial models.
- Adjust `search_space_updates` if the default `window_size` is not aligned with the problem.

## Predict shape surprises

**Symptoms**

- predictions do not match the horizon you expected
- the output is flattened when you expected a 3D forecast array

**Likely cause**

The task always reshapes predictions around the forecast horizon and target count.

**Recovery**

- Check `n_prediction_steps`.
- Check whether the task has one target or multiple targets.
- Remember that the public `predict(...)` return shape is task-shaped, not raw network-shaped.
