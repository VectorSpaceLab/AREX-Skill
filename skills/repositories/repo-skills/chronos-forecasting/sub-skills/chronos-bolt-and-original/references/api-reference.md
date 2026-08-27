# Chronos-Bolt and original Chronos API reference

This reference covers the public `chronos-forecasting` APIs for `ChronosBoltPipeline`, `ChronosPipeline`, and their shared base methods. It deliberately excludes Chronos-2 covariate and multivariate workflows; route those to `../chronos-2-forecasting/`.

## Family differences

| Family | Pipeline class | Forecast type | Core mechanism | Best fit |
|---|---|---|---|---|
| Chronos-Bolt | `ChronosBoltPipeline` | `ForecastType.QUANTILES` | Patch the historical context, encode patches, then directly produce multi-step quantiles. | Fast univariate probabilistic forecasts and low memory use. |
| Original Chronos/T5 | `ChronosPipeline` | `ForecastType.SAMPLES` | Scale and quantize the time series into tokens, then sample future token trajectories from a language model. | Sample trajectories, sampling controls, and original Chronos compatibility. |
| Chronos-2 | `Chronos2Pipeline` | Quantile-oriented universal pipeline | Supports univariate, multivariate, and covariate-informed tasks. | Use `../chronos-2-forecasting/` for this family. |

README evidence describes Chronos-Bolt as up to 250x faster and 20x more memory-efficient than original Chronos models of the same size, while Chronos-2 is the latest family and wins most head-to-head comparisons against Bolt. Treat those as model-family selection signals, not as a substitute for task-specific validation.

## Available model IDs

Chronos-Bolt public model IDs:

- `amazon/chronos-bolt-tiny` — 9M parameters
- `amazon/chronos-bolt-mini` — 21M parameters
- `amazon/chronos-bolt-small` — 48M parameters
- `amazon/chronos-bolt-base` — 205M parameters

Original Chronos/T5 public model IDs:

- `amazon/chronos-t5-tiny` — 8M parameters
- `amazon/chronos-t5-mini` — 20M parameters
- `amazon/chronos-t5-small` — 46M parameters
- `amazon/chronos-t5-base` — 200M parameters
- `amazon/chronos-t5-large` — 710M parameters

Chronos-2 model IDs such as `amazon/chronos-2`, `autogluon/chronos-2-synth`, and `autogluon/chronos-2-small` belong to `../chronos-2-forecasting/`.

## Imports

```python
from chronos import BaseChronosPipeline, ChronosBoltPipeline, ChronosPipeline, ForecastType
```

`chronos.__all__` exports these names. `BaseChronosPipeline.from_pretrained(...)` can auto-route to the pipeline class declared in the model config.

## Loading API

```python
BaseChronosPipeline.from_pretrained(
    pretrained_model_name_or_path,
    *model_args,
    force_s3_download=False,
    **kwargs,
)
ChronosBoltPipeline.from_pretrained(pretrained_model_name_or_path, *args, **kwargs)
ChronosPipeline.from_pretrained(pretrained_model_name_or_path, *args, **kwargs)
```

`pretrained_model_name_or_path` can be:

- a local model directory;
- a Hugging Face model ID;
- an `s3://...` URI.

Important loading behavior:

- For `s3://...`, loading is delegated through `BaseChronosPipeline.from_pretrained` and requires `boto3` support. Use `force_s3_download=True` to refresh the local S3 cache.
- For Hugging Face/local loading, loader keyword arguments are forwarded to Transformers `AutoConfig` and `from_pretrained` methods.
- `torch_dtype=` and `dtype=` are both accepted by the base loader. String values `"float32"` and `"bfloat16"` are mapped to Torch dtypes; otherwise the resolved value is forwarded to Transformers.
- The base loader checks that the config has `chronos_pipeline_class` or `chronos_config`, then uses the registered pipeline class. Non-Chronos configs fail with `ValueError("Not a Chronos config file")`.

## Shared input contract

For `ChronosBoltPipeline` and original `ChronosPipeline`, tensor-style inputs are univariate:

```python
inputs: torch.Tensor | list[torch.Tensor]
```

Accepted shapes:

- one series: a 1D tensor shaped `(context_length,)`; it is promoted to batch size 1;
- batch: a 2D tensor shaped `(batch_size, context_length)`;
- ragged batch: a Python list of 1D tensors; the pipeline left-pads shorter series with `torch.nan` before stacking.

