---
name: mljar-supervised
description: "Use MLJAR AutoML for tabular classification, regression,
  fairness-aware training, reports, persistence, and generated Mercury apps."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MLJAR Supervised

Use this repo skill when a task involves `mljar-supervised`, `supervised.AutoML`, MLJAR AutoML, automated tabular machine learning, MLJAR reports, fairness-aware AutoML, or generated Mercury prediction apps.

MLJAR Supervised trains supervised AutoML pipelines for tabular binary classification, multiclass classification, and regression. It handles common preprocessing, model search, reports, explainability outputs, fairness options, persistence, and app generation through the Python package imported as `supervised`.

## Start here

1. Confirm the package is installed and importable:

   ```python
   from supervised import AutoML
   print(AutoML)
   ```

   For a more detailed local check, run [`scripts/check_mljar_supervised_install.py`](scripts/check_mljar_supervised_install.py).
2. Identify whether the user wants to train a model, prepare data, inspect an existing run, add fairness constraints, or build an app.
3. Route to the focused sub-skill below before giving detailed API, data, report, or deployment instructions.
4. Keep user examples bounded: disable expensive feature engineering and explanations for smoke checks; use larger `Perform`, `Compete`, or `Optuna` runs only when the user accepts the runtime.

## Route map

| User intent | Read |
| --- | --- |
| Train/configure `AutoML`, choose `mode`, algorithms, validation, metrics, time limits, ensembling/stacking, predict/score/retrain | [`training-core`](sub-skills/training-core/) |
| Prepare `X`, `y`, `sample_weight`, custom CV, missing/categorical/text/datetime columns, target inference, preprocessing and feature-engineering flags | [`data-preprocessing`](sub-skills/data-preprocessing/) |
| Inspect `results_path`, load saved runs, use leaderboards, reports, structured reports, explainability artifacts, SHAP/importance/learning curves, persistence | [`artifacts-reports`](sub-skills/artifacts-reports/) |
| Configure fairness-aware training with `sensitive_features`, fairness metrics, thresholds, privileged/underprivileged groups, fairness reports | [`fairness-workflows`](sub-skills/fairness-workflows/) |
| Generate app files, preview locally with Mercury, or prepare guarded publishing with `app()`, `local_app()`, `publish_app()` | [`app-deployment`](sub-skills/app-deployment/) |

## Package assumptions

- Distribution name: `mljar-supervised`; import name: `supervised`.
- Main public class: `supervised.AutoML`.
- Supported ML tasks: binary classification, multiclass classification, and regression.
- Built-in modes: `Explain`, `Perform`, `Compete`, and `Optuna`.
- Common algorithms include `Baseline`, `Linear`, `Decision Tree`, `Random Forest`, `Extra Trees`, `LightGBM`, `Xgboost`, `CatBoost`, `Neural Network`, and `Nearest Neighbors`.
- Core workflows are CPU-compatible. GPU hardware is not required for this skill's selected scope.
- Optional surfaces can need extra system/runtime setup: Graphviz for some tree visualizations and Mercury plus browser/network/auth for local or hosted apps.

Read [`references/package-overview.md`](references/package-overview.md) for install prerequisites, high-level capabilities, optional dependencies, and safe smoke-test strategy. Read [`references/troubleshooting.md`](references/troubleshooting.md) for cross-cutting install/import/dependency failures.

## Common operating patterns

- For a quick user-data smoke, use `AutoML(mode="Explain", algorithms=["Baseline", "Decision Tree"], explain_level=0, train_ensemble=False, stack_models=False, golden_features=False, features_selection=False, total_time_limit=30)` and a disposable `results_path`.
- For production-style tabular modeling, start from `mode="Perform"`, set a realistic `total_time_limit`, and keep `results_path` stable for later reports and reload.
- For competition or maximum-performance work, use `mode="Compete"` or `mode="Optuna"` only after discussing runtime, validation, stacking, and per-algorithm tuning budgets.
- For saved runs, load the full AutoML results directory with `AutoML(results_path="...")`; do not load learner files directly unless a sub-skill explicitly says why.
- For fairness, pass sensitive features to `fit(..., sensitive_features=...)` and choose task-compatible fairness metrics.
- For generated apps, call `automl.app()` to create files first; do not start Mercury or publish without explicit user approval.

## Bundled checks

- [`scripts/check_mljar_supervised_install.py`](scripts/check_mljar_supervised_install.py): import/version/signature and optional dependency probe.
- [`sub-skills/training-core/scripts/mljar_automl_smoke.py`](sub-skills/training-core/scripts/mljar_automl_smoke.py): tiny synthetic training/prediction smoke.
- [`sub-skills/data-preprocessing/scripts/inspect_preprocessing_behaviour.py`](sub-skills/data-preprocessing/scripts/inspect_preprocessing_behaviour.py): lightweight preprocessing utility checks.
- [`sub-skills/artifacts-reports/scripts/structured_report_smoke.py`](sub-skills/artifacts-reports/scripts/structured_report_smoke.py): tiny structured-report and reload smoke.
- [`sub-skills/fairness-workflows/scripts/fairness_smoke.py`](sub-skills/fairness-workflows/scripts/fairness_smoke.py): tiny fairness-aware fit and report signal check.
- [`sub-skills/app-deployment/scripts/generate_app_workspace_smoke.py`](sub-skills/app-deployment/scripts/generate_app_workspace_smoke.py): tiny app-workspace generation check without serving or publishing.

## Refresh and provenance

Read [`references/repo-provenance.md`](references/repo-provenance.md) before deciding whether this skill is current for a checkout. If the package version, commit, public `AutoML` signatures, docs, examples, or test-backed behavior changed, run `refresh-repo-skill` instead of relying on this snapshot.
