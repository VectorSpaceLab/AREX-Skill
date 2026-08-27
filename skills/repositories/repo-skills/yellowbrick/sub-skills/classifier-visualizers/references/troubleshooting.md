# Classifier Visualizer Troubleshooting

Use this guide after choosing a visualizer from
[api-reference.md](api-reference.md) and a recipe from [workflows.md](workflows.md).
For cross-cutting install/import, Matplotlib backend, font, display, and style
issues, also read root [troubleshooting](../../../references/troubleshooting.md).

## Fast triage

| Symptom | Likely cause | Fix |
|---|---|---|
| `This estimator is not a classifier` for `LogisticRegression`, `SVC`, etc. | Yellowbrick 1.5 classifier type detection is incompatible with a too-new scikit-learn stack. | Pin to a compatible stack such as `scikit-learn==1.3.2` with `numpy<2`; then rerun the visualizer smoke. |
| `This estimator is not a classifier` for a custom wrapper | Wrapper lacks classifier metadata or final estimator is hidden. | Wrap a real classifier pipeline, expose classifier methods/metadata, or use `force_model=True` only after verifying `predict`/score methods. |
| `ROCAUC requires estimators with predict_proba or decision_function methods` | Estimator exposes only `predict`. | Choose a probabilistic/scored classifier, set `SVC(probability=True)`, or calibrate with `CalibratedClassifierCV`. |
| `PrecisionRecallCurve requires an estimator with predict_proba or decision_function` | Same score-method issue. | Use a model with `decision_function` or `predict_proba`; check pipeline final step exposes the method. |
| `DiscriminationThreshold requires a probabilistic binary classifier` | Estimator is not binary-classifier-compatible or lacks score methods. | Use a binary classifier with `predict_proba`/`decision_function`; do not use multiclass targets. |
| `multiclass format is not supported` from threshold visualizer | `DiscriminationThreshold` received multiclass `y`. | Convert to a one-vs-rest binary problem or choose ROC/PR/classification report instead. |
| `no curves will be drawn; set binary=True` or related ROC error | Binary estimator returns one-dimensional decision scores while micro/macro curves are requested. | Use `ROCAUC(..., binary=True)` or set `micro=False, macro=False` and choose `per_class`. |
| `no curves will be drawn; specify micro, macro, or per_class` | All multiclass ROC curve flags are false. | Turn at least one curve flag on. |
| `both X_test and y_test are required` or `must specify both X_test and y_test or neither` | Quick method received only one test array. | Pass both test arrays, or pass neither and score on training data. |
| `could not decode ... y values to ... labels` | `classes`/`encoder` do not match target values. | Remove display labels, provide a correct encoder mapping, or refit with aligned train/test labels. |
| Class balance says labels count does not match classes | `labels` length differs from unique classes in `y_train`/`y_test`. | Inspect `np.unique(y_train)` and `np.unique(y_test)`, then supply one label per unique class. |
| `fit has changed to only require a 1D array, y` | Old `ClassBalance.fit(X, y)` pattern. | Call `ClassBalance().fit(y_train, y_test=None)`; do not pass feature matrix `X`. |
| Empty/missing output PNG | GUI backend, missing outdir, or not calling `show(outpath=...)`. | Force `Agg`, create parent directory, and call `viz.show(outpath=..., clear_figure=True)`. |
| Font warnings fill logs but PNG exists | Matplotlib cannot find a requested generic font. | Usually safe to ignore; install/configure fonts only if typography matters. |

## Estimator type failures

### Normal sklearn classifier rejected

Yellowbrick 1.5 relies on classifier type checks that can fail with newer
scikit-learn releases even for normal classifiers. If this happens for standard
estimators such as `LogisticRegression`, `SVC`, `GaussianNB`, or a `Pipeline`
ending in a classifier, do not rewrite the visualization first. Repair the
runtime stack:

```bash
python -m pip install "scikit-learn==1.3.2" "numpy<2"
```

Then rerun the bundled smoke helper or a tiny `ClassificationReport` check.
Also consider pinning SciPy to a version compatible with that scikit-learn/numpy
combination when the package manager does not resolve it automatically.

### Custom estimator or wrapper rejected

Check these points before using `force_model=True`:

1. The object implements `fit`, `predict`, and `score` in sklearn style.
2. ROC/PR/threshold workflows also expose `predict_proba` or
   `decision_function`.
3. If the object is a `Pipeline`, its final step is a classifier.
4. If it is an adapter around another library, prefer contrib wrappers from the
   contrib sub-skill or implement classifier metadata in the adapter.

`force_model=True` skips Yellowbrick's type guard but cannot add missing methods;
it may move the failure from initialization to `fit` or `score`.

## Probability and decision-score failures

`ClassificationReport`, `ConfusionMatrix`, and `ClassPredictionError` need
predicted classes. `ROCAUC`, `PrecisionRecallCurve`, and
`DiscriminationThreshold` need score-like outputs.

Fixes by estimator:

- `SVC`: pass `probability=True` if you need `predict_proba`; otherwise use
  `decision_function`-compatible ROC/PR settings.
- `LinearSVC`: no `predict_proba`; use `decision_function`. For binary ROC, set
  `binary=True` or disable micro/macro curves.
