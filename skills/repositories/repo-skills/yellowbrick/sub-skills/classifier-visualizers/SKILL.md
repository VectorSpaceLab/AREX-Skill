---
name: classifier-visualizers
description: "Use Yellowbrick classification diagnostics for scikit-learn
  classifiers, probability curves, class labels, class balance, pipelines, and
  saved visual reports."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Yellowbrick Classifier Visualizers

## Use this sub-skill when

- You need visual diagnostics for a scikit-learn **classifier** rather than a
  regressor, clusterer, feature matrix, or text corpus.
- The user asks for a classification report, confusion matrix, ROC-AUC curve,
  precision-recall curve, class prediction error chart, discrimination threshold
  curve, class balance chart, or classifier quick method.
- The workflow involves train/test splits, fitted estimators, class labels,
  label encoders, probability or decision scores, pipelines, or saved PNG/SVG
  classifier figures.

## Route elsewhere when

- The request is about display setup, `Agg`, axes reuse, style palettes,
  notebooks, or generic `show(outpath=...)` behavior: first read
  [visualizer patterns](../../references/visualizer-patterns.md), then use this
  sub-skill for classifier-specific choices.
- The failure is a package import, backend, font, Matplotlib display, or broad
  scikit-learn compatibility issue: read root
  [troubleshooting](../../references/troubleshooting.md) before applying the
  classifier-specific fixes here.
- The task is target-only EDA beyond classifier support, such as broader target
  distributions or feature-target correlations: route to
  [feature-target visualizers](../feature-target-visualizers/SKILL.md).
- The user wants experimental decision-boundary plots or contrib wrappers:
  route to [contrib and extensions](../contrib-and-extensions/SKILL.md), not to
  core `yellowbrick.classifier` score visualizers.

## Classifier visualizer map

| Need | Use | Important constraints |
|---|---|---|
| Per-class precision/recall/F1 heatmap | `ClassificationReport` | Needs classifier `predict`; `support` controls support column. |
| True-vs-predicted matrix | `ConfusionMatrix` | Use `percent=True` for row percentages; avoid percent with filtered classes. |
| ROC/AUC curves | `ROCAUC` / `roc_auc` | Needs `predict_proba` or `decision_function`; configure binary vs multiclass. |
| Precision-recall curves | `PrecisionRecallCurve` / `PRCurve` | Needs `predict_proba` or `decision_function`; use for imbalanced classes. |
| Wrong-class distribution | `ClassPredictionError` | Binary/multiclass only; class filtering is not fully supported. |
| Threshold tuning | `DiscriminationThreshold` | Binary classifiers only; repeats split/fit trials on clones. |
| Target support before/after split | `ClassBalance` / `class_balance` | Target-only, no estimator; use `labels` matching discovered classes. |

## Required read order for future agents

1. Read [API reference](references/api-reference.md) to choose the correct
   visualizer, import path, signature, and parameter settings.
2. Read [workflows](references/workflows.md) for end-to-end recipes covering
   reports, binary/multiclass ROC and PR, threshold tuning, class balance,
   pipelines, and headless saving.
3. If anything fails, read classifier-specific
   [troubleshooting](references/troubleshooting.md), then root
   [troubleshooting](../../references/troubleshooting.md) for shared display or
   dependency issues.
4. For a safe local smoke check, run
   [classification_smoke.py](scripts/classification_smoke.py). It uses synthetic
   data, forces Matplotlib `Agg`, performs no network access, and writes PNGs.

## Canonical lifecycle

Use the explicit visualizer lifecycle when you need control over fitting,
scoring, saving, or already-fitted estimators:

```python
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from yellowbrick.classifier import ClassificationReport

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=42
)

model = LogisticRegression(max_iter=1000)
viz = ClassificationReport(model, classes=class_names, support=True)
viz.fit(X_train, y_train)      # fits the wrapped estimator unless already fitted
score = viz.score(X_test, y_test)  # draws and returns estimator score/metric
viz.show(outpath="classification_report.png", clear_figure=True)
```

Prefer the explicit lifecycle over quick methods when saving files, when the
estimator is already fitted, when you need to reuse axes, or when you need to
catch scores and visualizer attributes such as `scores_`, `confusion_matrix_`,
`roc_auc`, `score_`, `predictions_`, or `support_`.

## Quick-method policy

Yellowbrick quick methods instantiate the visualizer, call `fit`, call `score`
when applicable, optionally call `show()`, and return the visualizer:

