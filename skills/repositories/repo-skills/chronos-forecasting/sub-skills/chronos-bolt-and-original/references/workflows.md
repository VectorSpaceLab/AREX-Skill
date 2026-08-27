# Chronos-Bolt and original Chronos workflows

Use these recipes after deciding that the user needs Chronos-Bolt or original Chronos/T5, not Chronos-2. If the request includes covariates, multivariate targets, `future_df`, or Chronos-2 fine-tuning, route to `../chronos-2-forecasting/`.

## 1. Choose the model family

Ask what output the user needs:

- Need **fast univariate quantile forecasts** and a compact model: choose Chronos-Bolt (`amazon/chronos-bolt-*`).
- Need **sample trajectories** or generation controls: choose original Chronos/T5 (`amazon/chronos-t5-*`).
- Need **known future covariates, multiple targets, cross-series learning, or the latest family**: route to `../chronos-2-forecasting/`.
- Need **DataFrame schema diagnosis** rather than model use: route to `../data-formats-and-validation/`.
- Need **training/evaluation scripts, SageMaker, fev benchmark orchestration, or aggregate score processing**: route to `../training-evaluation-deployment/`.

Size selection rule of thumb:

- Use `tiny` or `mini` for examples, CPU checks, and constrained memory.
- Use `small` or `base` when accuracy matters and resources permit.
- Use original `large` only when the user explicitly accepts the memory/latency cost.

## 2. Load a model safely

Prefer `BaseChronosPipeline.from_pretrained` when the model config should decide the pipeline class:

```python
from chronos import BaseChronosPipeline, ChronosBoltPipeline, ChronosPipeline

pipeline = BaseChronosPipeline.from_pretrained(
    "amazon/chronos-bolt-small",  # or a local model directory
    device_map="cpu",             # use "cuda" or an explicit map when appropriate
    torch_dtype="float32",        # "bfloat16" can reduce memory on supported hardware
)

if isinstance(pipeline, ChronosBoltPipeline):
    print("Bolt quantile pipeline")
elif isinstance(pipeline, ChronosPipeline):
    print("original Chronos sample pipeline")
```

Use direct classes when the user explicitly names a family and you want a mismatch to fail early:

```python
from chronos import ChronosBoltPipeline, ChronosPipeline

bolt = ChronosBoltPipeline.from_pretrained("amazon/chronos-bolt-tiny", device_map="cpu")
original = ChronosPipeline.from_pretrained("amazon/chronos-t5-tiny", device_map="cpu")
```

Remote identifiers can download model weights through Transformers. For offline or production-safe work, prefer a local model directory and configure the Hugging Face cache before loading. S3 URIs require optional `boto3` support and can be refreshed with `force_s3_download=True` through the base loader.

## 3. Run Chronos-Bolt tensor forecasts

`ChronosBoltPipeline.predict` returns training quantile channels directly:

```python
import torch
from chronos import ChronosBoltPipeline

pipeline = ChronosBoltPipeline.from_pretrained("amazon/chronos-bolt-tiny", device_map="cpu")

context = torch.tensor([
    [1.0, 1.5, 2.0, 2.5, 3.0],
    [2.0, 2.1, 2.4, 2.8, 3.3],
])

forecast = pipeline.predict(context, prediction_length=12)
print(forecast.shape)  # (batch_size, len(pipeline.quantiles), 12)
print(pipeline.quantiles)  # official models: [0.1, 0.2, ..., 0.9]
```

When the user requests custom quantile levels or a point forecast, call `predict_quantiles`:

```python
quantiles, point = pipeline.predict_quantiles(
    context,
    prediction_length=12,
    quantile_levels=[0.1, 0.5, 0.9],
)
print(quantiles.shape)  # (batch_size, 12, 3)
print(point.shape)      # (batch_size, 12)
```

For Bolt, `point` is the `0.5` quantile channel, not an arithmetic sample mean.

## 4. Run original Chronos/T5 tensor forecasts

`ChronosPipeline.predict` returns sampled trajectories:

```python
import torch
from chronos import ChronosPipeline

pipeline = ChronosPipeline.from_pretrained("amazon/chronos-t5-tiny", device_map="cpu")
context = torch.tensor([[1.0, 1.5, 2.0, 2.5, 3.0]])

samples = pipeline.predict(
    context,
    prediction_length=12,
    num_samples=32,
    temperature=1.0,
    top_k=50,
    top_p=1.0,
)
print(samples.shape)  # (batch_size, num_samples, 12)
```

Convert samples to quantiles and a mean with `predict_quantiles`:

```python
quantiles, mean = pipeline.predict_quantiles(
    context,
    prediction_length=12,
    quantile_levels=[0.1, 0.5, 0.9],
    num_samples=64,
)
print(quantiles.shape)  # (batch_size, 12, 3)
print(mean.shape)       # (batch_size, 12)
```

For original Chronos, `mean` is the arithmetic mean across sample trajectories.

