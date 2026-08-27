# Thresholding and Score Combination

This reference covers operating tasks that happen after detectors produce anomaly scores: turning scores into labels with PyThresh-backed thresholders and combining multiple detector score streams.

## PyOD Default Thresholding

Most PyOD detectors inherit `BaseDetector` behavior:

- `contamination` may be a float in `(0, 0.5]`.
- After `fit`, PyOD sets `decision_scores_`, `threshold_`, and `labels_`.
- For numeric contamination, `threshold_` is the percentile at `100 * (1 - contamination)` over training `decision_scores_`.
- `predict(X)` computes `decision_function(X)` and returns `(score > threshold_).astype(int)`.
- `predict_proba(X, method="linear"|"unify")` converts scores to probabilities.
- `predict_confidence(X)` and `predict_with_rejection(X, ...)` rely on fitted scores and threshold state.

Operational check:

```python
clf.fit(X_train)
assert clf.decision_scores_.shape == (X_train.shape[0],)
assert clf.labels_.shape == (X_train.shape[0],)
assert isinstance(float(clf.threshold_), float)
```

## PyThresh-Backed Thresholding

`pyod.models.thresholds` exposes factory functions that return PyThresh thresholder objects. These can be passed as the detector's `contamination` argument instead of a numeric contamination fraction.

```python
from pyod.models.kde import KDE
from pyod.models.thresholds import FILTER, IQR, ZSCORE

clf = KDE(contamination=FILTER())
clf.fit(X_train)
labels = clf.predict(X_test)
```

When `contamination` is a PyThresh object, `BaseDetector._process_decision_scores()` calls:

```python
self.contamination.fit(self.decision_scores_)
self.labels_ = self.contamination.labels_
self.threshold_ = self.contamination.thresh_
```

and `predict` delegates to:

```python
prediction = self.contamination.predict(pred_score)
```

The `pythresh` package is optional. Install it explicitly:

```bash
pip install 'pyod[pythresh]'
# or: pip install pythresh
```

## Threshold Factories

The module provides these factory function names:

| Function | Family / meaning |
|---|---|
| `AUCP` | Area Under Curve Percentage |
| `BOOT` | Bootstrapping |
| `CHAU` | Chauvenet's Criterion |
| `CLF` | Trained linear classifier |
| `CLUST` | Clustering-based thresholding |
| `CPD` | Change point detection |
| `DECOMP` | Decomposition-based thresholding |
| `DSN` | Distance shift from normal |
| `EB` | Elliptical boundary |
| `FGD` | Fixed gradient descent |
| `FILTER` | Filtering-based thresholding |
| `FWFM` | Full width at full minimum |
| `GAMGMM` | Gamma/GMM posterior contamination estimate |
| `GESD` | Generalized Extreme Studentized Deviate |
| `HIST` | Histogram-based thresholding |
| `IQR` | Inter-quartile region |
| `KARCH` | Karcher mean |
| `MAD` | Median absolute deviation |
| `MCST` | Monte Carlo Shapiro Tests |
| `META` | Meta-model thresholding |
| `MIXMOD` | Normal/non-normal mixture models |
| `MOLL` | Friedrichs' mollifier |
| `MTT` | Modified Thompson Tau test |
| `OCSVM` | One-class SVM thresholding |
| `QMCD` | Quasi-Monte Carlo discrepancy |
| `REGR` | Regression-based thresholding |
| `VAE` | VAE thresholder; needs torch through pythresh/PyTorch stack |
| `WIND` | Topological winding number |
| `YJ` | Yeo-Johnson transformation |
| `ZSCORE` | Z-score thresholding |

Most factories accept `**kwargs` and forward them to the corresponding `pythresh.thresholds.*` class. Common arguments include `random_state`; some methods expose method-specific arguments such as `FILTER(method=...)`, `CLUST(method=...)`, or `GAMGMM(skip=True)`.

## Thresholding Validation Pattern

Use this when a task asks whether thresholding worked, not just whether `fit` returned:

```python
import numpy as np

clf.fit(X_train)
train_labels = clf.labels_
test_labels = clf.predict(X_test)
test_scores = clf.decision_function(X_test)

assert train_labels.shape == (X_train.shape[0],)
assert test_labels.shape == (X_test.shape[0],)
assert test_scores.shape == (X_test.shape[0],)
assert np.isfinite(test_scores).all()
assert set(np.unique(test_labels)).issubset({0, 1})
```