Do not pass 3D tensors, multivariate tensors, dictionaries, covariates, or `future_df` to these pipelines. Use `../chronos-2-forecasting/` for those workflows. If you manually batch unequal-length series, left-pad with `torch.nan`; do not right-pad or fill missing history with zeros unless zero is an observed value.

All `predict` and `predict_quantiles` outputs are returned as `torch.float32` on CPU, even when the model runs with a lower precision dtype or on an accelerator.

## `ChronosBoltPipeline`

### Properties

```python
pipeline.forecast_type == ForecastType.QUANTILES
pipeline.model_context_length      # from model.chronos_config.context_length
pipeline.model_prediction_length   # from model.chronos_config.prediction_length
pipeline.quantiles                 # training quantile levels, official models use [0.1, ..., 0.9]
```

### `predict`

```python
ChronosBoltPipeline.predict(
    inputs: torch.Tensor | list[torch.Tensor],
    prediction_length: int | None = None,
    limit_prediction_length: bool = False,
) -> torch.Tensor
```

Returns a tensor shaped:

```text
(batch_size, num_training_quantiles, prediction_length)
```

For official Bolt models, `num_training_quantiles == 9` for the `0.1, 0.2, ..., 0.9` quantiles. This is already a quantile forecast, not sample trajectories.

Prediction-length behavior:

- `prediction_length=None` uses `pipeline.model_prediction_length`.
- If `prediction_length > model_prediction_length`, the pipeline warns that quality may degrade.
- If the request is longer and `limit_prediction_length=True`, it raises `ValueError`.
- If longer horizons are allowed, Bolt generates recursive forecast blocks. After the first direct block, the batch is expanded across quantiles and reduced back to the training quantiles, so memory can increase by roughly the number of training quantiles.

Context behavior:

- If the context is longer than `model_context_length`, Bolt uses the last `model_context_length` observations.
- Patch creation left-pads to an input patch boundary with `torch.nan` when needed.

### `predict_quantiles`

```python
ChronosBoltPipeline.predict_quantiles(
    inputs: torch.Tensor | list[torch.Tensor],
    prediction_length: int | None = None,
    quantile_levels: list[float] = [0.1, 0.2, ..., 0.9],
    **predict_kwargs,
) -> tuple[torch.Tensor, torch.Tensor]
```

Returns:

```text
quantiles: (batch_size, prediction_length, len(quantile_levels))
mean:      (batch_size, prediction_length)
```

Bolt-specific interpretation:

- If requested `quantile_levels` are exactly among `pipeline.quantiles`, the pipeline selects those channels directly.
- Otherwise it interpolates across the trained quantile channels; for official models this assumes the trained grid is evenly spaced at `0.1, ..., 0.9`.
- If requested levels are outside the trained range, the pipeline warns and effectively uses the minimum/maximum trained channels at the extremes.
- The returned `mean` is the model's median channel (`0.5`), not an arithmetic mean over samples. Code consuming Bolt forecasts should call it a point forecast or median-like point forecast when precision matters.
- Extra `predict_kwargs`, such as `limit_prediction_length`, are forwarded to `predict`.

### `embed`

```python
ChronosBoltPipeline.embed(
    context: torch.Tensor | list[torch.Tensor]
) -> tuple[torch.Tensor, tuple[torch.Tensor, torch.Tensor]]
```

Returns:

```text
embeddings: (batch_size, num_patch_windows [+ optional REG token], d_model)
loc_scale:  (loc, scale), each shaped (batch_size,)
```

The context is truncated to the model context length, converted to `float32` on the model device, patch-embedded, and returned to CPU. Embeddings keep the model dtype; `loc` and `scale` are returned as `float32`.

## Original `ChronosPipeline`

### Properties

```python
pipeline.forecast_type == ForecastType.SAMPLES
pipeline.model_context_length      # from model.config.context_length
pipeline.model_prediction_length   # from model.config.prediction_length
```

### `predict`

```python
ChronosPipeline.predict(
    inputs: torch.Tensor | list[torch.Tensor],
    prediction_length: int | None = None,
    num_samples: int | None = None,
    temperature: float | None = None,
    top_k: int | None = None,
    top_p: float | None = None,
    limit_prediction_length: bool = False,
) -> torch.Tensor
```

Returns sample trajectories shaped:

```text
(batch_size, num_samples, prediction_length)
```

Sampling parameters default to the model config when omitted. Use them only on original Chronos; Bolt does not accept `num_samples`, `temperature`, `top_k`, or `top_p`.

Prediction-length behavior:

