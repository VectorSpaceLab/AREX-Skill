---
name: chronos-bolt-and-original
description: "Use Chronos-Bolt and original Chronos/T5 pipelines for univariate
  forecasting, quantiles, samples, DataFrames, embeddings, fev, and model-family
  selection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Chronos-Bolt and original Chronos/T5

Use this sub-skill when the task is about the **Chronos-Bolt** or **original Chronos/T5** families from the `chronos-forecasting` package:

- load a Bolt or original Chronos model from a Hugging Face model ID, an S3 URI, or a local directory;
- choose between Bolt direct quantile forecasts and original Chronos sample-path forecasts;
- run tensor/list forecasts with `predict` or `predict_quantiles`;
- run univariate long-format pandas forecasts with `predict_df`;
- obtain encoder embeddings with `embed`;
- use the base `predict_fev` bridge for fev tasks;
- handle prediction-length, dtype/device, cache, and shape issues.

## Route first

- For **Chronos-2**, multivariate targets, covariates, `future_df`, `cross_learning`, Chronos-2 fine-tuning, or Chronos-2 deployment choices, route to `../chronos-2-forecasting/`.
- For detailed pandas schema/frequency/covariate validation, route to `../data-formats-and-validation/`.
- For training, benchmark evaluation scripts, aggregate scores, or SageMaker/cloud operations, route to `../training-evaluation-deployment/`.

## Load these references

1. `references/api-reference.md` — exact public signatures, tensor shapes, forecast-type differences, loading behavior, and family properties.
2. `references/workflows.md` — practical loading, tensor/list prediction, quantile/mean, DataFrame, embeddings, fev, and model-selection recipes.
3. `references/troubleshooting.md` — shape, padding/NaN, sample-vs-quantile, prediction-length, S3/HF cache, dtype/device, and dependency fixes.

## Bundled safe script

- `scripts/bolt_original_smoke.py` defaults to import/signature inspection when no model is provided.
- It only loads a model when `--model-id-or-path` is supplied; non-local Hugging Face or S3 identifiers additionally require `--allow-remote`.
- Use it to validate that an installed package can import the public APIs and, with an explicit user model, run a tiny tensor forecast.

## Minimal selection rule

- Prefer **Chronos-Bolt** for fast univariate probabilistic forecasts where direct quantile output is desired.
- Prefer **original Chronos/T5** when the user explicitly needs sample trajectories, sampling controls (`num_samples`, `temperature`, `top_k`, `top_p`), or compatibility with original Chronos behavior.
- Prefer **Chronos-2** instead of this sub-skill for covariates, multivariate forecasting, or the latest model family.
