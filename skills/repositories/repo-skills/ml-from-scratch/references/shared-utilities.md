# Shared utilities

Use this reference when a task depends on `mlfromscratch.utils` preprocessing, batching, metrics, kernels, or plotting helpers. These utilities are used by several sub-skills and have repo-specific behavior.

## Import surface

```python
from mlfromscratch.utils import (
    shuffle_data, batch_iterator, divide_on_feature, polynomial_features,
    get_random_subsets, normalize, standardize, train_test_split,
    k_fold_cross_validation_sets, to_categorical, to_nominal, make_diagonal,
    calculate_entropy, mean_squared_error, calculate_variance,
    calculate_std_dev, euclidean_distance, accuracy_score,
    calculate_covariance_matrix, calculate_correlation_matrix, Plot,
)
```

Kernel helpers for SVM live under `mlfromscratch.utils.kernels` and include `linear_kernel`, `polynomial_kernel`, and `rbf_kernel`.

## Data manipulation helpers

| Helper | Signature | Use | Cautions |
| --- | --- | --- | --- |
| `shuffle_data` | `shuffle_data(X, y, seed=None)` | Jointly shuffle feature and target arrays. | `seed=0` is treated as false by the implementation; use a positive integer for deterministic shuffles. |
| `batch_iterator` | `batch_iterator(X, y=None, batch_size=64)` | Yield mini-batches for neural-network training. | Last batch may be smaller than `batch_size`. |
| `divide_on_feature` | `divide_on_feature(X, feature_i, threshold)` | Split rows by numeric `>= threshold` or categorical equality. | Current NumPy can reject the returned heterogeneous partition array when split sizes differ; tree-family models inherit this issue. |
| `polynomial_features` | `polynomial_features(X, degree)` | Expand features using combinations with replacement up to `degree`. | `X` must be 2-D. Feature count grows quickly with degree. |
| `get_random_subsets` | `get_random_subsets(X, y, n_subsets, replacements=True)` | Bootstrap/subsample helper for ensembles. | Expects `y` as a 1-D vector. |
| `normalize` | `normalize(X, axis=-1, order=2)` | L2-normalize samples or features. | Zero norms are set to one to avoid divide-by-zero. Use deliberately with clustering and SVM. |
| `standardize` | `standardize(X)` | Column-wise mean/std scaling. | It mutates the passed array when possible. Copy first if the original data must be preserved. |
| `train_test_split` | `train_test_split(X, y, test_size=0.5, shuffle=True, seed=None)` | Simple train/test split. | Returns `(X_train, X_test, y_train, y_test)` and uses a package-specific split formula. |
| `k_fold_cross_validation_sets` | `k_fold_cross_validation_sets(X, y, k, shuffle=True)` | Build k folds. | Returns a NumPy array of fold objects; leftover appends in the implementation are not assigned back, so inspect folds before relying on exact counts. |

## Encoding helpers

| Helper | Signature | Use | Cautions |
| --- | --- | --- | --- |
| `to_categorical` | `to_categorical(x, n_col=None)` | Convert non-negative integer labels to one-hot matrix. | Labels must be integer-coded from `0` upward. Pass `n_col` when classes are missing from a tiny split. |
| `to_nominal` | `to_nominal(x)` | Convert one-hot or class-score rows to class indices. | Uses `argmax(axis=1)`; do not use for multilabel outputs. |
| `make_diagonal` | `make_diagonal(x)` | Convert a vector to a diagonal matrix, used by logistic regression. | Avoid for large vectors because it allocates dense square matrices. |

## Metrics and math helpers

| Helper | Signature | Use | Cautions |
| --- | --- | --- | --- |
| `calculate_entropy` | `calculate_entropy(y)` | Entropy for classification trees. | Labels should be discrete. |
| `mean_squared_error` | `mean_squared_error(y_true, y_pred)` | Regression loss/metric. | Flatten predictions first when model returns lists or column vectors. |
| `calculate_variance` | `calculate_variance(X)` | Per-feature variance. | Expects 2-D numeric arrays. |
| `calculate_std_dev` | `calculate_std_dev(X)` | Per-feature standard deviation. | Derived from `calculate_variance`. |
| `euclidean_distance` | `euclidean_distance(x1, x2)` | Distance for KNN/clustering. | Pure Python loop; fine for small educational examples. |
| `accuracy_score` | `accuracy_score(y_true, y_pred)` | Fraction of exact label matches. | Compare labels in the same encoding; do not score `{-1, 1}` predictions against `0/1` truth. |
| `calculate_covariance_matrix` | `calculate_covariance_matrix(X, Y=None)` | Covariance for PCA/GMM/LDA-style workflows. | Uses `1/(n_samples - 1)`; need at least two samples. |
| `calculate_correlation_matrix` | `calculate_correlation_matrix(X, Y=None)` | Correlation matrix. | Constant features can produce divide-by-zero or NaNs. |

## Plot helper

`Plot` supports regression plotting and PCA-based 2-D/3-D visualization. It is useful for interactive exploration, but automated agent checks should avoid display-dependent calls.

Headless pattern:

```python
import os
os.environ.setdefault("MPLBACKEND", "Agg")
```

Set the backend before importing Matplotlib or any package module that imports plotting. In smoke checks, prefer numeric assertions over `plt.show()`.

## Shape and encoding mini-checklist

Before routing to a model-specific sub-skill, normalize the shared data contract:

```python
import numpy as np

X = np.asarray(raw_X, dtype=float)
if X.ndim == 1:
    X = X.reshape(-1, 1)
y = np.asarray(raw_y)
assert X.shape[0] == y.shape[0]
```

Then choose target encoding by owner:

- Regression: 1-D numeric `y`.
- Logistic regression/LDA: binary `0/1`.
- SVM/Adaboost: binary `{-1, 1}`.
- KNN/NaiveBayes/tree/boosting: nominal integer labels.
- Neural `CrossEntropy`: one-hot `to_categorical(y_int, n_col=n_classes)`.
