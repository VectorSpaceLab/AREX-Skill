---
name: batched-performance
description: "Guides TabPFN batched multi-dataset inference, cache placement,
  and performance tradeoffs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# TabPFN batched performance

Use this sub-skill when the user wants to score many datasets in one call or
needs to understand how TabPFN trades memory for speed.

## Start here

- Read `references/batched-workflows.md` for `predict_proba_batched` and `predict_batched` semantics.
- Read `references/memory-and-performance.md` for `fit_mode`, cache behavior, and chunking guidance.
- Read `references/troubleshooting.md` for ragged batches, float64, and unsupported option failures.
- Run `scripts/batched_prediction_smoke.py --help` when you have a local checkpoint and want a source-free batch smoke check.

## Use this sub-skill when

- The task mentions cross-validation folds, repeated train/test splits, or a list of datasets.
- The user asks how to reduce repeated preprocessing or repeated inference cost.
- The user wants to understand `fit_mode`, `fit_with_cache`, `keep_cache_on_device`, or `kv_cache_precision`.
- The user is comparing memory use vs latency for one checkpoint on many datasets.

## Route elsewhere

- One dataset, logits, quantiles, embeddings, or estimator basics: `../tabular-prediction/SKILL.md`.
- Input cleaning, categorical detection, NaNs, infinities, or config fields: `../preprocessing-config/SKILL.md`.
- `eval_metric`, tuning, differentiable input, or fine-tuning: `../tuning-and-advanced/SKILL.md`.
- Model download, auth, persistence, or checkpoint conversion: `../model-management/SKILL.md`.

## What this route owns

- `predict_proba_batched` for classifiers.
- `predict_batched` for regressors.
- The shape and class-set constraints that come from fused batched scoring.
- Memory and cache tradeoffs for repeated fits and repeated prediction calls.

## What to remember

- Batched inference is only worth it when multiple datasets share the same shape family.
- Ragged batches are rejected instead of padded.
- Some classifier post-processing options are not supported in batched mode because their fitted state is dataset-specific.
- `float64` is rejected by the fused batched path even though ordinary per-dataset prediction may still work.
