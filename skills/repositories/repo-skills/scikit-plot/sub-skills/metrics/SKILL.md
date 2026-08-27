---
name: metrics
description: "Routes scikit-plot metric-curve requests for confusion matrices,
  ROC, precision-recall, KS, calibration, gain, lift, and silhouette plots."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Metrics

Use this sub-skill for the current `scikitplot.metrics` plotting functions. These functions consume labels, predictions, probabilities, scores, or cluster labels and return Matplotlib `Axes` objects.

## Route here

- Confusion matrices: `plot_confusion_matrix`.
- Multiclass or binary ROC curves: `plot_roc`; legacy code may still call `plot_roc_curve`.
- Multiclass or binary precision-recall curves: `plot_precision_recall`; legacy code may still call `plot_precision_recall_curve`.
- Binary probability diagnostics: `plot_ks_statistic`, `plot_calibration_curve`, `plot_cumulative_gain`, `plot_lift_curve`.
- Silhouette analysis from `X` plus cluster labels: `plot_silhouette`.
- Quick validation of the metric family: `scripts/metrics_smoke.py`.

## Inputs to check first

1. For confusion matrices, provide `y_true` and `y_pred` with aligned sample order.
2. For ROC and precision-recall, pass a 2-D probability matrix shaped `(n_samples, n_classes)`.
3. For KS, cumulative gain, lift, and calibration, use binary targets unless the function explicitly supports multiclass.
4. For silhouette, provide the feature matrix and one cluster label per sample.
5. Pass `ax=` when composing figures; every route should return the axes it drew on.

## Common decisions

- Use `labels`, `true_labels`, and `pred_labels` to reorder or subset confusion-matrix axes.
- Use `plot_micro`, `plot_macro`, and `classes_to_plot` on the current ROC/PR APIs instead of the older `curves` tuple where possible.
- Use `n_bins` for calibration only after confirming enough binary samples per bin.
- Keep probability columns in the same class order used by the fitted classifier.
- Set a non-interactive Matplotlib backend such as `Agg` for automation or smoke checks.

## Reroute

- Feature importance or learning curves: `../estimators/SKILL.md`.
- Elbow-curve cluster sweeps: `../clustering/SKILL.md`.
- PCA variance or 2-D projection: `../decomposition/SKILL.md`.
- Factory-injected bound methods or deprecated `scikitplot.plotters`: `../legacy-factories/SKILL.md`.

## Read next

- `references/api-reference.md` for verified signatures, input constraints, and deprecated aliases.
- `references/workflows.md` for concrete call patterns by plot family.
- `references/troubleshooting.md` for binary-only restrictions, shape errors, label validation, and compatibility failures.
- `scripts/metrics_smoke.py` for a tiny Agg-backed smoke run covering the main metric plot families.
