---
name: analytics
description: "Guides SecretFlow preprocessing, statistics, and classical ML
  workflows that use the direct Python APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Analytics

Use this sub-skill when the task is about direct SecretFlow preprocessing,
statistics, or classical ML APIs rather than the component CLI.

## Owns

- preprocessing helpers such as `StandardScaler`
- statistics helpers such as `psi_eval`, table statistics, and score-card flows
- direct ML classes in `secretflow.ml.linear`, `secretflow.ml.cluster`,
  `secretflow.ml.naive_bayes`, `secretflow.ml.gaussian_process`, and
  `secretflow.ml.neighbors`
- training / prediction workflows that use the direct Python APIs
- common optional-dependency and SPU configuration failures

## Does not own

- component CLI / component export workflows — use `component-cli`
- device/object setup and federated containers — use `runtime-data`
- PSI deployment, Kuscia, or TEEU orchestration — use `privacy-orchestration`

## Trigger phrases

Use this route when a user asks things like:
- how to scale or preprocess federated data
- how to compute PSI or score-card metrics directly
- how to fit SecretFlow's direct ML estimators
- how to compare SecretFlow's model APIs with scikit-learn
- why a model needs SPU, HEU, or a particular party layout

## Reading order

1. Read `references/analytics.md` for the algorithm map and workflow choices.
2. Read the root troubleshooting page if the import or optional dependency path
   is broken.
3. Use `scripts/analytics_smoke.py` when you need a tiny import-only proof that
   the analytics surface is available.

## Workflow

1. Decide whether the user wants a data transform, a metric, or a model.
2. Identify the required party/device layout before choosing the class or
   metric.
3. For preprocessing and statistics, confirm the dataframe shape and the owning
   parties before you fit or evaluate anything.
4. For ML classes, start with the direct Python constructor and only escalate to
   a component-based path if the user specifically needs export or CLI-driven
   execution.

## Common decisions

- Use `StandardScaler` for federated tabular normalization.
- Use `psi_eval` for the PSI-style score calculations already built into the
  direct API.
- Use the `secretflow.ml.linear` classes for logistic-regression and GLM-style
  tasks.
- Use `KMeans`, `GNB`, `GPC`, or `KNNClassifer` when the task names a classical
  estimator family directly.

## Bundled files

- `references/analytics.md` — algorithm catalog, input expectations, and troubleshooting.
- `scripts/analytics_smoke.py` — small import and signature smoke helper.
