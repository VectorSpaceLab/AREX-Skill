# Classifier Visualizer Workflows

Use these recipes for Yellowbrick classification diagnostics. For shared
Matplotlib lifecycle, style, axes, and headless patterns, also read
[visualizer patterns](../../../references/visualizer-patterns.md). For package
and display failures, read root [troubleshooting](../../../references/troubleshooting.md).

## 1. Common classifier report suite

Use this when a user asks for a compact diagnostic bundle after fitting a
classifier.

```python
import matplotlib
matplotlib.use("Agg")

from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from yellowbrick.classifier import (
    ClassificationReport,
    ConfusionMatrix,
    ClassPredictionError,
)

outdir = Path("classifier-report")
outdir.mkdir(parents=True, exist_ok=True)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=42
)
classes = ["negative", "positive"]  # replace with labels matching y order

model = LogisticRegression(max_iter=1000)

for name, factory in {
    "classification_report": lambda: ClassificationReport(
        model, classes=classes, support=True
    ),
    "confusion_matrix": lambda: ConfusionMatrix(
        LogisticRegression(max_iter=1000), classes=classes, percent=False
    ),
    "class_prediction_error": lambda: ClassPredictionError(
        LogisticRegression(max_iter=1000), classes=classes
    ),
}.items():
    viz = factory()
    viz.fit(X_train, y_train)
    score = viz.score(X_test, y_test)
    viz.show(outpath=str(outdir / f"{name}.png"), clear_figure=True)
    print(name, score)
```

Notes:

- Use separate estimator instances when creating multiple visualizers unless you
  deliberately want to share an already-fitted estimator.
- Use `support=True`, `support='count'`, or `support='percent'` on
  `ClassificationReport` to expose class support.
- Use `percent=True` on `ConfusionMatrix` only when you want row-normalized
  percentages for all classes.

## 2. Quick one-liners for exploration

Quick methods are useful in notebooks or small scripts:

```python
from yellowbrick.classifier import classification_report, confusion_matrix

viz = classification_report(
    estimator,
    X_train,
    y_train,
    X_test,
    y_test,
    classes=classes,
    support=True,
    show=False,
)
viz.show(outpath="classification_report.png", clear_figure=True)

cm = confusion_matrix(
    estimator,
    X_train,
    y_train,
    X_test,
    y_test,
    classes=classes,
    percent=True,
    show=False,
)
cm.show(outpath="confusion_matrix.png", clear_figure=True)
```

Quick-method rules:

- For classifier score quick methods, pass both `X_test` and `y_test`, or pass
  neither. Passing only one test array raises an error.
- `show=False` finalizes without opening a GUI; save with the returned
  visualizer's `show(outpath=...)`.
- If saving and resource cleanup are important, the explicit class lifecycle is
  clearer than quick methods.

## 3. Binary ROC-AUC

Use `ROCAUC` when you need sensitivity/specificity tradeoffs.

```python
from sklearn.linear_model import LogisticRegression
from yellowbrick.classifier import ROCAUC

model = LogisticRegression(max_iter=1000)
viz = ROCAUC(model, classes=["not_spam", "spam"], binary=True)
viz.fit(X_train, y_train)
auc = viz.score(X_test, y_test)
viz.show(outpath="roc_auc_binary.png", clear_figure=True)
print("AUC", auc)
```

Decision guidance:

- `binary=True` is the simplest setting for one binary ROC curve.
- If the estimator has `predict_proba`, Yellowbrick uses it before
  `decision_function`.
- For binary estimators with one-dimensional `decision_function` output,
  default micro/macro curves are not defined. Use `binary=True` or
  `micro=False, macro=False`.
- If the estimator exposes only `predict`, choose a different model, set
  `SVC(probability=True)`, or use `CalibratedClassifierCV`.

## 4. Multiclass ROC-AUC

Use multiclass ROC when the user needs one-vs-rest class separation diagnostics.

```python
from sklearn.linear_model import LogisticRegression
from yellowbrick.classifier import ROCAUC

model = LogisticRegression(max_iter=1000, multi_class="auto")
viz = ROCAUC(
    model,
    classes=["win", "loss", "draw"],
    micro=True,
    macro=True,
    per_class=True,
)
viz.fit(X_train, y_train)
viz.score(X_test, y_test)
viz.show(outpath="roc_auc_multiclass.png", clear_figure=True)
```

Keep at least one of `micro`, `macro`, or `per_class` true. Turn off curves to
reduce clutter, not to change the underlying fitted classifier.

## 5. Binary precision-recall

Use PR curves when false positives/false negatives and class imbalance matter
more than ROC summaries.

```python
from sklearn.linear_model import LogisticRegression
from yellowbrick.classifier import PrecisionRecallCurve

viz = PrecisionRecallCurve(
    LogisticRegression(max_iter=1000),
    classes=["majority", "minority"],
    iso_f1_curves=True,
)
viz.fit(X_train, y_train)
ap = viz.score(X_test, y_test)
viz.show(outpath="precision_recall_binary.png", clear_figure=True)
print("average precision", ap)
```

