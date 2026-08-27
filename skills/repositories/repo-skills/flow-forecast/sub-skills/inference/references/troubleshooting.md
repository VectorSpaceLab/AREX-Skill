# Inference Troubleshooting

## Config / Weight Problems

### Model load fails with a registry error

- **Likely cause:** the saved config's `model_name` does not match the current registry.
- **Fix:** compare the name against the root model catalog and refresh the config if the repo version changed.

### State dict loading fails

- **Likely cause:** checkpoint keys do not match the model constructor arguments.
- **Fix:** verify `model_params` first, then consider `weight_path_add` rules from the training sub-skill.

### `inference_params.dataset_params` is missing

- **Likely cause:** a training config did not persist a test-time loader block.
- **Fix:** reconstruct the test-time loader block with `file_path`, `forecast_history`, `forecast_length`, `relevant_cols`, `target_col`, `scaling`, and `interpolate_param`.

## Data And Date Problems

### `datetime_start` cannot be found

- **Likely cause:** the requested forecast start is not present in the test dataframe after sorting or timezone cleanup.
- **Fix:** normalize timestamps, sort the CSV, and choose a start date that occurs after at least `forecast_history` rows.

### Inference produces empty or shifted predictions

- **Likely cause:** `hours_to_forecast`, `forecast_length`, and the decoder parameters do not agree.
- **Fix:** align the horizon values before loading the model.

## Scaling Problems

### Inverse scaling fails or prediction columns are not added

- **Likely cause:** inference-time `dataset_params` used `scaler` instead of `scaling`, or the scaler object was not constructed.
- **Fix:** use `scaling: "StandardScaler"` or another valid scaler in `inference_params.dataset_params`.

## Series-ID And Prediction-Sample Problems

### Series-ID inference works but prediction samples fail

- **Likely cause:** the low-level prediction-sampling path does not support `SeriesIDTestLoader`.
- **Fix:** run per-series deterministic inference first and skip CI samples for that path unless you implement per-series sampling.

## Plot And Explainability Problems

### SHAP fails for a model family

- **Likely cause:** some multi-output, probabilistic, multitask, or `SimpleTransformer` paths are not supported by the explanation helpers.
- **Fix:** produce deterministic predictions first, then fall back to metric/plot outputs if SHAP is unsupported.

### `tensor() got an unexpected keyword argument 'names'`

- **Likely cause:** the SHAP summary helper constructs a named tensor in a way that the current PyTorch runtime rejects.
- **Fix:** bypass SHAP for the current run and use deterministic prediction/evaluation outputs, or patch the explanation helper for the active PyTorch version.

### Plotly confidence intervals are empty

- **Likely cause:** `num_prediction_samples` was not set or the model has no stochastic output.
- **Fix:** set a positive sample count and verify that prediction samples are returned.

## TorchScript Problems

### Trace assertion or input-shape failure

- **Likely cause:** `n_time_series` or `forecast_history` in the saved config does not match the real model input.
- **Fix:** validate the config and run a local forward pass before tracing.

## Cloud / Logging Problems

### GCS upload fails after local inference succeeds

- **Likely cause:** storage credentials or bucket permissions are unavailable.
- **Fix:** keep local output first, then enable `save_buck` and `save_name` only after credentials are confirmed.

### W&B run creation fails

- **Likely cause:** W&B is not installed, not authenticated, or has a protobuf compatibility issue.
- **Fix:** disable W&B for local smoke or repair the environment.

## When To Stop And Ask

Ask the user for checkpoint paths, credentials, or exact deployment requirements when the issue depends on private model artifacts or cloud output side effects.
