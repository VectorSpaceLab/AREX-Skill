# Classical estimator API reference

## Purpose

Read this when a task needs exact import paths, constructor defaults, labels, outputs, or estimator-specific caveats for MLAlgorithms supervised models. Facts here are derived from package source and live signature inspection for distribution `mla` version `0.0.1`.

## Shared estimator contract

Most estimators inherit `BaseEstimator`:

- `fit(X, y=None)` stores NumPy-converted inputs and records `n_samples` and `n_features`.
- Supervised estimators require `y`; unsupervised estimators set `y_required = False` in their own modules.
- `predict(X)` converts `X` to a NumPy array and calls the estimator's `_predict` implementation. Fit-required estimators must call `fit` first.
- Empty feature arrays raise `ValueError("Got an empty matrix.")`; missing target arrays for supervised estimators raise `ValueError("Missed required argument y")`.

Use 2D feature matrices for normal tabular models. One-dimensional input handling is minimal and can set surprising `n_features` values, so reshape single-feature data as `(n_samples, 1)`.

## Linear models

```python
from mla.linear_models import LinearRegression, LogisticRegression
```

| Class | Signature | Target/output | Notes |
| --- | --- | --- | --- |
| `LinearRegression` | `LinearRegression(lr=0.001, penalty='None', C=0.01, tolerance=0.0001, max_iters=1000)` | continuous `y`; `predict` returns numeric vector | Uses autograd gradient descent on mean squared error. Adds an intercept column internally. |
| `LogisticRegression` | same constructor | binary `y`; `predict` returns sigmoid probabilities, not hard labels | Convert to labels with a threshold when metrics require classes. Uses binary cross entropy. |

`penalty` is checked against the lowercase strings `"l1"` and `"l2"`; any other value is treated as no regularization. `C` is the regularization coefficient. Convergence is based on the norm of successive cost changes being smaller than `tolerance`.

## K-nearest neighbors

```python
from mla.knn import KNNClassifier, KNNRegressor
```

| Class | Signature | Target/output | Notes |
| --- | --- | --- | --- |
| `KNNClassifier` | `KNNClassifier(k=5, distance_func=scipy.spatial.distance.euclidean)` | labels; `predict` returns most common label among neighbors | Ties are arbitrary because `Counter(...).most_common(1)` is used. |
| `KNNRegressor` | `KNNRegressor(k=5, distance_func=scipy.spatial.distance.euclidean)` | continuous target; `predict` returns neighbor-target mean | `k=0` means use all training examples because the implementation stores `None`. |

Any `distance_func(a, b)` callable may be supplied. For reproducible comparisons, standardize features before fitting.

## Naive Bayes

```python
from mla.naive_bayes import NaiveBayesClassifier
```

`NaiveBayesClassifier()` is a Gaussian binary classifier. `fit(X, y)` asserts that sorted unique labels are exactly `[0, 1]`. `predict(X)` returns a two-column probability array normalized with softmax over class log-likelihoods.

Avoid features with zero variance inside a class; the implementation computes a Gaussian PDF with variance in the denominator and does not add smoothing.

## SVM and kernels

```python
from mla.svm.svm import SVM
from mla.svm.kernerls import Linear, Poly, RBF
```

The kernel module name is intentionally spelled `kernerls` in this package.

| Object | Signature | Notes |
| --- | --- | --- |
| `SVM` | `SVM(C=1.0, kernel=None, tol=0.001, max_iter=100)` | Simplified SMO optimizer. Default kernel is `Linear()`. Labels must be `-1` and `1` for margin calculations. |
| `Linear` | `Linear()` | Computes `np.dot(x, y.T)`. |
| `Poly` | `Poly(degree=2)` | Computes polynomial dot product power. |
| `RBF` | `RBF(gamma=0.1)` | Uses `scipy.spatial.distance.cdist` and returns a flattened radial-basis vector. |

`predict(X)` returns signed class labels from `np.sign`. SVM training is quadratic in examples and can be slow compared with the other smoke workflows.

## Random forests

```python
from mla.ensemble.random_forest import RandomForestClassifier, RandomForestRegressor
# also exported from mla.ensemble import RandomForestClassifier, RandomForestRegressor
```

| Class | Signature | Output | Notes |
| --- | --- | --- | --- |
| `RandomForestClassifier` | `RandomForestClassifier(n_estimators=10, max_features=None, min_samples_split=10, max_depth=None, criterion='entropy')` | class-probability rows; use `argmax(axis=1)` for labels | Only `criterion='entropy'` is accepted. |
| `RandomForestRegressor` | `RandomForestRegressor(n_estimators=10, max_features=None, min_samples_split=10, max_depth=None, criterion='mse')` | numeric vector | Only `criterion='mse'` is accepted. |

If `max_features` is `None`, it becomes `int(np.sqrt(X.shape[1]))`. If you pass it explicitly, it must be strictly less than the number of input features because the source asserts `X.shape[1] > max_features`.

## Gradient boosting

```python
from mla.ensemble.gbm import GradientBoostingClassifier, GradientBoostingRegressor
```

| Class | Signature | Output | Notes |
| --- | --- | --- | --- |
| `GradientBoostingClassifier` | `GradientBoostingClassifier(n_estimators, learning_rate=0.1, max_features=10, max_depth=2, min_samples_split=10)` | logistic-transformed scores in `(0, 1)` | Converts `{0, 1}` labels to `{-1, 1}` internally. |
| `GradientBoostingRegressor` | `GradientBoostingRegressor(n_estimators, learning_rate=0.1, max_features=10, max_depth=2, min_samples_split=10)` | numeric vector | Uses least-squares gradients. |

The tree learner samples `max_features` feature indices, so keep `max_features <= X.shape[1]`.

## Factorization machines

```python
from mla.fm import FMRegressor, FMClassifier
```

| Class | Signature | Status |
| --- | --- | --- |
| `FMRegressor` | `FMRegressor(n_components=10, max_iter=100, init_stdev=0.1, learning_rate=0.01, reg_v=0.1, reg_w=0.5, reg_w0=0.0)` | Experimental in this version. |
| `FMClassifier` | same constructor | Experimental in this version. |

The classes are present, but the current `fit` methods call the base training routine before assigning `loss` and `loss_grad`. A straightforward `fit` can fail with a `NoneType` loss-gradient error. If a user specifically needs factorization machines, inspect or patch that initialization order before promising a working training recipe.
