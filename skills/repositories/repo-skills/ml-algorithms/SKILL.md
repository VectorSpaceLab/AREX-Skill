---
name: ml-algorithms
description: "Use this skill for MLAlgorithms (`mla`) educational
  machine-learning implementations: classical estimators, clustering/reduction,
  metrics, NeuralNet building blocks, and DQN examples."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MLAlgorithms Repo Skill

Use this skill when a task asks about the `rushter/MLAlgorithms` package, the `mla` Python distribution, or its minimal NumPy/SciPy/autograd implementations of common machine-learning algorithms. The package is educational rather than production-optimized: favor small examples, explicit NumPy arrays, deterministic seeds, and direct metric checks.

## First checks

- Install the package and its scientific Python dependencies in an isolated environment. The public distribution name is `mla`.
- Confirm the package imports:

  ```bash
  python - <<'PY'
  import mla
  from mla.linear_models import LinearRegression
  from mla.kmeans import KMeans
  from mla.neuralnet import NeuralNet
  print("mla import ok")
  PY
  ```

- Run `scripts/run_import_smoke.py --json` from this skill directory to inspect package imports, dependency versions, important signatures, and compatibility warnings without training, plotting, downloading, or reading original examples.
- Read `references/repo-provenance.md` before deciding whether this skill is current for a checkout or should be refreshed.

## Route by user goal

- **Classical supervised estimators**: use `sub-skills/classical-estimators/SKILL.md` for linear/logistic regression, KNN, Naive Bayes, SVM kernels, random forests, gradient boosting, and experimental factorization machines.
- **Unsupervised and reduction workflows**: use `sub-skills/unsupervised-and-reduction/SKILL.md` for KMeans, GaussianMixture, PCA, t-SNE, RBM, demo dataset loaders, distances, and no-display clustering/reduction checks.
- **Neural network building blocks**: use `sub-skills/neural-network-building-blocks/SKILL.md` for `NeuralNet`, layers, activations, initializers, constraints, regularizers, optimizers, CNN/RNN/LSTM recipes, and DQN wiring.

## Common decisions

- **Package name**: install/query distribution `mla`; import package `mla`.
- **No CLIs**: the project exposes Python APIs and example modules, not console entry points. Use bundled skill scripts for safe checks.
- **Backend**: selected workflows are CPU-only. A visible GPU is not required for this package.
- **Compatibility**: the current dataset text loader uses deprecated `np.bool`; prefer NumPy `<1.24` or patch the loader before using `load_nietzsche()` with modern NumPy. The DQN loop expects legacy Gym reset/step signatures, so do not assume Gymnasium compatibility.
- **Shapes**: most estimators expect 2D feature arrays. Neural layers use explicit 2D dense, 3D sequence, or 4D image tensors.
- **Plots and long examples**: repo examples include plotting, MNIST ConvNet, RNN text generation, and CartPole DQN training. Treat those as reference workflows unless the user explicitly authorizes longer runs or display side effects.

## Root references

- `references/api-reference.md`: package-wide imports, metrics, datasets, dependency facts, and public API index.
- `references/workflows.md`: how to select and combine the sub-skills for common tasks.
- `references/troubleshooting.md`: cross-cutting install/import, dependency, data-loader, plotting, and runtime problems.
- `references/repo-provenance.md`: source snapshot and refresh triggers.
- `references/repo-routing-metadata.json`: structured metadata for the managed repo-skills router.

## Bundled helpers

- `scripts/run_import_smoke.py`: safe package/dependency/signature check for the active Python environment.
- `sub-skills/classical-estimators/scripts/run_classical_smoke.py`: small supervised estimator checks.
- `sub-skills/unsupervised-and-reduction/scripts/run_unsupervised_smoke.py`: small clustering/reduction/RBM checks.
- `sub-skills/neural-network-building-blocks/scripts/run_neural_smoke.py`: small dense/RBM/DQN-wiring checks.

## Minimal examples

Classical estimator:

```python
from mla.linear_models import LogisticRegression

model = LogisticRegression(lr=0.01, max_iters=300)
model.fit(X_train, y_train)
proba = model.predict(X_test)
labels = (proba >= 0.5).astype(int)
```

Unsupervised estimator:

```python
from mla.kmeans import KMeans

model = KMeans(K=3, init="++", max_iters=50)
model.fit(X)
labels = model.predict()
```

Neural model:

```python
from mla.neuralnet import NeuralNet
from mla.neuralnet.layers import Dense, Activation
from mla.neuralnet.optimizers import Adam

model = NeuralNet([Dense(16), Activation("relu"), Dense(1)], Adam(), loss="mse", max_epochs=5)
```
