---
name: unsupervised-and-reduction
description: "Use this sub-skill for MLAlgorithms clustering, Gaussian mixtures,
  PCA, t-SNE, RBM feature learning, metrics/distances, and packaged demo dataset
  loaders."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Unsupervised and Reduction

Use this sub-skill when a task asks for MLAlgorithms' unsupervised estimators, dimensionality reduction, small visualization-oriented workflows, RBM feature learning, or demo data loaders. These APIs are CPU-only educational implementations; keep workloads small and validate output shapes or assignments before scaling.

## Route elsewhere

- Supervised regression/classification, SVM kernels, random forests, gradient boosting, KNN supervised modes, and factorization machines belong in `../classical-estimators/SKILL.md`.
- The custom neural-network container, layer stack, optimizers, CNN/RNN/LSTM recipes, and DQN belong in `../neural-network-building-blocks/SKILL.md`.
- Cross-cutting installation, provenance, and route selection are in the root skill.

## Start here

1. Confirm the public imports you need:

   ```python
   from mla.kmeans import KMeans
   from mla.gaussian_mixture import GaussianMixture
   from mla.pca import PCA
   from mla.tsne import TSNE
   from mla.rbm import RBM
   from mla.datasets import load_mnist, load_nietzsche
   ```

2. Choose the workflow:
   - Cluster assignments: `KMeans(K=..., init="random"|"++")`.
   - Soft density-style clusters: `GaussianMixture(K=..., init="random"|"kmeans")`.
   - Linear reduction for downstream models: `PCA(n_components, solver="svd"|"eigen")`.
   - 2D nonlinear visualization: `TSNE(n_components=2, perplexity=..., max_iter=...)`.
   - Binary/continuous unsupervised features: `RBM(n_hidden=..., max_epochs=...)`.
3. Avoid plotting in headless or automated runs; inspect returned labels, component shapes, likelihoods, embeddings, or errors instead.
4. Run `scripts/run_unsupervised_smoke.py --workflow all` for a safe no-display check.

## Common workflows

### KMeans clustering

```python
from sklearn.datasets import make_blobs
from mla.kmeans import KMeans

X, _ = make_blobs(n_samples=120, centers=3, n_features=2, random_state=42)
model = KMeans(K=3, max_iters=50, init="++")
model.fit(X)
labels = model.predict()     # labels for the fitted training data
centroids = model.centroids
```

Call `fit(X)` before `predict()`. `KMeans.predict()` without an argument returns assignments for the stored training data because the class overrides `_predict` around `self.X`.

### Gaussian mixture model

```python
from mla.gaussian_mixture import GaussianMixture

model = GaussianMixture(K=3, init="kmeans", max_iters=50, tolerance=1e-3)
model.fit(X)
assignments = model.predict(X)
```

GMM uses full covariance matrices and SciPy's `multivariate_normal.pdf`. Tiny or duplicate clusters can produce singular-covariance failures; increase samples, reduce `K`, or add slight jitter.

### PCA reduction

```python
from mla.pca import PCA

pca = PCA(n_components=2, solver="svd")
pca.fit(X_train)
X_train_2d = pca.transform(X_train)
X_test_2d = pca.transform(X_test)
```

Fit PCA on training data only, then transform held-out data with the learned mean and components.

### t-SNE embedding

```python
from mla.tsne import TSNE

embedding = TSNE(n_components=2, perplexity=10.0, max_iter=250, learning_rate=200).fit_transform(X)
```

Use t-SNE for visualization-style embeddings rather than predictive features. Keep sample counts small; this implementation uses dense pairwise distances and a Python loop.

### RBM feature learning

```python
import numpy as np
from mla.rbm import RBM

X = np.random.RandomState(0).uniform(0, 1, (100, 8))
rbm = RBM(n_hidden=4, learning_rate=0.05, batch_size=10, max_epochs=5)
rbm.fit(X)
features = rbm.predict(X)
```

RBM stores per-epoch reconstruction errors in `rbm.errors`.

### Demo dataset loaders

`load_mnist()` returns `(X_train, X_test, y_train, y_test)` with image arrays shaped for the ConvNet example. `load_nietzsche()` creates one-hot text sequences for recurrent examples. Both read package data shipped with the distribution; do not copy those datasets into generated skills. With modern NumPy, `load_nietzsche()` may need `numpy<1.24` or a source patch because it uses deprecated `np.bool`.

## Bundled references and helpers

- Read `references/api-reference.md` for import paths, signatures, state attributes, and outputs.
- Read `references/workflows.md` for cluster/reduction/RBM recipes and validation ideas.
- Read `references/troubleshooting.md` for singular covariance, plotting, data-loader, t-SNE runtime, and NumPy compatibility issues.
- Run `scripts/run_unsupervised_smoke.py --workflow all` to exercise small no-display checks against an installed `mla` package.
