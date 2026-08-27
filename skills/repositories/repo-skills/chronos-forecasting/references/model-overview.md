# Chronos model overview

Use this reference to choose the right Chronos family before opening a focused sub-skill.

## Public model families

| Family | Pipeline | Forecast type | Best fit | Key limitations |
| --- | --- | --- | --- | --- |
| Chronos-2 | `Chronos2Pipeline` | Quantiles | Current default for zero-shot univariate, multivariate, and covariate-informed forecasting; supports fine-tuning via `fit`. | Model download may be required; full training/evaluation can need GPU and optional dependencies. |
| Chronos-Bolt | `ChronosBoltPipeline` | Quantiles | Fast direct multi-step probabilistic forecasts for univariate tensor/list/DataFrame tasks; strong speed/memory option. | Does not expose Chronos-2 native multivariate/covariate dictionary API. |
| Original Chronos/T5 | `ChronosPipeline` | Samples | Sampling-based probabilistic forecasts and compatibility with original Chronos models/paper workflows. | Samples need post-processing for quantiles/means; no native covariate API. |

Use `BaseChronosPipeline.from_pretrained(...)` when the model anchor may be any Chronos family; it dispatches from the loaded config. After loading, inspect `type(pipeline).__name__` and `pipeline.forecast_type` before choosing workflow-specific methods.

## Model IDs from package documentation

Chronos-2:

- `amazon/chronos-2`
- `autogluon/chronos-2-synth`
- `autogluon/chronos-2-small`

Chronos-Bolt:

- `amazon/chronos-bolt-tiny`
- `amazon/chronos-bolt-mini`
- `amazon/chronos-bolt-small`
- `amazon/chronos-bolt-base`

Original Chronos/T5:

- `amazon/chronos-t5-tiny`
- `amazon/chronos-t5-mini`
- `amazon/chronos-t5-small`
- `amazon/chronos-t5-base`
- `amazon/chronos-t5-large`

Do not hard-code model limits from the list. Inspect the loaded pipeline's model properties such as `model_context_length`, `model_prediction_length`, `quantiles`, and family-specific attributes.

## Output interpretation

- Chronos-2 `predict` returns a list of quantile tensors shaped `(n_variates, n_model_quantiles, horizon)`; `predict_quantiles` returns selected quantiles and a median-style point forecast.
- Chronos-Bolt `predict` returns a tensor shaped `(batch, n_model_quantiles, horizon)`; `predict_quantiles` transposes/interpolates selected levels and returns a median-style point forecast.
- Original Chronos `predict` returns sample trajectories shaped `(batch, num_samples, horizon)`; `predict_quantiles` computes quantiles and sample mean.
- DataFrame outputs standardize on `predictions` plus string quantile columns where supported.

## Backend and dependency expectations

- Base installation requires Python >=3.10 plus PyTorch, Transformers, Accelerate, NumPy, pandas, and einops.
- `boto3` is needed for `s3://` loading.
- `peft` is needed for LoRA adapters/fine-tuning.
- `fev` and `datasets` are needed for benchmark bridge workflows.
- `pandas[pyarrow]` or pyarrow is needed for parquet examples.
- CUDA is optional for selected API correctness but usually important for large-model latency and training.

## Routing summary

- For Chronos-2 forecasting, read `sub-skills/chronos-2-forecasting/`.
- For DataFrame/covariate validation, read `sub-skills/data-formats-and-validation/`.
- For Bolt/original models, read `sub-skills/chronos-bolt-and-original/`.
- For fine-tuning, evaluation, KernelSynth, aggregate scores, or deployment, read `sub-skills/training-evaluation-deployment/`.
