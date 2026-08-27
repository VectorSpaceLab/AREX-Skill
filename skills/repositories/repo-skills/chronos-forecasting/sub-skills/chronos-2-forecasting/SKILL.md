---
name: chronos-2-forecasting
description: "Use Chronos2Pipeline for Chronos-2 zero-shot, covariate-aware,
  multivariate, and fine-tuned forecasting workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Chronos-2 forecasting router

Use this sub-skill when the task is to run or reason about `Chronos2Pipeline` inference or model loading for Chronos-2: zero-shot forecasts, saved or fine-tuned Chronos-2 checkpoints, tensor/list/list-of-dicts inputs, multivariate targets, covariates, `predict`, `predict_quantiles`, `predict_df`, `predict_fev`, `embed`, long-horizon unrolling, and model-selection tradeoffs.

## Start here

- API signatures, parameters, return shapes, model properties, and loading behavior: [references/api-reference.md](references/api-reference.md)
- Task recipes for model loading, tensor/list/list-dict inputs, DataFrame covariates, long horizons, embeddings, fev bridge, and save/load: [references/workflows.md](references/workflows.md)
- Symptoms and recovery for schema, covariate, future horizon, frequency, cache/download, and device/dtype issues: [references/troubleshooting.md](references/troubleshooting.md)
- Safe helper script with no default model download: [scripts/chronos2_smoke_forecast.py](scripts/chronos2_smoke_forecast.py)

## Route out of this sub-skill

- Detailed DataFrame, future covariate, categorical, timestamp, and preprocessing validation rules belong in [data-formats-and-validation](../data-formats-and-validation/).
- Chronos-Bolt and original Chronos/T5 pipelines belong in [chronos-bolt-and-original](../chronos-bolt-and-original/).
- Full fine-tuning, evaluation benchmarks, aggregate scoring, and deployment operations belong in [training-evaluation-deployment](../training-evaluation-deployment/).

## Operating guardrails

- Prefer `BaseChronosPipeline.from_pretrained(...)` for general loading and confirm that the returned object is `Chronos2Pipeline` before using Chronos-2-specific covariate or multivariate behavior.
- Do not trigger Hugging Face, S3, benchmark, or cloud downloads unless the user explicitly provides a model/dataset/URI and asks to load or evaluate it.
- Keep `prediction_length`, `context_length`, `batch_size`, `device_map`, and dtype explicit in reproducible snippets; inspect loaded model properties instead of hard-coding model limits.
- Use sibling validation guidance before disabling `validate_inputs` or building heterogeneous list-of-dicts inputs.
