# Forecasting models troubleshooting

## Quick symptom map

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ImportError: No module named torch` or Lightning import failure | `gluonts` installed without the PyTorch extra | Install/activate an environment with `gluonts[torch]`, or use local non-PyTorch predictors only. |
| Neural training is unexpectedly slow | Defaults are large (`max_epochs=100`, many batches per epoch) | Set explicit `trainer_kwargs`, `batch_size`, `num_batches_per_epoch`, and model dimensions. |
| `MisconfigurationException` around checkpointing | GluonTS PyTorch estimators add their own `ModelCheckpoint` callback during training | Do not pass `enable_checkpointing=False` to actual `train(...)`; instead set `default_root_dir` to a temporary directory and disable logging/model summary. Construction-only checks may use `enable_checkpointing=False`. |
| Forecast count does not match dataset item count | Input dataset iterator was consumed or filtered, or prediction failed for some item | Materialize the dataset if it is one-shot; inspect the first entries and run a local baseline predictor. |
| Forecast horizon is wrong | `prediction_length` mismatch between split/test generation, estimator, and evaluator | Use one `prediction_length` variable across split, estimator, predictor, and metric code. |
| Forecast starts at an unexpected timestamp | Dataset `start`, `freq`, or split point is wrong | Inspect `entry["start"]`, target length, and `forecast.index[0]`; verify dataset construction with `data-pipelines`. |
| `NPTSPredictor` complains that trailing context is all `NaN` | The selected `context_length` contains no observed targets | Repair/impute data, increase `context_length`, or choose a different baseline. |
| Feature-shape error during training or prediction | Constructor feature counts/dimensions do not match dataset fields | Align `num_feat_dynamic_real`, `num_feat_static_real`, `num_feat_static_cat`, cardinalities, and `feat_dynamic_real` future length. |
| `Predictor.deserialize` cannot locate a class | The predictor's package or custom class is not importable | Activate the same package environment; avoid custom non-importable predictors for portable artifacts. |
| `torch.cuda.is_available()` is false | CUDA stack is absent or incompatible | Use CPU or report that GPU is unavailable; CUDA is optional for this skill unless the user explicitly requires it. |
| MXNet import/model examples fail | MXNet backend is legacy and not verified in this scope | Do not treat MXNet as required; create a separate verified MXNet environment if explicitly requested. |

## Optional PyTorch extra missing

The selected neural workflows require PyTorch and Lightning. Detect this before training:

```python
try:
    import torch
    import lightning.pytorch
    from gluonts.torch import DeepAREstimator
except ImportError as exc:
    raise RuntimeError("PyTorch/Lightning extra is unavailable") from exc
```

If the extra is unavailable, still use local predictors such as `SeasonalNaivePredictor`, `NPTSPredictor`, or the trivial predictors.

## Bounding PyTorch Lightning work

Always specify a bounded trainer configuration for examples and tests:

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

For actual `train(...)`, avoid `enable_checkpointing=False` because GluonTS inserts a `ModelCheckpoint` callback internally. If you need no persistent checkpoint artifacts, use a temporary `default_root_dir`:

```python
from tempfile import TemporaryDirectory

with TemporaryDirectory() as tmp:
    trainer_kwargs["default_root_dir"] = tmp
    predictor = estimator.train(training_data)
```

## Dataset history too short

DeepAR defaults `context_length` to `prediction_length`. SimpleFeedForward, PatchTST, DLinear, and LagTST commonly default `context_length` to `10 * prediction_length`. For tiny examples, set context explicitly and ensure each item has enough target history:

```python
prediction_length = 2
context_length = 4
# target length should comfortably exceed context_length + prediction_length
```

For `PatchTSTEstimator`, also ensure `context_length` is compatible with `patch_len` and stride. For very small smoke data, use `patch_len=4` or choose `DeepAREstimator`/`SimpleFeedForwardEstimator` instead.

## Feature mismatch

Common feature problems:

- `num_feat_dynamic_real` is nonzero but `feat_dynamic_real` is absent.
- `feat_dynamic_real` has only historical length, but prediction needs future dynamic features through the forecast horizon.
- `num_feat_static_cat > 0` but `cardinality` is missing or too small for category values.
- TFT dimension lists (`static_dims`, `dynamic_dims`, `past_dynamic_dims`) do not match the arrays provided in each dataset entry.

Use a local predictor first when debugging feature fields, because local predictors usually ignore extra neural-feature metadata and can prove basic time indexing.

## Forecast quantile surprises

For `SampleForecast`, quantiles are computed from sorted samples. More samples give smoother quantiles.

For `QuantileForecast`:

- `forecast_keys` are normalized; `"p50"` becomes the equivalent float-style name internally.
- If `"mean"` is not stored, `forecast.mean` falls back to median with a warning.
- If only `"mean"` is stored, `forecast.quantile(q)` returns `NaN` arrays.
- Interpolation/extrapolation may be used for quantiles not explicitly stored.

When downstream code requires a specific quantile, assert it is finite:

```python
import numpy as np

p90 = forecast.quantile(0.9)
assert np.isfinite(p90).all()
```

## Persistence failures

Checklist:

1. Create the output directory before `serialize`.
2. Use `pathlib.Path`, not a string-only API assumption.
3. Keep the same installed package available for deserialization.
4. For PyTorch predictors, reload to CPU if portability matters:

```python
reloaded = Predictor.deserialize(model_dir, device="cpu")
```

If a predictor type is not serializable, switch the persistence smoke to a local `RepresentablePredictor` such as `SeasonalNaivePredictor`, then report that the requested custom predictor lacks a verified serialization path.

## Reusing estimators and callbacks

PyTorch estimator training consumes callback configuration from `trainer_kwargs` when constructing the Lightning trainer. For repeated training, warm-starting, or callback-heavy workflows, prefer constructing a fresh estimator object for each run rather than reusing a previously trained estimator.

## CUDA-specific issues

Before setting `accelerator="gpu"`, run:

```python
import torch
print(torch.cuda.is_available())
```

If false, do not use GPU trainer kwargs. If true but training still fails, report the CUDA/PyTorch/driver mismatch and rerun the same tiny case on CPU to separate API errors from hardware errors.

## Legacy MXNet caveat

Older examples and model tables may mention MXNet estimators. The selected verified workflow for this skill is base package + PyTorch, not MXNet. Treat MXNet as optional legacy support requiring a separate compatibility probe; do not claim MXNet serialization, training, or warm-start behavior is verified here.
