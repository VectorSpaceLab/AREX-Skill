---
name: artifacts-reports
description: "Use mljar-supervised AutoML artifacts, reports, structured
  reports, explainability outputs, persistence, and retrain checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# artifacts-reports

Use this sub-skill after an `mljar-supervised` `AutoML` run exists or when a task is primarily about saved run artifacts, report extraction, explainability files, reload/prediction behavior, or deciding whether a saved model needs retraining.

## Route here for

- Locating and interpreting an AutoML `results_path` directory, `params.json`, `leaderboard.csv`, top-level report files, and model subdirectories.
- Loading a trained run with `AutoML(results_path=...)` or `automl.load(path)` and predicting after reload.
- Calling `get_leaderboard(...)`, `report()`, and `report_structured(format="markdown"|"dict"|"json", model_name=...)`.
- Explaining why SHAP, permutation-importance, tree, coefficient, or learning-curve artifacts are present or absent.
- Checking preservation/move requirements for saved runs and using `need_retrain(...)` on new labeled data.

## Start with these references

1. [Artifact layout and persistence](references/artifact-layout.md) for `results_path`, `params.json`, model folders, loading, leaderboard, and prediction-after-load checks.
2. [Reporting and explainability](references/reporting-and-explainability.md) for `report()`, `report_structured(...)`, report payload fields, `model_name`, and explainability artifacts.
3. [Troubleshooting](references/troubleshooting.md) for stale/conflicting result directories, wrong object loading, missing model files, report format mistakes, optional Graphviz/SHAP gaps, and moved directories.

For package assumptions and cross-cutting install/import issues, use the root references: [package overview](../../references/package-overview.md) and [package troubleshooting](../../references/troubleshooting.md).

## Boundaries

- Route new training configuration, mode/algorithm/time-limit selection, validation design, and metric choice to [`training-core`](../training-core/).
- Route generated Mercury app workspaces and `app()`, `local_app()`, or `publish_app()` behavior to [`app-deployment`](../app-deployment/).
- Route the meaning of fairness metrics, sensitive-feature declarations, privileged/underprivileged groups, and mitigation tradeoffs to [`fairness-workflows`](../fairness-workflows/). This sub-skill only explains where fairness fields appear in leaderboards and reports.
- Do not treat backend learner files as the public persistence API. Standard users should load the full AutoML directory.

## Bundled helper

Run [`scripts/structured_report_smoke.py`](scripts/structured_report_smoke.py) to train a tiny synthetic model in a temporary or chosen output directory, reload it, call `report_structured` in multiple formats, optionally request a model-specific report, and print stable pass/fail signals.
