# MLAlgorithms package API reference

## Purpose

Read this for repo-wide import paths, package metadata, metrics, utilities, and route-level API ownership. For estimator-specific signatures, read the owning sub-skill reference.

## Package identity

- Distribution name: `mla`
- Import package: `mla`
- Verified package version during skill generation: `0.0.1`
- Public purpose: minimal educational implementations of machine-learning algorithms using NumPy, SciPy, autograd, and scikit-learn-style example data.
- Console entry points: none found in package metadata. Use Python APIs and bundled skill scripts.

## Dependency surface

The runtime requirements file lists `tqdm`, `matplotlib`, `numpy`, `scikit-learn`, `scipy`, `seaborn`, `autograd`, and `gym`. `pytest` is needed only for native test verification, not normal package use.

Compatibility notes:

- `mla.datasets.load_nietzsche()` uses `np.bool` in version `0.0.1`; NumPy below `1.24` avoids that error, or patch the source to use `bool`/`np.bool_`.
- `mla.rl.dqn.DQN` expects legacy Gym reset/step signatures; Gymnasium or newer Gym APIs need an adapter.

## Route-level API owners

| Capability | Imports | Owning sub-skill |
| --- | --- | --- |
| Linear/logistic regression | `mla.linear_models.LinearRegression`, `LogisticRegression` | `sub-skills/classical-estimators/` |
| KNN, Naive Bayes | `mla.knn`, `mla.naive_bayes.NaiveBayesClassifier` | `sub-skills/classical-estimators/` |
| SVM kernels | `mla.svm.svm.SVM`, `mla.svm.kernerls.Linear`, `Poly`, `RBF` | `sub-skills/classical-estimators/` |
| Random forests, gradient boosting | `mla.ensemble.random_forest`, `mla.ensemble.gbm` | `sub-skills/classical-estimators/` |
| Factorization machines | `mla.fm.FMRegressor`, `FMClassifier` | `sub-skills/classical-estimators/` |
| KMeans/GMM/PCA/t-SNE/RBM | `mla.kmeans`, `mla.gaussian_mixture`, `mla.pca`, `mla.tsne`, `mla.rbm` | `sub-skills/unsupervised-and-reduction/` |
| Dataset loaders | `mla.datasets.load_mnist`, `load_nietzsche` | `sub-skills/unsupervised-and-reduction/`, with neural references for CNN/RNN use |
| NeuralNet stack | `mla.neuralnet`, `mla.neuralnet.layers`, `mla.neuralnet.optimizers` | `sub-skills/neural-network-building-blocks/` |
| DQN | `mla.rl.dqn.DQN` | `sub-skills/neural-network-building-blocks/` |

## Metrics and validation helpers

```python
from mla.metrics.metrics import (
    absolute_error, classification_error, accuracy,
    mean_absolute_error, squared_error, squared_log_error,
    mean_squared_log_error, mean_squared_error,
    root_mean_squared_error, root_mean_squared_log_error,
    logloss, hinge, binary_crossentropy, get_metric,
)
from mla.metrics.base import check_data, validate_input
from mla.metrics.distance import euclidean_distance, l2_distance
```

Important behavior:

- `accuracy` and `classification_error` use the `unhot` decorator, so one-hot actual/predicted arrays are converted to class indices with `argmax(axis=1)`.
- `validate_input(function)` wraps a metric with `check_data`, converting inputs to NumPy arrays and requiring equal total size.
- `logloss` clips predicted probabilities with `EPS = 1e-15`.
- `get_metric(name)` looks up a metric by global function name and raises `ValueError("Invalid metric function.")` when missing.

## Utilities

```python
from mla.utils import one_hot, batch_iterator
```

- `one_hot(y)` creates an identity-matrix encoding using `np.max(y) + 1`; labels should be non-negative integers.
- `batch_iterator(X, batch_size=64)` yields consecutive array chunks and a final remainder chunk.

## Minimal import smoke

Use the root bundled helper when you need a safe environment check:

```bash
python scripts/run_import_smoke.py --json
```

The helper imports representative modules, reports key dependency versions, inspects constructor signatures, and warns about NumPy/Gym compatibility without running native examples.
