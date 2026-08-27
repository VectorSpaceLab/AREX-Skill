# Classifier Visualizer API Reference

This reference is distilled for runtime use from Yellowbrick's public classifier
and class-balance APIs. It intentionally uses only importable package APIs and
bundled guidance; do not depend on source checkout files or external docs.

## Imports

```python
from yellowbrick.classifier import (
    ClassificationReport,
    ConfusionMatrix,
    ROCAUC,
    PrecisionRecallCurve,
    PRCurve,
    ClassPredictionError,
    DiscriminationThreshold,
    classification_report,
    confusion_matrix,
    roc_auc,
    precision_recall_curve,
    class_prediction_error,
    discrimination_threshold,
)
from yellowbrick.classifier import ClassBalance, class_balance  # hoisted alias
# Equivalent target import for target-only use:
from yellowbrick.target import ClassBalance, class_balance
```

`PRCurve` is an alias for `PrecisionRecallCurve`. `ClassBalance` is target-only;
it is present in `yellowbrick.classifier` for classification workflow
convenience but also belongs with feature/target diagnostics.

## Score visualizer lifecycle

Classifier score visualizers wrap a scikit-learn classifier-like estimator:

```python
viz = Visualizer(estimator, ...)
viz.fit(X_train, y_train)       # fits estimator unless is_fitted says not to
metric = viz.score(X_test, y_test)  # draws the visualization
viz.show(outpath="plot.png", clear_figure=True)
```

Common constructor parameters across score visualizers:

| Parameter | Meaning | Decision guidance |
|---|---|---|
| `estimator` | scikit-learn classifier or final classifier `Pipeline` | Must satisfy Yellowbrick's classifier check unless `force_model=True`. |
| `ax` | Matplotlib axes | Use for controlled layout; otherwise let Yellowbrick create axes. |
| `classes` | display labels ordered by discovered class order | Use for simple display names only; length/order must match classes. |
| `encoder` | dict or fitted label encoder | Use when encoded y values need stable human-readable labels. |
| `is_fitted` | `"auto"`, `True`, or `False` | Use `True` for already-fitted estimators; `False` to always fit. |
| `force_model` | skip classifier type check | Last resort for wrapped/custom estimators; can hide real API errors. |

## Core visualizers

| Visualizer | Signature | Use when | Key attributes after scoring |
|---|---|---|---|
| `ClassificationReport` | `(estimator, ax=None, classes=None, cmap='YlOrRd', support=None, encoder=None, is_fitted='auto', force_model=False, colorbar=True, fontsize=None, **kwargs)` | You need per-class precision, recall, F1, and optionally support as a heatmap. | `score_`, `scores_`, `support_score_`, `classes_`. |
| `ConfusionMatrix` | `(estimator, ax=None, sample_weight=None, percent=False, classes=None, encoder=None, cmap='YlOrRd', fontsize=None, is_fitted='auto', force_model=False, **kwargs)` | You need counts or row percentages of true vs predicted classes. | `score_`, `confusion_matrix_`, `class_counts_`, `classes_`. |
| `ROCAUC` | `(estimator, ax=None, micro=True, macro=True, per_class=True, binary=False, classes=None, encoder=None, is_fitted='auto', force_model=False, **kwargs)` | You need ROC curves and AUC from classifier probability or decision scores. | `score_`, `fpr`, `tpr`, `roc_auc`, `target_type_`. |
| `PrecisionRecallCurve` / `PRCurve` | `(estimator, ax=None, classes=None, colors=None, cmap=None, encoder=None, fill_area=True, ap_score=True, micro=True, iso_f1_curves=False, iso_f1_values=(0.2, 0.4, 0.6, 0.8), per_class=False, fill_opacity=0.2, line_opacity=0.8, is_fitted='auto', force_model=False, **kwargs)` | You need precision/recall tradeoffs, especially with imbalanced classes. | `score_`, `precision_`, `recall_`, `target_type_`. |
| `ClassPredictionError` | `(estimator, ax=None, classes=None, encoder=None, is_fitted='auto', force_model=False, **kwargs)` | You need a stacked bar chart showing which classes were predicted for each true class. | `score_`, `predictions_`, `classes_`. |
| `DiscriminationThreshold` | `(estimator, ax=None, n_trials=50, cv=0.1, fbeta=1.0, argmax='fscore', exclude=None, quantiles=array([0.1, 0.5, 0.9]), random_state=None, is_fitted='auto', force_model=False, **kwargs)` | You need binary threshold tuning over precision, recall, F-score, and queue rate. | `thresholds_`, `cv_scores_`. |
| `ClassBalance` | `(ax=None, labels=None, colors=None, colormap=None, **kwargs)` | You need target class support before modeling or to compare train/test split support. | `classes_`, `support_`, `_mode`. |

## Quick methods

Quick methods instantiate, fit, score where applicable, optionally call
`show()`, and return the visualizer instance. Use `show=False` to avoid opening a
window and to save later with the returned visualizer.

