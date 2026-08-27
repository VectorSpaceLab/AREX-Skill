# Chronos-2 workflows

These recipes assume the installed package is importable and the user has explicitly authorized any model download or remote URI access. For schema-level fixes, route to [../../data-formats-and-validation/](../../data-formats-and-validation/).

## 1. Load a Chronos-2 model

Prefer dispatch loading, then assert the returned pipeline type:

```python
from chronos import BaseChronosPipeline, Chronos2Pipeline

pipeline = BaseChronosPipeline.from_pretrained(
    "amazon/chronos-2",       # or a local checkpoint directory, or explicit s3:// URI
    device_map="cuda",        # use "cpu" for CPU-only hosts; "auto" for Accelerate placement
    torch_dtype="bfloat16",   # omit or use "float32" on CPU if bfloat16 is not appropriate
)
assert isinstance(pipeline, Chronos2Pipeline), type(pipeline)

print(pipeline.model_context_length)
print(pipeline.model_prediction_length)
print(pipeline.quantiles)
```

Safe loading choices:

- CPU smoke or low-memory debugging: `device_map="cpu"`, usually `torch_dtype="float32"` or omit dtype.
- GPU inference: `device_map="cuda"` for one visible GPU, or `device_map="auto"` when using Accelerate placement.
- S3 model prefix: use `BaseChronosPipeline.from_pretrained("s3://...", force_s3_download=False, ...)`; requires optional S3 dependencies and explicit user authorization.
- Local fine-tuned or saved model: pass the local directory to `BaseChronosPipeline.from_pretrained(...)`.
- LoRA adapter directory: `Chronos2Pipeline.from_pretrained(adapter_dir, device_map=...)` can detect PEFT adapter metadata, requires `peft`, merges the adapter, and returns a `Chronos2Pipeline`.

Model-selection implication: start with `amazon/chronos-2` when the user wants the default released Chronos-2 model and can load it. Choose `autogluon/chronos-2-small` when resource limits matter, then validate quality on the user's series. Treat `autogluon/chronos-2-synth` as a distinct variant that also needs task-level validation.

## 2. Tensor or array prediction

Use this path when all series are already numerical arrays and no covariates are needed.

```python
import numpy as np

# batch=4, n_variates=3, history=128. n_variates > 1 means multivariate forecasting.
inputs = np.random.randn(4, 3, 128).astype("float32")

raw = pipeline.predict(inputs, prediction_length=24, batch_size=16)
# raw is list length 4; each tensor is (3, len(pipeline.quantiles), 24)

quantiles, point = pipeline.predict_quantiles(
    inputs,
    prediction_length=24,
    quantile_levels=[0.1, 0.5, 0.9],
    batch_size=16,
)
# quantiles[0]: (3, 24, 3); point[0]: (3, 24)
```

Interpretation:

- `predict` returns the model's native quantile axis in `pipeline.quantiles` order.
- `predict_quantiles` returns only the requested quantiles in time-major layout.
- The point output is named `mean` by the API but is implemented as the model's `0.5` quantile for Chronos-2.

## 3. List input with mixed history lengths

Use a list when series have different history lengths. Each item may be univariate `(history,)` or multivariate `(n_variates, history)`.

```python
import torch

inputs = [
    torch.randn(100),        # univariate
    torch.randn(2, 150),     # two target variates
    torch.randn(1, 80),      # one variate with explicit variate axis
]

quantiles, point = pipeline.predict_quantiles(inputs, prediction_length=12)
for q, m in zip(quantiles, point):
    print(q.shape, m.shape)
```

If different items have incompatible task semantics, loop and forecast each group separately rather than mixing them in one call.

## 4. List-of-dicts prediction with covariates

Use this path for programmatic covariate inputs without pandas. All dictionaries in the same call must share schema: same target variate count, same `past_covariates` keys, and same `future_covariates` keys.

```python
import numpy as np

prediction_length = 24
inputs = []
for history_length in [96, 120, 144]:
    inputs.append(
        {
            "target": np.random.randn(2, history_length).astype("float32"),  # two target variates
            "past_covariates": {
                "temperature": np.random.randn(history_length).astype("float32"),
                "holiday_type": np.random.choice(["none", "local", "national"], size=history_length),
            },
            "future_covariates": {
                "temperature": np.random.randn(prediction_length).astype("float32"),
                "holiday_type": np.random.choice(["none", "local", "national"], size=prediction_length),
            },
        }
    )

quantiles, point = pipeline.predict_quantiles(
    inputs,
    prediction_length=prediction_length,
    quantile_levels=[0.1, 0.5, 0.9],
    batch_size=32,
)
```

Notes:

- Categorical covariates should be NumPy/pandas arrays or series; PyTorch tensors cannot carry string dtype.
- A future covariate must also appear in `past_covariates` so the model has its historical scale/category context.
- If schemas differ, split into homogeneous groups.

## 5. DataFrame covariate forecast