- `classification_report(...)`
- `confusion_matrix(...)`
- `roc_auc(...)`
- `precision_recall_curve(...)`
- `class_prediction_error(...)`
- `discrimination_threshold(...)`
- `class_balance(...)`

Use quick methods for notebook-style one-liners or simple scripts. Pass
`show=False` when embedding in a pipeline step or when you will save later with
`viz.show(outpath=..., clear_figure=True)`. For score visualizer quick methods,
provide both `X_test` and `y_test`, or neither; passing only one raises a
Yellowbrick value error.

## Binary vs multiclass decisions

- `ClassificationReport`, `ConfusionMatrix`, and `ClassPredictionError` support
  ordinary binary and multiclass classifier targets.
- `ROCAUC` supports binary and multiclass single-output targets. For a binary
  estimator with one-dimensional `decision_function` scores, set `binary=True`
  for one positive-class curve, or set `micro=False, macro=False` and choose
  `per_class` deliberately.
- Multiclass `ROCAUC` requires at least one of `micro`, `macro`, or `per_class`
  to be true; defaults draw per-class plus micro/macro curves.
- `PrecisionRecallCurve` draws a binary curve for binary targets. For multiclass
  targets it wraps the estimator with a one-vs-rest strategy; use
  `per_class=True, micro=False` for individual class curves, or keep the default
  `micro=True, per_class=False` for the micro-average curve.
- `DiscriminationThreshold` is binary only. It rejects multiclass targets and
  non-probability/non-decision-score estimators.
- `ClassBalance` is target-only and works before any model is created.

## Class labels and encoders

Use `classes` only to provide display names in the order Yellowbrick discovers
sorted classes. Use `encoder` when the target values are encoded and you need a
mapping from encoded values to human-readable labels. If both are supplied,
Yellowbrick prefers the encoder and may warn.

For `ConfusionMatrix`, `ClassificationReport`, `ROCAUC`, `PrecisionRecallCurve`,
and `ClassPredictionError`, fit on representative labels so that train/test
classes align with the estimator's `classes_`. If a rare class is missing from a
split, use a stratified split or provide more data rather than forcing labels.
For target-only `ClassBalance`, `labels` must have the same length as the unique
classes discovered across `y_train` and `y_test`.

## Probability and decision-score requirements

`ROCAUC`, `PrecisionRecallCurve`, and `DiscriminationThreshold` need score-like
estimator outputs:

- Good defaults: `LogisticRegression`, `GaussianNB`, `BernoulliNB`, many tree
  ensembles with `predict_proba`.
- `SVC` needs `probability=True` for `predict_proba`; otherwise use its
  `decision_function` where compatible.
- `LinearSVC` and `RidgeClassifier` can work for some ROC/PR cases through
  `decision_function`, but binary curve flags may need adjustment.
- Plain classifiers with only `predict` cannot produce ROC, PR, or threshold
  curves; use a calibrated wrapper or a model exposing scores.

## Pipeline use

Two patterns are safe:

1. Wrap the complete preprocessing-plus-classifier `Pipeline` as the estimator:
   `ClassificationReport(pipe, classes=names).fit(X_train, y_train)`.
2. Put a visualizer as the final pipeline step when you want a scikit-learn
   pipeline whose final `.score()` draws the figure. Keep visualizers at the end;
   they are not feature transformers for downstream model steps.

For quick methods, pass the complete pipeline as `estimator`. Keep train/test
arrays in the same feature representation expected by the pipeline's first step.

## Saving and headless execution

- Use `matplotlib.use("Agg")` before importing `pyplot` in scripts and CI.
- Prefer `viz.show(outpath="plot.png", clear_figure=True)` for saved files.
- Reuse explicit Matplotlib axes only when combining plots intentionally; most
  classifier diagnostics are easiest as separate figures.
- Use [classification_smoke.py](scripts/classification_smoke.py) to verify that
  the installed package, compatible scikit-learn stack, and `Agg` output path can
  generate classifier PNGs without external data.

## Validation checklist

Before handing a classifier visualization to a user:

- Confirm the estimator is a classifier and, for ROC/PR/threshold, exposes
  `predict_proba` or `decision_function`.
- Confirm binary-only visualizers are not receiving multiclass targets.
- Confirm class display names match discovered classes and are stable across
  train/test splits.
- Confirm the split is stratified when class support matters.
- Confirm `show(outpath=...)` wrote a non-empty file in headless contexts.
- If a normal scikit-learn classifier is rejected as "not a classifier", check
  root dependency compatibility guidance before rewriting code.
