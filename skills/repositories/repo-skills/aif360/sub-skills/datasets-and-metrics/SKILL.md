---
name: datasets-and-metrics
description: "Use AIF360 legacy dataset containers and fairness metric classes
  for tabular protected-group analysis."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AIF360 datasets and metrics router

Use this sub-skill when the task is about AIF360's legacy dataset objects and metric classes: constructing `StructuredDataset`, `BinaryLabelDataset`, `StandardDataset`, or `RegressionDataset` instances; loading legacy raw-dataset wrappers; defining privileged/unprivileged protected groups; and computing dataset, classification, regression, sample-distortion, or MDSS classification metrics.

## Read first

- [Data formats](references/data-formats.md): dataset object conventions, in-memory pandas construction, built-in dataset wrapper caveats, and group/label encoding rules.
- [API reference](references/api-reference.md): constructor signatures, metric class selection, method groups, and optional OT metric caveats.
- [Workflows](references/workflows.md): runnable patterns for synthetic datasets, prediction metric reports, raw wrappers, sample distortion, and regression metrics.
- [Troubleshooting](references/troubleshooting.md): import/install warnings, optional dependencies, raw-data failures, group/schema errors, and workflow-specific metric failures.

## Fast routing

1. **In-memory legacy dataset**: read [data formats](references/data-formats.md#in-memory-binarylabeldataset-from-pandas) and build a numeric, NA-free pandas `DataFrame`; pass `label_names`, `protected_attribute_names`, and explicit `favorable_label`/`unfavorable_label` when labels are not `1.0`/`0.0`.
2. **Built-in wrappers**: read [built-in dataset wrappers](references/data-formats.md#built-in-legacy-dataset-wrappers) before calling `AdultDataset`, `GermanDataset`, `CompasDataset`, `BankDataset`, `MEPSDataset19/20/21`, or `LawSchoolGPADataset`; legacy wrappers are not safe smoke tests because public raw files may be absent or network-bound.
3. **Metric choice**: use `BinaryLabelDatasetMetric` for one true dataset, `ClassificationMetric` for true-vs-predicted `BinaryLabelDataset` pairs, `SampleDistortionMetric` for original-vs-distorted `StructuredDataset` pairs, `RegressionDatasetMetric` for ranked regression datasets, and `MDSSClassificationMetric` only when a classification metric object must score a known group.
4. **Group definitions**: create `privileged_groups` and `unprivileged_groups` as lists of dictionaries keyed by `dataset.protected_attribute_names`; the dictionary values must match the encoded numeric protected attributes.
5. **Smoke check**: run the bundled no-data script with `python scripts/metric_report_smoke.py --pretty` from this sub-skill directory, or pass its path to a Python interpreter from another working directory.

## Route away when appropriate

- If the task asks for bias mitigation `fit`, `transform`, `predict`, postprocessing thresholds, or algorithm selection after metric diagnosis, route to [mitigation-algorithms](../mitigation-algorithms/SKILL.md).
- If the task asks for the preferred pandas/scikit-learn interface, `aif360.sklearn.datasets.fetch_*`, protected attributes in pandas indexes, sklearn scorers, or sklearn pipelines, route to [sklearn-interface](../sklearn-interface/SKILL.md).
- If the task asks for subgroup search, FACTS, bias scanning beyond `MDSSClassificationMetric.score_groups`, or metric text/JSON explainers, route to [detectors-and-explainers](../detectors-and-explainers/SKILL.md).

## Minimal operating checklist

- Confirm `aif360` imports and note that base dataset/metric workflows are CPU-only.
- Keep raw benchmark data and network access out of smoke tests; use synthetic `BinaryLabelDataset` examples first.
- Check `dataset.protected_attribute_names`, `dataset.privileged_protected_attributes`, and `dataset.unprivileged_protected_attributes` before constructing metric group dictionaries.
- For `ClassificationMetric`, make the predicted dataset by deep-copying the true dataset and changing only `labels` and optionally `scores`; otherwise equality validation will fail.
- Mark optional-dependency metrics such as optimal transport as optional/unverified unless the required extra has been installed and tested in the current task environment.
