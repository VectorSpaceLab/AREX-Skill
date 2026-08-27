# Forecasting model workflows

These workflows are self-contained recipes for operating installed GluonTS forecasting APIs. They assume the dataset has already been constructed correctly.

## 1. Minimal `Estimator.train -> Predictor.predict`

```python
from gluonts.torch import DeepAREstimator

estimator = DeepAREstimator(
    freq="D",
    prediction_length=7,
    trainer_kwargs={
        "max_epochs": 1,
        "logger": False,
        "enable_model_summary": False,
        "accelerator": "cpu",
        "devices": 1,
        "num_sanity_val_steps": 0,
    },
    batch_size=4,
    num_batches_per_epoch=2,
)

predictor = estimator.train(training_data)
forecasts = list(predictor.predict(prediction_data))
```

Rules:

- Match `freq` to the dataset timestamp frequency.
- Ensure each training target is long enough for the model context and prediction length.
- Keep `max_epochs`, `batch_size`, and `num_batches_per_epoch` small for smoke tests.
- Increase training only when the task explicitly requires a meaningful fitted model.

## 2. README-style split/train/predict pattern on local data

Use this shape when the user has a pandas data frame and wants a quick train/test demonstration. The actual data-splitting details are covered by the `data-pipelines` sub-skill.

```python
from gluonts.dataset.pandas import PandasDataset
from gluonts.dataset.split import split
from gluonts.torch import DeepAREstimator

# df: pandas DataFrame indexed by timestamps and containing a target column.
dataset = PandasDataset(df, target="target", freq="D")
training_data, test_template = split(dataset, offset=-14)
test_data = test_template.generate_instances(prediction_length=7, windows=2)

predictor = DeepAREstimator(
    freq="D",
    prediction_length=7,
    batch_size=4,
    num_batches_per_epoch=2,
    trainer_kwargs={"max_epochs": 1, "logger": False, "accelerator": "cpu", "devices": 1},
).train(training_data)

forecasts = list(predictor.predict(test_data.input))
```

The returned `test_data` has aligned `input` entries for prediction and labels for evaluation. Use `evaluation-backtesting` when metrics are required.

## 3. Deterministic local baseline

```python
from gluonts.dataset.common import ListDataset
from gluonts.model.seasonal_naive import SeasonalNaivePredictor

series = ListDataset(
    [
        {"start": "2024-01-01", "target": [10, 12, 11, 13, 10, 12, 11, 13]},
    ],
    freq="D",
)

predictor = SeasonalNaivePredictor(prediction_length=4, season_length=4)
forecast = next(iter(predictor.predict(series)))
print(forecast.mean.tolist())  # [10.0, 12.0, 11.0, 13.0]
```

Use this before neural training to prove that dataset fields, forecast starts, and downstream evaluation code are wired correctly.

## 4. NPTS local probabilistic baseline

```python
from gluonts.model.npts import NPTSPredictor, KernelType

predictor = NPTSPredictor(
    prediction_length=12,
    context_length=240,
    kernel_type=KernelType.exponential,
    use_seasonal_model=True,
)

forecasts = list(predictor.predict(dataset, num_samples=200))
```

Operational guardrails:

- Keep `context_length` bounded for long histories.
- If the trailing context is all `NaN`, repair the data or increase `context_length` so at least one non-`NaN` value is visible.
- If using `feat_dynamic_real`, provide enough future dynamic feature values for the prediction range.

## 5. Forecast extraction

```python
forecast = forecasts[0]

summary = {
    "prediction_length": forecast.prediction_length,
    "start": str(forecast.index[0]),
    "mean": forecast.mean.tolist(),
    "median": forecast.median.tolist(),
    "p10": forecast.quantile(0.1).tolist(),
    "p90": forecast.quantile("p90").tolist(),
}
```

For `SampleForecast` only:

```python
if hasattr(forecast, "samples"):
    samples = forecast.samples  # shape: (num_samples, prediction_length[, target_dim])
```

For multivariate forecasts:

```python
import numpy as np

first_dimension = forecast.copy_dim(0)
summed = forecast.copy_aggregate(np.sum)
```

## 6. Predictor persistence

```python
from pathlib import Path
from gluonts.model.predictor import Predictor

model_dir = Path("saved_predictor")
model_dir.mkdir(parents=True, exist_ok=True)

predictor.serialize(model_dir)
reloaded = Predictor.deserialize(model_dir, device="cpu")
forecasts = list(reloaded.predict(prediction_data))
```

