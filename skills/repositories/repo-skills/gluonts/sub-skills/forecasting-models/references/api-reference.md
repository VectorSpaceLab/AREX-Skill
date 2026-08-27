# Forecasting models API reference

This reference distills the installed GluonTS forecasting APIs needed by a future agent. It intentionally avoids source-checkout links and uses only importable package names.

## Core abstractions

| Concept | Import | Main operation | Notes |
| --- | --- | --- | --- |
| `Estimator` | `gluonts.model.estimator.Estimator` or concrete estimator modules | `predictor = estimator.train(training_data, validation_data=None, ...)` | Trainable/global models expose estimators; training returns a `Predictor`. |
| `Predictor` | `gluonts.model.predictor.Predictor` | `forecasts = predictor.predict(dataset, **kwargs)` | Abstract base with `prediction_length` and `lead_time`; concrete predictors emit forecasts in dataset order. |
| `RepresentablePredictor` | `gluonts.model.predictor.RepresentablePredictor` | `predict_item(item)` through `predict(dataset)` | Constructor-argument based equality and JSON-style serialization are implemented for validated subclasses. |
| `PyTorchPredictor` | `gluonts.torch.model.predictor.PyTorchPredictor` | `predict(dataset, num_samples=None)` | Wraps a PyTorch module plus GluonTS transform; can be moved with `.to(device)`. |
| `Forecast` | `gluonts.model.forecast.Forecast` | `forecast.mean`, `forecast.quantile(q)`, `forecast.index` | Base class for forecast distributions and quantile tables. |

### Predictor signature

```python
Predictor(prediction_length: int, lead_time: int = 0)
```

Important methods:

```python
predictor.predict(dataset, **kwargs) -> Iterator[Forecast]
predictor.serialize(path: pathlib.Path) -> None
Predictor.deserialize(path: pathlib.Path, **kwargs) -> Predictor
```

Operational notes:

- The output iterator order matches the input dataset order.
- `serialize(path)` expects `path` to be an existing directory for most predictors.
- `Predictor.deserialize(path, device="cpu")` is accepted by `PyTorchPredictor` through the base dispatcher; use it when restoring a PyTorch predictor onto CPU.
- Deserialization uses the serialized concrete class name, so the package containing that class must be importable in the active environment.

## Forecast objects

### `SampleForecast`

```python
from gluonts.model.forecast import SampleForecast

SampleForecast(
    samples: numpy.ndarray,
    start_date: pandas.Period,
    item_id: str | None = None,
    info: dict | None = None,
)
```

Behavior:

- `samples` shape is `(num_samples, prediction_length)` for univariate forecasts or `(num_samples, prediction_length, target_dim)` for multivariate forecasts.
- `forecast.mean` is the sample mean along the sample axis.
- `forecast.quantile(q)` accepts floats such as `0.5`, strings such as `"0.5"`, or percentile strings such as `"p50"`.
- `forecast.median` is `forecast.quantile(0.5)`.
- `forecast.mean_ts` and `forecast.quantile_ts(q)` return pandas series indexed by the forecast period index.
- `forecast.copy_dim(dim)` extracts a univariate forecast from a multivariate forecast.
- `forecast.copy_aggregate(np.sum)` or another aggregation function aggregates over the target dimension.

### `QuantileForecast`

```python
from gluonts.model.forecast import QuantileForecast

QuantileForecast(
    forecast_arrays: numpy.ndarray,
    start_date: pandas.Period,
    forecast_keys: list[str],
    item_id: str | None = None,
    info: dict | None = None,
)
```

Behavior:

- `forecast_arrays` first axis must match `forecast_keys`; the second axis is prediction length.
- `forecast_keys` can include quantiles such as `"0.1"`, `"0.5"`, `"p90"`, and optionally `"mean"`.
- If a requested quantile is not stored and enough quantiles are present, GluonTS interpolates or extrapolates tail values.
- If only `"mean"` is stored, quantile requests return `NaN` arrays.
- If `"mean"` is absent, `forecast.mean` returns the median/`p50` value and logs a warning.

## Local and simple predictors

Local predictors operate online on each time series; they are useful as fast baselines and persistence smoke targets.