## 5. Use list inputs for ragged univariate batches

Both families accept a list of 1D tensors. The helper pads shorter series on the left with `torch.nan`:

```python
import torch

context = [
    torch.tensor([10.0, 11.0, 12.0]),
    torch.tensor([20.0, 21.0, 22.0, 23.0, 24.0]),
]

# Bolt: returns (2, num_quantiles, horizon)
forecast = bolt.predict(context, prediction_length=6)

# Original: returns (2, num_samples, horizon)
samples = original.predict(context, prediction_length=6, num_samples=16)
```

Manual equivalent for a 2D tensor is left-padding with `torch.nan`, not zero-filling:

```python
context = torch.tensor([
    [float("nan"), float("nan"), 10.0, 11.0, 12.0],
    [20.0, 21.0, 22.0, 23.0, 24.0],
])
```

## 6. Use univariate `predict_df`

`predict_df` is shared by Bolt and original Chronos. It converts a long-format pandas DataFrame to independent univariate series, calls `predict_quantiles`, and returns a long forecast DataFrame.

```python
import pandas as pd

history = pd.DataFrame({
    "item_id": ["A"] * 5 + ["B"] * 5,
    "timestamp": pd.date_range("2024-01-01", periods=5, freq="D").tolist()
    + pd.date_range("2024-01-01", periods=5, freq="D").tolist(),
    "target": [1.0, 1.1, 1.2, 1.3, 1.4, 10.0, 10.5, 10.7, 10.8, 11.0],
})

forecast_df = pipeline.predict_df(
    history,
    prediction_length=3,
    quantile_levels=[0.1, 0.5, 0.9],
    id_column="item_id",
    timestamp_column="timestamp",
    target="target",
)

print(forecast_df.columns)
# item_id, timestamp, target_name, predictions, 0.1, 0.5, 0.9
```

Remember:

- `target` must be one column name, not a list.
- These pipelines ignore covariates and extra columns.
- For custom validation, irregular timestamp fixes, or future covariates, route to `../data-formats-and-validation/` or `../chronos-2-forecasting/`.

## 7. Generate embeddings

Bolt embeddings:

```python
embeddings, (loc, scale) = bolt.embed(context)
print(embeddings.shape)  # (batch_size, patch_windows [+ optional REG token], d_model)
print(loc.shape, scale.shape)  # each (batch_size,)
```

Original Chronos/T5 embeddings:

```python
embeddings, tokenizer_state = original.embed(context)
print(embeddings.shape)  # (batch_size, token_context_length [+ EOS], d_model)
```

Use embeddings for analysis or downstream feature extraction. Do not assume embedding sequence lengths match raw context lengths for Bolt because Bolt uses patch windows and optional register tokens. For original causal models, `embed` can be unsupported; official T5 models are encoder-decoder.

## 8. Evaluate with fev through `predict_fev`

If optional `fev` and `datasets` dependencies are installed and the task data is available:

```python
predictions_per_window, inference_time_s = pipeline.predict_fev(
    task,
    batch_size=32,
    prediction_length=task.horizon,
)
```

This bridge treats Bolt/original pipelines as univariate forecasters. It converts windows to DataFrame inputs, splits multivariate targets into independent univariate series, and ignores covariates. For benchmark scripts, dataset acquisition, or aggregate scoring, route to `../training-evaluation-deployment/`.

## 9. Handle long prediction lengths

Both Bolt and original Chronos have a configured `model_prediction_length`:

```python
print(pipeline.model_prediction_length)
```

Default behavior allows longer horizons but warns about possible quality degradation:

```python
forecast = pipeline.predict(context, prediction_length=2 * pipeline.model_prediction_length)
```

Set `limit_prediction_length=True` when the user wants a hard guardrail:

```python
forecast = pipeline.predict(
    context,
    prediction_length=2 * pipeline.model_prediction_length,
    limit_prediction_length=True,  # raises ValueError instead of warning
)
```

Long-horizon mechanics differ:

- Bolt recursively appends quantile forecasts and reduces expanded quantile combinations back to the training quantile grid; this can increase memory use for horizons beyond the model default.
- Original Chronos recursively appends the median sample path between generated blocks.

## 10. Use the bundled smoke script

Inspection only, no model load:

```sh
python sub-skills/chronos-bolt-and-original/scripts/bolt_original_smoke.py --help
python sub-skills/chronos-bolt-and-original/scripts/bolt_original_smoke.py
```

Local model smoke:

```sh
python sub-skills/chronos-bolt-and-original/scripts/bolt_original_smoke.py \
  --family bolt \
  --model-id-or-path /path/to/local/chronos-bolt-model \
  --prediction-length 3
```

Remote model smoke requires an explicit remote opt-in:

```sh
python sub-skills/chronos-bolt-and-original/scripts/bolt_original_smoke.py \
  --family original \
  --model-id-or-path amazon/chronos-t5-tiny \
  --allow-remote \
  --prediction-length 3 \
  --num-samples 4
```