If a PyThresh method returns no anomalies on a tiny or easy synthetic set, do not immediately treat that as an import failure. Validate shapes, finite scores, and whether the selected threshold family is appropriate for the score distribution.

## Score Combination API

`pyod.models.combination` wraps functions from the optional `combo` package:

```python
from pyod.models.combination import (
    average, maximization, median, majority_vote, aom, moa
)
```

Input shape is generally a 2-D NumPy array:

```text
scores.shape == (n_samples, n_estimators)
```

Functions:

| Function | Use | Key arguments | Output |
|---|---|---|---|
| `average(scores, estimator_weights=None)` | Mean or weighted mean of detector scores | optional weights shape compatible with estimators | `(n_samples,)` |
| `maximization(scores)` | Maximum score across detectors | none | `(n_samples,)` |
| `median(scores)` | Median score across detectors | none | `(n_samples,)` |
| `majority_vote(scores, weights=None)` | Vote over binary labels rather than continuous scores | optional weights | `(n_samples,)` |
| `aom(scores, n_buckets=5, method="static", bootstrap_estimators=False, random_state=None)` | Average of Maximum: split estimators into buckets, max within each, average bucket maxima | `n_buckets`, `method`, bootstrap, seed | `(n_samples,)` |
| `moa(scores, n_buckets=5, method="static", bootstrap_estimators=False, random_state=None)` | Maximization of Average: split into buckets, average within each, max bucket averages | `n_buckets`, `method`, bootstrap, seed | `(n_samples,)` |

Install `combo` before importing this module:

```bash
pip install 'pyod[combo]'
# or: pip install combo
```

In the verified base environment, importing `pyod.models.combination` without `combo` raised `ModuleNotFoundError: No module named 'combo'` after printing an install hint. Treat that as an optional-extra issue.

## Combination Workflow

The key operational requirement is score normalization. Different detectors may produce scores on very different scales.

```python
import numpy as np
from pyod.models.knn import KNN
from pyod.models.combination import average, maximization, aom, moa, median
from pyod.utils.data import generate_data
from pyod.utils.utility import standardizer

X_train, X_test, y_train, y_test = generate_data(
    n_train=200, n_test=100, contamination=0.1, random_state=42
)
X_train_norm, X_test_norm = standardizer(X_train, X_test)

k_list = [10, 20, 30, 40, 50]
train_scores = np.zeros((X_train.shape[0], len(k_list)))
test_scores = np.zeros((X_test.shape[0], len(k_list)))

for i, k in enumerate(k_list):
    clf = KNN(n_neighbors=k, method="largest").fit(X_train_norm)
    train_scores[:, i] = clf.decision_scores_
    test_scores[:, i] = clf.decision_function(X_test_norm)

train_scores_norm, test_scores_norm = standardizer(train_scores, test_scores)
combined = {
    "average": average(test_scores_norm),
    "max": maximization(test_scores_norm),
    "median": median(test_scores_norm),
    "aom": aom(test_scores_norm, n_buckets=5, random_state=42),
    "moa": moa(test_scores_norm, n_buckets=5, random_state=42),
}
for name, values in combined.items():
    assert values.shape == (X_test.shape[0],), name
    assert np.isfinite(values).all(), name
```

## AOM/MOA Bucket Pitfall

For static AOM/MOA without bootstrapping, `n_buckets` must be compatible with the number of estimator columns. PyOD's tests assert a `ValueError` when using 6 estimator columns with `n_buckets=5` in static/no-repeat mode.

Recovery: choose a bucket count that divides or can be validly partitioned by the number of estimator columns, reduce `n_buckets`, or use dynamic/bootstrapped settings intentionally.

## Result Validation for Combined Scores

After combination:

1. Check shape: `(n_samples,)`.
2. Check finite values.
3. Confirm score orientation: PyOD convention is higher means more abnormal. If one base detector has the opposite convention, invert or standardize appropriately before combination.
4. If converting to labels, choose an explicit thresholding rule and document it. Combination functions return scores, not labels, except `majority_vote` over label-like inputs.
5. Recompute evaluation metrics from the combined scores; do not assume the combination improves every dataset.