- `RidgeClassifier`: can expose `decision_function`; useful for PR in tests, but
  verify the target and curve flags.
- Hard-label classifiers with only `predict`: use a different model or wrap in
  `CalibratedClassifierCV` when calibrated probabilities are acceptable.
- Pipelines: call the visualizer on the complete pipeline and verify that the
  pipeline object exposes the score method needed by the visualizer.

## Binary and multiclass mistakes

### Threshold on multiclass target

`DiscriminationThreshold` only supports binary y. If the user wants threshold
behavior for a multiclass problem, ask which class is the positive class and
construct a binary target, e.g. `y_binary = (y == positive_label).astype(int)`.
Otherwise use `ROCAUC` or `PrecisionRecallCurve` with multiclass settings.

### ROC with binary decision scores

Some binary classifiers return one-dimensional decision scores. Default `ROCAUC`
requests micro/macro/per-class curves, which can be undefined for that output.
Use:

```python
ROCAUC(model, binary=True)
# or, for deliberate per-class binary curves:
ROCAUC(model, micro=False, macro=False, per_class=True)
```

### ROC with no multiclass curves

For multiclass ROC, at least one of `micro`, `macro`, or `per_class` must be
true. Use `per_class=False` only if `micro` or `macro` remains true.

### PR multiclass warning about micro ignored

If `PrecisionRecallCurve(..., micro=True, per_class=True)` warns that micro is
ignored, choose one:

- `micro=True, per_class=False` for a single micro-average curve.
- `micro=False, per_class=True` for class-wise curves.

## Labels, encoders, and class support

### Choosing `classes`

Use `classes` for display labels only, ordered by the sorted target classes that
Yellowbrick discovers. Example: if `np.unique(y)` is `[0, 1]`, pass
`classes=["no", "yes"]`.

Do not use `classes` to hide a class unless the visualizer explicitly supports
filtering. `ClassPredictionError` does not fully support class filtering and may
raise `NotImplementedError` or `ModelError` when labels are missing or extra.

### Choosing `encoder`

Use `encoder` for encoded targets:

```python
encoder = {0: "setosa", 1: "versicolor", 2: "virginica"}
viz = ConfusionMatrix(model, encoder=encoder)
```

A fitted `LabelEncoder` is also accepted. If both `classes` and `encoder` are
provided, Yellowbrick uses the encoder and may warn.

### Missing labels in splits

If a rare class appears in training but not in testing, or vice versa, reports
can show zero support or label mismatch errors. Use a stratified split:

```python
train_test_split(X, y, test_size=0.25, stratify=y, random_state=42)
```

If stratification is impossible because a class has too few examples, collect
more data or use a grouped evaluation plan; do not mask the class mismatch with
incorrect labels.

## Quick-method failures

Quick methods for score visualizers require complete split information:

```python
# Good
classification_report(model, X_train, y_train, X_test, y_test, show=False)

# Good: scores on training data
classification_report(model, X_train, y_train, show=False)

# Bad: only one test array
classification_report(model, X_train, y_train, X_test=X_test, show=False)
```

When quick methods call `show=True`, they render immediately and do not expose an
`outpath` argument. For saved figures, either use the class lifecycle or set
`show=False`, keep the returned visualizer, then call `viz.show(outpath=...)`.

## ClassBalance failures

`ClassBalance` is not a score visualizer and no longer takes an estimator or
feature matrix. Correct usage:

```python
from yellowbrick.target import ClassBalance

viz = ClassBalance(labels=class_names)
viz.fit(y_train, y_test)
viz.show(outpath="class_balance.png", clear_figure=True)
```

Common fixes:

- If y is a column vector or DataFrame, flatten/select the target series before
  calling `fit`.
- If labels mismatch, compare `len(labels)` with `len(np.unique(np.r_[y_train,
  y_test]))`.
- If the target is continuous, use regression/target diagnostics instead of
  class balance.

## Pipeline failures

Use the complete preprocessing pipeline as the estimator when feature scaling,
encoding, or selection must happen before classification:

```python
viz = ClassificationReport(preprocess_then_classifier_pipeline, classes=classes)
viz.fit(X_train, y_train)
viz.score(X_test, y_test)
```

If the visualizer is a final pipeline step, do not add downstream steps after
it. Yellowbrick score visualizers are meant to draw on `.score()`, not transform
features for later estimators.

## Saving, backend, and display failures

For scripts and automated agents:

```python
import matplotlib
matplotlib.use("Agg")
# import pyplot/yellowbrick after backend selection
```

Then save with:

```python
viz.show(outpath="plot.png", clear_figure=True)
```

If `outpath` is relative, it is relative to the current working directory. Create
parent directories first. If font warnings appear but non-empty PNGs are written,
treat them as display warnings, not classifier API failures.

## Validate after fixing

Run the bundled smoke helper from any directory:

```bash
python path/to/classification_smoke.py --outdir yellowbrick-classifier-smoke
```

It should write non-empty PNGs for classification report, confusion matrix,
ROC-AUC, precision-recall, class prediction error, discrimination threshold, and
class balance. If it fails at the first classifier visualizer with the type-check
message above, fix the dependency stack before debugging individual plots.
