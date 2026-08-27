# Model overview and selection guide

## Mental model

GluonTS separates forecasting into two layers:

1. **Estimator** — trains an offline/global model from a dataset.
2. **Predictor** — emits forecasts for one or more time series.

The canonical global-model flow is:

```python
predictor = estimator.train(training_data)
forecasts = list(predictor.predict(prediction_data))
```

Local models skip offline training and are available directly as predictors:

```python
predictor = SeasonalNaivePredictor(prediction_length=24, season_length=24)
forecasts = list(predictor.predict(data))
```

Use local predictors for quick baselines, sanity checks, or deterministic smoke tests. Use PyTorch estimators when the task requires learned cross-series structure, probabilistic neural forecasting, or model persistence after training.

## Selection checklist

| If the user needs... | Prefer... | Why |
| --- | --- | --- |
| A deterministic no-training baseline | `SeasonalNaivePredictor`, `IdentityPredictor`, `ConstantValuePredictor`, `MovingAveragePredictor` | Fast, simple, serializable, and good for pipeline verification. |
| A stochastic local nonparametric baseline | `NPTSPredictor` | Samples from historical values using time/index feature kernels. |
| A fast trainable neural smoke | `SimpleFeedForwardEstimator` or tiny `DeepAREstimator` | Small constructor surface and can run with `max_epochs=1`. |
| A general probabilistic autoregressive baseline | `DeepAREstimator` | Common GluonTS starting point for univariate time series. |
| Attention over lag/patch structure | `PatchTSTEstimator` or `LagTSTEstimator` | Transformer-style alternatives for univariate forecasting. |
| Lightweight linear decomposition | `DLinearEstimator` | Efficient linear baseline with probabilistic output support. |
| Rich static/dynamic feature modeling | `TemporalFusionTransformerEstimator` | Explicit feature dimension/cardinality controls; keep smoke tests small. |
| Evaluation metrics/backtesting | Produce forecasts first, then use `evaluation-backtesting` | This sub-skill handles model operation; metrics belong to evaluation. |

## Local predictors and baselines

### Seasonal naive

`SeasonalNaivePredictor` repeats the most recent season of length `season_length` for each series. If the history is shorter than the season length, it emits the observed mean. Use it when seasonality is known and the goal is a deterministic reference forecast.

```python
from gluonts.model.seasonal_naive import SeasonalNaivePredictor

predictor = SeasonalNaivePredictor(prediction_length=12, season_length=12)
forecasts = list(predictor.predict(dataset))
```

Tips:

- For hourly daily seasonality, start with `season_length=24`.
- For daily weekly seasonality, start with `season_length=7`.
- For monthly annual seasonality, start with `season_length=12`.
- Missing target values are imputed by default with the last valid value.

### NPTS

`NPTSPredictor` is a local non-parametric time-series predictor. It samples future values from historical target values using a kernel over time and optional dynamic features.

```python
from gluonts.model.npts import NPTSPredictor, KernelType

predictor = NPTSPredictor(
    prediction_length=12,
    context_length=120,
    kernel_type=KernelType.exponential,
)
forecasts = list(predictor.predict(dataset, num_samples=100))
```

Tips:

- Use a bounded `context_length` for long histories.
- Leave `use_seasonal_model=True` when the timestamp frequency carries seasonal structure.
- If using custom `feat_dynamic_real` with the seasonal model, provide features for both the historical range and the future prediction range.
- The predictor raises a data error if the considered trailing context is entirely `NaN`.

### Trivial predictors

Use these for pipeline and evaluation sanity checks:

- `ConstantValuePredictor(prediction_length, value=0.0, num_samples=1)` — always emits a fixed value.
- `IdentityPredictor(prediction_length, num_samples)` — repeats the last `prediction_length` observed values.
- `MeanPredictor(prediction_length, num_samples=100, context_length=None)` — draws samples around historical mean/std.
- `MovingAveragePredictor(prediction_length, context_length=None)` — recursive moving-average baseline.
- `MeanEstimator(prediction_length, num_samples)` — trains a `ConstantPredictor` from trailing target means.

## PyTorch model catalog

GluonTS currently emphasizes PyTorch-based neural models in the selected skill scope. The following global models are the main verified family for this sub-skill.

