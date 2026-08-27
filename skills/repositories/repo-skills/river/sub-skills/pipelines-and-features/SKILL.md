---
name: pipelines-and-features
description: "Build, debug, and validate River pipelines and online feature engineering."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Pipelines and Features

Use this sub-skill when you need to assemble River feature pipelines, feature branches, rolling
aggregates, or inspect feature flow.

## Scope

Covers:
- `compose.Pipeline`, `|`, `+`, `*`, `TransformerUnion`, `TransformerProduct`, `Grouper`
- `compose.Select`, `Discard`, `SelectType`, `FuncTransformer`
- `feature_extraction.Agg`, `TargetAgg`, `BagOfWords`, `TFIDF`, `PolynomialExtender`
- `preprocessing` transforms for scaling, encoding, hashing, and imputation
- `feature_selection`, `stats`, `sketch`, and `utils.Rolling` / `TimeRolling`
- `compose.learn_during_predict`, `debug_one`, and `utils.log_method_calls`

## Route elsewhere

- Base estimator and online interface rules: `online-core-api`
- Model-family choice and estimator selection: `supervised-models`
- Evaluation loops and streaming scoring: `streaming-evaluation`

## How to work

1. Read [`references/pipeline-workflows.md`](references/pipeline-workflows.md) for composition,
   learning order, routing, and debugging.
2. Read [`references/feature-engineering.md`](references/feature-engineering.md) for branch design,
   rolling stats, sketches, and text/numeric patterns.
3. Read [`references/troubleshooting.md`](references/troubleshooting.md) when names, keys, or
   timestamps behave unexpectedly.
4. Run [`scripts/pipeline_feature_smoke.py`](scripts/pipeline_feature_smoke.py) to sanity-check a
   local River setup.

## Practical rules

- Keep feature dictionaries pure; return fresh dicts from custom transformers.
- Split mixed text and numeric data into separate branches, then merge.
- Prefix or rename branch outputs when two branches can emit the same key.
- Pass `t=` only for steps that accept timestamps, and pass `w=` only where sample weights are
  supported.
- Use mini-batch methods only when the involved steps support them or when a row-by-row fallback
  is acceptable.
