# Chronos-2 API reference

This reference covers the Chronos-2 pipeline only. Use [../../data-formats-and-validation/](../../data-formats-and-validation/) for detailed data validation and preprocessing, [../../chronos-bolt-and-original/](../../chronos-bolt-and-original/) for other model families, and [../../training-evaluation-deployment/](../../training-evaluation-deployment/) for full training/evaluation/deployment operations.

## Imports and model family

```python
from chronos import BaseChronosPipeline, Chronos2Pipeline
```

Chronos-2 public model IDs listed by the package documentation:

| Model ID | Parameters | Typical use implication |
|---|---:|---|
| `amazon/chronos-2` | 120M | Default full Chronos-2 model when the user can load the checkpoint. |
| `autogluon/chronos-2-synth` | 120M | Chronos-2 variant; verify on the user's task before treating it as a drop-in accuracy win. |
| `autogluon/chronos-2-small` | 28M | Lower-resource Chronos-2 option; benchmark quality on the target data. |

Chronos-2 supports univariate, multivariate, cross-learning, past-only covariates, known-future real/categorical covariates, and fine-tuning. Chronos-Bolt/original Chronos do not expose the same native covariate/multivariate Chronos-2 API.

## Loading and saving

Verified public signatures:

```python
BaseChronosPipeline.from_pretrained(
    pretrained_model_name_or_path,
    *model_args,
    force_s3_download=False,
    **kwargs,
)

Chronos2Pipeline.from_pretrained(pretrained_model_name_or_path, *args, **kwargs)

pipeline.save_pretrained(save_directory, *args, **kwargs)
```

Operational notes:

- Prefer `BaseChronosPipeline.from_pretrained(...)` for generic loading; it dispatches to the pipeline class declared by the loaded config. Confirm `isinstance(pipeline, Chronos2Pipeline)` before using Chronos-2-specific features.
- Accepted model anchors include local checkpoint directories, Hugging Face model IDs, and `s3://...` prefixes. Hugging Face and S3 anchors may download/cache data; do this only when the user explicitly asks or supplies the anchor for loading.
- Common loading kwargs are forwarded to Hugging Face Transformers, for example `device_map="cpu"`, `device_map="cuda"`, `device_map="auto"`, `torch_dtype="bfloat16"`, `torch_dtype="float32"`, or `dtype=...` depending on Transformers version.
- S3 loading uses `force_s3_download` on `BaseChronosPipeline.from_pretrained`. S3 model loading requires the optional S3 dependency.
- `Chronos2Pipeline.from_pretrained` detects PEFT/LoRA adapter checkpoints when adapter metadata is present. It requires `peft`, loads the adapter model, merges it, and returns a `Chronos2Pipeline`. S3 LoRA adapters are not the supported path; load LoRA adapters from local/HF-style adapter directories.
- `save_pretrained(...)` delegates to the underlying model and can save a local directory or use Hugging Face `save_pretrained` kwargs such as hub push options when explicitly configured by the user.

## Model properties to inspect after loading

```python
pipeline.forecast_type              # ForecastType.QUANTILES for Chronos-2
pipeline.model_context_length       # maximum model context accepted by this checkpoint
pipeline.model_output_patch_size    # time steps per output patch
pipeline.model_prediction_length    # max_output_patches * output_patch_size
pipeline.quantiles                  # quantile levels the model was trained to emit
pipeline.max_output_patches         # default output patches per forward pass
```

Do not hard-code context or horizon limits. Public Chronos-2 examples describe an 8192 maximum context for Chronos-2, while the exact loaded checkpoint exposes the authoritative value through `pipeline.model_context_length`.

## `predict`: raw model quantiles

Verified signature:

```python
Chronos2Pipeline.predict(
    inputs,
    prediction_length: int | None = None,
    batch_size: int = 256,
    context_length: int | None = None,
    cross_learning: bool = False,
    limit_prediction_length: bool = False,
    **kwargs,
) -> list[torch.Tensor]
```

Accepted input families:

1. `torch.Tensor` or `np.ndarray` with shape `(batch, n_variates, history_length)`. All variates are forecast targets. If `n_variates > 1`, Chronos-2 performs multivariate forecasting within each batch item.
2. List of 1-D or 2-D tensors/arrays. Each element is `(history_length,)` for univariate or `(n_variates, history_length)` for multivariate; elements may have different history lengths.
3. List of dictionaries. Each dictionary has `target` plus optional `past_covariates` and `future_covariates` dictionaries. `target` is 1-D or 2-D; each past covariate is 1-D with history length; each future covariate is 1-D with `prediction_length`. Future covariate keys must be a subset of past covariate keys. All dictionaries in one call must share the same target variate count and covariate key schema.
4. Prepared inputs from `chronos.chronos2.preprocess` helpers. Route detailed preparation to [../../data-formats-and-validation/](../../data-formats-and-validation/).

Return shape:

- Returns a list with one tensor per input task/series.
- Each tensor has shape `(n_variates, n_model_quantiles, prediction_length)`.
- Output tensors are `torch.float32` on CPU.
- The quantile axis follows `pipeline.quantiles`.

Key parameters:

- `prediction_length=None` uses `pipeline.model_prediction_length`.
- `context_length=None` uses `pipeline.model_context_length`; values above the model limit are reset to the model limit with a warning.
- `batch_size` counts target and covariate series consumed by the model, not just item IDs. Multivariate targets and covariates reduce the number of items that fit in a batch.
- `cross_learning=True` assigns tasks in a batch to one shared group so the model can share information across related series. It is task-dependent, batch-size-dependent, and usually most useful for homogeneous related series with short context.
- `limit_prediction_length=True` raises when the requested horizon exceeds `pipeline.model_prediction_length`. The default is `False`, which warns and uses long-horizon unrolling.