| Quick method | Signature | Notes |
|---|---|---|
| `classification_report` | `(estimator, X_train, y_train, X_test=None, y_test=None, ax=None, classes=None, cmap='YlOrRd', support=None, encoder=None, is_fitted='auto', force_model=False, show=True, colorbar=True, fontsize=None, **kwargs)` | If either `X_test` or `y_test` is supplied, both are required. |
| `confusion_matrix` | `(estimator, X_train, y_train, X_test=None, y_test=None, ax=None, sample_weight=None, percent=False, classes=None, encoder=None, cmap='YlOrRd', fontsize=None, is_fitted='auto', force_model=False, show=True, **kwargs)` | Use the class interface when you need `show(outpath=...)` in the same call. |
| `roc_auc` | `(estimator, X_train, y_train, X_test=None, y_test=None, ax=None, micro=True, macro=True, per_class=True, binary=False, classes=None, encoder=None, is_fitted='auto', force_model=False, show=True, **kwargs)` | Needs `predict_proba` or `decision_function`; tune flags for binary decision scores. |
| `precision_recall_curve` | `(estimator, X_train, y_train, X_test=None, y_test=None, ax=None, classes=None, colors=None, cmap=None, encoder=None, fill_area=True, ap_score=True, micro=True, iso_f1_curves=False, iso_f1_values=(0.2, 0.4, 0.6, 0.8), per_class=False, fill_opacity=0.2, line_opacity=0.8, is_fitted='auto', force_model=False, show=True, **kwargs)` | Multiclass defaults to micro-average; set `per_class=True, micro=False` for class curves. |
| `class_prediction_error` | `(estimator, X_train, y_train, X_test=None, y_test=None, ax=None, classes=None, encoder=None, is_fitted='auto', force_model=False, show=True, **kwargs)` | Binary/multiclass only; filtering to a subset of classes is not implemented. |
| `discrimination_threshold` | `(estimator, X, y, ax=None, n_trials=50, cv=0.1, fbeta=1.0, argmax='fscore', exclude=None, quantiles=array([0.1, 0.5, 0.9]), random_state=None, is_fitted='auto', force_model=False, show=True, **kwargs)` | Binary-only; runs repeated split/fit trials, so lower `n_trials` in CI. |
| `class_balance` | `(y_train, y_test=None, ax=None, labels=None, color=None, colormap=None, show=True, **kwargs)` | Target-only; use `ClassBalance(colors=...)` if explicit per-class colors matter. |

## Parameter decisions by task

### Reports and confusion matrices

- `ClassificationReport(..., support=True)` shows support as a support column;
  `support='count'` shows counts, `support='percent'` shows fractions.
- `ClassificationReport(..., colorbar=False)` removes the color bar for compact
  multi-panel reports.
- `ConfusionMatrix(..., percent=True)` displays row percentages. Avoid combining
  `percent=True` with class filtering because row totals can be misleading.
- `sample_weight` on `ConfusionMatrix` is passed to scikit-learn's confusion
  matrix metric for weighted examples.
- Increase `fontsize` when many classes make tick labels unreadable.

### ROC-AUC

- `ROCAUC` resolves scores using `predict_proba` first, then
  `decision_function`.
- For a true binary report with one curve, use `binary=True`.
- For a binary classifier with only a one-dimensional `decision_function`, avoid
  default micro/macro curves; use `binary=True` or `micro=False, macro=False`.
- For multiclass, leave defaults for per-class plus micro/macro curves, or set
  `per_class=False` to emphasize aggregate curves. At least one curve flag must
  remain true.
- `score_` is set to macro AUC when `macro=True` and to micro AUC first when
  only micro is requested; check `roc_auc` dict for all values.

### Precision-recall

- `PrecisionRecallCurve` resolves scores using `decision_function` first, then
  `predict_proba`.
- Binary targets draw a single PR curve and return average precision.
- Multiclass targets are adapted with a one-vs-rest classifier internally.
- `micro=True, per_class=False` draws the multiclass micro-average curve.
- `per_class=True, micro=False` draws separate class curves. If both are true,
  Yellowbrick warns that micro is ignored.
- Use `iso_f1_curves=True` to overlay reference F1 curves for threshold tradeoff
  explanations.

### Discrimination threshold

- Use only for binary targets and estimators with `predict_proba` or
  `decision_function`.
- `n_trials` controls how many shuffle/split trials are run. Keep it low for
  smoke tests; use larger values for stable reports.
- `cv` can be a float test fraction or a splitter object. If it is a splitter,
  it should return one shuffled split for each trial.
- `exclude` may omit any of `precision`, `recall`, `fscore`, `queue_rate`.
- `argmax` can be one of those metrics or `None`; if the metric is excluded,
  the annotation is suppressed.
- `quantiles` must be three monotonic values less than 1, e.g. `(0.1, 0.5, 0.9)`.

### Class balance

- `ClassBalance().fit(y_train)` shows balance mode.
- `ClassBalance().fit(y_train, y_test)` shows compare mode with train/test bars.
- `labels` must match the number of unique classes discovered across supplied
  targets and should be ordered by target class order.
- It expects one-dimensional binary or multiclass targets. Passing a feature
  matrix is a common error after old examples that used `fit(X, y)`.

## Estimator and pipeline compatibility

- A plain classifier estimator is valid if Yellowbrick recognizes it as a
  classifier. Normal scikit-learn classifiers can be rejected by Yellowbrick 1.5
  under too-new scikit-learn releases; see troubleshooting for dependency pins.
- A preprocessing `Pipeline` is valid if its final step is a classifier and the
  pipeline exposes the needed methods (`predict`, `predict_proba`, or
  `decision_function`).
- For `SVC`, pass `probability=True` when you require `predict_proba`. Without
  it, use ROC/PR modes compatible with `decision_function`, or calibrate the
  classifier.
- Do not force `force_model=True` unless you have verified that the wrapped
  estimator implements the classifier methods Yellowbrick will call.
