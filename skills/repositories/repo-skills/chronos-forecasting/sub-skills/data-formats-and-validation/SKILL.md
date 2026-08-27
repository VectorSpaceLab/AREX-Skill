---
name: data-formats-and-validation
description: "Validate and prepare Chronos long-format data, covariates,
  timestamps, and preprocessing inputs before forecasting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Data Formats and Validation

Use this sub-skill when the task is about preparing Chronos inputs, checking
DataFrame schemas, or debugging preprocessing before forecasting.

## Covers
- Long-format pandas DataFrames for `Chronos2Pipeline.predict_df`
- `chronos.df_utils` normalization, validation, and future-timestamp generation
- `chronos.chronos2.preprocess` helpers for tensors, list-of-tensors,
  DataFrames, and list-of-dicts
- Target and covariate alignment, timestamp frequency rules, categorical
  covariates, and `validate_inputs=False` hazards

## Route elsewhere
- Model loading, forecasting, embeddings, or output interpretation:
  `../chronos-2-forecasting/` or `../chronos-bolt-and-original/`
- Fine-tuning, evaluation, benchmark configs, or deployment:
  `../training-evaluation-deployment/`

## Read first
1. `references/data-formats.md`
2. `references/preprocessing-api-reference.md`
3. `references/troubleshooting.md`
4. `scripts/validate_chronos_dataframe.py --help`

## Runtime files
- `references/data-formats.md`
- `references/preprocessing-api-reference.md`
- `references/troubleshooting.md`
- `scripts/validate_chronos_dataframe.py`

## Use this sub-skill to answer
- Which columns Chronos expects in `df` and `future_df`
- How `future_df` is matched to context rows
- Which helper to use for DataFrame, list-of-dicts, or tensor inputs
- How Chronos handles categorical covariates and known-future values
- What breaks when validation is skipped