| Model | Local/global | Data layout | Method family | Constructor highlights |
| --- | --- | --- | --- | --- |
| `DeepAREstimator` | Global | Mostly univariate | RNN autoregressive probabilistic model | Requires `freq`, `prediction_length`; optional static/dynamic feature counts; default `context_length=prediction_length`. |
| `SimpleFeedForwardEstimator` | Global | Univariate | MLP | Requires `prediction_length`; default `context_length=10 * prediction_length`; good tiny smoke model. |
| `TemporalFusionTransformerEstimator` | Global | Univariate plus static/dynamic features | LSTM + attention + feature selection | Requires `freq`, `prediction_length`; feature dimensions use `static_dims`, `dynamic_dims`, `past_dynamic_dims`, and cardinality lists. |
| `PatchTSTEstimator` | Global | Univariate | Patch Transformer | Requires `prediction_length`, `patch_len`; ensure enough context for patching. |
| `DLinearEstimator` | Global | Univariate | Linear decomposition | Requires `prediction_length`; optional `kernel_size`, `context_length`, and distribution output. |
| `LagTSTEstimator` | Global | Univariate | Transformer over lagged targets | Requires `freq`, `prediction_length`; optional `lags_seq`, transformer dimensions, and context length. |

Other PyTorch estimators may be importable in the package, but this sub-skill focuses on the listed constructors because their signatures were captured and their workflows fit the selected verification scope.

## Choosing constructor bounds

For smoke tests or agent-generated examples, keep training tiny and deterministic:

```python
trainer_kwargs = {
    "max_epochs": 1,
    "logger": False,
    "enable_model_summary": False,
    "accelerator": "cpu",
    "devices": 1,
    "num_sanity_val_steps": 0,
}

estimator = DeepAREstimator(
    freq="D",
    prediction_length=2,
    context_length=4,
    batch_size=2,
    num_batches_per_epoch=1,
    trainer_kwargs=trainer_kwargs,
)
```

For full training, increase `max_epochs`, `num_batches_per_epoch`, `batch_size`, and model dimensions deliberately. Do not silently use defaults for expensive work: many PyTorch estimators default to `max_epochs=100` and `num_batches_per_epoch=50`.

## CPU and optional CUDA

CPU is sufficient for API correctness, smoke tests, local predictors, serialization, and tiny PyTorch training. CUDA is optional acceleration.

Use CPU unless the user explicitly asks for GPU:

```python
trainer_kwargs={"accelerator": "cpu", "devices": 1, "max_epochs": 1}
```

Use CUDA only after checking availability:

```python
import torch

if torch.cuda.is_available():
    trainer_kwargs={"accelerator": "gpu", "devices": 1, "max_epochs": 1}
else:
    # fall back to CPU or report that CUDA is unavailable
    trainer_kwargs={"accelerator": "cpu", "devices": 1, "max_epochs": 1}
```

A visible GPU is not required to operate this skill.

## Forecast object handling

Most predictors return `SampleForecast` or another `Forecast` subtype. Read forecasts through the common properties:

```python
forecast = next(iter(predictor.predict(dataset)))
mean = forecast.mean
median = forecast.median
p10 = forecast.quantile(0.1)
p90 = forecast.quantile("p90")
index = forecast.index
```

For multivariate forecast objects, use:

```python
one_dim = forecast.copy_dim(0)
aggregate = forecast.copy_aggregate(np.sum)
```

For plotting, `forecast.plot()` uses matplotlib and is not needed in non-interactive smoke tests.

## Persistence posture

Prefer predictor-level persistence:

```python
from pathlib import Path
from gluonts.model.predictor import Predictor

model_dir = Path("model")
model_dir.mkdir(parents=True, exist_ok=True)
predictor.serialize(model_dir)
reloaded = Predictor.deserialize(model_dir, device="cpu")
```

Local `RepresentablePredictor` instances and trained `PyTorchPredictor` instances are serializable in the selected scope. If a custom predictor is not representable or does not implement serialization, report it clearly and use a supported local predictor for persistence smoke testing.

## Legacy MXNet caveat

Some GluonTS model tables and older examples mention MXNet implementations. MXNet was not selected as a verified required backend for this skill. Do not claim MXNet workflows are verified. If the user specifically requests MXNet, treat it as a separate optional/legacy environment task: install a compatible MXNet stack, verify imports, and run a bounded MXNet-specific smoke before relying on it.
