---
name: inference
description: "Repository operating skill for Flow Forecast saved-model
  inference, evaluation, TorchScript conversion, plots, and explainability."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Inference

Use this sub-skill when the task is about loading a Flow Forecast model, running saved-model forecasts or classification inference, computing evaluation metrics, creating confidence-interval plots, exporting TorchScript, or using SHAP/Plotly explainability helpers.

Start with:

- [../../references/model-overview.md](../../references/model-overview.md) for the package-wide registry when you need the exact model name or supported optional dependency note.
- [references/api-reference.md](references/api-reference.md) for `InferenceMode`, `load_model`, evaluator functions, and plotting helpers.
- [references/workflows.md](references/workflows.md) for local forecast, evaluator, TorchScript, and plotting workflows.
- [references/troubleshooting.md](references/troubleshooting.md) for weight/config/data/plot failures.
- [scripts/check_inference_config.py](scripts/check_inference_config.py) for a safe synthetic inference smoke or a real config preflight.

## What This Sub-skill Covers

- `flood_forecast.deployment.inference.InferenceMode` and `load_model`.
- `infer_now`, `infer_now_classification`, and `make_plots`.
- `flood_forecast.evaluator.infer_on_torch_model`, `evaluate_model`, and `run_evaluation`.
- `convert_to_torch_script` and the currently placeholder `convert_to_onnx`.
- Plotly confidence interval helpers and SHAP summary/heatmap routes.
- Optional GCS upload/download and W&B logging behavior.

## What Belongs Elsewhere

- Data cleaning, datetime normalization, and loader schema validation belong in [data-preparation](../data-preparation/SKILL.md).
- Training configs, checkpoint creation, and loss/optimizer selection belong in [training](../training/SKILL.md).
- Catchment encoders, CrossViViT, NeuralODE, and GR4 hybrid model internals belong in [multimodal-physics](../multimodal-physics/SKILL.md).

## Typical Workflow

1. Validate that the package imports and the desired model name is in the registry.
2. Validate the CSV and inference config locally.
3. Load the saved JSON config and checkpoint path.
4. Use `InferenceMode` or `infer_on_torch_model` to run the forecast.
5. Add plots, SHAP, W&B, or GCS only after the local forecast path works.

## Operating Notes

1. `InferenceMode` wraps `load_model`, which returns a `PyTorchForecast` instance.
2. `inference_params.dataset_params` should use the test-time loader field names; use `scaling` for inference-time scaler construction.
3. `datetime_start` can be a Python `datetime`; string parsing in low-level evaluator paths is more restrictive.
4. `num_prediction_samples` triggers prediction-sample dataframes for confidence intervals.
5. `save_buck`, `save_name`, `wandb_proj`, and GCS paths require external credentials and should not be enabled by default.

## Shared References And Scripts

- [references/api-reference.md](references/api-reference.md): API signatures and output tuples.
- [references/workflows.md](references/workflows.md): local forecast, classification, evaluation, TorchScript, GCS/W&B, and plotting recipes.
- [references/troubleshooting.md](references/troubleshooting.md): missing weights, dataset block mismatches, datetime failures, and SHAP/Plotly caveats.
- [scripts/check_inference_config.py](scripts/check_inference_config.py): synthetic or real-config preflight.

## Non-goals

- Do not use this as a cloud-serving infrastructure guide unrelated to Flow Forecast APIs.
- Do not assume GCS or W&B credentials are present.
- Do not require the original repository checkout to run an inference recipe.
