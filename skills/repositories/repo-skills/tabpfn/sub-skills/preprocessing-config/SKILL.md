---
name: preprocessing-config
description: "Guides TabPFN input validation, feature-modality detection,
  DataFrame cleanup, and inference/preprocessing configuration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# TabPFN preprocessing and configuration

Use this sub-skill when the user is asking about what shapes, dtypes,
feature types, missing values, or configuration fields TabPFN accepts before
fitting or predicting.

## Start here

- Read `references/data-validation.md` for shape checks, DataFrame cleanup, text and categorical handling, and infinity behavior.
- Read `references/inference-config.md` for `InferenceConfig`, `PreprocessorConfig`, and the settings fields that control preprocessing.
- Read `references/troubleshooting.md` for the most common validation failures and recovery steps.
- Run `scripts/inspect_inference_config.py --help` to inspect the installed defaults without downloading model weights.

## Use this sub-skill when

- The task is about DataFrame columns, nullable dtypes, categorical indices, text-like columns, or missing values.
- The user wants to know whether `NaN`, `inf`, or string columns are allowed.
- The user asks about `InferenceConfig`, `PreprocessorConfig`, or env vars such as `TABPFN_ALLOW_CPU_LARGE_DATASET` or `TABPFN_MPS_MEMORY_FRACTION`.
- The user needs to understand which feature columns are treated as categorical or numerical.
- The user wants to know why a validation error is raised before fit/predict begins.

## Route elsewhere

- Ordinary estimator usage, logits, quantiles, or embeddings: `../tabular-prediction/SKILL.md`.
- Multi-dataset batched scoring or cache/performance tuning: `../batched-performance/SKILL.md`.
- Tuning, differentiable input, and fine-tuning: `../tuning-and-advanced/SKILL.md`.
- Model downloads, auth, cache, persistence, or checkpoint conversion: `../model-management/SKILL.md`.

## What this route owns

- Input validation before `fit` and `predict`.
- Detection of numerical, categorical, text, and constant features.
- Cleanup of mixed pandas / NumPy inputs.
- Explicit configuration of preprocessing and inference defaults.
- CPU-size and MPS memory guardrails.

## What to remember

- TabPFN can handle mixed tabular data, but not every string column is a good feature.
- Free text is usually ordinal-encoded as a noisy high-cardinality categorical feature.
- `PASSTHROUGH_INF=True` changes whether infinities are rejected or temporarily preserved.
- `ignore_pretraining_limits=True` overrides model size guardrails, but it does not make a huge CPU dataset fast.