`PrecisionRecallCurve` uses `decision_function` before `predict_proba`, and for
binary `predict_proba` it uses the positive-class column.

## 6. Multiclass precision-recall

For a micro-average multiclass PR curve:

```python
from yellowbrick.classifier import PrecisionRecallCurve

viz = PrecisionRecallCurve(model, classes=classes, micro=True, per_class=False)
viz.fit(X_train, y_train)
viz.score(X_test, y_test)
viz.show(outpath="precision_recall_micro.png", clear_figure=True)
```

For per-class multiclass PR curves:

```python
viz = PrecisionRecallCurve(
    model,
    classes=classes,
    per_class=True,
    micro=False,
    fill_area=False,
)
viz.fit(X_train, y_train)
viz.score(X_test, y_test)
viz.show(outpath="precision_recall_per_class.png", clear_figure=True)
```

Yellowbrick adapts multiclass PR with a one-vs-rest classifier internally. If
`micro=True` and `per_class=True`, Yellowbrick warns that micro is ignored.

## 7. Threshold tuning for binary classifiers

Use `DiscriminationThreshold` when the user wants to tune the probability or
score threshold for a binary positive class.

```python
from sklearn.naive_bayes import BernoulliNB
from yellowbrick.classifier import DiscriminationThreshold

viz = DiscriminationThreshold(
    BernoulliNB(),
    n_trials=10,      # raise for a publication-quality curve
    cv=0.2,
    fbeta=1.0,
    argmax="fscore",
    random_state=42,
)
viz.fit(X_binary, y_binary)
viz.show(outpath="discrimination_threshold.png", clear_figure=True)
```

Guidance:

- The target must be binary. Multiclass targets raise `multiclass format is not
  supported`.
- The estimator must expose `predict_proba` or `decision_function`.
- `n_trials` multiplies the number of split/fit/evaluate runs. Use small values
  in CI and larger values only when runtime allows.
- Use `exclude=["queue_rate"]` or similar to reduce plot clutter.
- Use `argmax=None` when no single metric should be annotated.

## 8. Class balance before scoring

Use `ClassBalance` before model fitting or immediately after train/test split to
explain class support.

```python
from sklearn.model_selection import train_test_split
from yellowbrick.target import ClassBalance

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=42
)

viz = ClassBalance(labels=classes)
viz.fit(y_train, y_test)
viz.show(outpath="class_balance.png", clear_figure=True)
```

Use balance mode with one target array:

```python
viz = ClassBalance(labels=classes)
viz.fit(y)
viz.show(outpath="class_balance_all.png", clear_figure=True)
```

ClassBalance does not accept `X`; current Yellowbrick expects
`fit(y_train, y_test=None)`. If the target is encoded, make sure `labels` matches
the unique target classes.

## 9. Pipelines

When preprocessing is required, wrap the complete pipeline as the estimator:

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from yellowbrick.classifier import ClassificationReport, ROCAUC

pipe = Pipeline([
    ("scale", StandardScaler()),
    ("clf", LogisticRegression(max_iter=1000)),
])

report = ClassificationReport(pipe, classes=classes, support=True)
report.fit(X_train, y_train)
report.score(X_test, y_test)
report.show(outpath="pipeline_report.png", clear_figure=True)

roc = ROCAUC(pipe, classes=classes, binary=True)
roc.fit(X_train, y_train)
roc.score(X_test, y_test)
roc.show(outpath="pipeline_roc.png", clear_figure=True)
```

A visualizer can also be the final step in a scikit-learn pipeline for tests or
custom orchestration, but it should not be placed before downstream transformers
or estimators.

## 10. Already-fitted estimators

Use `is_fitted=True` when a user hands you a model that must not be refit:

```python
viz = ConfusionMatrix(fitted_model, classes=classes, is_fitted=True)
viz.fit(X_train, y_train)        # learns classes for the visualizer
viz.score(X_test, y_test)        # uses fitted_model.predict
viz.show(outpath="confusion_from_fitted_model.png", clear_figure=True)
```

Caveats:

- Still call `viz.fit(X_train, y_train)` so the visualizer can learn class
  metadata unless the visualizer has a specialized flow.
- If the fitted estimator's `classes_` do not match the visualizer's fitted
  target labels, Yellowbrick may warn or ignore class counts.
- For ROC/PR/threshold, verify the fitted model still exposes the needed score
  method after any pipeline wrapping.

## 11. Headless smoke check

Run the bundled helper from any working directory:

```bash
python path/to/classification_smoke.py --outdir yellowbrick-classifier-smoke
```

The helper options are:

- `--outdir PATH`: directory to create and populate with PNG files.
- `--n-samples N`: number of synthetic samples, default `240`.
- `--random-state SEED`: deterministic seed, default `42`.

Expected outputs include:

- `classification_report.png`
- `confusion_matrix.png`
- `roc_auc_binary.png`
- `precision_recall_binary.png`
- `class_prediction_error.png`
- `discrimination_threshold.png`
- `class_balance.png`

If the smoke fails with a normal sklearn classifier being rejected as "not a
classifier", treat it as a Yellowbrick/scikit-learn compatibility issue and see
[troubleshooting](troubleshooting.md).
