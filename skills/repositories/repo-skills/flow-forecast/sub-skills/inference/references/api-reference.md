# Inference API Reference

## `InferenceMode`

`InferenceMode(forecast_steps, num_prediction_samples, model_params, csv_path, weight_path, wandb_proj=None, torch_script=False)`

### Purpose

High-level runtime helper for saved-model forecasting and classification inference.

### Important fields

- `forecast_steps`: horizon for the prediction window.
- `num_prediction_samples`: number of prediction sample runs for confidence intervals.
- `model_params`: saved training/config dictionary.
- `csv_path`: CSV path or dataframe used for inference.
- `weight_path`: checkpoint path. An empty string can be used only for synthetic smoke paths that intentionally use an untrained model.
- `wandb_proj`: optional W&B project for logging.

## `InferenceMode.infer_now`

`infer_now(some_date, csv_path=None, save_buck=None, save_name=None, use_torch_script=False)`

Returns:

1. dataframe with observations and prediction columns,
2. raw prediction tensor,
3. historical input tensor,
4. forecast start index,
5. test loader object,
6. prediction sample dataframes.

Notes:

- If scaling is active, the method adds inverse-scaled columns such as `preds` or `pred_<target>`.
- If `save_buck` is set, the method writes a temporary CSV and uploads to GCS.

## `InferenceMode.infer_now_classification`

`infer_now_classification(data=None, over_lap_seq=True, save_buck=None, save_name=None, batch_size=1)`

Use this for sequence classification or anomaly-detection style models.

## `InferenceMode.make_plots`

`make_plots(date, csv_path=None, csv_bucket=None, save_name=None, wandb_plot_id=None)`

Runs inference and creates confidence-interval plots through Plotly helpers.

## `load_model`

`load_model(model_params_dict, file_path, weight_path)`

Returns a `PyTorchForecast` wrapper initialized from a saved config and optional weights.

## `convert_to_torch_script`

`convert_to_torch_script(model, save_path)`

Traces `model.model`, stores the traced module on `model.script_model`, and saves it to `save_path`.

Caveat:

- The helper constructs a trace input from `model.params["dataset_params"]["forecast_history"]` and `model.params["model_params"]["n_time_series"]`, so those fields must agree with the real model input shape.

## `convert_to_onnx`

This function is present but currently not implemented.

## `infer_on_torch_model`

`infer_on_torch_model(model, test_csv_path=None, datetime_start=datetime(...), hours_to_forecast=336, decoder_params=None, dataset_params={}, num_prediction_samples=None, probabilistic=False, criterion_params=None)`

Returns:

- dataframe with observations and predictions,
- prediction tensor,
- history length,
- forecast start index,
- test loader,
- prediction sample dataframes.

## `evaluate_model`

`evaluate_model(model, model_type, target_col, evaluation_metrics, inference_params, eval_log)`

Runs `infer_on_torch_model` and computes evaluation metrics using the configured criterion functions.

## Plot And Explainability Helpers

- `plot_df_test_with_confidence_interval`: creates a Plotly confidence interval chart from prediction samples.
- `plot_df_test_with_probabilistic_confidence_interval`: handles probabilistic outputs.
- `deep_explain_model_summary_plot`: SHAP summary route.
- `deep_explain_model_heatmap`: SHAP heatmap route.

## Output Columns

Common dataframe columns added during inference:

- `preds`: scalar prediction column for single-target forecasts.
- `pred_<target>`: per-target predictions when `n_targets` is configured.
- `std_dev`: probabilistic standard-deviation output when available.
