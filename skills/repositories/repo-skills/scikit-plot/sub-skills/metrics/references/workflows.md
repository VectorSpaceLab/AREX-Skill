# Metrics workflows

Use these recipes when you have labels, predictions, probabilities, or cluster labels and want a scikit-plot diagnostic figure.

## Confusion matrix

```python
import matplotlib.pyplot as plt
import scikitplot as skplt
from sklearn.datasets import load_digits
from sklearn.ensemble import RandomForestClassifier

X, y = load_digits(return_X_y=True)
clf = RandomForestClassifier(n_estimators=32, random_state=0, n_jobs=1).fit(X, y)
y_pred = clf.predict(X)

fig, ax = plt.subplots(figsize=(6, 6))
skplt.metrics.plot_confusion_matrix(y, y_pred, normalize=True, ax=ax)
```

Use `labels`, `true_labels`, and `pred_labels` only after you know the class order you want. Invalid or duplicate display labels raise validation errors.

## ROC and precision-recall curves

```python
import scikitplot as skplt
from sklearn.datasets import load_iris
from sklearn.naive_bayes import GaussianNB

X, y = load_iris(return_X_y=True)
clf = GaussianNB().fit(X, y)
y_probas = clf.predict_proba(X)

roc_ax = skplt.metrics.plot_roc(y, y_probas, plot_micro=True, plot_macro=True)
pr_ax = skplt.metrics.plot_precision_recall(y, y_probas, plot_micro=True)
```

Use the current `plot_roc` and `plot_precision_recall` functions for new code. The older `plot_roc_curve` and `plot_precision_recall_curve` names still exist in this snapshot but are deprecated.

## Binary probability diagnostics

KS, cumulative gain, lift, and calibration curves are binary workflows. Use a binary target and a two-column probability matrix where column 1 is the positive-class probability.

```python
import scikitplot as skplt
from sklearn.datasets import load_breast_cancer
from sklearn.linear_model import LogisticRegression

X, y = load_breast_cancer(return_X_y=True)
clf = LogisticRegression(max_iter=400, solver='liblinear').fit(X, y)
y_probas = clf.predict_proba(X)

ks_ax = skplt.metrics.plot_ks_statistic(y, y_probas)
gain_ax = skplt.metrics.plot_cumulative_gain(y, y_probas)
lift_ax = skplt.metrics.plot_lift_curve(y, y_probas)
```

For calibration, pass a list of probability arrays or score vectors. On modern scikit-learn, keep binary labels numeric (`0/1` or `-1/1`) because the wrapped `calibration_curve` cannot infer `pos_label` from arbitrary string labels:

```python
skplt.metrics.plot_calibration_curve(
    y,
    probas_list=[y_probas],
    clf_names=['Logistic Regression'],
    n_bins=8,
)
```

## Silhouette analysis

`plot_silhouette` consumes already-computed cluster labels. It does not fit or sweep a clusterer; use `../../clustering/SKILL.md` for elbow curves.

```python
import scikitplot as skplt
from sklearn.cluster import KMeans
from sklearn.datasets import load_iris

X, _ = load_iris(return_X_y=True)
labels = KMeans(n_clusters=3, random_state=0, n_init=10).fit_predict(X)
skplt.metrics.plot_silhouette(X, labels)
```

## Axes reuse and automation

For notebooks or report figures, create axes first and pass `ax=ax`. For automation, set a non-interactive backend and close figures after checks:

```python
import matplotlib
matplotlib.use('Agg', force=True)
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
out_ax = skplt.metrics.plot_confusion_matrix([0, 1], [1, 0], ax=ax)
assert out_ax is ax
plt.close(fig)
```

Run the bundled smoke helper for a broader family check:

```bash
python scripts/metrics_smoke.py
```