| Predictor | Import | Constructor | Output behavior |
| --- | --- | --- | --- |
| `SeasonalNaivePredictor` | `from gluonts.model.seasonal_naive import SeasonalNaivePredictor` | `SeasonalNaivePredictor(prediction_length, season_length, imputation_method=LastValueImputation())` | Repeats the last observed season; if the series is shorter than the season, emits the observed mean. Missing targets are imputed by default. |
| `NPTSPredictor` | `from gluonts.model.npts import NPTSPredictor, KernelType` | `NPTSPredictor(prediction_length, context_length=None, kernel_type=KernelType.exponential, exp_kernel_weights=1.0, use_seasonal_model=True, use_default_time_features=True, num_default_time_features=1, feature_scale=1000.0)` | Samples future values from historical targets using a kernel over time/index features. `predict(..., num_samples=100)` controls sample count. |
| `ConstantValuePredictor` | `from gluonts.model.trivial.constant import ConstantValuePredictor` | `ConstantValuePredictor(prediction_length, value=0.0, num_samples=1)` | Emits the same scalar value for every horizon step. |
| `ConstantPredictor` | `from gluonts.model.trivial.constant import ConstantPredictor` | `ConstantPredictor(samples: np.ndarray)` | Reuses an explicit sample array for every item. |
| `IdentityPredictor` | `from gluonts.model.trivial.identity import IdentityPredictor` | `IdentityPredictor(prediction_length, num_samples)` | Repeats the last `prediction_length` target values as identical samples. |
| `MeanPredictor` | `from gluonts.model.trivial.mean import MeanPredictor` | `MeanPredictor(prediction_length, num_samples=100, context_length=None)` | Draws normal samples using mean/std from the full target or trailing context. |
| `MovingAveragePredictor` | `from gluonts.model.trivial.mean import MovingAveragePredictor` | `MovingAveragePredictor(prediction_length, context_length=None)` | Forecasts recursive moving averages. |
| `MeanEstimator` | `from gluonts.model.trivial.mean import MeanEstimator` | `MeanEstimator(prediction_length, num_samples)` | Trains a `ConstantPredictor` from the mean trailing target slice across training entries. |

## PyTorch estimator catalog

Top-level imports are available from `gluonts.torch` for the selected PyTorch estimators.

| Estimator | Import | Required constructor fields | Common bounded choices | Best-fit use |
| --- | --- | --- | --- | --- |
| `DeepAREstimator` | `from gluonts.torch import DeepAREstimator` | `freq`, `prediction_length` | `context_length=prediction_length`, `batch_size=4`, `num_batches_per_epoch=1..3`, `trainer_kwargs={"max_epochs": 1, "logger": False}` | Autoregressive RNN probabilistic baseline for univariate series. |
| `SimpleFeedForwardEstimator` | `from gluonts.torch import SimpleFeedForwardEstimator` | `prediction_length` | `context_length=2*prediction_length` or default `10*prediction_length`; small hidden dimensions for smoke tests. | Fast MLP smoke/global baseline. |
| `TemporalFusionTransformerEstimator` | `from gluonts.torch import TemporalFusionTransformerEstimator` | `freq`, `prediction_length` | Keep `hidden_dim`, `variable_dim`, `num_heads`, batch size, and epochs small; provide feature dimension lists when using features. | Attention/LSTM-style model with support for grouped static/dynamic features. |
| `PatchTSTEstimator` | `from gluonts.torch import PatchTSTEstimator` | `prediction_length`, `patch_len` | Ensure `context_length` is at least `patch_len`; use `patch_len=4..16` in tiny tests. | Transformer-style patch model for univariate forecasting. |
| `DLinearEstimator` | `from gluonts.torch import DLinearEstimator` | `prediction_length` | Small `context_length`, `kernel_size` not larger than useful history. | Lightweight linear decomposition baseline. |
| `LagTSTEstimator` | `from gluonts.torch import LagTSTEstimator` | `freq`, `prediction_length` | Small `d_model`, `nhead`, `num_encoder_layers`; explicit `context_length` in smoke tests. | Transformer over lagged targets. |

All listed PyTorch Lightning estimators accept:

```python
trainer_kwargs: dict | None = None
batch_size: int = 32
num_batches_per_epoch: int = 50
train_sampler: InstanceSampler | None = None
validation_sampler: InstanceSampler | None = None
```

Common `trainer_kwargs` for safe local operation:

```python
trainer_kwargs = {
    "max_epochs": 1,
    "logger": False,
    "enable_model_summary": False,
    "accelerator": "cpu",
    "devices": 1,
    "num_sanity_val_steps": 0,
}
```

For optional CUDA after confirming `torch.cuda.is_available()`:

```python
trainer_kwargs.update({"accelerator": "gpu", "devices": 1})
```

## PyTorch feature fields

Feature-aware PyTorch estimators require consistency between dataset fields and constructor counts:

| Dataset field | Common constructor fields | Requirement |
| --- | --- | --- |
| `feat_dynamic_real` | `num_feat_dynamic_real` or `dynamic_dims` | Prediction data must include future dynamic feature values through `len(target) + prediction_length` when the model expects future dynamic features. |
| `feat_static_real` | `num_feat_static_real` or `static_dims` | Each item must provide the configured number of static real features. |
| `feat_static_cat` | `num_feat_static_cat`, `cardinality`, or `static_cardinalities` | Cardinality lists must match the number of categorical fields and cover all category values. |
| `target` | distribution/event-shape settings | Most selected models are univariate in the normal workflow; multivariate forecasts need compatible model/output choices. |

## Training and warm-start methods

PyTorch Lightning estimators expose:

```python
predictor = estimator.train(training_data, validation_data=None, cache_data=False, ckpt_path=None)
train_output = estimator.train_model(training_data, validation_data=None, from_predictor=None, ckpt_path=None)
warm_predictor = estimator.train_from(existing_pytorch_predictor, training_data)
```

`train_model(...)` returns a named tuple with `transformation`, `trained_net`, `trainer`, and `predictor`. Use `train_from(...)` only with a `PyTorchPredictor`; it loads the existing network state into a new training module.
