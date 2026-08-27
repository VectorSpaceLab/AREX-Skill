---
name: sklearn-interface
description: "Use AIF360's preferred sklearn-compatible pandas API for datasets,
  fairness metrics, scorers, estimators, and pipeline caveats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AIF360 sklearn Interface

Use this sub-skill when the task is best handled through the preferred `aif360.sklearn` API: pandas `DataFrame`/`Series` inputs, protected attributes stored in indexes, sklearn-compatible fairness metrics/scorers, estimators, meta-estimators, and pipeline caveats.

## Fast routing

- Dataset loading and conversion: start with [API reference](references/api-reference.md#dataset-functions) and [workflows](references/workflows.md#standardize-or-fetch-pandas-data).
- Group, individual, MDSS-score, and scorer functions: use [API reference](references/api-reference.md#metric-functions) and [workflows](references/workflows.md#compute-metrics-and-sklearn-scorers).
- `Reweighing`, postprocessors, and `PostProcessingMeta`: use [workflows](references/workflows.md#estimator-and-meta-estimator-patterns) and [optional estimators](references/optional-estimators.md).
- Missing extras, dropped indexes, scorer surprises, fetch/cache failures, or postprocessing errors: use [troubleshooting](references/troubleshooting.md).
- Quick self-check of the base metrics path: run [scripts/sklearn_metric_smoke.py](scripts/sklearn_metric_smoke.py) from this sub-skill directory.

## Boundaries and handoffs

- Route legacy `BinaryLabelDataset`, `StructuredDataset`, `StandardDataset`, and legacy metric-class tasks to the sibling `datasets-and-metrics` sub-skill.
- Route legacy `aif360.algorithms` preprocessing/inprocessing/postprocessing class workflows to the sibling `mitigation-algorithms` sub-skill.
- Route MDSS subgroup scans, FACTS counterfactual subgroup rules, and metric text/JSON explainers to the sibling `detectors-and-explainers` sub-skill. This sub-skill only covers `aif360.sklearn.metrics.mdss_bias_score` as a metric helper.
- Do not rely on source notebooks, tests, or external raw-data locations at runtime. Use the bundled references and scripts here, plus user-provided data or cache settings.

## Safety and verification status

- Base CPU imports and in-memory sklearn metric workflows are supported by this sub-skill.
- Dataset fetchers can require network access or a warmed cache; do not use them in no-network smoke checks.
- Optional extras were not installed in the verified base environment. Treat extra-gated estimators and `ot_distance` as optional/unverified until the matching extra is installed and checked.