- `prediction_length=None` uses the model's configured prediction length.
- Longer requests warn, or raise `ValueError` when `limit_prediction_length=True`.
- Longer forecasts are unrolled block by block. Between blocks, the pipeline appends the median of current sample trajectories to the context.

Context behavior:

- The tokenizer truncates long contexts to the last `model_context_length` observations.
- Missing or padded values are represented with `torch.nan` in the attention mask.

### `predict_quantiles`

```python
ChronosPipeline.predict_quantiles(
    inputs: torch.Tensor | list[torch.Tensor],
    prediction_length: int | None = None,
    quantile_levels: list[float] = [0.1, 0.2, ..., 0.9],
    **predict_kwargs,
) -> tuple[torch.Tensor, torch.Tensor]
```

Returns:

```text
quantiles: (batch_size, prediction_length, len(quantile_levels))
mean:      (batch_size, prediction_length)
```

Original Chronos computes these from sampled paths:

- it calls `predict(...)` to obtain `(batch, samples, horizon)`;
- swaps to `(batch, horizon, samples)`;
- uses `torch.quantile(..., dim=-1)` for requested quantiles;
- uses arithmetic mean across sample trajectories for `mean`.

Forward original-only sampling kwargs through `predict_quantiles`, for example `num_samples=100` or `temperature=0.7`.

### `embed`

```python
ChronosPipeline.embed(
    context: torch.Tensor | list[torch.Tensor]
) -> tuple[torch.Tensor, object]
```

Returns:

```text
embeddings:      (batch_size, token_context_length [+ EOS for seq2seq], d_model)
tokenizer_state: usually scale shaped (batch_size,)
```

Embeddings are supported for encoder-decoder original Chronos models. The official `chronos-t5-*` models are encoder-decoder. A causal original Chronos model can raise an assertion because encoder embeddings require a seq2seq model.

## Shared `predict_df`

Both Bolt and original Chronos inherit the same univariate DataFrame adapter:

```python
pipeline.predict_df(
    df: pandas.DataFrame,
    *,
    id_column: str = "item_id",
    timestamp_column: str = "timestamp",
    target: str = "target",
    prediction_length: int | None = None,
    quantile_levels: list[float] = [0.1, 0.2, ..., 0.9],
    batch_size: int = 256,
    validate_inputs: bool = True,
    freq: str | None = None,
    **predict_kwargs,
) -> pandas.DataFrame
```

Contract:

- `target` must be a single string column name; these base pipelines do not forecast multiple target columns together.
- Non-target columns other than ID and timestamp are ignored by these pipelines.
- With `validate_inputs=True`, rows are normalized and checked for regular timestamps and common frequency.
- `prediction_length=None` uses `model_prediction_length`.
- Forecasting is batched across series according to `batch_size`.
- Internally the adapter calls `predict_quantiles(..., limit_prediction_length=False, **predict_kwargs)`, so DataFrame forecasts can exceed the model default horizon. Do not pass another `limit_prediction_length` through `predict_df`; use the tensor/list API first if the user needs a hard prediction-length guard.

Returned columns:

```text
id_column
timestamp_column
target_name
predictions
str(q) for each quantile level q
```

Rows are in long format: one row per item and forecast timestamp. For DataFrame schema validation, irregular timestamps, custom columns, or known future covariates, route to `../data-formats-and-validation/` or `../chronos-2-forecasting/` as appropriate.

## Shared `predict_fev`

```python
pipeline.predict_fev(task: fev.Task, batch_size: int = 32, **kwargs) -> tuple[list[datasets.DatasetDict], float]
```

Behavior:

- Requires `fev` and `datasets` at runtime.
- Converts each evaluation window to a univariate DataFrame input, splits multivariate targets into independent univariate series, and ignores covariates.
- Calls `predict_df(...)` and returns `(predictions_per_window, inference_time_s)`.
- For point forecast metrics `MSE`, `RMSE`, and `RMSSE`, the `predictions` column uses the adapter's point forecast. For other metrics, the bridge requests the median when needed and uses the `0.5` quantile as the point forecast.

Use `../training-evaluation-deployment/` when the task is about benchmark script orchestration, aggregate score files, or full benchmark reproduction.

## Quantile helper utilities

`chronos.utils.left_pad_and_stack_1D` pads lists of 1D tensors on the left with `torch.nan` before stacking.

`chronos.utils.interpolate_quantiles` and `weighted_quantile` provide lower-level interpolation helpers. They require floating point tensors, 1D quantile/query levels in `[0, 1]`, and compatible last dimensions. They are useful for interpreting how quantiles are constructed but are not usually needed for normal pipeline use.
