# API Reference

Use this reference when you need exact constructor defaults, which methods
mutate in place, or what learned attributes to inspect after fitting.

## Core estimator families

### Linear models

- `LinearRegression(fit_intercept=True)`
- `RidgeRegression(alpha=1, fit_intercept=True)`
- `LogisticRegression(penalty='l2', gamma=0, fit_intercept=True)`
- `GaussianNBClassifier(eps=1e-06)`
- `GeneralizedLinearModel(link, fit_intercept=True, tol=1e-05, max_iter=100)`
- Bayesian linear regression variants:
  - `BayesianLinearRegressionKnownVariance(...)`
  - `BayesianLinearRegressionUnknownVariance(...)`

### Tree and ensemble models

- `DecisionTree(classifier=True, max_depth=None, n_feats=None, criterion='entropy', seed=None)`
- `RandomForest(n_trees, max_depth, n_feats, classifier=True, criterion='entropy')`
- `GradientBoostedDecisionTree(n_iter, max_depth=None, classifier=True, learning_rate=1, loss='crossentropy', step_size='constant')`

### Nonparametric models

- `KNN(k=5, leaf_size=40, classifier=True, metric=None, weights='uniform')`
- `KernelRegression(kernel=None)`
- `GPRegression(kernel='RBFKernel', alpha=1e-10)`

### Factorization

- `VanillaALS(K, alpha=1, max_iter=200, tol=0.0001)`
- `NMF(K, max_iter=200, tol=0.0001)`

## Method conventions

- Most `fit(...)` methods mutate the object and return `None`.
- Prediction methods usually return NumPy arrays or Python lists of predictions.
- The exact attribute names differ by family; inspect the trained object rather
  than assuming scikit-learn conventions.

### Linear regression

- `fit(X, y, weights=None)` trains in place.
- `update(...)` exists on the incremental linear-regression implementation.
- Inspect trained coefficients via `beta`.

### Logistic / Gaussian NB / GLM

- `fit(X, y, ...)` trains in place.
- `predict(X)` returns class labels or responses.
- For logistic and GLM tasks, pass numeric arrays with the expected target shape.

### Trees

- `fit(X, y)` trains in place.
- `predict(X)` returns class labels or regressions depending on the classifier flag.
- Tree structure is stored on the estimator object; keep the model around for inspection.

### Nonparametric models

- `fit(X, y)` trains in place for KNN and GP regression.
- `predict(X)` returns the model output for the query array.
- For GP regression, `predict(X)` returns a tuple of mean and covariance-like output.

### Factorization

- `fit(X, ...)` mutates the model and stores factors in `W` and `H`.
- Inspect `parameters` to confirm factor shapes after fitting.

## Input/shape notes

- Use 2D arrays for sample-by-feature data unless the model explicitly accepts
  a different structure.
- For classifiers, label arrays should be consistent and not mixed types.
- For regression targets, keep dimensionality explicit (`(N, 1)` is often safer
  than a flat vector when examples show matrix targets).
- For nonparametric kernels or metrics, pass a callable or kernel object only
  when the constructor documentation says so.

## When to inspect source or tests

Read the source or repo tests only if you need an exact output contract for a
corner case, such as incremental updates, ensemble defaults, or comparison with
external libraries. The bundled smoke script is usually enough for day-to-day
use.
