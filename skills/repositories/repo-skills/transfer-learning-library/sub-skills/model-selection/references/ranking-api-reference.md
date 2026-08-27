# TLLib Ranking API Reference

This reference is self-contained for installed `tllib` usage. It covers the ranking metric functions used to select pretrained models before fine-tuning.

## Common array contract

Use NumPy arrays with one row per target-split sample. Keep all arrays in the **same sample order**.

| Symbol | Meaning | Shape | Notes |
| --- | --- | --- | --- |
| `N` | number of ranked samples | scalar | Use the same `N` for features, predictions, and labels. |
| `F` | feature dimension | scalar | Usually the activation before the source classifier head, flattened to 2-D. |
| `C_t` | target classes | scalar | TLLib infers this as `labels.max() + 1`; reindex labels to contiguous `0..C_t-1`. |
| `C_s` | source/pretraining classes | scalar | Number of source-head output classes in probabilities or predicted source labels. |
| `features` | extracted representation | `(N, F)` | Floating NumPy array; no NaN/inf; constant columns hurt covariance metrics. |
| `labels` / `targets` | target labels | `(N,)` | Integer target labels for classification; continuous values only for LogME regression. |
| `predictions` | source-head probabilities | `(N, C_s)` | Non-negative probabilities, typically softmax outputs. Rows should sum to 1. Do not pass logits. |
| `source_labels` | source-head class ids | `(N,)` | Usually `predictions.argmax(axis=1)` for NCE. |

Recommended preflight:

```python
import numpy as np

features = np.asarray(features, dtype=np.float64)
labels = np.asarray(labels, dtype=np.int64).reshape(-1)
assert features.ndim == 2 and labels.ndim == 1
assert features.shape[0] == labels.shape[0]
assert np.isfinite(features).all()
assert labels.min() >= 0
```

If target labels are not contiguous, remap them before calling TLLib:

```python
classes, labels0 = np.unique(labels, return_inverse=True)
labels0 = labels0.astype(np.int64)
```

## Import paths and signatures

| Metric | Import | Signature | Inputs | Higher is better? |
| --- | --- | --- | --- | --- |
| H-score | `from tllib.ranking import h_score` | `h_score(features, labels)` | `(N,F)` features, `(N,)` target labels | generally yes |
| Regularized H-score | `from tllib.ranking.hscore import regularized_h_score` | `regularized_h_score(features, labels)` | same as H-score | generally yes |
| LEEP | `from tllib.ranking import log_expected_empirical_prediction` | `log_expected_empirical_prediction(predictions, labels)` | `(N,C_s)` source probabilities, target labels | generally yes; values are often negative |
| NCE | `from tllib.ranking import negative_conditional_entropy` | `negative_conditional_entropy(source_labels, target_labels)` | `(N,)` source predicted classes, target labels | generally yes; closer to `0` is better |
| LogME | `from tllib.ranking import log_maximum_evidence` | `log_maximum_evidence(features, targets, regression=False, return_weights=False)` | features plus classification labels or regression targets | generally yes |
| TransRate | `from tllib.ranking.transrate import transrate` | `transrate(features, labels, eps=1e-4)` | features plus target labels | generally yes |

`regularized_h_score` and `transrate` are implemented in the package but are not part of the top-level `tllib.ranking.__all__` export in TLLib 0.4, so import them from their modules as shown.

## Metric details

### H-score

```python
from tllib.ranking import h_score
score = h_score(features, labels)
```

- Uses feature covariance and class-conditional feature means.
- Requires target labels and feature vectors.
- The implementation uses a pseudo-inverse, so it can return a value for singular covariance matrices, but the result can be unstable with too few samples, duplicate features, or very high-dimensional unnormalized features.
- Use the regularized variant when `N` is small compared with `F` or covariance warnings appear.

### Regularized H-score

```python
from tllib.ranking.hscore import regularized_h_score
score = regularized_h_score(features, labels)
```

- Uses Ledoit-Wolf shrinkage covariance and centers features internally.
- Needs `scikit-learn` available in the environment.
- More stable than vanilla H-score for small or correlated feature sets, but still needs at least a few samples per target class.

### LEEP

```python
from tllib.ranking import log_expected_empirical_prediction
score = log_expected_empirical_prediction(predictions, labels)
```

- Requires source-head **probability** predictions for every target sample.
- Convert logits with softmax before passing them:

```python
prob = np.exp(logits - logits.max(axis=1, keepdims=True))
prob = prob / prob.sum(axis=1, keepdims=True)
```

- Convert log-probabilities with `np.exp(log_probs)` and renormalize if needed.
- Every source column should have nonzero total probability; all-zero source classes can cause invalid division.

### NCE

```python
from tllib.ranking import negative_conditional_entropy
source_labels = predictions.argmax(axis=1)
score = negative_conditional_entropy(source_labels, labels)
```

- Uses hard source-class predictions and target labels.
- Values are non-positive in normal use; closer to `0` means lower conditional entropy and usually better transferability.
- TLLib masks unused source classes after forming the empirical distribution, but avoiding impossible or missing source labels makes debugging easier.

### LogME

```python
from tllib.ranking import log_maximum_evidence
score = log_maximum_evidence(features, labels)
score, weights = log_maximum_evidence(features, labels, return_weights=True)
```

- For classification, `labels` are integer target labels; the implementation trains one evidence calculation per target class.
- For regression:

```python
score = log_maximum_evidence(features, regression_targets, regression=True)
```

where `regression_targets` is `(N, C)` floating values.
- First calls can be slower because the package uses `numba` JIT compilation.
- Degenerate features or targets can make evidence updates unstable; inspect NaNs and remove constant columns if needed.

### TransRate

```python
from tllib.ranking.transrate import transrate
score = transrate(features, labels, eps=1e-4)
```

- Computes a coding-rate difference between all features and per-class features.
- Centers features internally.
- Tune `eps` only when the default produces numerical problems; compare candidates with the same `eps`.

## Minimal ranking helper

```python
import numpy as np
from tllib.ranking import h_score, log_expected_empirical_prediction, negative_conditional_entropy, log_maximum_evidence
from tllib.ranking.hscore import regularized_h_score
from tllib.ranking.transrate import transrate

features = np.load("features.npy")      # shape (N, F)
pred = np.load("predictions.npy")       # shape (N, C_s), probabilities
targets = np.load("targets.npy")        # shape (N,)

scores = {
    "h_score": h_score(features, targets),
    "regularized_h_score": regularized_h_score(features, targets),
    "logme": log_maximum_evidence(features, targets),
    "transrate": transrate(features, targets),
    "leep": log_expected_empirical_prediction(pred, targets),
    "nce": negative_conditional_entropy(pred.argmax(axis=1), targets),
}
print({k: float(v) for k, v in scores.items()})
```

Use the same target split and extraction layer for every candidate model. Do not compare scores computed from different target subsets, different preprocessing, or different feature layers.
