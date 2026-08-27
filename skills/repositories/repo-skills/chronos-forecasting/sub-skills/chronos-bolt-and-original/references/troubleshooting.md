# Chronos-Bolt and original Chronos troubleshooting

This page covers common failures for `ChronosBoltPipeline` and original `ChronosPipeline`. For Chronos-2 covariate/multivariate issues, route to `../chronos-2-forecasting/`. For detailed DataFrame schema/frequency validation, route to `../data-formats-and-validation/`.

## Shape and input-rank errors

Symptoms:

- `AssertionError` from context preparation;
- confusing output batch size;
- a 3D tensor is rejected;
- a list input fails unexpectedly.

Fix:

- Use a 1D tensor for one univariate series: `(context_length,)`.
- Use a 2D tensor for a univariate batch: `(batch_size, context_length)`.
- Use a list of 1D tensors for ragged univariate batches.
- Do not pass multivariate arrays shaped `(batch, variables, time)` or dictionaries to Bolt/original Chronos. Route these to `../chronos-2-forecasting/`.

Examples:

```python
# OK: one series
context = torch.tensor([1.0, 2.0, 3.0])

# OK: two same-length univariate series
context = torch.tensor([[1.0, 2.0, 3.0], [10.0, 11.0, 12.0]])

# OK: ragged univariate batch
context = [torch.tensor([1.0, 2.0]), torch.tensor([10.0, 11.0, 12.0])]

# Not OK for this sub-skill: multivariate/covariate tensor
context = torch.zeros(2, 4, 64)
```

## NaN, padding, and missing values

Symptoms:

- missing values treated as real zeros;
- forecasts change unexpectedly after manual padding;
- batch outputs look misaligned.

Fix:

- Use `torch.nan` for missing values and left-padding.
- Let the list-input path do padding when series lengths differ.
- Do not right-pad shorter series; the most recent observations must align at the right edge.
- Avoid all-NaN histories. The code has scale fallbacks for numerical stability, but an all-missing series is not a meaningful forecasting context.

Why:

- `left_pad_and_stack_1D` pads with `torch.nan`.
- Original Chronos tokenization masks NaNs and computes scale from observed values.
- Bolt instance normalization ignores NaNs and the patcher left-pads to patch boundaries with NaNs.

## Sample-vs-quantile confusion

Symptoms:

- user expects `(batch, samples, horizon)` from Bolt but receives `(batch, quantiles, horizon)`;
- user expects quantile columns from original `predict` but receives sample paths;
- code averages Bolt quantile channels as if they were samples.

Fix:

- Bolt `predict(...)` returns direct quantile channels shaped `(batch, len(pipeline.quantiles), horizon)`.
- Original `predict(...)` returns sample trajectories shaped `(batch, num_samples, horizon)`.
- For a consistent quantile/point interface across both families, call `predict_quantiles(...)`.
- For Bolt, the returned `mean` from `predict_quantiles` is the `0.5` quantile channel, not an arithmetic mean.
- For original Chronos, the returned `mean` is the arithmetic mean over sample trajectories.

## Prediction-length limits

Symptoms:

- `ValueError` mentioning recommended prediction length;
- warning about quality degrading for long horizons;
- memory growth on long Bolt forecasts.

Fix:

- Inspect `pipeline.model_prediction_length`.
- If the user wants a hard limit, call with `limit_prediction_length=True` and keep `prediction_length <= pipeline.model_prediction_length`.
- If the user accepts quality risk, keep the default `limit_prediction_length=False` and document that long horizons are recursively unrolled.
- For `predict_df`, remember the shared adapter always supplies `limit_prediction_length=False` internally; do not pass another `limit_prediction_length` through `predict_df`. Use the tensor/list API when a hard horizon guard is required.

Family-specific notes:

- Bolt long horizons expand context across trained quantiles after the first block, then reduce back to the quantile grid. This can increase memory use roughly with the number of training quantiles.
- Original Chronos long horizons append median sample paths between generated blocks.

## Quantile-level issues

Symptoms:

- warning that requested Bolt quantiles are outside the trained range;
- invalid quantile-level errors;
- unexpected point forecast for Bolt.

