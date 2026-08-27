---
name: online-core-api
description: "Explain River's estimator lifecycle, base interfaces, cloning,
  tags, and estimator validation checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# online-core-api

Use this sub-skill when a task asks how a River object should learn, predict, transform, clone, expose tags, or pass generic estimator checks.

## Read first

- `references/estimator-contracts.md`
- `references/api-reference.md`
- `references/troubleshooting.md`
- `scripts/estimator_contract_smoke.py --help`

## Use this for

- Explaining `learn_one`, `predict_one`, `predict_proba_one`, `transform_one`, `score_one`, `update`, and mini-batch counterparts.
- Adding or reviewing a River estimator, transformer, clusterer, anomaly detector, drift detector, or wrapper.
- Deciding whether a model is supervised, multiclass, stochastic, or tag-sensitive.
- Using `clone`, `mutate`, `_unit_test_params`, `_unit_test_skips`, and `checks.check_estimator`.
- Diagnosing why a classifier emits `None` or `{}` before seeing labels.

## Route elsewhere

- Pipeline composition, selectors, feature extraction, preprocessing, and feature-routing patterns belong to `pipelines-and-features`.
- Datasets, stream adapters, progressive validation, and metrics loops belong to `streaming-evaluation`.
- Choosing a supervised model family belongs to `supervised-models`.
- Drift, anomaly, clustering, time-series, bandit, and recommender workflows belong to `specialized-workflows`.

## Core decision points

- Use one-sample methods unless the task explicitly names mini-batch APIs or pandas dataframes.
- Treat dictionaries as the canonical feature container; missing and new feature keys are normal in River.
- Prefer generic checks for new estimator compatibility, then add model-family-specific tests for behavior not covered by generic checks.
- If a pipeline is checked with `isinstance(pipeline, base.Classifier)`, River unwraps the last step for estimator-type checks.
