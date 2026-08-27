# Classic Detector API Reference

Read this when you need the common API surface that most PyOD tabular detectors
share. Facts here are distilled from `pyod.models.base.BaseDetector`, public
examples, and installed-package signature inspection.

## Common fitted detector contract

All standard outlier detectors subclass or follow `BaseDetector` conventions:

```python
clf = Detector(contamination=0.1, ...)
clf.fit(X_train)                     # returns self
scores_train = clf.decision_scores_  # shape (n_train,), higher = more abnormal
labels_train = clf.labels_           # 0=inlier, 1=outlier
threshold = clf.threshold_           # threshold derived from contamination
scores_test = clf.decision_function(X_test)
labels_test = clf.predict(X_test)
```

Common methods:

| Method | Purpose | Notes |
|---|---|---|
| `fit(X, y=None)` | Fit on training samples. | In unsupervised detectors `y` is ignored; `X` should be numeric with shape `(n_samples, n_features)`. |
| `decision_function(X)` | Score new samples. | Higher scores indicate more abnormal samples. |
| `predict(X, return_confidence=False)` | Return binary labels. | Uses `threshold_`; returns `(labels, confidence)` if requested. |
| `predict_proba(X, method="linear"|"unify")` | Convert scores to two-column probabilities. | Useful for ranking confidence, not calibrated class probabilities. |
| `predict_confidence(X)` | Confidence of a prediction under perturbation logic. | Requires fitted detector. |
| `predict_with_rejection(X, T=32, ...)` | Return labels with possible `-2` rejection. | Use when abstaining on uncertain samples is acceptable. |
| `get_params()` / `set_params()` | sklearn-style parameter inspection and updates. | Nested parameters use `component__parameter`. |

Common attributes after `fit`:

- `decision_scores_`: raw anomaly scores for training samples.
- `threshold_`: cutoff used to produce labels, normally percentile based on
  `contamination`.
- `labels_`: training labels where `1` means outlier/anomaly and `0` means
  inlier.
- `_classes`: usually 2 unless a supervised/label-aware path sets otherwise.

## Verified representative signatures

Installed inspection confirmed these signatures for common routes:

```text
IForest(n_estimators=100, max_samples='auto', contamination=0.1,
        max_features=1.0, bootstrap=False, n_jobs=1, behaviour='old',
        random_state=None, verbose=0)

KNN(contamination=0.1, n_neighbors=5, method='largest', radius=1.0,
    algorithm='auto', leaf_size=30, metric='minkowski', p=2,
    metric_params=None, n_jobs=1)
```

Use `inspect.signature(Detector)` in the user's environment when a task depends
on an exact detector-specific parameter; PyOD has many detectors and not every
constructor uses `random_state` or `n_jobs`.

## Data helper signatures and returns

`pyod.utils.data.generate_data` returns by default:

```python
X_train, X_test, y_train, y_test = generate_data(
    n_train=1000, n_test=500, n_features=2,
    contamination=0.1, train_only=False, random_state=None,
)
```

Important options:

- `behaviour="new"` is the default and returns `X_train, X_test, y_train,
  y_test`. `behaviour="old"` is deprecated and returns a different order.
- `train_only=True` returns `X_train, y_train`.
- `n_nan` and `n_inf` can inject invalid values for testing error handling.

Other useful helpers:

- `generate_data_clusters(...)`: synthetic clustered data with global/local
  outlier structure.
- `generate_data_categorical(...)`: categorical string fixtures; encode before
  fitting ordinary detectors.
- `get_outliers_inliers(X, y)`: split ground truth into outlier and inlier
  arrays.
- `check_consistent_shape(...)`: validate train/test feature and label lengths.
- `evaluate_print(name, y_true, raw_scores)`: prints ROC-AUC and precision at n.

## Score interpretation contract

- PyOD's convention is **higher score = more abnormal**.
- `decision_scores_` and `decision_function` outputs are raw detector-specific
  scores. Compare ranks/percentiles more readily than absolute values across
  detector families.
- `labels_` and `predict` use the detector's threshold. If contamination is
  wrong, labels can be systematically too broad or too narrow even when ranking
  is useful.
- `predict_proba` maps detector scores to `[normal, outlier]` style columns but
  does not make unsupervised results ground-truth calibrated.

## Optional-extra warning

Some files under `pyod.models` import optional packages. Base PyOD installs do
not include `combo`, `suod`, `xgboost`, `torch`, `torch_geometric`, or
`pythresh`. If a detector import fails, check whether that detector belongs in
`model-operations` or `specialized-modalities` before treating it as a PyOD bug.
