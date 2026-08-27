---
name: fairness-workflows
description: "Configure and inspect fairness-aware AutoML workflows in mljar-supervised."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# fairness-workflows

Use this sub-skill when the task asks for fairness-aware `supervised.AutoML` training or inspection with `sensitive_features`, `fairness_metric`, `fairness_threshold`, `privileged_groups`, or `underprivileged_groups`.

## Route here for

- Binary classification, multiclass classification, or regression training that passes sensitive features to `AutoML.fit()`.
- Choosing a task-compatible fairness metric and threshold.
- Declaring privileged and underprivileged groups, including multiple sensitive columns.
- Interpreting fairness leaderboard columns, fairness summaries, certificates, and fairness fields in `report_structured()` output.
- Diagnosing fairness-specific errors such as invalid metric names, task/metric mismatches, missing thresholds, or sensitive-feature shape issues.

## Read first

- [Fairness guide](references/fairness-guide.md) for API shape, workflow recipes, reports, and safe patterns.
- [Fairness metrics](references/fairness-metrics.md) for metric names, default thresholds, directionality, and task compatibility.
- [Troubleshooting](references/troubleshooting.md) for common failure modes and corrective actions.
- [Synthetic smoke helper](scripts/fairness_smoke.py) for a tiny no-network fit plus structured-report fairness signal check.

## Boundaries

- For generic `AutoML` mode, algorithm, validation, time-budget, scoring, and prediction setup, route to `../training-core/`.
- For generic report serialization, result-directory layout, model-specific structured reports, loading saved runs, and explainability artifacts, route to `../artifacts-reports/`.
- For generated Mercury apps, local serving, or publishing, route to `../app-deployment/`.
- For package install/import and optional dependency issues, start from `../../references/package-overview.md` and `../../references/troubleshooting.md`.

Do not run large or network-backed fairness examples as runtime checks. Use the bundled synthetic helper or a user-provided local dataset instead.
