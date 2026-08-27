---
name: classical-estimators
description: "Use this sub-skill for MLAlgorithms supervised tabular estimators:
  linear/logistic regression, KNN, Naive Bayes, SVM kernels, random forests,
  gradient boosting, and experimental factorization machines."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Classical Estimators

Use this sub-skill when a task asks for MLAlgorithms' CPU-only supervised learning APIs, estimator selection, fit/predict examples, or debugging for tabular models. The package exposes scikit-learn-like classes but is intentionally minimal and educational; prefer explicit NumPy arrays, small datasets, and direct metric checks.

## Route elsewhere

- Clustering, Gaussian mixtures, PCA, t-SNE, RBM, and package demo dataset loaders belong in `../unsupervised-and-reduction/SKILL.md`.
- The custom `NeuralNet` stack, MLP/CNN/RNN/LSTM recipes, optimizers, activations, and DQN belong in `../neural-network-building-blocks/SKILL.md`.
- Repo-wide install/import checks, package compatibility, provenance, and cross-cutting metrics are summarized in the root skill.

## Start here

1. Confirm the environment imports the package and scientific stack:

   ```bash
   python - <<'PY'
   import mla, numpy, scipy, sklearn, autograd
   from mla.linear_models import LinearRegression, LogisticRegression
   print("mla import ok")
   PY
   ```

2. Pick the estimator family from the data and output shape:
   - Continuous targets: `LinearRegression`, `KNNRegressor`, `RandomForestRegressor`, `GradientBoostingRegressor`; treat `FMRegressor` as experimental in this version.
   - Binary class labels `{0, 1}`: `LogisticRegression`, `NaiveBayesClassifier`, tree/boosting classifiers, KNN.
   - SVM: convert labels to `{-1, 1}` before fitting.
3. Convert inputs to NumPy arrays before calling `fit`. The shared `BaseEstimator` converts array-like inputs, but explicit arrays make shapes and dtype errors easier to diagnose.
4. After `fit`, call `predict(X_test)` and validate with `mla.metrics` or an external metric such as `sklearn.metrics.roc_auc_score`.
5. For a deterministic smoke check, run `scripts/run_classical_smoke.py` from this sub-skill. It uses small synthetic datasets and does not read original repository examples.

## Primary workflows

### Linear and logistic regression

Use `mla.linear_models.LinearRegression` for continuous targets and `LogisticRegression` for binary probabilities. Both use gradient descent, so `lr`, `max_iters`, `tolerance`, `penalty`, and `C` directly affect convergence.

```python
import numpy as np
from mla.linear_models import LogisticRegression
from mla.metrics.metrics import accuracy

X = np.asarray([[0.0], [0.2], [1.0], [1.2]])
y = np.asarray([0, 0, 1, 1])
model = LogisticRegression(lr=0.01, max_iters=200, penalty="l1", C=0.01)
model.fit(X, y)
proba = model.predict(np.asarray([[0.1], [1.1]]))
labels = (proba >= 0.5).astype(int)
```

### K-nearest neighbors

Use `KNNClassifier` or `KNNRegressor` for simple instance-based baselines. The default distance function is `scipy.spatial.distance.euclidean`; pass another two-argument distance callable when needed. Set `k=0` to use all training examples.

### Naive Bayes

`NaiveBayesClassifier` implements Gaussian Naive Bayes for binary labels exactly `[0, 1]`. It returns normalized class-probability rows. Avoid constant-variance features unless you add preprocessing, because the Gaussian PDF divides by per-class variance.

### SVM kernels

Import kernels from the repository's real module spelling, `mla.svm.kernerls`:

```python
from mla.svm.svm import SVM
from mla.svm.kernerls import Linear, Poly, RBF

signed_y = (binary_y * 2) - 1
model = SVM(C=0.6, kernel=RBF(gamma=0.05), max_iter=200)
model.fit(X_train, signed_y)
pred = model.predict(X_test)
```

### Tree ensembles and boosting

Use `RandomForestClassifier`/`Regressor` for bagged decision trees and `GradientBoostingClassifier`/`Regressor` for additive trees. Keep `max_features` less than the number of columns when you pass it explicitly.

### Factorization machines

`FMRegressor` and `FMClassifier` exist in the package and expose the `BaseFM` constructor, but the current source initializes loss functions after the base training call. Treat these classes as experimental and verify a focused smoke before relying on `fit`.

## Bundled references and helpers

- Read `references/api-reference.md` for import paths, signatures, outputs, and version-specific caveats.
- Read `references/workflows.md` for supervised recipes and model-family selection guidance.
- Read `references/troubleshooting.md` when fitting fails, scores are unstable, labels have the wrong encoding, or dependency versions drift.
- Run `scripts/run_classical_smoke.py --workflow all` to test a small installed-package baseline without original examples or downloads.
