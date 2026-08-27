# Inference Workflows

## 1. Local Saved-Model Forecast

1. Load the saved config JSON.
2. Confirm `model_name`, `dataset_params`, and `inference_params.dataset_params` match the checkpoint.
3. Validate the test CSV with the data-preparation script.
4. Create `InferenceMode` with the forecast horizon, prediction-sample count, config, CSV path, and checkpoint path.
5. Call `infer_now(datetime_start)`.
6. Inspect the returned dataframe for `preds` or `pred_<target>` columns.

```python
from datetime import datetime
import json
from flood_forecast.deployment.inference import InferenceMode

with open("saved_config.json", "r", encoding="utf-8") as handle:
    params = json.load(handle)

mode = InferenceMode(
    forecast_steps=params["inference_params"]["hours_to_forecast"],
    num_prediction_samples=params["inference_params"].get("num_prediction_samples", 1),
    model_params=params,
    csv_path=params["inference_params"]["test_csv_path"],
    weight_path="model.pth",
)
df, tensor, history, start_idx, test_loader, samples = mode.infer_now(datetime(2020, 5, 31))
```

## 2. Direct Evaluation From A Trained Wrapper

Use `evaluate_model` when you already have a `PyTorchForecast` object in memory.

```python
from flood_forecast.evaluator import evaluate_model

metrics, df, start_idx, samples = evaluate_model(
    trained_model,
    "PyTorch",
    target_col=["cfs"],
    evaluation_metrics=["MSE"],
    inference_params=trained_model.params["inference_params"],
    eval_log={},
)
```

## 3. Classification Inference

Use `infer_now_classification` when the trained model uses `GeneralClassificationLoader` or a classification-style sequence setup.

Checklist:

- Confirm the model was trained with compatible classification labels.
- Pass `data` only when you want to override the internal test data.
- Tune `batch_size` for local memory.

## 4. Confidence Intervals And Plots

Set `num_prediction_samples` to a positive integer, then use `make_plots` or the Plotly helper functions.

Notes:

- Prediction samples require enough stochasticity or probabilistic output to be meaningful.
- Series-ID prediction samples are not supported in all low-level paths.
- W&B plot logging requires a live W&B run.

## 5. TorchScript Export

Use `convert_to_torch_script` after a local inference smoke succeeds.

Checklist:

- The model must be deterministic under tracing for the equality assertion.
- `model.params["model_params"]["n_time_series"]` must equal the input feature count.
- `model.params["dataset_params"]["forecast_history"]` must equal the trace input history length.

## 6. GCS And W&B Output

Enable cloud/logging output only after local inference passes.

- `save_buck` and `save_name` upload the inference dataframe through GCS helpers.
- `wandb_proj` initializes a W&B run in `InferenceMode`.
- Required credentials are not bundled in this skill.

## 7. Safe Smoke Check

Run:

```bash
python scripts/check_inference_config.py --smoke --torchscript
```

This uses a synthetic CSV and `DummyTorchModel` to exercise config validation, `InferenceMode`, `infer_now`, and optional TorchScript export without a checkpoint or cloud access.