Notes:

- For local `RepresentablePredictor` objects, serialization stores constructor metadata and predictor parameters.
- For trained `PyTorchPredictor` objects, serialization stores both predictor metadata and network weights.
- Use `device="cpu"` when reloading a PyTorch predictor in a CPU-only process.
- Avoid saving smoke models into shared or permanent directories unless the user requested an artifact; use a temporary directory for checks.

## 7. PyTorch construction-only smoke

Construction-only checks catch missing optional dependencies and invalid constructor choices without paying training cost.

```python
from gluonts.torch import DeepAREstimator

estimator = DeepAREstimator(
    freq="D",
    prediction_length=2,
    context_length=4,
    batch_size=2,
    num_batches_per_epoch=1,
    trainer_kwargs={
        "max_epochs": 1,
        "logger": False,
        "enable_checkpointing": False,
        "enable_model_summary": False,
        "accelerator": "cpu",
        "devices": 1,
    },
)
```

Do this before `train(...)` in constrained environments. In full training, GluonTS' PyTorch estimator internals create a temporary model checkpoint callback; keep any checkpoint directory temporary if you do not want persisted files.

## 8. Tiny PyTorch train/predict smoke

```python
from tempfile import TemporaryDirectory
import numpy as np
import pandas as pd
from gluonts.dataset.pandas import PandasDataset
from gluonts.torch import DeepAREstimator

index = pd.date_range("2024-01-01", periods=40, freq="D")
df = pd.DataFrame({"target": np.sin(np.arange(40) / 3.0) + 10.0}, index=index)
dataset = PandasDataset(df, target="target", freq="D")

with TemporaryDirectory() as tmp:
    estimator = DeepAREstimator(
        freq="D",
        prediction_length=2,
        context_length=4,
        batch_size=2,
        num_batches_per_epoch=1,
        trainer_kwargs={
            "max_epochs": 1,
            "logger": False,
            "enable_model_summary": False,
            "accelerator": "cpu",
            "devices": 1,
            "num_sanity_val_steps": 0,
            "default_root_dir": tmp,
        },
    )
    predictor = estimator.train(dataset)
    forecast = next(iter(predictor.predict(dataset)))
    assert forecast.mean.shape == (2,)
```

If the task only needs API coverage, run the bundled `torch_forecast_smoke.py` without `--train`. Use `--train` for a bounded end-to-end check.

## 9. Optional CUDA training

```python
import torch

trainer_kwargs = {
    "max_epochs": 1,
    "logger": False,
    "enable_model_summary": False,
    "num_sanity_val_steps": 0,
}

if torch.cuda.is_available():
    trainer_kwargs.update({"accelerator": "gpu", "devices": 1})
else:
    trainer_kwargs.update({"accelerator": "cpu", "devices": 1})
```

CUDA availability is a performance option, not a correctness requirement for this skill. If the user explicitly requires GPU and `torch.cuda.is_available()` is false, report the GPU block instead of silently claiming GPU coverage.

## 10. Warm-starting a PyTorch estimator

For PyTorch estimators, use `train_from` with an existing `PyTorchPredictor`:

```python
first_predictor = estimator.train(initial_training_data)

updated_estimator = DeepAREstimator(
    freq="D",
    prediction_length=7,
    trainer_kwargs={"max_epochs": 1, "logger": False, "accelerator": "cpu", "devices": 1},
)
updated_predictor = updated_estimator.train_from(first_predictor, updated_training_data)
```

Guardrails:

- The existing predictor must be a `PyTorchPredictor` with a compatible network architecture.
- Recreate the estimator with matching model hyperparameters when warm-starting.
- Use a fresh estimator object for repeated runs because trainer callback configuration is consumed during training.

## 11. Model choice escalation pattern

When generating a robust user workflow, escalate in this order:

1. Validate the dataset with a local predictor such as `SeasonalNaivePredictor`.
2. Extract forecast mean/quantiles and verify prediction length/start index.
3. If learning is required, do construction-only PyTorch estimator smoke.
4. Run one-epoch tiny train/predict if the environment has the `torch` extra.
5. Persist/reload the predictor if the user needs model storage or deployment.
6. Evaluate with the evaluation sub-skill only after forecasts align with labels.
