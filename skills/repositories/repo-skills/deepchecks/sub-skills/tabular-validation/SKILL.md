---
name: tabular-validation
description: "Build Deepchecks tabular Dataset objects, suites, checks, model
  inputs, scorers, and failure recovery for tabular validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Tabular Validation

Use this sub-skill when the task involves pandas/numpy tabular data, `deepchecks.tabular.Dataset`, tabular built-in suites, individual tabular checks, sklearn-style tabular models, precomputed tabular predictions, or tabular scorer/condition customization.

## Fast route

1. Build `Dataset` objects with explicit metadata: `label`, `features`, `cat_features`, `index_name`, `datetime_name`, `label_type`, and `dataset_name` where available.
2. Choose the smallest suite:
   - single dataset quality: `deepchecks.tabular.suites.data_integrity`
   - train/test split validation: `deepchecks.tabular.suites.train_test_validation`
   - model performance, predictions, drift, and weak segments: `deepchecks.tabular.suites.model_evaluation`
   - broad first-pass investigation: `deepchecks.tabular.suites.full_suite`
3. Prefer `with_display=False` in automation; send HTML/JSON/CI/report saving to [results-and-integrations](../results-and-integrations/SKILL.md).
4. For model checks, pass either a fitted sklearn-style `model` or aligned `y_pred_*` / `y_proba_*` arrays, plus `model_classes` and `feature_importance` when needed.
5. For check/suite API details, load [API reference](references/api-reference.md). For copyable recipes, load [workflows](references/workflows.md). For failures, load [tabular troubleshooting](references/troubleshooting.md).

## Boundaries and routing

- Use [nlp-validation](../nlp-validation/SKILL.md) for `TextData`, text classification, token labels, embeddings, and NLP properties.
- Use [vision-validation](../vision-validation/SKILL.md) for `VisionData`, image batches, detection, segmentation, torch/torchvision loaders, and vision metrics.
- Use [results-and-integrations](../results-and-integrations/SKILL.md) for `show`, `save_as_html`, JSON serialization, pytest/CI gating, and integration artifact handling.
- Use [root troubleshooting](../../references/troubleshooting.md) for package installation, import, optional dependency, or environment-wide display issues before debugging a tabular object.

## Bundled helper

Run [scripts/deepchecks_tabular_smoke.py](scripts/deepchecks_tabular_smoke.py) for a safe local smoke using a tiny in-memory DataFrame and sklearn model. It performs no downloads, credentials, or destructive writes by default; `--html-out` writes only to the path explicitly supplied by the caller.