Use `predict_df` for normal long-format time-series tables. The DataFrame route is usually easier to audit than raw dictionaries.

```python
import pandas as pd

history = pd.DataFrame(
    {
        "id": ["A"] * 6 + ["B"] * 6,
        "timestamp": list(pd.date_range("2024-01-01", periods=6, freq="h")) * 2,
        "sales": [10, 11, 13, 12, 14, 15, 30, 31, 32, 34, 33, 35],
        "temperature": [20, 21, 21, 22, 23, 23, 18, 18, 19, 20, 20, 21],
        "store_open": ["yes"] * 12,
    }
)
future = pd.DataFrame(
    {
        "id": ["A"] * 3 + ["B"] * 3,
        "timestamp": list(pd.date_range("2024-01-01 06:00", periods=3, freq="h")) * 2,
        "temperature": [24, 24, 23, 21, 22, 22],
        "store_open": ["yes", "yes", "no", "yes", "yes", "yes"],
    }
)

forecast = pipeline.predict_df(
    history,
    future_df=future,
    id_column="id",
    timestamp_column="timestamp",
    target="sales",
    prediction_length=3,
    quantile_levels=[0.1, 0.5, 0.9],
    batch_size=16,
)
print(forecast)
```

Expected output columns: `id`, `timestamp`, `target_name`, `predictions`, `0.1`, `0.5`, `0.9`.

For multiple targets:

```python
forecast = pipeline.predict_df(
    history,
    future_df=future,
    id_column="id",
    timestamp_column="timestamp",
    target=["sales", "returns"],
    prediction_length=3,
)
# rows = n_items * 2 targets * 3 steps
```

## 6. Cross-learning across related items

Cross-learning can help when many related, homogeneous series have short histories. It can also hurt; evaluate with and without it.

```python
forecast_joint = pipeline.predict_df(
    history,
    future_df=future,
    id_column="id",
    timestamp_column="timestamp",
    target="sales",
    prediction_length=24,
    cross_learning=True,
    batch_size=100,
)
```

Use a stable `batch_size` when comparing runs because cross-learning results depend on which tasks share a batch. Avoid mixing unrelated task schemas.

## 7. Long-horizon forecasting

Chronos-2 can forecast beyond `pipeline.model_prediction_length`, but quality may degrade because the model unrolls predictions autoregressively.

```python
horizon = 3 * pipeline.model_prediction_length
forecast = pipeline.predict_df(
    history,
    prediction_length=horizon,
    id_column="id",
    timestamp_column="timestamp",
    target="sales",
    freq="h",  # provide explicit frequency if inference is ambiguous
)
```

For strict workflows, reject long horizons yourself before calling `predict_df`:

```python
if horizon > pipeline.model_prediction_length:
    raise ValueError("Requested horizon exceeds loaded Chronos-2 default prediction length")
```

For raw `predict`, you can instead set `limit_prediction_length=True` to have the pipeline raise. If using long-horizon unrolling, keep `unrolled_quantiles` to a subset of `pipeline.quantiles`.

## 8. Embeddings

Use `embed` for encoder representations of numerical target arrays. It does not accept raw list-of-dicts covariate inputs.

```python
import numpy as np

inputs = np.random.randn(8, 2, 512).astype("float32")
embeddings, loc_scale = pipeline.embed(inputs, batch_size=16)
for emb, (loc, scale) in zip(embeddings, loc_scale):
    print(emb.shape, loc.shape, scale.shape)
```

Expect each embedding tensor to be `(n_variates, num_patches + 2, d_model)`.

## 9. fev bridge at a high level

Use `predict_fev` only when optional fev dependencies and benchmark data access are available and explicitly in scope.

```python
# task = fev.Task(...)
predictions_per_window, inference_time_s = pipeline.predict_fev(
    task,
    batch_size=256,
    as_univariate=False,
)
```

- `as_univariate=True` ignores covariates and splits targets.
- `finetune_kwargs={...}` triggers fine-tuning on the first window before prediction; route setup to [../../training-evaluation-deployment/](../../training-evaluation-deployment/).

## 10. Save and reload

```python
save_dir = "chronos2-saved-model"
pipeline.save_pretrained(save_dir)

reloaded = BaseChronosPipeline.from_pretrained(save_dir, device_map="cpu")
assert isinstance(reloaded, Chronos2Pipeline)
```

Avoid writing checkpoints into runtime skill directories. Use a user-selected output directory for real model artifacts.

## 11. Safe smoke helper

The bundled helper does not load or download a model by default:

```bash
python sub-skills/chronos-2-forecasting/scripts/chronos2_smoke_forecast.py --help
python sub-skills/chronos-2-forecasting/scripts/chronos2_smoke_forecast.py
```

To run a tiny forecast, the user must provide a model anchor:

```bash
python sub-skills/chronos-2-forecasting/scripts/chronos2_smoke_forecast.py \
  --model-id-or-path amazon/chronos-2 \
  --device-map cpu \
  --prediction-length 4
```