Supported `**kwargs` observed in the implementation:

- `max_output_patches`: cap output patches per forward pass before long-horizon unrolling.
- `unrolled_quantiles`: quantile levels used when unrolling horizons beyond the model default; must be a subset of `pipeline.quantiles`.
- `after_batch`: callback called after each batch. This is useful for timeouts or progress control.
- Deprecated: `predict_batches_jointly` maps to `cross_learning` and emits a future-warning.

## `predict_quantiles`: selected quantiles plus point forecast

Verified signature:

```python
Chronos2Pipeline.predict_quantiles(
    inputs,
    prediction_length: int | None = None,
    quantile_levels: list[float] = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
    **predict_kwargs,
) -> tuple[list[torch.Tensor], list[torch.Tensor]]
```

Return shape:

- `quantiles`: list of tensors, each `(n_variates, prediction_length, len(quantile_levels))`.
- `mean`: list of tensors, each `(n_variates, prediction_length)`.

Important interpretation:

- The implementation obtains model quantiles via `predict`, transposes axes, and selects/interpolates requested `quantile_levels`.
- If requested levels are outside the model-trained quantile range, they are clipped/interpolated at the available limits and quality may degrade.
- The return variable is named `mean`, but Chronos-2 currently uses the model's `0.5` training quantile for this point forecast. Treat it as the median-style point forecast unless you have separately computed an expectation.

## `predict_df`: long-format DataFrame forecasts with covariates

Verified signature:

```python
Chronos2Pipeline.predict_df(
    df,
    future_df=None,
    id_column="item_id",
    timestamp_column="timestamp",
    target="target",
    prediction_length=None,
    quantile_levels=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
    batch_size=256,
    context_length=None,
    cross_learning=False,
    validate_inputs=True,
    freq=None,
    **predict_kwargs,
) -> pandas.DataFrame
```

Input meaning:

- `df` is long format with one row per item/timestamp and at least `id_column`, `timestamp_column`, and target column(s).
- `target` may be a string or list of strings. Multiple target columns produce multivariate forecasts and output rows per `(item, target, step)`.
- Columns in `df` other than id/timestamp/targets are covariates. If a covariate is also present in `future_df`, it is treated as known future. Otherwise it is past-only.
- `future_df`, when present, contains id/timestamp and known-future covariate columns for exactly the forecast horizon per item. It must not contain target columns.
- `freq` supplies the timestamp frequency for generating forecast timestamps and bypasses inference; it is used as provided.

Output columns:

- `id_column`
- `timestamp_column`
- `target_name`
- `predictions`
- One string-named column per requested quantile level, such as `"0.1"`, `"0.5"`, `"0.9"`

Shape rule:

```text
rows = number_of_items * number_of_target_columns * prediction_length
```

`predict_df` internally calls `predict_quantiles(..., limit_prediction_length=False)`, so long horizons warn rather than fail. Use explicit horizon checks in your own code if the task requires rejecting horizons beyond the loaded model default.

## `embed`: encoder embeddings

Verified signature:

```python
Chronos2Pipeline.embed(
    inputs,
    batch_size: int = 256,
    context_length: int | None = None,
) -> tuple[list[torch.Tensor], list[tuple[torch.Tensor, torch.Tensor]]]
```

Input forms are tensors/arrays or lists of tensors/arrays, not raw covariate dictionaries. Return values:

- `embeddings`: list of tensors, each `(n_variates, num_patches + 2, d_model)`. The extra `+2` corresponds to the registration token and masked output patch token.
- `loc_scale`: list of `(loc, scale)` tensors, each with shape `(n_variates, 1)`.

Use embeddings for representation analysis or downstream modeling, not as forecast rows. Keep model/device constraints the same as forecasting.

## `predict_fev`: fev benchmark bridge

Verified signature:

```python
Chronos2Pipeline.predict_fev(
    task,
    batch_size: int = 256,
    as_univariate: bool = False,
    finetune_kwargs: dict | None = None,
    **kwargs,
) -> tuple[list[datasets.DatasetDict], float]
```

- Requires the optional `fev` dependency.
- Converts each fev evaluation window to DataFrames, calls `predict_df`, and converts forecast rows back to fev predictions.
- `as_univariate=True` splits targets and ignores covariates.
- If `finetune_kwargs` is supplied, the pipeline fine-tunes on the first window before evaluation. Route full use to [../../training-evaluation-deployment/](../../training-evaluation-deployment/).

## `fit`: high-level fine-tuning signature

Verified signature:

```python
Chronos2Pipeline.fit(
    inputs,
    prediction_length: int,
    validation_inputs=None,
    finetune_mode="full",
    lora_config=None,
    context_length=None,
    learning_rate=1e-6,
    num_steps=1000,
    batch_size=256,
    output_dir=None,
    min_past=None,
    finetuned_ckpt_name="finetuned-ckpt",
    callbacks=None,
    remove_printer_callback=False,
    disable_data_parallel=True,
    **extra_trainer_kwargs,
) -> Chronos2Pipeline
```

This API fine-tunes a copy of the current model and returns a new pipeline; it should not mutate the original pipeline. `finetune_mode="lora"` requires `peft` and uses a default LoRA configuration if none is supplied. Treat full fine-tuning, LoRA training recipes, validation, checkpoint naming, and trainer kwargs as training operations and route details to [../../training-evaluation-deployment/](../../training-evaluation-deployment/).