Fix:

- Keep quantile levels in `[0, 1]`.
- For official Bolt models, prefer levels from `[0.1, 0.2, ..., 0.9]` or common subsets such as `[0.1, 0.5, 0.9]`.
- Bolt can interpolate untrained levels, but values outside the trained range are effectively clamped to the extreme trained levels and should be treated cautiously.
- Original Chronos estimates requested quantiles from sample trajectories; increase `num_samples` when quantile estimates are too noisy.

## DataFrame errors

Symptoms:

- `ValueError` saying the target column is missing;
- `Expected target to be str`;
- errors about not inferring frequency or inconsistent frequencies;
- user wants `future_df`, covariates, or multiple target columns.

Fix:

- For Bolt/original `predict_df`, pass one target column name as a string.
- Ensure the DataFrame has ID, timestamp, and target columns.
- With `validate_inputs=True`, ensure every item has regular timestamps and a common frequency.
- If the data is already validated and sorted, `validate_inputs=False` can skip validation overhead, but wrong ordering or frequency will silently produce wrong forecasts.
- For detailed repairs, route to `../data-formats-and-validation/`.
- For `future_df`, covariates, or multi-target forecasts, route to `../chronos-2-forecasting/`.

## S3 loading and `boto3`

Symptoms:

- `ImportError` when loading `s3://...` model URI;
- stale S3-cached model contents;
- unexpected cloud/network access.

Fix:

- Install optional dependencies that include `boto3`, or install `boto3` directly.
- Load S3 models through `BaseChronosPipeline.from_pretrained("s3://...", ...)` or a family class that delegates to the base loader.
- Use `force_s3_download=True` when the user explicitly wants to refresh a cached S3 model.
- Do not attempt S3 loading without user approval for cloud/network access and credentials.

## Hugging Face cache and network issues

Symptoms:

- model load hangs or fails because weights are not cached;
- authentication or gated-model errors;
- accidental download in an offline workflow.

Fix:

- Prefer local model directories when network access is not allowed.
- Configure Transformers/Hugging Face cache and offline mode according to the execution environment before loading.
- Treat a remote model ID such as `amazon/chronos-bolt-tiny` or `amazon/chronos-t5-tiny` as a network/download operation unless the model is already cached.
- The bundled smoke script refuses non-local model IDs unless `--allow-remote` is passed.

## dtype and device mistakes

Symptoms:

- model unexpectedly runs on CPU;
- CUDA unavailable despite GPU hardware;
- dtype keyword warning across Transformers versions;
- downstream code expects GPU outputs but receives CPU tensors.

Fix:

- Use `device_map="cpu"` for safe CPU execution.
- Use `device_map="cuda"` or a Transformers device map only when the runtime has a compatible Torch/CUDA installation.
- Use `torch_dtype="float32"` for maximum compatibility; use `"bfloat16"` only when the model and hardware support it.
- The base loader handles both `torch_dtype` and newer `dtype` keyword forms.
- Forecast outputs are intentionally returned on CPU as `torch.float32`; move them manually if downstream code requires another device.

## Family mismatch after loading

Symptoms:

- a supposedly Bolt model returns sample forecasts;
- a supposedly original model returns quantiles;
- direct class loading fails with a config assertion.

Fix:

- Inspect the loaded class and forecast type:

```python
print(type(pipeline).__name__)
print(pipeline.forecast_type)
```

- Use `BaseChronosPipeline.from_pretrained` to auto-route based on config.
- Use `ChronosBoltPipeline.from_pretrained` or `ChronosPipeline.from_pretrained` only when the family is known and a mismatch should fail.

## Optional dependency issues for fev

Symptoms:

- `ImportError: fev is required for predict_fev`;
- benchmark task downloads data unexpectedly;
- covariates are ignored in fev output.

Fix:

- Install optional evaluation dependencies before calling `predict_fev`.
- Ensure the fev task dataset is already available or explicitly allow dataset download.
- Remember the shared Bolt/original fev bridge is univariate: multivariate targets are split and covariates are ignored.
- Route full benchmark orchestration and aggregate scoring to `../training-evaluation-deployment/`.
